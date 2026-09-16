"""Commerce/marketplace idempotency tests."""

import pytest
import uuid
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.testclient import TestClient

from services.api_gateway.middleware.idempotency import IdempotencyMiddleware, PROTECTED_PREFIXES


def _scope(method: str, path: str, headers: dict = None) -> dict:
    raw_headers = []
    for k, v in (headers or {}).items():
        raw_headers.append((k.lower().encode(), v.encode()))
    return {
        "type": "http",
        "method": method,
        "scheme": "http",
        "server": ("test", 80),
        "path": path,
        "query_string": b"",
        "headers": raw_headers,
        "http_version": "1.1",
        "client": ("127.0.0.1", 8000),
        "root_path": "",
        "app": None,
        "extensions": {},
    }


def _run_async(coro):
    import asyncio
    return asyncio.run(coro)


class TestIdempotencyMiddlewareDirect:
    """Test IdempotencyMiddleware behavior directly."""

    def test_requires_idempotency_for_marketplace_orders_post(self):
        m = IdempotencyMiddleware(app=None)
        assert m._requires_idempotency("/api/v1/marketplace/orders", "POST") is True

    def test_requires_idempotency_for_marketplace_orders_put(self):
        m = IdempotencyMiddleware(app=None)
        assert m._requires_idempotency("/api/v1/marketplace/orders", "PUT") is True

    def test_get_does_not_require_idempotency(self):
        m = IdempotencyMiddleware(app=None)
        assert m._requires_idempotency("/api/v1/marketplace/orders", "GET") is False

    def test_all_protected_prefixes_present(self):
        assert len(PROTECTED_PREFIXES) >= 5
        for prefix in PROTECTED_PREFIXES:
            assert prefix.startswith("/api/v1/")

    def test_finance_endpoints_protected(self):
        m = IdempotencyMiddleware(app=None)
        assert m._requires_idempotency("/api/v1/finance/wallet/earn", "POST") is True
        assert m._requires_idempotency("/api/v1/finance/wallet/redeem", "POST") is True
        assert m._requires_idempotency("/api/v1/finance/payments/intent", "POST") is True

    def test_marketplace_endpoints_protected(self):
        m = IdempotencyMiddleware(app=None)
        assert m._requires_idempotency("/api/v1/marketplace/payments", "POST") is True
        assert m._requires_idempotency("/api/v1/marketplace/orders", "POST") is True

    def test_non_protected_endpoints_free(self):
        m = IdempotencyMiddleware(app=None)
        assert m._requires_idempotency("/api/v1/products", "POST") is False
        assert m._requires_idempotency("/api/v1/commerce/orders", "POST") is False
        assert m._requires_idempotency("/api/v1/health", "POST") is False

    def test_invalid_uuid_rejected(self):
        m = IdempotencyMiddleware(app=None)

        async def call_next(req):
            return Response("ok")

        req = Request(_scope("POST", "/api/v1/marketplace/orders", {"Idempotency-Key": "not-uuid"}))
        resp = _run_async(m.dispatch(req, call_next))
        assert resp.status_code == 400
        body = resp.body.decode() if resp.body else ""
        assert "INVALID_IDEMPOTENCY_KEY" in body

    def test_missing_key_rejected(self):
        m = IdempotencyMiddleware(app=None)

        async def call_next(req):
            return Response("ok")

        req = Request(_scope("POST", "/api/v1/marketplace/orders"))
        resp = _run_async(m.dispatch(req, call_next))
        assert resp.status_code == 400
        body = resp.body.decode() if resp.body else ""
        assert "IDEMPOTENCY_KEY_REQUIRED" in body

    def test_non_money_endpoint_allowed_without_key(self):
        m = IdempotencyMiddleware(app=None)

        async def call_next(req):
            return Response("ok")

        req = Request(_scope("GET", "/api/v1/products"))
        resp = _run_async(m.dispatch(req, call_next))
        assert resp.status_code == 200

    def test_body_hash_deterministic(self):
        m = IdempotencyMiddleware(app=None)
        h1 = m._body_hash(b'{"a":1}')
        h2 = m._body_hash(b'{"a":1}')
        h3 = m._body_hash(b'{"a":2}')
        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 64

    def test_user_id_extraction(self):
        m = IdempotencyMiddleware(app=None)

        req = Request(_scope("POST", "/api/v1/marketplace/orders"))
        assert m._user_id(req) == "anonymous"

        req.state.user_id = "user-123"
        assert m._user_id(req) == "user-123"

    def test_protected_prefixes_complete_coverage(self):
        protected_endpoints = [
            ("/api/v1/finance/wallet/earn", "POST", True),
            ("/api/v1/finance/wallet/redeem", "POST", True),
            ("/api/v1/finance/wallet/redeem", "GET", False),
            ("/api/v1/finance/payments/intent", "POST", True),
            ("/api/v1/finance/payments/intent", "PUT", True),
            ("/api/v1/marketplace/payments", "POST", True),
            ("/api/v1/marketplace/payments/callback", "POST", True),
            ("/api/v1/marketplace/orders", "POST", True),
            ("/api/v1/marketplace/orders/123", "POST", True),
            ("/api/v1/marketplace/orders/123", "GET", False),
        ]
        m = IdempotencyMiddleware(app=None)
        for path, method, expected in protected_endpoints:
            assert m._requires_idempotency(path, method) == expected, (
                f"Failed: {method} {path}"
            )


