"""
PawCare — Feedback model. Trace: FR-13, requirements.md §5.

`target_id` is a deliberately un-constrained polymorphic reference — it
points at either a SymptomAssessment.id or a Message.id depending on
`target_type`, and Postgres can't enforce "this UUID exists in table A or
table B" with a single FK constraint. This is an application-level
integrity rule, not a database one.

If this ever becomes a real data-integrity problem in practice (orphaned
feedback rows, etc.), the standard fix is two nullable FK columns
(assessment_id, message_id) with a CHECK constraint that exactly one is
set, instead of one polymorphic column — noted here rather than silently
changed later, since it's a real schema trade-off, not just a style
choice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin
from .enums import FeedbackTargetType

if TYPE_CHECKING:
    from .user import User


class Feedback(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "feedback"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    target_type: Mapped[FeedbackTargetType] = mapped_column(
        Enum(FeedbackTargetType, name="feedback_target_type"), nullable=False
    )
    # Not a ForeignKey — see module docstring.
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="feedback_entries")
