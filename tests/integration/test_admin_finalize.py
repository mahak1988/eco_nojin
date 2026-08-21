"""Tests: admin overview (metrics) + security (login history) endpoints."""
import pytest
from fastapi.testclient import TestClient

from engine.hydroma.core.database import Base, engine
from database.config import SessionLocal
from database import models as db_models
from services.api_gateway.auth import hash_password
from services.api_gateway.main import app


@pytest.fixture()
def admin_client():
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
    client = TestClient(app)
    # one successful + one failed login -> audit rows
    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "boss@test.com", "password": "testpass123"},
    )
    assert ok.status_code == 200
    client.post(
        "/api/v1/auth/login",
        json={"email": "boss@test.com", "password": "wrongpass"},
    )
    token = ok.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client


def test_overview_counts_and_uptime(admin_client):
    resp = admin_client.get("/api/v1/admin/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["counts"]["users"] == 2
    assert data["counts"]["audit_entries"] >= 2  # 1 ok + 1 failed login
    assert data["uptime_seconds"] >= 0
    assert "recent_audit" in data and isinstance(data["recent_audit"], list)


def test_overview_error_counts_honest(admin_client):
    db = SessionLocal()
    db.add(
        db_models.ErrorLog(
            path="/api/v1/x", method="GET", status=500, message="boom", acked=False
        )
    )
    db.commit()
    db.close()
    resp = admin_client.get("/api/v1/admin/overview")
    data = resp.json()
    assert data["counts"]["errors_total"] == 1
    assert data["counts"]["errors_open"] == 1
    assert data["recent_errors"][0]["path"] == "/api/v1/x"


def test_security_login_history(admin_client):
    resp = admin_client.get("/api/v1/admin/security")
    assert resp.status_code == 200
    events = resp.json()["events"]
    assert len(events) >= 2
    ok_events = [e for e in events if e["detail"].startswith("ok")]
    fail_events = [e for e in events if e["detail"].startswith("failed")]
    assert len(ok_events) >= 1
    assert len(fail_events) >= 1


def test_security_requires_admin_role():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(
        db_models.User(
            email="farmer2@test.com",
            full_name="f",
            hashed_password=hash_password("testpass123"),
            role="farmer",
            is_active=True,
        )
    )
    db.commit()
    db.close()
    client = TestClient(app)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer2@test.com", "password": "testpass123"},
    )
    token = r.json()["access_token"]
    resp = client.get(
        "/api/v1/admin/security", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
