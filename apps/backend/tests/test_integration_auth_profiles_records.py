"""
PawCare — Integration tests for auth / profiles / records (P1-QA-001).

Trace: plan.md §6 ("Integration tests — API-level tests covering
service-to-service flows").

Unlike the per-module CRUD suites (`test_auth_service.py`,
`test_pet_crud.py`, `test_records_crud.py`), these tests deliberately exercise
*flows that cross module boundaries* rather than one endpoint in isolation:

- register → login → create profile → add records → see them on the dashboard
  (auth → pets → records → dashboard aggregation)
- archiving a pet closes off every module that reads through it
- one user's pets/records/dashboard are unreachable — and unlistable — by another
- records stay scoped to the pet they were created under, not just the user
- a revoked (logged-out) token is rejected by every protected route, not just auth
- changing a password re-establishes access to the same profiles/records

The SQLite in-memory wiring mirrors the existing suites so the whole file runs
under the same `pytest` invocation as the rest of the backend.
"""

from __future__ import annotations

import datetime as dt
import uuid

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


# --- helpers ---------------------------------------------------------------


def unique_email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.com"


def register(prefix: str = "user") -> tuple[dict[str, str], str, str]:
    """Register a user; return (auth headers, token, user id)."""
    email = unique_email(prefix)
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Integration User", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    token = body["access_token"]
    return {"Authorization": f"Bearer {token}"}, token, body["user"]["id"]


