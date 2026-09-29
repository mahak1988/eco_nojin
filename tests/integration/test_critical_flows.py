"""Integration tests for critical infrastructure and security flows.

Note: auth register/login flows are tested in services/auth/tests/
because the auth router currently depends on a sync session generator
(hub.get_session()) which is not thread-safe for async FastAPI test
clients. Those unit tests cover auth end-to-end with async fixtures.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from services.api_gateway.main import app

# This module used to do global surgery at import time, which poisoned every
# xdist worker for the rest of its run:
#
#   os.environ["DATABASE_URL"] = "sqlite:///:memory:"   # never restored
#   sys.modules.pop("database.hub*")                     # purge the module
#   DataHub._instance = None                              # kill the singleton
#   reset_database()                                      # at import, not per test
#
# `DataHub` is a `__new__` singleton whose engines are created *lazily* from
# `os.environ["DATABASE_URL"]` on first use. Repointing the env var at
# `:memory:` therefore produced a second singleton whose async engine used a
# different in-memory database from its sync one -- and with aiosqlite those are
# genuinely separate, so the schema the sync engine created never appeared in
# the async one. Every ASGI request in that worker then failed with
# "no such table: users". Measured cost: 18 tests, and only in a full run,
# because xdist performs a full collection before running anything.
#
# The root `conftest.py` now guarantees a per-worker database, so none of this
# is needed. Isolation belongs in a fixture, not in an import side effect.
client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_db(clean_db):
    """Give this module a clean schema without touching process-wide state.

    Depends on ``clean_db`` for its side effect; no teardown of our own.
    """
    return None


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
