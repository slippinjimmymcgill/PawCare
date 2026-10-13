from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)

app.dependency_overrides.clear()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


def _register(email: str) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Owner", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_pet(headers: dict[str, str], name: str = "Bella", weight: float | None = 25.0) -> str:
    payload: dict[str, object] = {"name": name, "species": "dog", "sex": "female"}
    if weight is not None:
        payload["weight_kg"] = weight
    res = client.post("/api/v1/pets", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _add_record(headers: dict[str, str], pet_id: str, body: dict[str, object]) -> None:
    res = client.post(
        f"/api/v1/records/pets/{pet_id}/health-records", json=body, headers=headers
    )
    assert res.status_code == 201, res.text


def _add_vaccination(headers: dict[str, str], pet_id: str, body: dict[str, object]) -> None:
    res = client.post(
        f"/api/v1/records/pets/{pet_id}/vaccinations", json=body, headers=headers
    )
    assert res.status_code == 201, res.text


def _add_medication(headers: dict[str, str], pet_id: str, body: dict[str, object]) -> None:
    res = client.post(
        f"/api/v1/records/pets/{pet_id}/medications", json=body, headers=headers
    )
    assert res.status_code == 201, res.text


def setup_pet_with_data() -> tuple[dict[str, str], str, dict[str, dt.date]]:
    email = f"dashboard_owner_{dt.datetime.now().timestamp()}@example.com"
    headers = _register(email)
    pet_id = _create_pet(headers)

    today = _today()
    overdue = today - dt.timedelta(days=5)
    due_soon = today + dt.timedelta(days=10)
    far_future = today + dt.timedelta(days=400)

    _add_record(headers, pet_id, {"type": "visit", "description": "Wellness", "date": "2026-03-15"})
    _add_record(headers, pet_id, {"type": "weight_log", "weight_kg": 26.2, "date": "2026-04-01"})
    _add_record(headers, pet_id, {"type": "weight_log", "weight_kg": 25.8, "date": "2026-04-20"})
    _add_record(headers, pet_id, {"type": "note", "description": "Appetite good", "date": "2026-04-25"})

    _add_vaccination(headers, pet_id, {"vaccine_name": "Rabies", "next_due_date": overdue.isoformat()})
    _add_vaccination(headers, pet_id, {"vaccine_name": "DHPP", "next_due_date": due_soon.isoformat()})
    _add_vaccination(headers, pet_id, {"vaccine_name": "Bordetella", "next_due_date": far_future.isoformat()})

    _add_medication(headers, pet_id, {"name": "Apoquel", "start_date": "2026-04-01"})
    _add_medication(
        headers,
        pet_id,
        {"name": "Antibiotic", "start_date": "2026-04-01", "end_date": due_soon.isoformat()},
    )
    _add_medication(
        headers,
        pet_id,
        {"name": "Painkiller", "start_date": "2026-01-01", "end_date": overdue.isoformat()},
    )

    return headers, pet_id, {"overdue": overdue, "due_soon": due_soon, "far_future": far_future}


def test_dashboard_summary_returns_all_four_widgets() -> None:
    headers, pet_id, _ = setup_pet_with_data()

    res = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary", headers=headers)
    assert res.status_code == 200, res.text
    summary = res.json()

    assert summary["pet_id"] == pet_id
    assert summary["pet_name"] == "Bella"
    assert summary["generated_at"]

    # Weight trend — two weight logs, ascending by date.
    trend = summary["weight_trend"]
    assert [point["date"] for point in trend] == ["2026-04-01", "2026-04-20"]
    assert [point["weight_kg"] for point in trend] == [26.2, 25.8]

    # Reminders — 3 vaccinations + 2 active medications; completed med excluded.
    reminders = summary["reminders"]
    assert len(reminders) == 5
    by_title = {reminder["title"]: reminder for reminder in reminders}
    assert by_title["Rabies"]["status"] == "overdue"
    assert by_title["DHPP"]["status"] == "due_soon"
    assert by_title["Bordetella"]["status"] == "scheduled"
    assert by_title["Apoquel"]["kind"] == "medication"
    assert by_title["Apoquel"]["status"] == "active"
    assert by_title["Apoquel"]["due_date"] is None
    assert by_title["Antibiotic"]["status"] == "due_soon"
    assert "Painkiller" not in by_title

    # Reminders sorted by urgency: overdue first, then due_soon, active, scheduled.
    statuses = [reminder["status"] for reminder in reminders]
    assert statuses[0] == "overdue"
    order = {"overdue": 0, "due_soon": 1, "active": 2, "scheduled": 3}
    assert statuses == sorted(statuses, key=lambda status: order[status])

    # Assessments — none persisted yet (P2-BE-001), so an empty list.
    assert summary["assessments"] == []

    # Record summary.
    record_summary = summary["record_summary"]
    assert record_summary["total"] == 4
    assert record_summary["visits"] == 1
    assert record_summary["weight_logs"] == 2
    assert record_summary["notes"] == 1
    assert record_summary["last_record_date"] == "2026-04-25"
    assert record_summary["active_medications"] == 2
    assert record_summary["upcoming_vaccinations"] == 2


def test_dashboard_summary_empty_pet_uses_profile_weight() -> None:
    headers = _register(f"empty_pet_{dt.datetime.now().timestamp()}@example.com")
    pet_id = _create_pet(headers, name="Newbie", weight=12.5)

    res = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary", headers=headers)
    assert res.status_code == 200, res.text
    summary = res.json()

    assert len(summary["weight_trend"]) == 1
    assert summary["weight_trend"][0]["weight_kg"] == 12.5
    assert summary["reminders"] == []
    assert summary["assessments"] == []
    assert summary["record_summary"]["total"] == 0
    assert summary["record_summary"]["last_record_date"] is None
    assert summary["record_summary"]["active_medications"] == 0


def test_dashboard_summary_new_pet_without_weight_has_empty_trend() -> None:
    headers = _register(f"no_weight_{dt.datetime.now().timestamp()}@example.com")
    pet_id = _create_pet(headers, name="NoWeight", weight=None)

    res = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["weight_trend"] == []


def test_dashboard_summary_requires_auth() -> None:
    headers, pet_id, _ = setup_pet_with_data()
    res = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary")
    assert res.status_code == 401


def test_dashboard_summary_cannot_read_other_users_pet() -> None:
    _, pet_id, _ = setup_pet_with_data()
    other = _register(f"intruder_{dt.datetime.now().timestamp()}@example.com")
    res = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary", headers=other)
    assert res.status_code == 404


def test_dashboard_overview_rolls_up_across_pets() -> None:
    headers, _, _ = setup_pet_with_data()

    res = client.get("/api/v1/dashboard/overview", headers=headers)
    assert res.status_code == 200, res.text
    overview = res.json()

    assert overview["pet_count"] == 1
    assert overview["total_records"] == 4
    assert overview["active_medications"] == 2
    assert overview["upcoming_reminders"] == 5


def test_dashboard_overview_empty_for_new_user() -> None:
    headers = _register(f"fresh_{dt.datetime.now().timestamp()}@example.com")
    res = client.get("/api/v1/dashboard/overview", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json() == {
        "pet_count": 0,
        "upcoming_reminders": 0,
        "active_medications": 0,
        "total_records": 0,
    }
