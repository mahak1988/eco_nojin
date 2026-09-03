"""Tests: AI draft generation, scheduling, due-publisher, bot dispatch."""
import pytest
from fastapi.testclient import TestClient

from database.base import Base
from database.config import engine
from tests.conftest import TEST_SESSION_FACTORY as SessionLocal
from database import models  # noqa: F401
from database.hub import hub as db_models
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
    db.commit()
    db.close()
    client = TestClient(app)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "boss@test.com", "password": "testpass123"},
    )
    assert r.status_code == 200
    client.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    yield client


def _make(client, title="مقاله", body="متن مقاله"):
    r = client.post(
        "/api/v1/admin/content",
        json={"title": title, "body": body, "category": "water", "language": "fa"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_ai_draft_generation_ok(admin_client, monkeypatch):
    from services.bots.core import ai as ai_mod

    class FakeOllama:
        async def available(self):
            return True

        async def chat(self, system, user, temperature=0.4):
            return "مدیریت آب در خاکهای شور\n## مقدمه\n- نکته اول\n- نکته دوم"

    monkeypatch.setattr(ai_mod, "OllamaClient", lambda config: FakeOllama())
    r = admin_client.post(
        "/api/v1/admin/content/generate-draft?topic=آبیاری+قطرهای&category=water"
    )
    assert r.status_code == 200, r.text
    item = r.json()
    assert item["generated_by_ai"] is True
    assert item["source"] == "ai-generated"
    assert "## مقدمه" in item["body"]
    versions = admin_client.get(f"/api/v1/admin/content/{item['id']}/versions").json()
    assert len(versions) == 1


def test_ai_draft_honest_503_when_ollama_offline(admin_client, monkeypatch):
    from services.bots.core import ai as ai_mod

    class FakeOllama:
        async def available(self):
            return False

        async def chat(self, system, user, temperature=0.4):
            return None

    monkeypatch.setattr(ai_mod, "OllamaClient", lambda config: FakeOllama())
    r = admin_client.post(
        "/api/v1/admin/content/generate-draft?topic=test&category=water"
    )
    assert r.status_code == 503


def test_schedule_and_cancel(admin_client):
    item = _make(admin_client)
    r = admin_client.post(
        f"/api/v1/admin/content/{item['id']}/schedule?at=2030-01-01T00:00:00Z"
    )
    assert r.status_code == 200
    items = admin_client.get("/api/v1/admin/content").json()
    scheduled = [i for i in items if i["id"] == item["id"]][0]
    assert scheduled["scheduled_at"] is not None
    r2 = admin_client.post(f"/api/v1/admin/content/{item['id']}/cancel-schedule")
    assert r2.status_code == 200
    items = admin_client.get("/api/v1/admin/content").json()
    cancelled = [i for i in items if i["id"] == item["id"]][0]
    assert cancelled["scheduled_at"] is None


def test_schedule_rejects_bad_datetime(admin_client):
    item = _make(admin_client)
    r = admin_client.post(
        f"/api/v1/admin/content/{item['id']}/schedule?at=not-a-date"
    )
    assert r.status_code == 400


def test_due_publisher_publishes_past_schedule(admin_client):
    from datetime import datetime, timedelta, UTC

    item = _make(admin_client)
    db = SessionLocal()
    row = db.get(db_models.ContentItem, item["id"])
    row.scheduled_at = datetime.now(UTC) - timedelta(minutes=5)
    db.commit()
    db.close()
    from services.content.bot_dispatch import run_due_publishes

    db = SessionLocal()
    ids = run_due_publishes(db)
    db.close()
    assert item["id"] in ids
    items = admin_client.get("/api/v1/admin/content").json()
    published = [i for i in items if i["id"] == item["id"]][0]
    assert published["status"] == "published"
    assert published["rag_synced"] is True


def test_dispatch_honest_no_token(admin_client, monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    db = SessionLocal()
    db.add(db_models.Setting(key="content_auto_publish_bot", value="true"))
    db.commit()
    db.close()
    from services.content.bot_dispatch import dispatch_to_bots

    db = SessionLocal()
    result = dispatch_to_bots(db, "t", "b")
    db.close()
    assert result["dispatched"] == 0
    assert "BOT_TOKEN" in result["reason"]


def test_dispatch_sends_when_configured(admin_client, monkeypatch):
    import httpx as httpx_mod

    monkeypatch.setenv("BOT_TOKEN", "123:abc")
    db = SessionLocal()
    db.add(db_models.Setting(key="content_auto_publish_bot", value="true"))
    db.add(db_models.Setting(key="content_publish_channel", value="-100123"))
    db.commit()
    db.close()

    class FakeResp:
        def raise_for_status(self):
            return None

    def fake_post(url, json=None, timeout=None):
        return FakeResp()

    monkeypatch.setattr(httpx_mod, "post", fake_post)
    from services.content.bot_dispatch import dispatch_to_bots

    db = SessionLocal()
    result = dispatch_to_bots(db, "t", "b")
    db.close()
    assert result["dispatched"] == 1
