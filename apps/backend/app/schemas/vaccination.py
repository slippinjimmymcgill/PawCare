from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class VaccinationBase(BaseModel):
    vaccine_name: str = Field(..., min_length=1, max_length=120)
    administered_date: date | None = None
    next_due_date: date | None = None
    notes: str | None = None


class VaccinationCreate(VaccinationBase):
    pass


class VaccinationUpdate(BaseModel):
    vaccine_name: str | None = Field(default=None, min_length=1, max_length=120)
    administered_date: date | None = None
    next_due_date: date | None = None
    notes: str | None = None


class VaccinationRead(VaccinationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pet_id: str
    created_at: datetime
    updated_at: datetime
