"""Phase 0 tests: rate limiting + security headers middleware."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api_gateway.security import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)


def _build_app(limit: int = 5, window: int = 60, enabled: bool = True) -> FastAPI:
    """Build a test app with small rate-limit values.

    Starlette builds middleware stack outermost-last, so the rate
    limiter must be added last to wrap the security middleware.
    """
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, limit=limit, window=window, enabled=enabled)
    return app


class TestRateLimit:
    def test_under_limit_ok(self):
        client = TestClient(_build_app(limit=5))
        for _ in range(5):
            assert client.get("/ping").status_code == 200

    def test_over_limit_429(self):
        client = TestClient(_build_app(limit=3))
        for _ in range(3):
            assert client.get("/ping").status_code == 200
        r = client.get("/ping")
        assert r.status_code == 429
        body = r.json()
        assert "retry_after_seconds" in body
        assert "Retry-After" in r.headers

    def test_disabled_ok(self):
        client = TestClient(_build_app(limit=1, enabled=False))
        for _ in range(10):
            assert client.get("/ping").status_code == 200


class TestHeaders:
    def test_security_headers_present(self):
        client = TestClient(_build_app())
        r = client.get("/ping")
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "X-Request-ID" in r.headers

    def test_request_id_echoed(self):
        client = TestClient(_build_app())
        r = client.get("/ping", headers={"X-Request-ID": "abc123"})
        assert r.headers["X-Request-ID"] == "abc123"
