"""Phase 5 modules 2-5 integration tests (content, bots, errors, settings)."""
from fastapi.testclient import TestClient

from database.models import Base
from database.config import engine
from services.api_gateway.main import app
from tests.conftest import TEST_SESSION_FACTORY as SessionLocal
from database import models
from services.api_gateway.auth import hash_password

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _make_admin():
    db = SessionLocal()
    u = models.User(
        email="boss@test.com",
        full_name="boss",
        hashed_password=hash_password("testpass123"),
        role="admin",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()
    resp = client.post("/api/v1/auth/login", json={"email": "boss@test.com", "password": "testpass123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

def test_content_crud_and_publish():
    h = _make_admin()

    # create
    resp = client.post(
        "/api/v1/admin/content",
        json={"title": "کمپوست چیست", "body": "متن آموزشی", "category": "soil", "language": "fa"},
        headers=h,
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["status"] == "draft"

    # update
    resp = client.put(f"/api/v1/admin/content/{item['id']}", json={"title": "کمپوست و کربن"}, headers=h)
    assert resp.status_code == 200
    assert resp.json()["title"] == "کمپوست و کربن"

    # publish
    resp = client.post(f"/api/v1/admin/content/{item['id']}/publish", headers=h)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # list
    resp = client.get("/api/v1/admin/content", headers=h)
    assert resp.status_code == 200
    assert resp.json()[0]["status"] == "published"

    # invalid category rejected
    resp = client.post(
        "/api/v1/admin/content",
        json={"title": "x", "body": "y", "category": "bogus"},
        headers=h,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Bots
# ---------------------------------------------------------------------------

def test_bots_list_and_toggle():
    h = _make_admin()
    resp = client.get("/api/v1/admin/bots", headers=h)
    assert resp.status_code == 200
    keys = {b["key"] for b in resp.json()}
    assert {"telegram", "eitaa", "bale", "rubika"} <= keys

    resp = client.post("/api/v1/admin/bots/eitaa/toggle", headers=h)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # persisted flag visible in subsequent list
    resp = client.get("/api/v1/admin/bots", headers=h)
    eitaa = next(b for b in resp.json() if b["key"] == "eitaa")
    assert "enabled" in eitaa


def test_bots_unknown_platform_404():
    h = _make_admin()
    resp = client.post("/api/v1/admin/bots/nope/toggle", headers=h)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

def test_errors_list_and_ack():
    h = _make_admin()
    db = SessionLocal()
    db.add(models.ErrorLog(path="/api/v1/boom", method="GET", status=500, message="boom"))
    db.commit()
    db.close()

    resp = client.get("/api/v1/admin/errors", headers=h)
    assert resp.status_code == 200
    err = resp.json()[0]
    assert err["path"] == "/api/v1/boom"

    resp = client.post(f"/api/v1/admin/errors/{err['id']}/ack", headers=h)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def test_settings_update_and_validation():
    h = _make_admin()
    resp = client.put("/api/v1/admin/settings/site_announcement", json={"value": "تعمیرات شبانه"}, headers=h)
    assert resp.status_code == 200
    assert resp.json()["value"] == "تعمیرات شبانه"

    resp = client.get("/api/v1/admin/settings", headers=h)
    assert any(s["key"] == "site_announcement" for s in resp.json())

    # unknown key rejected
    resp = client.put("/api/v1/admin/settings/not_a_key", json={"value": "x"}, headers=h)
    assert resp.status_code == 422
