"""
PawCare — Symptom assessment Pydantic schemas.
Trace: FR-04, FR-05, FR-06, requirements.md §5.

Placeholder only — real schemas (the free-text/structured input shape,
and the ranked-concerns/confidence/urgency response shape) land with
P2-BE-001 (Phase 2), once the Assessment Service and Safety Layer exist
to actually produce that response. Defining the response schema before
FR-08's Safety Layer sits in front of it would risk the schema implying
a diagnosis-shaped output — deliberately deferred, not an oversight.
"""

from pydantic import BaseModel


class SymptomAssessmentBase(BaseModel):
    """Placeholder — fields added in P2-BE-001."""
