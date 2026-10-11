"""
PawCare — Vaccination model. Trace: FR-03, FR-09, requirements.md §5.

Split out from HealthRecord because `next_due` is what the Reminder
Service (P2-BE-003, FR-09) actually queries against — keeping it a plain
column on its own table is simpler than extracting it from a generic
record's description text.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .pet import Pet


class Vaccination(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vaccinations"

    pet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    vaccine_name: Mapped[str] = mapped_column(String(120), nullable=False)
    date_given: Mapped[date] = mapped_column(Date, nullable=False)
    next_due: Mapped[Optional[date]] = mapped_column(Date, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    pet: Mapped["Pet"] = relationship(back_populates="vaccinations")
