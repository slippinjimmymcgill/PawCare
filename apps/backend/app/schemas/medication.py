from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    dosage: str | None = Field(default=None, max_length=255)
    frequency: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    dosage: str | None = Field(default=None, max_length=255)
    frequency: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class MedicationRead(MedicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pet_id: str
    created_at: datetime
    updated_at: datetime
