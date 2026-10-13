"""PawCare — KnowledgeDocument ORM model.

Task: P1-RAG-004. Trace: requirements.md §5–§6, FR-07, FR-12,
docs/design/models/knowledge_document.py.

One row per ingested source document (batch 1 = `data/knowledge_base/raw/*.md`).
It carries the licensing provenance (`license`, `source_url`, `author`) that
FR-07 requires to be traceable from every answer back to its source. The
license is never blank: the ingestion pipeline (`P1-RAG-003`) refuses any
document whose source is not registered as cleared.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.chunk import Chunk


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    license: Mapped[str] = mapped_column(String(200), nullable=False)
    license_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    retrieved_at: Mapped[str | None] = mapped_column(String(10), nullable=True)
    species_applicability: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    body_system_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_text_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
