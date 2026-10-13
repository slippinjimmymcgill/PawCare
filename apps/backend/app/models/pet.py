from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.health_record import HealthRecord
    from app.models.medication import Medication
    from app.models.user import User
    from app.models.vaccination import Vaccination


class Species(str, Enum):
    DOG = "dog"
    CAT = "cat"


class PetSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    species: Mapped[Species] = mapped_column(
        SAEnum(Species, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        nullable=False,
    )
    breed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sex: Mapped[PetSex] = mapped_column(
        SAEnum(PetSex, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        default=PetSex.UNKNOWN,
        nullable=False,
    )
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    owner: Mapped[User] = relationship(back_populates="pets")
    health_records: Mapped[list[HealthRecord]] = relationship(back_populates="pet", cascade="all, delete-orphan")
    vaccinations: Mapped[list[Vaccination]] = relationship(back_populates="pet", cascade="all, delete-orphan")
    medications: Mapped[list[Medication]] = relationship(back_populates="pet", cascade="all, delete-orphan")

    @property
    def is_archived(self) -> bool:
        return self.deleted_at is not None
