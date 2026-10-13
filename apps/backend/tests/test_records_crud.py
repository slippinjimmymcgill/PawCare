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


def setup_auth_and_pet() -> tuple[dict[str, str], str]:
    email = f"records_owner_{dt.datetime.now().timestamp()}@example.com"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Owner", "email": email, "password": "Password123!"},
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pet_res = client.post(
        "/api/v1/pets",
        json={
            "name": "Bella",
            "species": "dog",
            "breed": "Golden Retriever",
            "sex": "female",
            "date_of_birth": "2022-01-01",
            "weight_kg": 25.0,
        },
        headers=headers,
    )
    assert pet_res.status_code == 201
    pet_id = pet_res.json()["id"]
    return headers, pet_id


def test_health_record_crud() -> None:
    headers, pet_id = setup_auth_and_pet()

    # Create visit record
    visit_res = client.post(
        f"/api/v1/records/pets/{pet_id}/health-records",
        json={
            "type": "visit",
            "description": "Annual wellness examination. Healthy vitals.",
            "date": "2026-03-15",
            "attachment_url": "https://storage.pawcare.local/visit-1.pdf",
        },
        headers=headers,
    )
    assert visit_res.status_code == 201, visit_res.text
    record = visit_res.json()
    record_id = record["id"]
    assert record["type"] == "visit"
    assert record["description"] == "Annual wellness examination. Healthy vitals."

    # Create weight log record
    weight_res = client.post(
        f"/api/v1/records/pets/{pet_id}/health-records",
        json={
            "type": "weight_log",
            "weight_kg": 26.2,
            "date": "2026-04-01",
        },
        headers=headers,
    )
    assert weight_res.status_code == 201

    # List health records
    list_res = client.get(
        f"/api/v1/records/pets/{pet_id}/health-records",
        headers=headers,
    )
    assert list_res.status_code == 200
    records = list_res.json()
    assert len(records) == 2

    # Get single record
    get_res = client.get(
        f"/api/v1/records/pets/{pet_id}/health-records/{record_id}",
        headers=headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == record_id

    # Update record
    update_res = client.put(
        f"/api/v1/records/pets/{pet_id}/health-records/{record_id}",
        json={"description": "Annual checkup - heartworm negative"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Annual checkup - heartworm negative"

    # Delete record
    del_res = client.delete(
        f"/api/v1/records/pets/{pet_id}/health-records/{record_id}",
        headers=headers,
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"

    # Verify deleted
    get_del = client.get(
        f"/api/v1/records/pets/{pet_id}/health-records/{record_id}",
        headers=headers,
    )
    assert get_del.status_code == 404


def test_medication_crud() -> None:
    headers, pet_id = setup_auth_and_pet()

    # Create medication
    med_res = client.post(
        f"/api/v1/records/pets/{pet_id}/medications",
        json={
            "name": "Amoxicillin",
            "dosage": "250mg",
            "frequency": "Twice daily with meals",
            "start_date": "2026-05-01",
            "end_date": "2026-05-10",
            "notes": "Course for skin infection",
        },
        headers=headers,
    )
    assert med_res.status_code == 201, med_res.text
    med = med_res.json()
    med_id = med["id"]
    assert med["name"] == "Amoxicillin"

    # List medications
    list_res = client.get(f"/api/v1/records/pets/{pet_id}/medications", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Update medication
    update_res = client.put(
        f"/api/v1/records/pets/{pet_id}/medications/{med_id}",
        json={"frequency": "Once daily with meals"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["frequency"] == "Once daily with meals"

    # Delete medication
    del_res = client.delete(f"/api/v1/records/pets/{pet_id}/medications/{med_id}", headers=headers)
    assert del_res.status_code == 200


def test_vaccination_crud() -> None:
    headers, pet_id = setup_auth_and_pet()

    # Create vaccination
    vac_res = client.post(
        f"/api/v1/records/pets/{pet_id}/vaccinations",
        json={
            "vaccine_name": "Rabies 3-Year",
            "administered_date": "2026-01-10",
            "next_due_date": "2029-01-10",
            "notes": "Tag #8912 issued by City Vet",
        },
        headers=headers,
    )
    assert vac_res.status_code == 201, vac_res.text
    vac = vac_res.json()
    vac_id = vac["id"]
    assert vac["vaccine_name"] == "Rabies 3-Year"

    # List vaccinations
    list_res = client.get(f"/api/v1/records/pets/{pet_id}/vaccinations", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Update vaccination
    update_res = client.put(
        f"/api/v1/records/pets/{pet_id}/vaccinations/{vac_id}",
        json={"notes": "Updated: Tag #8912 certified"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["notes"] == "Updated: Tag #8912 certified"

    # Delete vaccination
    del_res = client.delete(f"/api/v1/records/pets/{pet_id}/vaccinations/{vac_id}", headers=headers)
    assert del_res.status_code == 200
