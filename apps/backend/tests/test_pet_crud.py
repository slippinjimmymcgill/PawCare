from __future__ import annotations

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


def register_user(email: str = "petowner@example.com") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Pet Owner", "email": email, "password": "Password123!"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_pet_crud_and_archive_flow() -> None:
    token = register_user()
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/pets",
        json={
            "name": "Luna",
            "species": "dog",
            "breed": "Cocker Spaniel",
            "sex": "female",
            "date_of_birth": "2021-06-01",
            "weight_kg": 18.5,
            "allergies": "None known",
            "medical_history": "Recovered from mild ear infection in 2024.",
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    pet_id = created["id"]
    assert created["name"] == "Luna"

    list_response = client.get("/api/v1/pets", headers=headers)
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()) == 1

    update_response = client.put(
        "/api/v1/pets/" + pet_id,
        json={"name": "Luna Updated", "weight_kg": 19.2},
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["name"] == "Luna Updated"
    assert update_response.json()["weight_kg"] == 19.2

    delete_response = client.delete(f"/api/v1/pets/{pet_id}", headers=headers)
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["status"] == "ok"

    get_after_delete = client.get(f"/api/v1/pets/{pet_id}", headers=headers)
    assert get_after_delete.status_code == 404, get_after_delete.text
