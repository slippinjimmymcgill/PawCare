"""knowledge_base_tables

Task: P1-RAG-004.

Creates the ``knowledge_documents`` and ``chunks`` tables for the retrieval
knowledge base.

On PostgreSQL this also enables the ``pgvector`` extension, creates the
``chunks.embedding`` column as a native ``vector(384)`` and adds an HNSW index
for cosine ANN search. On every other dialect (SQLite tests, Postgres without
the extension) the ``embedding`` column degrades to JSON via
``app.db.types.Vector``.

Revision ID: c4a1f0b2d3e5
Revises: 8dc0a941e766
Create Date: 2026-10-13 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op
from app.db.types import DEFAULT_EMBEDDING_DIM, Vector

# revision identifiers, used by Alembic.
revision = "c4a1f0b2d3e5"
down_revision = "8dc0a941e766"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    is_postgres = _is_postgres()
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=500), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("license", sa.String(length=200), nullable=False),
        sa.Column("license_url", sa.String(length=1000), nullable=True),
        sa.Column("author", sa.String(length=500), nullable=True),
        sa.Column("published_date", sa.String(length=10), nullable=True),
        sa.Column("retrieved_at", sa.String(length=10), nullable=True),
        sa.Column("species_applicability", sa.JSON(), nullable=False),
        sa.Column("body_system_tags", sa.JSON(), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_text_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_knowledge_documents_source_id", "knowledge_documents", ["source_id"]
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=36),
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("section_heading", sa.String(length=500), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("author", sa.String(length=500), nullable=True),
        sa.Column("license", sa.String(length=200), nullable=False),
        sa.Column("citation_text", sa.String(length=500), nullable=False),
        sa.Column("published_date", sa.String(length=10), nullable=True),
        sa.Column("retrieved_date", sa.String(length=10), nullable=False),
        sa.Column("species_applicability", sa.JSON(), nullable=False),
        sa.Column("body_system", sa.String(length=80), nullable=True),
        sa.Column("symptom_tags", sa.JSON(), nullable=False),
        sa.Column("condition_tags", sa.JSON(), nullable=False),
        sa.Column("is_red_flag_relevant", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("embedding", Vector(DEFAULT_EMBEDDING_DIM), nullable=True),
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
        sa.Column("embedding_dim", sa.Integer(), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("ix_chunks_source_id", "chunks", ["source_id"])
    op.create_index("ix_chunks_body_system", "chunks", ["body_system"])
    op.create_index("ix_chunks_is_red_flag_relevant", "chunks", ["is_red_flag_relevant"])

    if is_postgres:
        # Cosine-distance ANN index; P2-RAG-001's retrieval uses `<=>` on this.
        op.create_index(
            "ix_chunks_embedding_hnsw",
            "chunks",
            ["embedding"],
            unique=False,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        )


def downgrade() -> None:
    if _is_postgres():
        op.drop_index("ix_chunks_embedding_hnsw", table_name="chunks")
    op.drop_index("ix_chunks_is_red_flag_relevant", table_name="chunks")
    op.drop_index("ix_chunks_body_system", table_name="chunks")
    op.drop_index("ix_chunks_source_id", table_name="chunks")
    op.drop_index("ix_chunks_document_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("ix_knowledge_documents_source_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
