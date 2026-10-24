"""ASVS-lite security regression tests for the gateway hardening work.

Four layers are pinned here, each with the minimal app + dependency-override
pattern used by ``test_http_*.py`` and ``test_finance_router_wallet.py``:

1. **Security headers** — the hardened header set is present on a sample
   route (including error responses), and ``Strict-Transport-Security`` is
   sent only when the request arrived over HTTPS.
2. **Auth rate limiting** — the credential endpoints return 429 with a
   ``Retry-After`` once the bucket is spent, refill after the window, and are
   completely inert when disabled (the escape the test suite relies on).
3. **Bank-transfer webhook** — the payment webhook maps a bank callback onto
   the provider's real, idempotent verification path (200, then an
   acknowledged duplicate) instead of raising ``AttributeError`` on a method
   that exists nowhere; unknown providers are a 4xx, never a 500.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from database.models import AuditEvent, ComPaymentIntent
from services.api_gateway.middleware.rate_limit import (
    DEFAULT_PROTECTED_PATHS,
    AuthRateLimitMiddleware,
)
from services.api_gateway.middleware.security_headers import (
    SecurityHeadersMiddleware as GatewaySecurityHeadersMiddleware,
)
from services.api_gateway.security import (
    SecurityHeadersMiddleware as ApiSecurityHeadersMiddleware,
)
from services.finance.payment_provider import payment_registry
from services.finance.routers.finance import get_db as finance_get_db
from services.finance.routers.finance import router as finance_router

_WEBHOOK_URL = "/api/v1/finance/payments/webhook"
_WEBHOOK_SECRET = "test-bank-webhook-secret"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _db_override(session):
    async def _override():
        yield session

    return _override


def _add_error_handlers(app: FastAPI) -> FastAPI:
    """Keep an unexpected error a 500 response, never a transport crash."""

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def _server_error_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    return app


def _sample_headers_app() -> FastAPI:
    """The same two-layer header stack the gateway mounts, in the same order.

    ``services.api_gateway.security`` (inner) owns the Content-Security-Policy;
    ``middleware.security_headers`` (outer) owns the conditional HSTS and the
    rest of the ASVS-lite set. Since 2026-10-12 the CSP is declared in exactly
    one layer (review finding 8) — this app reproduces the real stack so the
    header tests assert the wire, not a layer's private constants.
    """
    app = FastAPI()
    app.add_middleware(ApiSecurityHeadersMiddleware)
    app.add_middleware(GatewaySecurityHeadersMiddleware)

    @app.get("/sample")
    async def sample():
        return {"ok": True}

    @app.get("/docs")
    async def docs_page():
        return {"ok": True}

    @app.get("/redoc")
    async def redoc_page():
        return {"ok": True}

    return app


def _limiter_app(**kwargs) -> AuthRateLimitMiddleware:
    """A tiny ASGI stack whose only routes are one protected and one plain."""

    inner = FastAPI()

    @inner.post("/api/v1/auth/login")
    async def login():
        return {"ok": True}

    @inner.post("/api/v1/other")
    async def other():
        return {"ok": True}

    return AuthRateLimitMiddleware(inner, **kwargs)


# ===========================================================================
# 1. Security headers
# ===========================================================================


class TestSecurityHeaders:
    def test_standard_headers_are_present(self):
        client = TestClient(_sample_headers_app())
        response = client.get("/sample")

        assert response.status_code == 200, response.text
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert response.headers["Permissions-Policy"]
        # the gateway is a JSON API: deny every source class by default
        assert "default-src 'none'" in response.headers["Content-Security-Policy"]

    def test_csp_is_conservative(self):
        response = TestClient(_sample_headers_app()).get("/sample")
        csp = response.headers["Content-Security-Policy"]

        assert "default-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "base-uri 'none'" in csp
        assert "form-action 'none'" in csp

    def test_docs_paths_get_the_scoped_policy_with_the_redoc_fonts(self):
        client = TestClient(_sample_headers_app())

        for path in ("/docs", "/redoc"):
            csp = client.get(path).headers["Content-Security-Policy"]
            assert "default-src 'self'" in csp
            assert "script-src 'self' https://cdn.jsdelivr.net" in csp
            # ReDoc pulls Google Fonts; without these two hosts it renders
            # un-styled (2026-10-12 review finding 7)
            assert "https://fonts.googleapis.com" in csp
            assert "font-src 'self' https://fonts.gstatic.com" in csp

    def test_hsts_is_absent_over_plain_http(self):
        response = TestClient(_sample_headers_app()).get("/sample")
        assert "Strict-Transport-Security" not in response.headers

    def test_hsts_is_present_over_https(self):
        client = TestClient(_sample_headers_app(), base_url="https://testserver")
        response = client.get("/sample")

        assert response.headers["Strict-Transport-Security"].startswith("max-age=")
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]

    def test_hsts_follows_forwarded_proto(self):
        client = TestClient(_sample_headers_app())
        response = client.get("/sample", headers={"X-Forwarded-Proto": "https"})
        assert "Strict-Transport-Security" in response.headers

        plain = client.get("/sample", headers={"X-Forwarded-Proto": "http"})
        assert "Strict-Transport-Security" not in plain.headers

    def test_headers_are_added_to_error_responses(self):
        response = TestClient(_sample_headers_app()).get("/does-not-exist")
        assert response.status_code == 404
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" in response.headers


# ===========================================================================
# 2. Auth rate limiting
# ===========================================================================


class TestAuthRateLimit:
    def test_protected_paths_are_the_credential_routes(self):
        assert DEFAULT_PROTECTED_PATHS == {
            "/api/v1/auth/login",
            "/api/v1/auth/token",
            "/api/v1/auth/refresh",
            "/api/v1/auth/register",
        }

    def test_returns_429_with_retry_after_once_the_bucket_is_spent(self, monkeypatch):
        monkeypatch.setenv("HYDROMA_AUTH_RATE_LIMIT_ENABLED", "true")
        client = TestClient(_limiter_app(max_requests=2, window_seconds=60))

        assert client.post("/api/v1/auth/login").status_code == 200
        assert client.post("/api/v1/auth/login").status_code == 200
        limited = client.post("/api/v1/auth/login")

        assert limited.status_code == 429, limited.text
        assert int(limited.headers["Retry-After"]) >= 1
        assert "detail" in limited.json()

    def test_bucket_refills_after_the_window(self, monkeypatch):
        monkeypatch.setenv("HYDROMA_AUTH_RATE_LIMIT_ENABLED", "true")
        limiter = _limiter_app(max_requests=1, window_seconds=60)
        clock = {"now": time.monotonic()}
        limiter._now = lambda: clock["now"]
        client = TestClient(limiter)

        assert client.post("/api/v1/auth/login").status_code == 200
        assert client.post("/api/v1/auth/login").status_code == 429

        clock["now"] += 61  # a full window later the token is back
        assert client.post("/api/v1/auth/login").status_code == 200

    def test_unprotected_routes_are_never_limited(self):
        client = TestClient(_limiter_app(max_requests=1, window_seconds=60))
        for _ in range(5):
            assert client.post("/api/v1/other").status_code == 200

    def test_preflight_is_not_charged_to_the_bucket(self):
        client = TestClient(_limiter_app(max_requests=1, window_seconds=60))
        assert client.options("/api/v1/auth/login").status_code != 429
        assert client.post("/api/v1/auth/login").status_code == 200

    def test_limits_are_configurable_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("HYDROMA_AUTH_RATE_LIMIT_ENABLED", "true")
        monkeypatch.setenv("HYDROMA_AUTH_RATE_LIMIT_MAX_REQUESTS", "1")
        monkeypatch.setenv("HYDROMA_AUTH_RATE_LIMIT_WINDOW_SECONDS", "30")
        client = TestClient(_limiter_app())

        assert client.post("/api/v1/auth/login").status_code == 200
        limited = client.post("/api/v1/auth/login")
        assert limited.status_code == 429
        assert int(limited.headers["Retry-After"]) <= 30

    def test_disabled_layer_is_inert(self, monkeypatch):
        monkeypatch.setenv("HYDROMA_AUTH_RATE_LIMIT_ENABLED", "false")
        client = TestClient(_limiter_app())
        for _ in range(10):
            assert client.post("/api/v1/auth/login").status_code == 200

    def test_explicitly_disabled_layer_is_inert(self):
        client = TestClient(_limiter_app(enabled=False, max_requests=1, window_seconds=60))
        for _ in range(10):
            assert client.post("/api/v1/auth/login").status_code == 200


# ===========================================================================
# 3. Bank-transfer webhook
# ===========================================================================


async def _seed_intent(session, payment_id: str, amount: str = "150000") -> None:
    session.add(
        ComPaymentIntent(
            id=payment_id,
            order_id="ord-wh-1",
            provider="bank_transfer",
            amount=Decimal(amount),
            currency="IRR",
            status="awaiting_transfer",
            provider_reference="BT-wh-1",
            payment_metadata={"idempotency_key": "wh-key"},
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


@pytest.fixture
async def webhook_app(db_session, monkeypatch):
    monkeypatch.setenv("BANK_WEBHOOK_SECRET", _WEBHOOK_SECRET)
    app = FastAPI()
    app.include_router(finance_router)
    app.dependency_overrides[finance_get_db] = _db_override(db_session)
    _add_error_handlers(app)
    yield app, db_session


def _sign(raw: bytes) -> str:
    return hmac.new(
        _WEBHOOK_SECRET.encode("utf-8"), raw, hashlib.sha256
    ).hexdigest()


async def _post_webhook(app, provider: str, payload, *, raw: bytes | None = None):
    body = raw if raw is not None else json.dumps(payload).encode("utf-8")
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        return await client.post(
            f"{_WEBHOOK_URL}/{provider}",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Signature": _sign(body),
            },
        )


@pytest.mark.asyncio
class TestBankTransferWebhook:
    async def test_callback_marks_the_payment_succeeded(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-wh-ok")

        response = await _post_webhook(
            app,
            "bank_transfer",
            {"event_id": "evt-wh-1", "payment_id": "pay-wh-ok", "amount": 150000},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["processed"] is True
        assert body["event_id"] == "evt-wh-1"
        assert body["outcome"]["status"] == "succeeded"
        assert body["outcome"]["duplicate"] is False

        row = await session.get(ComPaymentIntent, "pay-wh-ok")
        assert row is not None
        assert row.status == "succeeded"

    async def test_redelivered_callback_is_acknowledged_not_replayed(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-wh-dup")
        payload = {"event_id": "evt-wh-2", "payment_id": "pay-wh-dup", "amount": 150000}

        first = await _post_webhook(app, "bank_transfer", payload)
        second = await _post_webhook(app, "bank_transfer", payload)

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert second.json()["outcome"]["duplicate"] is True

        audits = await session.execute(
            select(AuditEvent).where(AuditEvent.resource_id == "pay-wh-dup")
        )
        assert len(audits.scalars().all()) == 1  # verified exactly once

    async def test_partial_transfer_is_recorded(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-wh-partial")

        response = await _post_webhook(
            app,
            "bank_transfer",
            {"event_id": "evt-wh-3", "payment_id": "pay-wh-partial", "amount": 1000},
        )

        assert response.status_code == 200, response.text
        assert response.json()["outcome"]["status"] == "partial"
        row = await session.get(ComPaymentIntent, "pay-wh-partial")
        assert row.status == "partial"

    async def test_unknown_provider_is_400_not_500(self, webhook_app):
        app, _ = webhook_app
        response = await _post_webhook(
            app, "no_such_provider", {"payment_id": "pay-wh-ok", "amount": 150000}
        )
        assert response.status_code == 400
        assert "Unknown payment provider" in response.json()["detail"]

    async def test_provider_without_webhook_support_is_501(self, webhook_app, monkeypatch):
        app, _ = webhook_app
        # The route used to call provider.handle_webhook — a method that exists
        # nowhere — so every webhook raised AttributeError (500). A registered
        # provider with no webhook support must be a clear 501 instead.
        registry = dict(payment_registry._providers)
        registry["wallet"] = SimpleNamespace(provider_name="wallet")
        monkeypatch.setattr(payment_registry, "_providers", registry)

        response = await _post_webhook(app, "wallet", {"payment_id": "x", "amount": 1})

        assert response.status_code == 501, response.text
        assert "does not support webhook" in response.json()["detail"]

    async def test_malformed_payload_is_400(self, webhook_app):
        app, _ = webhook_app
        response = await _post_webhook(app, "bank_transfer", None, raw=b"not-json")
        assert response.status_code == 400

    async def test_payload_without_payment_id_is_400(self, webhook_app):
        app, _ = webhook_app
        response = await _post_webhook(app, "bank_transfer", {"amount": 150000})
        assert response.status_code == 400
        assert "payment_id" in response.json()["detail"]

    async def test_unknown_payment_is_404(self, webhook_app):
        app, _ = webhook_app
        response = await _post_webhook(
            app,
            "bank_transfer",
            {"event_id": "evt-wh-4", "payment_id": "pay-wh-missing", "amount": 150000},
        )
        assert response.status_code == 404
