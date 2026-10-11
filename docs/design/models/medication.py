"""
PawCare — Medication model. Trace: FR-03, requirements.md §5.

IMPORTANT (safety, not just a style note): `notes` is strictly an
owner/vet-entered record of what the pet is currently or was previously
on — it is never populated or suggested by the AI components. Nothing in
requirements.md §7's "no prescription/dosage output" constraint is relaxed
by this table existing; it is a record-keeping field, not a generation
target. Any code that writes to this table from the AI/RAG services rather
than a user-initiated form submission is a bug, not a feature.
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


class Medication(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "medications"

    pet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    pet: Mapped["Pet"] = relationship(back_populates="medications")
