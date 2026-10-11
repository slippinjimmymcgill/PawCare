"""
PawCare — SymptomAssessment model. Trace: FR-04, FR-05, FR-06, FR-08,
requirements.md §4–§5.

`urgency` is the field the Veterinary Safety Layer (FR-08, built in
P2-RAG-004) reads and can override — it is set by the triage model but
the Safety Layer has the final say before a response reaches the user.
This table stores the *final* urgency after any override, plus enough of
the raw model output (extracted_symptoms, predicted_concerns, confidence)
to support the evaluation work in P2-AI-001 / P3-QA-002.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import JSON, Enum, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin
from .enums import UrgencyLevel

if TYPE_CHECKING:
    from .pet import Pet


class SymptomAssessment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "symptom_assessments"

    pet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Structured output of the NLP pipeline (P1-AI-003) — symptom entities,
    # duration/severity modifiers, etc. Shape documented in plan.md §3
    # (Phase 5) once the pipeline is built; JSON here deliberately, since
    # the extraction schema is expected to iterate during model work.
    extracted_symptoms: Mapped[Optional[dict]] = mapped_column(JSON)
    # Ranked list of {condition, confidence} from the classifier (P1-AI-004).
    predicted_concerns: Mapped[Optional[dict]] = mapped_column(JSON)

    urgency: Mapped[UrgencyLevel] = mapped_column(
        Enum(UrgencyLevel, name="urgency_level"), nullable=False, index=True
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    pet: Mapped["Pet"] = relationship(back_populates="assessments")

    # Note: Feedback rows reference this table via Feedback.target_id, as
    # an application-level polymorphic reference — not a declared FK here.
    # See feedback.py and schema-notes.md §4 for why.
