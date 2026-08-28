"""Integration tests for the Phase 5 admin API (RBAC + audit)."""
import pytest
from fastapi.testclient import TestClient

from database.models import Base
from services.api_gateway.main import app
from database import get_db
from tests.test_db import SessionLocal, engine as test_engine
from database import models
from services.api_gateway.auth import hash_password


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with DB override."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


def _make_user(email, role="regular", is_active=True, db_session=None):
    u = models.User(
        email=email,
        full_name=email.split("@")[0],
        hashed_password=hash_password("testpass123"),
        role=role,
        is_active=is_active,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u.id


def _login(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "testpass123"})
    print(f'Login status for {email}: {resp.status_code}')
    print(f'Login body: {resp.text[:200]}')
    assert resp.status_code == 200, f"Login failed with status {resp.status_code}: {resp.text}"
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_health_requires_admin_role(client, db_session):
    _make_user("farmer@test.com", role="farmer", db_session=db_session)
    token = _login(client, "farmer@test.com")
    resp = client.get("/api/v1/admin/health", headers=_auth(token))
    print(f'Admin health (farmer): {resp.status_code} - {resp.text[:100]}')
    assert resp.status_code == 403


def test_admin_health_ok_for_admin(client, db_session):
    _make_user("boss@test.com", role="admin", db_session=db_session)
    token = _login(client, "boss@test.com")
    resp = client.get("/api/v1/admin/health", headers=_auth(token))
    print(f'Admin health (admin): {resp.status_code} - {resp.text[:100]}')
    assert resp.status_code == 200


def test_admin_users_list_and_block_flow(client, db_session):
    boss_id = _make_user("boss@test.com", role="admin", db_session=db_session)
    _make_user("victim@test.com", role="farmer", is_active=True, db_session=db_session)
    token = _login(client, "boss@test.com")

    # List users
    resp = client.get("/api/v1/admin/users", headers=_auth(token))
    print(f'List users: {resp.status_code}')
    assert resp.status_code == 200

    # Block
    victims = [u for u in resp.json() if u["email"] == "victim@test.com"]
    victim_id = victims[0]["id"]
    resp = client.post(f"/api/v1/admin/users/{victim_id}/block", headers=_auth(token))
    assert resp.status_code == 200

    # Cannot block yourself
    resp = client.post(f"/api/v1/admin/users/{boss_id}/block", headers=_auth(token))
    assert resp.status_code == 400

    # Audit trail exists
    resp = client.get("/api/v1/admin/audit", headers=_auth(token))
    assert resp.status_code == 200
