"""
PawCare — Dashboard aggregation service. Trace: FR-10.

Composes the read-only dashboard views from the data other modules own:
health records (weight trend + record summary), vaccinations and medications
(reminders), and — once it exists (P2-BE-001) — symptom assessments.

The reminder/urgency rules here deliberately mirror the client-side logic that
shipped with `P1-FE-005` (`apps/frontend/lib/dashboard.ts`) so switching the
dashboard from client-side composition to this endpoint is behaviour-preserving.
The reminder *service* (scheduling, delivery, status transitions) is
`P2-BE-003`; this module only derives the dashboard's view of what is already
in the records tables.
"""

from __future__ import annotations

import datetime as dt
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.health_record import HealthRecord, HealthRecordType
from app.models.medication import Medication
from app.models.pet import Pet
from app.models.user import User
from app.models.vaccination import Vaccination
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardRecordSummary,
    DashboardReminder,
    DashboardReminderKind,
    DashboardReminderStatus,
    DashboardSummary,
    WeightTrendPoint,
)

# A reminder due within this many days is surfaced as "due soon" rather than
# just "scheduled"/"active". Matches the frontend's DUE_SOON_DAYS.
DUE_SOON_DAYS = 30

_STATUS_ORDER: dict[DashboardReminderStatus, int] = {
    DashboardReminderStatus.OVERDUE: 0,
    DashboardReminderStatus.DUE_SOON: 1,
    DashboardReminderStatus.ACTIVE: 2,
    DashboardReminderStatus.SCHEDULED: 3,
}


def _today() -> dt.date:
    return dt.datetime.now(UTC).date()


def _days_until(target: dt.date, today: dt.date) -> int:
    return (target - today).days


def _vaccination_status(next_due: dt.date, today: dt.date) -> DashboardReminderStatus:
    days = _days_until(next_due, today)
    if days < 0:
        return DashboardReminderStatus.OVERDUE
    if days <= DUE_SOON_DAYS:
        return DashboardReminderStatus.DUE_SOON
    return DashboardReminderStatus.SCHEDULED


def _is_medication_active(medication: Medication, today: dt.date) -> bool:
    return medication.end_date is None or medication.end_date >= today


def _medication_status(medication: Medication, today: dt.date) -> DashboardReminderStatus:
    if medication.end_date is None:
        return DashboardReminderStatus.ACTIVE
    days = _days_until(medication.end_date, today)
    if days < 0:
        return DashboardReminderStatus.OVERDUE
    if days <= DUE_SOON_DAYS:
        return DashboardReminderStatus.DUE_SOON
    return DashboardReminderStatus.ACTIVE


def _build_weight_trend(pet: Pet, records: list[HealthRecord]) -> list[WeightTrendPoint]:
    points = [
        WeightTrendPoint(date=record.date, weight_kg=float(record.weight_kg))
        for record in records
        if record.type == HealthRecordType.WEIGHT_LOG and record.weight_kg is not None
    ]
    points.sort(key=lambda point: point.date)

    if not points and pet.weight_kg is not None:
        reference = pet.updated_at or pet.created_at
        points.append(
            WeightTrendPoint(date=reference.date(), weight_kg=float(pet.weight_kg))
        )

    return points


def _build_reminders(
    vaccinations: list[Vaccination],
    medications: list[Medication],
    today: dt.date,
) -> list[DashboardReminder]:
    reminders: list[DashboardReminder] = []

    for vaccination in vaccinations:
        if vaccination.next_due_date is None:
            continue
        reminders.append(
            DashboardReminder(
                id=f"vaccination-{vaccination.id}",
                kind=DashboardReminderKind.VACCINATION,
                title=vaccination.vaccine_name,
                due_date=vaccination.next_due_date,
                status=_vaccination_status(vaccination.next_due_date, today),
            )
        )

    for medication in medications:
        if not _is_medication_active(medication, today):
            continue
        reminders.append(
            DashboardReminder(
                id=f"medication-{medication.id}",
                kind=DashboardReminderKind.MEDICATION,
                title=medication.name,
                due_date=medication.end_date,
                status=_medication_status(medication, today),
            )
        )

    reminders.sort(
        key=lambda reminder: (
            _STATUS_ORDER[reminder.status],
            reminder.due_date or dt.date.max,
        )
    )
    return reminders


def build_dashboard_summary(db: Session, pet: Pet) -> DashboardSummary:
    records = list(
        db.scalars(select(HealthRecord).where(HealthRecord.pet_id == pet.id)).all()
    )
    vaccinations = list(
        db.scalars(select(Vaccination).where(Vaccination.pet_id == pet.id)).all()
    )
    medications = list(
        db.scalars(select(Medication).where(Medication.pet_id == pet.id)).all()
    )

    today = _today()
    active_medications = [med for med in medications if _is_medication_active(med, today)]

    last_record_date = max((record.date for record in records), default=None)

    return DashboardSummary(
        pet_id=pet.id,
        pet_name=pet.name,
        generated_at=dt.datetime.now(UTC),
        weight_trend=_build_weight_trend(pet, records),
        reminders=_build_reminders(vaccinations, medications, today),
        assessments=[],
        record_summary=DashboardRecordSummary(
            total=len(records),
            visits=sum(1 for record in records if record.type == HealthRecordType.VISIT),
            weight_logs=sum(
                1 for record in records if record.type == HealthRecordType.WEIGHT_LOG
            ),
            notes=sum(1 for record in records if record.type == HealthRecordType.NOTE),
            last_record_date=last_record_date,
            active_medications=len(active_medications),
            upcoming_vaccinations=sum(
                1
                for vaccination in vaccinations
                if vaccination.next_due_date is not None
                and _days_until(vaccination.next_due_date, today) >= 0
            ),
        ),
    )


def build_dashboard_overview(db: Session, user: User) -> DashboardOverview:
    pets = list(
        db.scalars(
            select(Pet).where(Pet.user_id == user.id, Pet.deleted_at.is_(None))
        ).all()
    )
    pet_ids = [pet.id for pet in pets]
    if not pet_ids:
        return DashboardOverview(
            pet_count=0,
            upcoming_reminders=0,
            active_medications=0,
            total_records=0,
        )

    today = _today()
    records = list(
        db.scalars(
            select(HealthRecord).where(HealthRecord.pet_id.in_(pet_ids))
        ).all()
    )
    vaccinations = list(
        db.scalars(
            select(Vaccination).where(Vaccination.pet_id.in_(pet_ids))
        ).all()
    )
    medications = list(
        db.scalars(select(Medication).where(Medication.pet_id.in_(pet_ids))).all()
    )

    active_medications = [med for med in medications if _is_medication_active(med, today)]
    upcoming_vaccinations = [
        vaccination
        for vaccination in vaccinations
        if vaccination.next_due_date is not None
    ]

    return DashboardOverview(
        pet_count=len(pets),
        upcoming_reminders=len(upcoming_vaccinations) + len(active_medications),
        active_medications=len(active_medications),
        total_records=len(records),
    )
