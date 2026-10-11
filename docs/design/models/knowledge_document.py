"""
PawCare — KnowledgeDocument model. Trace: requirements.md §5–§6, specs.md §8.

`license` is not optional and not free text in practice — it should be
populated from the licensing tracking sheet started in P0-RAG-002 /
P1-RAG-001. A document with no recorded license should not be ingestable
(enforce at the ingestion-pipeline level, P1-RAG-003, not just here).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .chunk import Chunk


class KnowledgeDocument(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    license: Mapped[str] = mapped_column(String(120), nullable=False)

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
