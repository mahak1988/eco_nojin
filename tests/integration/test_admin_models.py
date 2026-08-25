"""Tests for the Phase 5 models module (honest Ollama state)."""
import pytest
from fastapi.testclient import TestClient

from database.models import Base
from database.config import engine
from tests.conftest import TEST_SESSION_FACTORY as SessionLocal
from database import models as db_models
from services.api_gateway.auth import hash_password
from services.api_gateway.main import app


@pytest.fixture()
def admin_client(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(
        db_models.User(
            email="boss@test.com",
            full_name="boss",
            hashed_password=hash_password("testpass123"),
            role="admin",
            is_active=True,
        )
    )
    db.commit()
    db.close()
    # Force Ollama unreachable -> deterministic honest behavior
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "0.2")
    client = TestClient(app)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "boss@test.com", "password": "testpass123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client


def test_models_list_honest_when_ollama_down(admin_client):
    resp = admin_client.get("/api/v1/admin/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data["models"] == []
    assert data["loaded"] == []
    assert "error" in data and data["error"]


def test_models_stop_honest_503_when_ollama_down(admin_client):
    resp = admin_client.post("/api/v1/admin/models/llama3.1:8b/stop")
    assert resp.status_code == 503
    assert "Ollama" in resp.json()["detail"]


def test_models_requires_admin_role(admin_client):
    # non-admin user
    db = SessionLocal()
    db.add(
        db_models.User(
            email="farmer@test.com",
            full_name="farmer",
            hashed_password=hash_password("testpass123"),
            role="farmer",
            is_active=True,
        )
    )
    db.commit()
    db.close()
    resp = admin_client.post(
        "/api/v1/auth/login",
        json={"email": "farmer@test.com", "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    resp = admin_client.get(
        "/api/v1/admin/models", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
