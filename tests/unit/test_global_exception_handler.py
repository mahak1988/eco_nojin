"""Regression tests for the catch-all 500 handler.

The handler gated its diagnostic detail on ``_settings.app_env == "development"``.
Because a misconfigured ``ENVIRONMENT`` silently satisfied that condition, every
unhandled 500 in production returned the raw exception text, the exception class
name and the request path to the client. The gate is now the explicit ``debug``
flag, and a stable error id is returned for support correlation.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from services.api_gateway import main as gw_main


class _Exploding(Exception):
    """Exception carrying an internal-only message."""

    def __str__(self) -> str:
        return "psycopg2.errors.UndefinedColumn: column users.ssn does not exist"


@pytest.fixture
def handler_app(monkeypatch):
    """Minimal app carrying the real catch-all handler and a request id."""
    app = FastAPI()

    @app.get("/boom")
    async def _boom(request: Request):
        raise _Exploding()

    @app.middleware("http")
    async def _request_id(request: Request, call_next):
        request.state.request_id = "req-test-1234"
        return await call_next(request)

    # Register the handler under test: an Exception handler is a ServerErrorMiddleware
    # re-raise, so TestClient(raise_server_exceptions=False) surfaces the response.
    app.add_exception_handler(Exception, gw_main.global_exception_handler)
    return app


def _client(handler_app) -> TestClient:
    return TestClient(handler_app, raise_server_exceptions=False)


def test_production_response_hides_exception_detail(handler_app, monkeypatch):
    """Raw exception text and class name must not reach a non-debug client."""
    monkeypatch.setattr(gw_main._settings, "debug", False)

    with _client(handler_app) as c:
        r = c.get("/boom")

    assert r.status_code == 500
    body = r.json()
    assert body["detail"] == "Internal server error"
    assert "error_type" not in body
    assert "ssn" not in r.text, "internal column name leaked to the client"
    assert "_Exploding" not in r.text, "exception class name leaked to the client"


def test_production_response_is_correlatable(handler_app, monkeypatch):
    """A stable error id plus the request id lets support find the traceback."""
    monkeypatch.setattr(gw_main._settings, "debug", False)

    with _client(handler_app) as c:
        r = c.get("/boom")

    body = r.json()
    assert body["error_id"] == "req-test-1234"
    assert r.headers.get("X-Request-ID") == "req-test-1234"


def test_debug_response_includes_detail_for_development(handler_app, monkeypatch):
    """With debug explicitly enabled the detail is still available locally."""
    monkeypatch.setattr(gw_main._settings, "debug", True)

    with _client(handler_app) as c:
        r = c.get("/boom")

    body = r.json()
    assert body["error_type"] == "_Exploding"
    assert "ssn" in body["detail"]
    assert body["error_id"] == "req-test-1234"


def test_response_always_carries_a_path(handler_app, monkeypatch):
    monkeypatch.setattr(gw_main._settings, "debug", False)

    with _client(handler_app) as c:
        body = c.get("/boom").json()

    assert body["path"] == "/boom"


def test_handler_is_stable_under_repeated_failures(handler_app, monkeypatch):
    """No cross-request leakage through module-level state."""
    monkeypatch.setattr(gw_main._settings, "debug", False)

    with _client(handler_app) as c:
        first = c.get("/boom").json()
        second = c.get("/boom").json()

    assert first == second


def test_eco_nojin_exception_still_surfaces_its_own_detail(monkeypatch):
    """Domain errors are intentional API contract, not leakage."""
    from services.api_gateway.exceptions import EcoNojinException

    app = FastAPI()

    @app.get("/domain")
    async def _domain():
        raise EcoNojinException("Insufficient balance", code="BALANCE_LOW", status_code=402)

    app.add_exception_handler(Exception, gw_main.global_exception_handler)
    monkeypatch.setattr(gw_main._settings, "debug", False)

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/domain")

    assert r.status_code == 402
    assert r.json()["code"] == "BALANCE_LOW"
