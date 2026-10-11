"""
PawCare — Medication Pydantic schemas. Trace: FR-03, requirements.md §5.

Placeholder only — real schemas land with P1-BE-005, matching
docs/design/models/medication.py. Note (carried from that model's own
docstring): the `notes` field must never be written to by the AI/RAG
services — owner-entered only. Worth re-flagging here since this is the
first touchpoint a future API-layer implementer will see.
"""

from pydantic import BaseModel


class MedicationBase(BaseModel):
    """Placeholder — fields added in P1-BE-005."""
