"""
PawCare — Reminder model. Trace: FR-09, requirements.md §5.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Date, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin
from .enums import ReminderStatus, ReminderType

if TYPE_CHECKING:
    from .pet import Pet


class Reminder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "reminders"

    pet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type: Mapped[ReminderType] = mapped_column(Enum(ReminderType, name="reminder_type"), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, name="reminder_status"), default=ReminderStatus.PENDING, nullable=False
    )

    pet: Mapped["Pet"] = relationship(back_populates="reminders")
