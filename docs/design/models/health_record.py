"""
PawCare — HealthRecord model. Trace: FR-03, requirements.md §5.

Covers vet visits, weight logs, and free-text notes. Vaccinations and
medications are deliberately NOT HealthRecordType values here — they have
their own lifecycle fields (next_due, start/end date) that don't fit this
generic shape. See vaccination.py, medication.py, and schema-notes.md §2.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin
from .enums import HealthRecordType

if TYPE_CHECKING:
    from .pet import Pet


class HealthRecord(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "health_records"

    pet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type: Mapped[HealthRecordType] = mapped_column(
        Enum(HealthRecordType, name="health_record_type"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    # Only meaningful when type == WEIGHT_LOG; left nullable rather than
    # split into a separate table since it's a single extra column.
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500))

    pet: Mapped["Pet"] = relationship(back_populates="health_records")
