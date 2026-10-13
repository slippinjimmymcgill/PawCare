"""PawCare — embedding + indexing pipeline and retrieval for the knowledge base.

Task: P1-RAG-004. Trace: docs/design/rag-ingestion-pipeline-design.md §7
(steps 5–7: embedding, indexing, retrieval smoke test), requirements.md §6.

Consumes the P1-RAG-003 artifacts (`data/knowledge_base/batch1/*.jsonl`):

1. upserts one :class:`~app.models.knowledge_document.KnowledgeDocument` per source;
2. embeds each chunk and stores the vector + provenance on
   :class:`~app.models.chunk.Chunk`;
3. exposes :func:`semantic_search` for the retrieval smoke test — top-k cosine
   ranking plus the hard filters the design calls for (species, body system,
   red-flag relevance).

Retrieval here is a portable in-Python cosine scan over the filtered rows. On
PostgreSQL the same column is a native pgvector `vector` with an HNSW index
(see the ``knowledge_base_tables`` migration), so P2-RAG-001 can move the scan
into SQL without a schema change; this function deliberately stays
dialect-agnostic so it works on SQLite and on Postgres-without-pgvector alike.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.core.config import get_settings
from app.db.types import DEFAULT_EMBEDDING_DIM
from app.models.chunk import Chunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.knowledge_base.embeddings import (
    EmbeddingError,
    EmbeddingProvider,
    build_embedding_provider,
    cosine_similarity,
)
from app.services.knowledge_base.pipeline import DEFAULT_OUT_DIR

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class IndexingError(RuntimeError):
    """Raised when the batch artifacts or provider cannot be indexed."""


@dataclass
class IndexReport:
    batch_dir: str
    provider: str
    dim: int
    documents_indexed: int
    chunks_embedded: int
    chunks_reused: int

    @property
    def chunks_total(self) -> int:
        return self.chunks_embedded + self.chunks_reused


@dataclass
class SearchHit:
    chunk: Chunk
    score: float


def load_batch_artifacts(batch_dir: str | Path = DEFAULT_OUT_DIR) -> tuple[list[dict], list[dict]]:
    """Read ``documents.jsonl`` and ``chunks.jsonl`` from a batch directory."""
    batch_dir = Path(batch_dir)
    documents_path = batch_dir / "documents.jsonl"
    chunks_path = batch_dir / "chunks.jsonl"
    if not documents_path.is_file() or not chunks_path.is_file():
        raise IndexingError(
            f"{batch_dir} does not contain documents.jsonl and chunks.jsonl; "
            "run `python scripts/ingest_knowledge_base.py` first"
        )
    documents = _read_jsonl(documents_path)
    chunks = _read_jsonl(chunks_path)
    return documents, chunks


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _upsert_document(db: Session, data: dict) -> KnowledgeDocument:
    document = db.get(KnowledgeDocument, data["document_id"])
    if document is None:
        document = KnowledgeDocument(id=data["document_id"])
        db.add(document)
    document.source_id = data["source_id"]
    document.title = data["title"]
    document.source = data["source"]
    document.source_url = data["source_url"]
    document.license = data["license"]
    document.license_url = data.get("license_url")
    document.author = data.get("author")
    document.published_date = data.get("published_at")
    document.retrieved_at = data.get("retrieved_at")
    document.species_applicability = list(data.get("species_applicability", []))
    document.body_system_tags = list(data.get("body_system_tags", []))
    document.content_type = data["content_type"]
    document.status = data["status"]
    document.notes = data.get("notes")
    document.source_text_path = data.get("source_text_path")
    return document


def _build_chunk(data: dict) -> Chunk:
    metadata = {key: value for key, value in data.items() if key != "chunk_text"}
    return Chunk(
        id=data["chunk_id"],
        document_id=data["document_id"],
        chunk_index=data["chunk_index"],
        chunk_text=data["chunk_text"],
        section_heading=data.get("section_heading"),
        token_count=data["token_count"],
        word_count=data["word_count"],
        source_id=data["source_id"],
        source_title=data["source_title"],
        source_url=data["source_url"],
        author=data.get("author"),
        license=data["license"],
        citation_text=data["citation_text"],
        published_date=data.get("published_date"),
        retrieved_date=data["retrieved_date"],
        species_applicability=list(data.get("species_applicability", [])),
        body_system=data.get("body_system"),
        symptom_tags=list(data.get("symptom_tags", [])),
        condition_tags=list(data.get("condition_tags", [])),
        is_red_flag_relevant=bool(data.get("is_red_flag_relevant", False)),
        metadata_json=metadata,
    )


def index_batch(
    db: Session,
    batch_dir: str | Path = DEFAULT_OUT_DIR,
    provider: EmbeddingProvider | None = None,
    *,
    force: bool = False,
) -> IndexReport:
    """Embed and persist a batch's documents + chunks. Idempotent unless ``force``.

    Chunk ids are deterministic (P1-RAG-003), so a re-run updates rows in place.
    A chunk is re-embedded only when it has no vector, when its recorded
    ``embedding_model`` differs from the current provider, or when ``force``.
    """
    settings = get_settings()
    if provider is None:
        provider = build_embedding_provider(settings)
    if provider.dim != DEFAULT_EMBEDDING_DIM:
        raise IndexingError(
            f"provider {provider.name!r} produces {provider.dim}-dim vectors but the "
            f"`chunks.embedding` column is vector({DEFAULT_EMBEDDING_DIM}); "
            "change one to match (and migrate) before indexing"
        )

    documents, chunk_rows = load_batch_artifacts(batch_dir)
    for data in documents:
        _upsert_document(db, data)
    db.flush()

    existing = {
        chunk.id: chunk
        for chunk in db.execute(
            select(Chunk).where(Chunk.id.in_([row["chunk_id"] for row in chunk_rows]))
        ).scalars()
    }

    embedded = 0
    reused = 0
    pending: list[tuple[Chunk, str]] = []
    for data in chunk_rows:
        chunk = existing.get(data["chunk_id"]) or _build_chunk(data)
        if data["chunk_id"] not in existing:
            db.add(chunk)
        needs_embedding = (
            force
            or chunk.embedding is None
            or chunk.embedding_model != provider.name
        )
        if needs_embedding:
            pending.append((chunk, data["chunk_text"]))
        else:
            reused += 1

    now = datetime.now(UTC)
    batch_size = max(1, settings.EMBEDDING_BATCH_SIZE)
    for start in range(0, len(pending), batch_size):
        slice_ = pending[start : start + batch_size]
        vectors = provider.embed([text for _, text in slice_])
        if len(vectors) != len(slice_):
            raise IndexingError(
                f"provider {provider.name!r} returned {len(vectors)} vectors for "
                f"{len(slice_)} inputs"
            )
        for (chunk, _), vector in zip(slice_, vectors, strict=True):
            chunk.embedding = vector
            chunk.embedding_model = provider.name
            chunk.embedding_dim = provider.dim
            chunk.indexed_at = now
            embedded += 1

    db.commit()
    return IndexReport(
        batch_dir=str(Path(batch_dir)),
        provider=provider.name,
        dim=provider.dim,
        documents_indexed=len(documents),
        chunks_embedded=embedded,
        chunks_reused=reused,
    )


def semantic_search(
    db: Session,
    query: str,
    provider: EmbeddingProvider,
    *,
    top_k: int = 5,
    species: str | None = None,
    body_system: str | None = None,
    red_flag_only: bool = False,
) -> list[SearchHit]:
    """Top-k cosine search with the design's hard filters (species/body system).

    Returns citation-ready chunks — every hit carries source, license and
    ``citation_text`` (FR-07), so a caller never renders an anonymous source.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    statement = select(Chunk).where(Chunk.embedding.is_not(None))
    if body_system is not None:
        statement = statement.where(Chunk.body_system == body_system)
    if red_flag_only:
        statement = statement.where(Chunk.is_red_flag_relevant.is_(True))

    candidates = list(db.execute(statement).scalars())
    if species is not None:
        candidates = [
            chunk for chunk in candidates if species in (chunk.species_applicability or [])
        ]

    query_vector = provider.embed([query])[0]
    scored = [
        SearchHit(chunk=chunk, score=cosine_similarity(query_vector, chunk.embedding))
        for chunk in candidates
        if chunk.embedding
    ]
    scored.sort(key=lambda hit: hit.score, reverse=True)
    return scored[:top_k]


__all__ = [
    "EmbeddingError",
    "IndexReport",
    "IndexingError",
    "SearchHit",
    "index_batch",
    "load_batch_artifacts",
    "semantic_search",
]
