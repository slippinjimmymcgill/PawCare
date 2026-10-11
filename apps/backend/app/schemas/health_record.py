"""
PawCare — Health record Pydantic schemas. Trace: FR-03, requirements.md §5.

Placeholder only — real schemas (HealthRecordCreate/Read, plus attachment
handling) land with P1-BE-005/P1-BE-006, matching
docs/design/models/health_record.py.
"""

from pydantic import BaseModel


class HealthRecordBase(BaseModel):
    """Placeholder — fields added in P1-BE-005."""
