from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db import session as db_session
from app.db.base import Base
from app.db.session import get_db
from app.main import app

settings = get_settings()

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)

db_session.engine = engine
db_session.SessionLocal = TestingSessionLocal

client = TestClient(app)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db


def test_register_and_login_flow() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "user@example.com", "password": "Password123!"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["email"] == "user@example.com"
    assert "password" not in body["user"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    assert token

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["email"] == "user@example.com"

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_response.status_code == 200, logout_response.text

    repeated = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert repeated.status_code == 401


def test_password_reset_flow() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Reset User", "email": "reset@example.com", "password": "Password123!"},
    )
    assert response.status_code == 201

    reset_request = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset@example.com"},
    )
    assert reset_request.status_code == 200

    token = reset_request.json()["reset_token"]
    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"email": "reset@example.com", "token": token, "new_password": "NewPassword456!"},
    )
    assert confirm.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "NewPassword456!"},
    )
    assert login_response.status_code == 200
