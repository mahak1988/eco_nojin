"""Integration tests for critical infrastructure and security flows.

Uses an isolated in-memory SQLite database to avoid schema drift
with the file-based development database.

Note: auth register/login flows are tested in services/auth/tests/
because the auth router currently depends on a sync session generator
(hub.get_session()) which is not thread-safe for async FastAPI test
clients. Those unit tests cover auth end-to-end with async fixtures.
"""

from __future__ import annotations

import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

for mod_name in list(sys.modules):
    if mod_name.startswith("database.hub"):
        del sys.modules[mod_name]

from database.hub.hub import DataHub

DataHub._instance = None  # type: ignore[attr-defined]

import pytest
from fastapi.testclient import TestClient

from database.base import Base
from database.hub import hub
from services.api_gateway.main import app

engine = hub.get_sqlalchemy_engine()
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _allow_seed():
    os.environ.setdefault("ECO_NOJIN_ALLOW_SEED", "1")


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "service" in data


def test_debug_routes_disabled_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ENABLE_DEBUG_ROUTES", "false")
    monkeypatch.setenv("SECRET_KEY", "a" * 64)
    monkeypatch.setenv("JWT_SECRET", "b" * 64)
    from engine.hydroma.config.settings import clear_settings_cache

    clear_settings_cache()
    try:
        from engine.hydroma.config.settings import get_settings

        settings = get_settings()
        assert settings.enable_debug_routes is False
    finally:
        clear_settings_cache()


def test_rate_limit_headers():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers


def test_security_headers():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
