"""PawCare — knowledge base ingestion pipeline (batch 1).

Task: P1-RAG-003. Trace: docs/design/rag-ingestion-pipeline-design.md §7 steps 1–4.

Takes the raw corpus in ``data/knowledge_base/raw/`` and produces the batch-1
artifacts in ``data/knowledge_base/batch1/``:

* ``documents.jsonl`` — one normalized document per line;
* ``chunks.jsonl`` — one retrievable, citable chunk per line;
* ``manifest.json`` — run summary (counts, chunking parameters, source list).

Steps 5–7 of the design (embedding, pgvector indexing, retrieval smoke test) are
deliberately out of scope here — that is P1-RAG-004. This module never imports a
database or an embedding model.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from app.services.knowledge_base import chunking
from app.services.knowledge_base.chunking import SectionChunk
from app.services.knowledge_base.loader import RawDocument, load_raw_document
from app.services.knowledge_base.source_registry import SourceRecord, require_cleared
from app.services.knowledge_base.types import Chunk, Document

# D:\\PawCare\\apps\\backend\\app\\services\\knowledge_base\\pipeline.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "knowledge_base" / "raw"
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "knowledge_base" / "batch1"

_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://pawcare.local/knowledge-base")

# Section-heading keyword -> body system, used to give each chunk a tighter
# filter value than the document's broad tag set (design §4.1).
_BODY_SYSTEM_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("respirat", "respiratory"),
    ("breath", "respiratory"),
    ("dyspnea", "respiratory"),
    ("pneum", "respiratory"),
    ("airway", "respiratory"),
    ("seizure", "neurologic"),
    ("neurolog", "neurologic"),
    ("brain", "neurologic"),
    ("neuro", "neurologic"),
    ("hemorr", "hematologic"),
    ("bleed", "hematologic"),
    ("coagul", "hematologic"),
    ("blood", "hematologic"),
    ("gastr", "gastrointestinal"),
    ("vomit", "gastrointestinal"),
    ("abdomen", "gastrointestinal"),
    ("intestin", "gastrointestinal"),
    ("urin", "urinary"),
    ("renal", "urinary"),
    ("kidney", "urinary"),
    ("bladder", "urinary"),
    ("heat", "environmental"),
    ("hypertherm", "environmental"),
    ("trauma", "trauma"),
    ("fractur", "trauma"),
    ("wound", "trauma"),
    ("toxic", "toxicology"),
    ("poison", "toxicology"),
    ("cardiac", "cardiovascular"),
    ("cardio", "cardiovascular"),
    ("shock", "cardiovascular"),
)


class IngestionError(ValueError):
    """Raised when the raw corpus cannot be ingested as-is."""


def _normalize_body(body: str) -> str:
    """Collapse excessive blank lines and trailing whitespace, keep headings."""
    lines = [line.rstrip() for line in body.splitlines()]
    normalized: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            blank_run = 0
            normalized.append(line)
        else:
            blank_run += 1
            if blank_run <= 1:
                normalized.append("")
    return "\n".join(normalized).strip()


def _year(published_at: object) -> str:
    text = str(published_at) if published_at else ""
    return text[:4] if len(text) >= 4 and text[:4].isdigit() else "n.d."


def _infer_body_system(heading: str | None, doc_tags: list[str]) -> str | None:
    if heading:
        lowered = heading.lower()
        for keyword, system in _BODY_SYSTEM_KEYWORDS:
            if keyword in lowered:
                return system
    return doc_tags[0] if doc_tags else None


def _document_id(source_id: str) -> str:
    return str(uuid.uuid5(_ID_NAMESPACE, f"document:{source_id}"))


def _chunk_id(document_id: str, index: int) -> str:
    return str(uuid.uuid5(_ID_NAMESPACE, f"chunk:{document_id}:{index}"))


def build_document(raw: RawDocument, source: SourceRecord) -> Document:
    """Validate + normalize one raw document and chunk it.

    Raises :class:`~app.services.knowledge_base.source_registry.LicenseError` via
    ``require_cleared`` if the source is not licensed for ingestion.
    """
    source_id = str(raw.require("source_id"))
    if source_id != source.source_id:
        raise IngestionError(
            f"{raw.path.name}: front matter source_id {source_id!r} does not match "
            f"the requested source {source.source_id!r}"
        )

    body = _normalize_body(raw.body)
    if not body:
        raise IngestionError(f"{raw.path.name}: empty document body")

    document_id = _document_id(source_id)
    retrieved_at = str(raw.require("retrieved_at"))
    published_at = raw.metadata.get("published_date")
    author = raw.metadata.get("author") or None
    symptom_tags = [str(t) for t in raw.metadata.get("symptom_tags", [])]
    condition_tags = [str(t) for t in raw.metadata.get("condition_tags", [])]
    is_red_flag_relevant = bool(raw.metadata.get("is_red_flag_relevant", False))

    species = list(source.species_applicability)
    body_system_tags = list(source.body_system_tags)
    citation_text = f"{source.publisher}, {_year(published_at)}"

    try:
        source_text_path = raw.path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        source_text_path = raw.path.as_posix()

    document = Document(
        document_id=document_id,
        source_id=source_id,
        title=source.title,
        source=source.publisher,
        source_url=source.source_url,
        license=source.license,
        license_url=source.license_url,
        author=author,
        published_at=str(published_at) if published_at else None,
        retrieved_at=retrieved_at,
        species_applicability=species,
        body_system_tags=body_system_tags,
        content_type=source.content_type,
        status=source.status,
        notes=source.notes,
        source_text_path=source_text_path,
    )

    section_chunks: list[SectionChunk] = chunking.chunk_document(body)
    for index, section_chunk in enumerate(section_chunks):
        text = section_chunk.text
        document.chunks.append(
            Chunk(
                chunk_id=_chunk_id(document_id, index),
                document_id=document_id,
                chunk_index=index,
                chunk_text=text,
                section_heading=section_chunk.section_heading,
                token_count=chunking.count_tokens(text),
                word_count=chunking.count_words(text),
                source_id=source_id,
                source_title=source.title,
                source_url=source.source_url,
                author=author,
                license=source.license,
                species_applicability=species,
                body_system=_infer_body_system(section_chunk.section_heading, body_system_tags),
                symptom_tags=symptom_tags,
                condition_tags=condition_tags,
                published_date=str(published_at) if published_at else None,
                retrieved_date=retrieved_at,
                citation_text=citation_text,
                is_red_flag_relevant=is_red_flag_relevant,
            )
        )
    return document


def ingest_file(path: str | Path) -> Document:
    """Load one raw file, gate its license, and build its chunked document."""
    raw = load_raw_document(path)
    source_id = str(raw.require("source_id"))
    source = require_cleared(source_id)
    return build_document(raw, source)


def ingest_directory(raw_dir: str | Path = DEFAULT_RAW_DIR) -> list[Document]:
    """Ingest every ``*.md`` file in ``raw_dir``, in stable filename order."""
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir():
        raise IngestionError(f"raw directory not found: {raw_dir}")
    paths = sorted(raw_dir.glob("*.md"))
    if not paths:
        raise IngestionError(f"no raw .md documents found in {raw_dir}")
    return [ingest_file(path) for path in paths]


def write_artifacts(
    documents: Iterable[Document],
    out_dir: str | Path = DEFAULT_OUT_DIR,
) -> dict:
    """Write documents.jsonl, chunks.jsonl and manifest.json; return the manifest."""
    documents = list(documents)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_chunks: list[Chunk] = [chunk for doc in documents for chunk in doc.chunks]

    _write_jsonl(out_dir / "documents.jsonl", (doc.to_dict() for doc in documents))
    _write_jsonl(out_dir / "chunks.jsonl", (chunk.to_dict() for chunk in all_chunks))

    total_tokens = sum(chunk.token_count for chunk in all_chunks)
    manifest = {
        "task": "P1-RAG-003",
        "artifact_schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "chunking": {
            "target_min_tokens": chunking.TARGET_MIN_TOKENS,
            "target_max_tokens": chunking.TARGET_MAX_TOKENS,
            "overlap_tokens": chunking.OVERLAP_TOKENS,
            "small_paragraph_tokens": chunking.SMALL_PARAGRAPH_TOKENS,
            "large_paragraph_tokens": chunking.LARGE_PARAGRAPH_TOKENS,
            "tokenizer": "approx-word+punctuation",
        },
        "document_count": len(documents),
        "chunk_count": len(all_chunks),
        "total_tokens": total_tokens,
        "avg_chunk_tokens": round(total_tokens / len(all_chunks), 1) if all_chunks else 0,
        "sources": [
            {
                "source_id": doc.source_id,
                "title": doc.title,
                "license": doc.license,
                "species_applicability": doc.species_applicability,
                "chunk_count": len(doc.chunks),
            }
            for doc in documents
        ],
        "artifacts": {
            "documents": "documents.jsonl",
            "chunks": "chunks.jsonl",
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(raw_dir: str | Path = DEFAULT_RAW_DIR, out_dir: str | Path = DEFAULT_OUT_DIR) -> dict:
    """End-to-end: ingest the raw corpus and write batch-1 artifacts."""
    documents = ingest_directory(raw_dir)
    return write_artifacts(documents, out_dir)