class TestIdempotencyMiddlewareIntegration:
    """Integration tests using a minimal FastAPI app."""

    @pytest.fixture
    def app_with_middleware(self):
        from services.api_gateway.middleware.idempotency import IdempotencyMiddleware

        app = Starlette()
        app.add_middleware(IdempotencyMiddleware)

        async def create_order(request: Request):
            body = await request.json() if request.method == "POST" else {}
            return JSONResponse(status_code=201, content={"status": "created", "body": body})

        app.add_route("/api/v1/marketplace/orders", create_order, methods=["POST"])

        return app

    def test_first_post_accepted(self, app_with_middleware):
        client = TestClient(app_with_middleware)
        key = str(uuid.uuid4())
        resp = client.post(
            "/api/v1/marketplace/orders",
            json={"product_id": "p1"},
            headers={"Idempotency-Key": key},
        )
        assert resp.status_code == 201

    def test_duplicate_with_same_key_cached(self, app_with_middleware):
        client = TestClient(app_with_middleware)
        key = str(uuid.uuid4())
        body = {"product_id": "p1", "qty": 10}

        r1 = client.post("/api/v1/marketplace/orders", json=body, headers={"Idempotency-Key": key})
        r2 = client.post("/api/v1/marketplace/orders", json=body, headers={"Idempotency-Key": key})

        assert r1.status_code == r2.status_code == 201
        assert r1.json() == r2.json()

    def test_duplicate_with_different_payload_422(self, app_with_middleware):
        client = TestClient(app_with_middleware)
        key = str(uuid.uuid4())

        r1 = client.post(
            "/api/v1/marketplace/orders",
            json={"product_id": "p1"},
            headers={"Idempotency-Key": key},
        )
        r2 = client.post(
            "/api/v1/marketplace/orders",
            json={"product_id": "p2"},
            headers={"Idempotency-Key": key},
        )

        assert r1.status_code == 201
        assert r2.status_code == 422
        body = r2.json()
        assert "IDEMPOTENCY_KEY_REUSE" in str(body).upper()

    def test_different_keys_independent(self, app_with_middleware):
        client = TestClient(app_with_middleware)
        r1 = client.post(
            "/api/v1/marketplace/orders",
            json={"product_id": "p1"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        r2 = client.post(
            "/api/v1/marketplace/orders",
            json={"product_id": "p1"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert r1.status_code == r2.status_code == 201

    def test_get_bypasses_idempotency(self, app_with_middleware):
        client = TestClient(app_with_middleware)
        resp = client.get("/api/v1/marketplace/orders")
        assert resp.status_code != 400
