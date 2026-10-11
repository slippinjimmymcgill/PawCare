"""
PawCare — Vaccination Pydantic schemas. Trace: FR-03, requirements.md §5.

Placeholder only — real schemas land with P1-BE-005, matching
docs/design/models/vaccination.py (vaccine_name, date_given, next_due —
the fields the Reminder Service, P2-BE-003, queries directly).
"""

from pydantic import BaseModel


class VaccinationBase(BaseModel):
    """Placeholder — fields added in P1-BE-005."""
