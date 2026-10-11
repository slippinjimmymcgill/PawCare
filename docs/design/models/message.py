"""
PawCare — Message model. Trace: FR-07, requirements.md §4–§5.

`sources` is not optional polish — requirements.md FR-07's acceptance
criteria require every substantive assistant claim to be traceable to a
retrieved knowledge-base chunk, and `specs.md` lists source citations as
a Transparency NFR. An assistant message with empty `sources` should be
treated as a bug once the RAG pipeline (P2-RAG-001/002) is wired in, not
a normal state — enforce that in the Assistant Service, not just the UI.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPKMixin, utcnow
from .enums import ChatRole

if TYPE_CHECKING:
    from .chat_session import ChatSession


class Message(UUIDPKMixin, Base):
    __tablename__ = "messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole, name="chat_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # List of {chunk_id, doc_title, source} — see knowledge_document.py /
    # chunk.py. Empty list is valid for a `role == USER` message; an
    # assistant message with an empty list is the bug described above.
    sources: Mapped[Optional[dict]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    # Feedback rows reference this table via Feedback.target_id — see
    # feedback.py and schema-notes.md §4.