def create_pet(
    headers: dict[str, str], name: str = "Rex", weight: float | None = 20.0
) -> str:
    payload: dict[str, object] = {
        "name": name,
        "species": "dog",
        "sex": "male",
    }
    if weight is not None:
        payload["weight_kg"] = weight
    res = client.post("/api/v1/pets", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def add_health_record(
    headers: dict[str, str], pet_id: str, body: dict[str, object]
) -> str:
    res = client.post(
        f"/api/v1/records/pets/{pet_id}/health-records", json=body, headers=headers
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def add_vaccination(headers: dict[str, str], pet_id: str, body: dict[str, object]) -> str:
    res = client.post(
        f"/api/v1/records/pets/{pet_id}/vaccinations", json=body, headers=headers
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def add_medication(headers: dict[str, str], pet_id: str, body: dict[str, object]) -> str:
    res = client.post(
        f"/api/v1/records/pets/{pet_id}/medications", json=body, headers=headers
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


# --- flows -----------------------------------------------------------------


def test_register_to_dashboard_end_to_end_lifecycle() -> None:
    """auth → pet profile → records → dashboard aggregation, in one flow."""
    headers, _, user_id = register("lifecycle")

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == user_id

    pet_id = create_pet(headers, name="Luna", weight=18.5)

    # Profile is immediately visible.
    listed = client.get("/api/v1/pets", headers=headers)
    assert listed.status_code == 200
    assert [pet["id"] for pet in listed.json()] == [pet_id]

    # Add one record of each kind the dashboard reads from other modules.
    add_health_record(headers, pet_id, {"type": "visit", "description": "Checkup", "date": "2026-03-01"})
    add_health_record(headers, pet_id, {"type": "weight_log", "weight_kg": 18.9, "date": "2026-03-05"})
    add_vaccination(headers, pet_id, {"vaccine_name": "Rabies", "next_due_date": "2027-03-01"})
    add_medication(headers, pet_id, {"name": "Apoquel", "start_date": "2026-03-01"})

    summary = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["pet_id"] == pet_id
    assert body["record_summary"]["total"] == 2
    assert body["record_summary"]["visits"] == 1
    assert body["record_summary"]["weight_logs"] == 1
    assert body["record_summary"]["active_medications"] == 1
    assert len(body["reminders"]) == 2
    assert [point["weight_kg"] for point in body["weight_trend"]] == [18.9]

    # The user-level overview sees the same pet.
    overview = client.get("/api/v1/dashboard/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json() == {
        "pet_count": 1,
        "upcoming_reminders": 2,
        "active_medications": 1,
        "total_records": 2,
    }


def test_archiving_pet_closes_off_all_modules() -> None:
    """Soft-deleting a profile hides it and its records everywhere."""
    headers, _, _ = register("archive")
    pet_id = create_pet(headers, name="Ghost")
    record_id = add_health_record(
        headers, pet_id, {"type": "note", "description": "temp", "date": "2026-03-01"}
    )
    add_vaccination(headers, pet_id, {"vaccine_name": "DHPP", "next_due_date": "2027-01-01"})

    archive = client.delete(f"/api/v1/pets/{pet_id}", headers=headers)
    assert archive.status_code == 200
    assert archive.json()["status"] == "ok"

    # Pet profile gone from list and direct fetch.
    assert client.get("/api/v1/pets", headers=headers).json() == []
    assert client.get(f"/api/v1/pets/{pet_id}", headers=headers).status_code == 404

    # Every records route that reads through the pet is closed off.
    assert client.get(
        f"/api/v1/records/pets/{pet_id}/health-records", headers=headers
    ).status_code == 404
    assert client.get(
        f"/api/v1/records/pets/{pet_id}/health-records/{record_id}", headers=headers
    ).status_code == 404
    assert client.get(
        f"/api/v1/records/pets/{pet_id}/vaccinations", headers=headers
    ).status_code == 404
    assert client.get(
        f"/api/v1/records/pets/{pet_id}/medications", headers=headers
    ).status_code == 404
    assert client.post(
        f"/api/v1/records/pets/{pet_id}/health-records",
        json={"type": "note", "description": "x", "date": "2026-03-02"},
        headers=headers,
    ).status_code == 404

    # Dashboard no longer aggregates it.
    assert client.get(
        f"/api/v1/dashboard/pets/{pet_id}/summary", headers=headers
    ).status_code == 404
    assert client.get("/api/v1/dashboard/overview", headers=headers).json()["pet_count"] == 0


def test_multi_user_data_isolation_across_modules() -> None:
    """User B can neither list, read, mutate, nor aggregate user A's data."""
    owner_headers, _, _ = register("owner")
    pet_id = create_pet(owner_headers, name="Private")
    add_health_record(
        owner_headers, pet_id, {"type": "visit", "description": "secret", "date": "2026-03-01"}
    )
    add_vaccination(owner_headers, pet_id, {"vaccine_name": "Rabies", "next_due_date": "2027-01-01"})
    add_medication(owner_headers, pet_id, {"name": "SecretMed", "start_date": "2026-03-01"})

    intruder_headers, _, _ = register("intruder")

    # No leak in the intruder's own pet list.
    assert client.get("/api/v1/pets", headers=intruder_headers).json() == []

    # Profile reads/writes are 404 (not 403 — the resource is invisible).
    assert client.get(f"/api/v1/pets/{pet_id}", headers=intruder_headers).status_code == 404
    assert client.put(
        f"/api/v1/pets/{pet_id}", json={"name": "Hijacked"}, headers=intruder_headers
    ).status_code == 404
    assert client.delete(f"/api/v1/pets/{pet_id}", headers=intruder_headers).status_code == 404

    # Records under the other user's pet are unreachable.
    assert client.get(
        f"/api/v1/records/pets/{pet_id}/health-records", headers=intruder_headers
    ).status_code == 404
    assert client.get(
        f"/api/v1/records/pets/{pet_id}/vaccinations", headers=intruder_headers
    ).status_code == 404
    assert client.get(
        f"/api/v1/records/pets/{pet_id}/medications", headers=intruder_headers
    ).status_code == 404
    assert client.post(
        f"/api/v1/records/pets/{pet_id}/medications",
        json={"name": "Injected"},
        headers=intruder_headers,
    ).status_code == 404

    # Dashboard aggregation does not leak across users either.
    assert client.get(
        f"/api/v1/dashboard/pets/{pet_id}/summary", headers=intruder_headers
    ).status_code == 404
    assert client.get("/api/v1/dashboard/overview", headers=intruder_headers).json() == {
        "pet_count": 0,
        "upcoming_reminders": 0,
        "active_medications": 0,
        "total_records": 0,
    }

    # ...and the owner's data is still intact afterwards.
    assert client.get(f"/api/v1/pets/{pet_id}", headers=owner_headers).status_code == 200


def test_records_are_scoped_to_their_pet_within_one_account() -> None:
    """Two pets under one owner do not see each other's records."""
    headers, _, _ = register("two_pets")
    pet_a = create_pet(headers, name="Alpha")
    pet_b = create_pet(headers, name="Beta")

    record_a = add_health_record(
        headers, pet_a, {"type": "note", "description": "for alpha", "date": "2026-03-01"}
    )
    add_health_record(
        headers, pet_a, {"type": "weight_log", "weight_kg": 10.0, "date": "2026-03-02"}
    )

    assert len(client.get(f"/api/v1/records/pets/{pet_a}/health-records", headers=headers).json()) == 2
    assert client.get(f"/api/v1/records/pets/{pet_b}/health-records", headers=headers).json() == []

    # A record belonging to pet A cannot be fetched through pet B's path.
    cross = client.get(
        f"/api/v1/records/pets/{pet_b}/health-records/{record_a}", headers=headers
    )
    assert cross.status_code == 404

    # Dashboard summaries count per-pet, not per-account.
    assert client.get(
        f"/api/v1/dashboard/pets/{pet_a}/summary", headers=headers
    ).json()["record_summary"]["total"] == 2
    assert client.get(
        f"/api/v1/dashboard/pets/{pet_b}/summary", headers=headers
    ).json()["record_summary"]["total"] == 0


def test_logout_revokes_token_across_all_protected_routes() -> None:
    """A logged-out token is rejected everywhere, not just on /auth/me."""
    headers, _, _ = register("logout")
    pet_id = create_pet(headers, name="Token")

    # Sanity: the token works on several modules.
    assert client.get("/api/v1/pets", headers=headers).status_code == 200
    assert client.get("/api/v1/dashboard/overview", headers=headers).status_code == 200

    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200

    for path in (
        "/api/v1/auth/me",
        "/api/v1/pets",
        f"/api/v1/pets/{pet_id}",
        f"/api/v1/records/pets/{pet_id}/health-records",
        f"/api/v1/dashboard/pets/{pet_id}/summary",
        "/api/v1/dashboard/overview",
    ):
        assert client.get(path, headers=headers).status_code == 401, path


def test_protected_routes_reject_anonymous_requests() -> None:
    """No credentials at all is a 401 on every profile/record/dashboard route."""
    headers, _, _ = register("anon")
    pet_id = create_pet(headers, name="Guarded")

    for path in (
        "/api/v1/auth/me",
        "/api/v1/pets",
        f"/api/v1/pets/{pet_id}",
        f"/api/v1/records/pets/{pet_id}/health-records",
        f"/api/v1/records/pets/{pet_id}/vaccinations",
        f"/api/v1/records/pets/{pet_id}/medications",
        f"/api/v1/dashboard/pets/{pet_id}/summary",
        "/api/v1/dashboard/overview",
    ):
        assert client.get(path).status_code == 401, path


def test_password_change_preserves_access_to_profiles_and_records() -> None:
    """The auth/profile edge and its dependent records stay consistent after a
    password reset, and the old password stops working."""
    email = unique_email("reset_flow")
    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "Reset Flow", "email": email, "password": "Password123!"},
    )
    assert registered.status_code == 201
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    pet_id = create_pet(headers, name="Persistent")
    add_health_record(headers, pet_id, {"type": "note", "description": "kept", "date": "2026-03-01"})

    reset_request = client.post("/api/v1/auth/password-reset/request", json={"email": email})
    assert reset_request.status_code == 200
    reset_token = reset_request.json()["reset_token"]

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"email": email, "token": reset_token, "new_password": "BrandNew456!"},
    )
    assert confirm.status_code == 200

    # Old password no longer authenticates.
    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert old_login.status_code == 401

    # New password authenticates and reaches the same profile + records.
    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": "BrandNew456!"})
    assert new_login.status_code == 200
    new_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}
    assert client.get(f"/api/v1/pets/{pet_id}", headers=new_headers).status_code == 200
    assert len(
        client.get(f"/api/v1/records/pets/{pet_id}/health-records", headers=new_headers).json()
    ) == 1


