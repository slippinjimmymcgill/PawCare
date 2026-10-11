"""
PawCare — Pet model. Trace: FR-02, requirements.md §5.

Soft-delete policy (the modeling decision this task was asked to resolve —
see schema-notes.md §3 for the full reasoning): deleting a pet through the
normal product UI sets `deleted_at`, it does not remove the row. Dependent
records (HealthRecord, Vaccination, Medication, SymptomAssessment,
ChatSession, Reminder) are excluded from default queries once their parent
Pet is archived, but stay in the database. A true hard delete is a
separate, explicit, admin/account-level action — the FK `ondelete="CASCADE"`
on every dependent table exists for *that* path, not for routine deletes.

v1.1 (P0-PD-007 consolidation fix): added `medical_history`. FR-02 lists
"medical history" explicitly as a pet-profile attribute alongside
allergies; v1 of this schema had `allergies` but was missing this field.
See schema-notes.md §8 for the amendment note.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin
from .enums import Sex, Species

if TYPE_CHECKING:
    from .chat_session import ChatSession
    from .health_record import HealthRecord
    from .medication import Medication
    from .reminder import Reminder
    from .symptom_assessment import SymptomAssessment
    from .user import User
    from .vaccination import Vaccination


class Pet(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    species: Mapped[Species] = mapped_column(Enum(Species, name="species"), nullable=False)
    breed: Mapped[Optional[str]] = mapped_column(String(120))
    sex: Mapped[Sex] = mapped_column(Enum(Sex, name="sex"), default=Sex.UNKNOWN, nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    allergies: Mapped[Optional[str]] = mapped_column(Text)
    # v1.1 addition — see module docstring. A free-text owner-entered
    # summary (e.g. "history of hip dysplasia, TPLO surgery 2023"), distinct
    # from the itemized, time-series HealthRecord/Vaccination/Medication
    # tables — this is the profile-level summary FR-02 asks for, not a
    # replacement for the structured timeline.
    medical_history: Mapped[Optional[str]] = mapped_column(Text)

    # Soft-delete marker — see module docstring. Nullable; NULL = active.
    deleted_at: Mapped[Optional[date]] = mapped_column(DateTime(timezone=True))

    owner: Mapped["User"] = relationship(back_populates="pets")

    health_records: Mapped[list["HealthRecord"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )
    vaccinations: Mapped[list["Vaccination"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )
    medications: Mapped[list["Medication"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["SymptomAssessment"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )

    @property
    def is_archived(self) -> bool:
        return self.deleted_at is not None
