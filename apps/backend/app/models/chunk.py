"""PawCare — Chunk ORM model.

Task: P1-RAG-004. Trace: requirements.md §5–§6, FR-07,
docs/design/models/chunk.py, docs/design/rag-ingestion-pipeline-design.md §4.

One row per retrievable, citable chunk produced by `P1-RAG-003`. The scalar
columns duplicate the fields FR-07 needs for a visible citation (source, license,
author, citation label) so retrieval never has to join back to the document just
to render a source. The filter columns called out in the design's §4.1
(`body_system`, `is_red_flag_relevant`, and the JSON `species_applicability`)
are what P2-RAG-001's retrieval will filter on.

`embedding` is the dialect-sensitive `Vector` type (pgvector on Postgres). The
`embedding_model` / `embedding_dim` columns record which provider produced the
vector so a model swap can be detected without guessing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import DEFAULT_EMBEDDING_DIM, Vector

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Denormalized citation fields (FR-07) — no join needed to show a source.
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license: Mapped[str] = mapped_column(String(200), nullable=False)
    citation_text: Mapped[str] = mapped_column(String(500), nullable=False)
    published_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    retrieved_date: Mapped[str] = mapped_column(String(10), nullable=False)

    # Filter columns (design §4.1).
    species_applicability: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    body_system: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    symptom_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    condition_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_red_flag_relevant: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # Full metadata contract, kept verbatim for forward-compatibility.
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Vector (pgvector on Postgres; JSON elsewhere) + provenance.
    embedding: Mapped[list | None] = mapped_column(
        Vector(DEFAULT_EMBEDDING_DIM), nullable=True
    )
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    embedding_dim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")
