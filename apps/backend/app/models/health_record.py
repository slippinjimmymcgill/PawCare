from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if False:  # pragma: no cover - TYPE_CHECKING guard for relationship imports
    from app.models.pet import Pet


class HealthRecordType(str, Enum):
    VISIT = "visit"
    WEIGHT_LOG = "weight_log"
    NOTE = "note"


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[HealthRecordType] = mapped_column(
        SAEnum(HealthRecordType, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    pet: Mapped[Pet] = relationship(back_populates="health_records")
