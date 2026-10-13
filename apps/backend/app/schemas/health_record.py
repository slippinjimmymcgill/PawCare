from __future__ import annotations

import datetime as dt
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class HealthRecordType(str, Enum):
    VISIT = "visit"
    WEIGHT_LOG = "weight_log"
    NOTE = "note"


class HealthRecordBase(BaseModel):
    type: HealthRecordType
    description: str | None = None
    weight_kg: float | None = Field(default=None, ge=0.1, le=200.0)
    date: dt.date
    attachment_url: str | None = Field(default=None, max_length=500)


class HealthRecordCreate(HealthRecordBase):
    pass


class HealthRecordUpdate(BaseModel):
    type: HealthRecordType | None = None
    description: str | None = None
    weight_kg: float | None = Field(default=None, ge=0.1, le=200.0)
    date: dt.date | None = None
    attachment_url: str | None = Field(default=None, max_length=500)


class HealthRecordRead(HealthRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pet_id: str
    created_at: dt.datetime
    updated_at: dt.datetime
