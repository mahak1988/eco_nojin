"""Auth refresh token tests (rotation, rejection of misuse)."""
from fastapi.testclient import TestClient

from engine.hydroma.core.database import Base, engine
from services.api_gateway.main import app

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _register():
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "rt@example.com",
            "password": "testpass123",
            "full_name": "RT",
            "accept_tos": True,
            "accept_privacy": True,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_login_returns_refresh_token():
    body = _register()
    assert body.get("refresh_token")
    assert body["refresh_token"] != body["access_token"]


def test_refresh_rotates_access_token():
    body = _register()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert new["access_token"]
    assert new["access_token"] != body["access_token"]
    # new access token works
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "rt@example.com"


def test_refresh_rejects_garbage():
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-token"})
    assert r.status_code == 401


def test_refresh_rejects_access_token():
    body = _register()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": body["access_token"]})
    assert r.status_code == 401
