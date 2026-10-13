from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PetSpecies(str, Enum):
    DOG = "dog"
    CAT = "cat"


class PetSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class PetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    species: PetSpecies
    breed: str | None = Field(default=None, max_length=120)
    sex: PetSex = PetSex.UNKNOWN
    date_of_birth: date | None = None
    weight_kg: float | None = Field(default=None, ge=0.1, le=200.0)
    allergies: str | None = None
    medical_history: str | None = None


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    species: PetSpecies | None = None
    breed: str | None = Field(default=None, max_length=120)
    sex: PetSex | None = None
    date_of_birth: date | None = None
    weight_kg: float | None = Field(default=None, ge=0.1, le=200.0)
    allergies: str | None = None
    medical_history: str | None = None


class PetRead(PetBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
