"""
PawCare — Pet Pydantic schemas. Trace: FR-02, requirements.md §5.

Placeholder only — real schemas (PetCreate/PetRead/PetUpdate, covering
species, breed, age, sex, weight, medical_history, allergies,
medications) land with P1-BE-004, matching docs/design/models/pet.py.
"""

from pydantic import BaseModel


class PetBase(BaseModel):
    """Placeholder — fields added in P1-BE-004."""
