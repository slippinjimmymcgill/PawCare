"""
PawCare — Chunk model. Trace: requirements.md §4 (RAG Recall@5), §5, §6.

The `embedding` column assumes pgvector is viable on the chosen hosting
provider — that is exactly what P1-BE-002 is tasked with confirming
(plan.md §11 item 3). If pgvector turns out not to be viable there, this
is the one column in the whole schema that moves to a separate vector
store; everything else in this file is unaffected either way.

EMBEDDING_DIM is a placeholder — set it once the embedding model is chosen
in P1-RAG-002 (e.g. 1536 for an OpenAI embedding model, 384/768 for common
local sentence-embedding models). Do not leave this at the placeholder
value past Sprint Block 3–4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

# from pgvector.sqlalchemy import Vector  # uncomment once pgvector is confirmed (P1-BE-002)
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from .knowledge_document import KnowledgeDocument

EMBEDDING_DIM = 1536  # placeholder — confirm against the chosen embedding model (P1-RAG-002)


class Chunk(UUIDPKMixin, Base):
    __tablename__ = "chunks"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Placeholder column until pgvector is confirmed; swap for:
    #   embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    embedding: Mapped[Optional[str]] = mapped_column(
        Text, comment="TEMP placeholder — replace with pgvector Vector() once P1-BE-002 confirms viability"
    )

    species: Mapped[Optional[str]] = mapped_column(String(40))
    body_system: Mapped[Optional[str]] = mapped_column(String(80))
    # Catch-all for whatever the chunking design (P1-RAG-002) decides it
    # needs beyond the two explicit filter columns above. Named
    # `metadata_json`, not `metadata` — the latter is reserved by
    # SQLAlchemy's declarative Base and would silently shadow it.
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")
