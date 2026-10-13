from __future__ import annotations

import json

import pytest
from sqlalchemy import JSON, create_engine, select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.types import DEFAULT_EMBEDDING_DIM, Vector
from app.models.chunk import Chunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.knowledge_base.embeddings import (
    EmbeddingError,
    HashingEmbeddingProvider,
    build_embedding_provider,
    cosine_similarity,
)
from app.services.knowledge_base.indexer import (
    IndexingError,
    index_batch,
    load_batch_artifacts,
    semantic_search,
)
from app.services.knowledge_base.pipeline import DEFAULT_OUT_DIR

HASHING_384 = HashingEmbeddingProvider(DEFAULT_EMBEDDING_DIM)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _count(db, model) -> int:
    return len(list(db.execute(select(model)).scalars()))


def _write_synthetic_batch(tmp_path, *, species=("dog",), red_flag=True):
    documents = [
        {
            "document_id": "doc-1",
            "source_id": "test-source",
            "title": "Synthetic Toxin Guide",
            "source": "Test Journal",
            "source_url": "https://example.org/toxin",
            "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "author": "A. Author",
            "published_at": "2024-01-01",
            "retrieved_at": "2026-10-01",
            "species_applicability": list(species),
            "body_system_tags": ["gastrointestinal"],
            "content_type": "review",
            "status": "active",
        }
    ]
    chunks = [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "chunk_text": "Xylitol ingestion in dogs causes a rapid insulin release and hypoglycemia.",
            "section_heading": "Toxins",
            "token_count": 12,
            "word_count": 10,
            "source_id": "test-source",
            "source_title": "Synthetic Toxin Guide",
            "source_url": "https://example.org/toxin",
            "author": "A. Author",
            "license": "CC BY 4.0",
            "citation_text": "Test Journal, 2024",
            "published_date": "2024-01-01",
            "retrieved_date": "2026-10-01",
            "species_applicability": list(species),
            "body_system": "gastrointestinal",
            "symptom_tags": ["vomiting"],
            "condition_tags": ["hypoglycemia"],
            "is_red_flag_relevant": red_flag,
        }
    ]
    (tmp_path / "documents.jsonl").write_text(
        "\n".join(json.dumps(row) for row in documents) + "\n", encoding="utf-8"
    )
    (tmp_path / "chunks.jsonl").write_text(
        "\n".join(json.dumps(row) for row in chunks) + "\n", encoding="utf-8"
    )
    return tmp_path


# ── Vector type ──────────────────────────────────────────────────────────────


def test_vector_maps_to_json_on_sqlite():
    impl = Vector(8).load_dialect_impl(sqlite.dialect())
    assert isinstance(impl, JSON)


def test_vector_maps_to_pgvector_on_postgres():
    pgvector = pytest.importorskip("pgvector.sqlalchemy")
    impl = Vector(8).load_dialect_impl(postgresql.dialect())
    assert isinstance(impl, pgvector.Vector)
    assert impl.dim == 8


def test_vector_roundtrips_floats_and_copies():
    column_type = Vector(3)
    assert column_type.copy().dim == 3
    assert column_type.process_bind_param([1, 2.5, 3], sqlite.dialect()) == [1.0, 2.5, 3.0]
    assert column_type.process_result_value([1, 2, 3], sqlite.dialect()) == [1.0, 2.0, 3.0]
    assert column_type.process_bind_param(None, sqlite.dialect()) is None
    assert "Vector(3)" in repr(column_type)


def test_models_registered_on_metadata():
    assert "knowledge_documents" in Base.metadata.tables
    assert "chunks" in Base.metadata.tables


# ── Embedding providers ──────────────────────────────────────────────────────


def test_hashing_provider_is_deterministic_and_normalized():
    provider = HashingEmbeddingProvider(16)
    first, second = provider.embed(["dog vomiting"])[0], provider.embed(["dog vomiting"])[0]
    assert first == second
    assert len(first) == 16
    norm = sum(component * component for component in first) ** 0.5
    assert norm == pytest.approx(1.0)


def test_hashing_provider_empty_text_is_zero_vector():
    vector = HashingEmbeddingProvider(8).embed([""])[0]
    assert vector == [0.0] * 8


def test_hashing_provider_rejects_bad_dim():
    with pytest.raises(ValueError):
        HashingEmbeddingProvider(0)