def test_duplicate_registration_is_rejected_but_login_still_works() -> None:
    """Auth edge: a second registration on the same email fails, the original
    credential continues to work against profiles/records."""
    email = unique_email("dup")
    first = client.post(
        "/api/v1/auth/register",
        json={"name": "First", "email": email, "password": "Password123!"},
    )
    assert first.status_code == 201
    headers = {"Authorization": f"Bearer {first.json()['access_token']}"}
    create_pet(headers, name="Kept")

    duplicate = client.post(
        "/api/v1/auth/register",
        json={"name": "Second", "email": email, "password": "Password123!"},
    )
    assert duplicate.status_code == 400

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert login.status_code == 200
    relogin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/pets", headers=relogin_headers).status_code == 200
    assert len(client.get("/api/v1/pets", headers=relogin_headers).json()) == 1


def test_updating_profile_weight_flows_into_dashboard_trend() -> None:
    """A pet-profile change (weight) is reflected by the dashboard module."""
    headers, _, _ = register("weight_flow")
    pet_id = create_pet(headers, name="Chunky", weight=30.0)

    # No weight-log records yet → the trend seeds from the profile weight.
    before = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary", headers=headers).json()
    assert [point["weight_kg"] for point in before["weight_trend"]] == [30.0]

    updated = client.put(f"/api/v1/pets/{pet_id}", json={"weight_kg": 27.5}, headers=headers)
    assert updated.status_code == 200

    after = client.get(f"/api/v1/dashboard/pets/{pet_id}/summary", headers=headers).json()
    assert [point["weight_kg"] for point in after["weight_trend"]] == [27.5]


def test_timestamps_are_deterministic_iso_strings_across_modules() -> None:
    """Cross-module contract: created_at from pets and records is ISO-8601 and
    parseable, since the dashboard and records UI both format it defensively."""
    headers, _, _ = register("timestamps")
    pet_id = create_pet(headers, name="Clock")

    pet = client.get(f"/api/v1/pets/{pet_id}", headers=headers).json()
    assert dt.datetime.fromisoformat(pet["created_at"])
    assert dt.datetime.fromisoformat(pet["updated_at"])

    record_id = add_health_record(
        headers, pet_id, {"type": "note", "description": "x", "date": "2026-03-01"}
    )
    record = client.get(
        f"/api/v1/records/pets/{pet_id}/health-records/{record_id}", headers=headers
    ).json()
    assert dt.datetime.fromisoformat(record["created_at"])
