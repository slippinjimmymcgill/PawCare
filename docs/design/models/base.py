"""
PawCare — SQLAlchemy base & shared mixins.

Phase 0 design draft (P0-BE-001). These stubs define structure only — no
migrations are run from this draft; that happens in P1-BE-002 once this
schema has been reviewed. See ../schema-notes.md for the design decisions
behind this file (soft-delete policy, UUID keys, enum choices).

Target: SQLAlchemy 2.0 declarative style (Mapped / mapped_column).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base for every PawCare model."""
    pass


class UUIDPKMixin:
    """Every entity in requirements.md §5 uses a UUID surrogate key, not an
    auto-increment int — keeps IDs non-guessable and stable across services
    (useful once the AI services and the API are split, per the layered
    architecture in plan.md §2)."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """created_at is enough for most entities; updated_at is added only on
    the few models that are actually edited in place after creation (Pet,
    Medication) rather than append-only (SymptomAssessment, Message)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