def test_cosine_similarity_bounds_and_errors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
    with pytest.raises(ValueError):
        cosine_similarity([1.0], [1.0, 2.0])


def test_build_embedding_provider_selects_by_settings():
    assert isinstance(
        build_embedding_provider(Settings(EMBEDDING_PROVIDER="hashing", EMBEDDING_DIM=32)),
        HashingEmbeddingProvider,
    )
    with pytest.raises(EmbeddingError):
        build_embedding_provider(Settings(EMBEDDING_PROVIDER="nonsense"))


def test_sentence_transformer_provider_errors_when_absent():
    pytest.importorskip("sentence_transformers", reason="optional extra not installed")
    # If installed, construction is exercised elsewhere; nothing to assert here.


# ── Indexing ─────────────────────────────────────────────────────────────────


def test_index_synthetic_batch_maps_fields(db, tmp_path):
    batch_dir = _write_synthetic_batch(tmp_path)
    report = index_batch(db, batch_dir, HASHING_384)

    assert report.documents_indexed == 1
    assert report.chunks_embedded == 1
    assert report.chunks_total == 1
    assert _count(db, KnowledgeDocument) == 1
    assert _count(db, Chunk) == 1

    chunk = db.get(Chunk, "chunk-1")
    assert chunk.embedding is not None and len(chunk.embedding) == DEFAULT_EMBEDDING_DIM
    assert chunk.embedding_model == "hashing"
    assert chunk.embedding_dim == DEFAULT_EMBEDDING_DIM
    assert chunk.citation_text == "Test Journal, 2024"
    assert chunk.is_red_flag_relevant is True
    assert chunk.metadata_json["citation_text"] == "Test Journal, 2024"
    assert "chunk_text" not in chunk.metadata_json


def test_index_batch_is_idempotent(db, tmp_path):
    batch_dir = _write_synthetic_batch(tmp_path)
    index_batch(db, batch_dir, HASHING_384)
    second = index_batch(db, batch_dir, HASHING_384)

    assert second.chunks_embedded == 0
    assert second.chunks_reused == 1
    assert _count(db, Chunk) == 1


def test_index_batch_force_reembeds(db, tmp_path):
    batch_dir = _write_synthetic_batch(tmp_path)
    index_batch(db, batch_dir, HASHING_384)
    forced = index_batch(db, batch_dir, HASHING_384, force=True)
    assert forced.chunks_embedded == 1
    assert forced.chunks_reused == 0


def test_index_batch_dim_mismatch_raises(db, tmp_path):
    batch_dir = _write_synthetic_batch(tmp_path)
    with pytest.raises(IndexingError):
        index_batch(db, batch_dir, HashingEmbeddingProvider(64))


def test_missing_batch_dir_raises(tmp_path):
    with pytest.raises(IndexingError):
        load_batch_artifacts(tmp_path / "does-not-exist")


# ── Retrieval / smoke test over the real batch-1 corpus ──────────────────────


def test_semantic_search_over_real_batch_finds_red_flag_and_cites(db):
    report = index_batch(db, DEFAULT_OUT_DIR, HASHING_384)
    assert report.documents_indexed == 9
    assert report.chunks_total == 266
    assert _count(db, Chunk) == 266

    hits = semantic_search(
        db, "dog ate chocolate xylitol", HASHING_384, top_k=3, species="dog", red_flag_only=True
    )
    assert hits
    assert hits[0].score >= hits[-1].score
    assert hits[0].chunk.citation_text
    assert "dog" in hits[0].chunk.species_applicability
    assert hits[0].chunk.is_red_flag_relevant is True


def test_semantic_search_filters_species_and_body_system(db):
    index_batch(db, DEFAULT_OUT_DIR, HASHING_384)
    cat_hits = semantic_search(db, "difficulty breathing", HASHING_384, species="cat", top_k=5)
    assert all("cat" in hit.chunk.species_applicability for hit in cat_hits)


def test_semantic_search_validates_arguments(db):
    index_batch(db, DEFAULT_OUT_DIR, HASHING_384)
    with pytest.raises(ValueError):
        semantic_search(db, "   ", HASHING_384)
    with pytest.raises(ValueError):
        semantic_search(db, "dog", HASHING_384, top_k=0)
