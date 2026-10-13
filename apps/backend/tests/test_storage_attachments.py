from __future__ import annotations

import io
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.storage import (
    LocalStorageProvider,
    StorageService,
    get_storage_service,
)

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

# Create temporary upload directory for tests
test_temp_dir = tempfile.mkdtemp()
test_storage_provider = LocalStorageProvider(base_dir=test_temp_dir)
test_storage_service = StorageService(provider=test_storage_provider)


def override_get_storage_service():
    return test_storage_service


app.dependency_overrides[get_storage_service] = override_get_storage_service
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def cleanup_temp_dir():
    yield
    shutil.rmtree(test_temp_dir, ignore_errors=True)


def setup_auth_and_pet() -> tuple[dict[str, str], str]:
    email = f"storage_owner_{Path(tempfile.mktemp()).name}@example.com"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Storage Owner", "email": email, "password": "Password123!"},
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pet_res = client.post(
        "/api/v1/pets",
        json={
            "name": "Oliver",
            "species": "cat",
            "breed": "British Shorthair",
            "sex": "male",
            "weight_kg": 4.5,
        },
        headers=headers,
    )
    assert pet_res.status_code == 201
    return headers, pet_res.json()["id"]


def test_storage_provider_unit() -> None:
    provider = LocalStorageProvider(base_dir=test_temp_dir)
    test_content = b"%PDF-1.4 test document content"
    filename = "test_doc.pdf"

    url = provider.save(filename, test_content, "application/pdf")
    assert "/api/v1/records/attachments/test_doc.pdf" in url

    path = provider.get_file_path(filename)
    assert path is not None
    assert path.read_bytes() == test_content

    # Path traversal protection
    with pytest.raises(HTTPException):
        provider._get_safe_path("../../secret.txt")

    # Deletion
    deleted = provider.delete(filename)
    assert deleted is True
    assert provider.get_file_path(filename) is None


def test_upload_attachment_api() -> None:
    headers, pet_id = setup_auth_and_pet()

    # Upload valid PDF
    pdf_content = b"%PDF-1.4 sample vaccination certificate"
    files = {"file": ("vaccine_card.pdf", io.BytesIO(pdf_content), "application/pdf")}
    res = client.post(f"/api/v1/records/pets/{pet_id}/attachments", headers=headers, files=files)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["original_filename"] == "vaccine_card.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["size_bytes"] == len(pdf_content)
    assert "url" in data
    uploaded_filename = data["filename"]

    # Verify attachment retrieval endpoint
    retrieve_res = client.get(f"/api/v1/records/attachments/{uploaded_filename}")
    assert retrieve_res.status_code == 200
    assert retrieve_res.content == pdf_content


def test_upload_unsupported_file_rejected() -> None:
    headers, pet_id = setup_auth_and_pet()

    exe_content = b"MZ executable binary"
    files = {"file": ("malicious.exe", io.BytesIO(exe_content), "application/x-msdownload")}
    res = client.post(f"/api/v1/records/pets/{pet_id}/attachments", headers=headers, files=files)
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]


def test_upload_empty_file_rejected() -> None:
    headers, pet_id = setup_auth_and_pet()

    empty_content = b""
    files = {"file": ("empty.png", io.BytesIO(empty_content), "image/png")}
    res = client.post(f"/api/v1/records/pets/{pet_id}/attachments", headers=headers, files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_attach_file_directly_to_health_record() -> None:
    headers, pet_id = setup_auth_and_pet()

    # Create visit record without attachment
    create_rec = client.post(
        f"/api/v1/records/pets/{pet_id}/health-records",
        json={"type": "visit", "description": "Routine dental cleaning", "date": "2026-06-10"},
        headers=headers,
    )
    assert create_rec.status_code == 201
    record_id = create_rec.json()["id"]

    # Attach lab report image
    image_content = b"\x89PNG\r\n\x1a\nfake png dental radiograph"
    files = {"file": ("xray.png", io.BytesIO(image_content), "image/png")}
    attach_res = client.post(
        f"/api/v1/records/pets/{pet_id}/health-records/{record_id}/attachment",
        headers=headers,
        files=files,
    )
    assert attach_res.status_code == 200, attach_res.text
    updated = attach_res.json()
    assert updated["id"] == record_id
    assert updated["attachment_url"] is not None
    assert "/api/v1/records/attachments/" in updated["attachment_url"]


def test_attachment_not_found() -> None:
    res = client.get("/api/v1/records/attachments/non_existent_file.pdf")
    assert res.status_code == 404
