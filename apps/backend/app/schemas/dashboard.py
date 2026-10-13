"""
PawCare — Dashboard aggregation schemas. Trace: FR-10.

Response shapes for the read-only dashboard aggregation endpoints in
`app/api/v1/dashboard.py`. They are intentionally a *summary* of data owned by
other services (records, vaccinations, medications, and — later — assessments
and reminders); nothing here is independently persisted.

These shapes mirror the frontend contract in `apps/frontend/lib/types.ts`
(`DashboardSummary`, …) so the dashboard's client-side composition seam can be
replaced by a single server call without touching the UI.
"""

from __future__ import annotations

import datetime as dt
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DashboardReminderKind(str, Enum):
    VACCINATION = "vaccination"
    MEDICATION = "medication"


class DashboardReminderStatus(str, Enum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"
    ACTIVE = "active"
    SCHEDULED = "scheduled"


class WeightTrendPoint(BaseModel):
    date: dt.date
    weight_kg: float


class DashboardReminder(BaseModel):
    id: str
    kind: DashboardReminderKind
    title: str
    due_date: dt.date | None = None
    status: DashboardReminderStatus


class DashboardAssessment(BaseModel):
    """Placeholder until symptom assessments are persisted (P2-BE-001).

    The field exists now so the response shape is stable; the aggregator
    returns an empty list until there is a table to read from.
    """

    id: str
    date: dt.date
    summary: str
    urgency: str


class DashboardRecordSummary(BaseModel):
    total: int
    visits: int
    weight_logs: int
    notes: int
    last_record_date: dt.date | None = None
    active_medications: int
    upcoming_vaccinations: int


class DashboardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pet_id: str
    pet_name: str
    generated_at: dt.datetime
    weight_trend: list[WeightTrendPoint]
    reminders: list[DashboardReminder]
    assessments: list[DashboardAssessment]
    record_summary: DashboardRecordSummary


class DashboardOverview(BaseModel):
    """User-level roll-up across all non-archived pets, for the dashboard's
    top stat strip."""

    pet_count: int
    upcoming_reminders: int
    active_medications: int
    total_records: int
