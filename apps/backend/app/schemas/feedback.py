"""
PawCare — Feedback Pydantic schemas. Trace: FR-13, requirements.md §5.

Placeholder only — real schemas land with P2-BE-006 (Phase 2), matching
docs/design/models/feedback.py. Note the model-layer decision that
target_id/target_type is an application-level polymorphic reference, not
a DB foreign key (see schema-notes.md) — P2-BE-006's schema will need to
validate target_type against an allowed set (Assessment | Message)
itself, since the database won't do it.
"""

from pydantic import BaseModel


class FeedbackBase(BaseModel):
    """Placeholder — fields added in P2-BE-006."""
