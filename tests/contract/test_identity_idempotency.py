"""Regression tests for the request-identity / idempotency-scope fix.

Before Phase 1 nothing in production assigned ``request.state.user_id``, so
``IdempotencyMiddleware`` scoped every row as ``"anonymous"`` while
``database/models.py`` declares a unique index on ``(user_id, key)``. The
failure mode was cross-user response disclosure, not just a cache miss.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse


def _make_token(sub: str, platform_id: str | None = None) -> str:
    from services.api_gateway.auth import create_access_token

    return create_access_token({}, subject=sub, role="farmer", tenant_id=platform_id)


class TestIdentityMiddleware:
    def _client(self) -> tuple[TestClient, FastAPI]:
        from services.api_gateway.middleware.identity import IdentityMiddleware

        app = FastAPI()
        app.add_middleware(IdentityMiddleware)

        @app.get("/whoami")
        async def whoami(request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "user_id": getattr(request.state, "user_id", None),
                    "tenant_id": getattr(request.state, "tenant_id", None),
                }
            )

        return TestClient(app), app

    def test_publishes_subject_from_bearer_token(self):
        client, _ = self._client()
        token = _make_token("user-a")
        resp = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "user-a"

    def test_publishes_tenant_from_platform_claim(self):
        client, _ = self._client()
        token = _make_token("user-a", platform_id="tenant-7")
        resp = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
        assert resp.json()["tenant_id"] == "tenant-7"

    def test_does_not_fall_back_to_sub_for_tenant(self):
        client, _ = self._client()
        token = _make_token("user-a")
        resp = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
        assert resp.json()["tenant_id"] is None

    def test_unauthenticated_request_has_no_subject(self):
        client, _ = self._client()
        assert client.get("/whoami").json() == {"user_id": None, "tenant_id": None}

    def test_malformed_token_degrades_instead_of_raising(self):
        client, _ = self._client()
        resp = client.get("/whoami", headers={"Authorization": "Bearer not-a-jwt"})
        assert resp.status_code == 200
        assert resp.json()["user_id"] is None

    def test_cookie_authenticated_request_is_resolved(self):
        from services.api_gateway.auth import ACCESS_TOKEN_COOKIE

        client, _ = self._client()
        client.cookies.set(ACCESS_TOKEN_COOKIE, _make_token("user-cookie"))
        assert client.get("/whoami").json()["user_id"] == "user-cookie"

    def test_mounted_outside_idempotency_in_the_real_app(self):
        """The fix only holds if identity resolves before the idempotency scope."""
        from services.api_gateway.main import app

        order = [m.cls.__name__ for m in app.user_middleware]
        assert "IdentityMiddleware" in order, "IdentityMiddleware is not mounted"
        assert "IdempotencyMiddleware" in order
        # Starlette runs the last-registered middleware first.
        assert order.index("IdentityMiddleware") < order.index("IdempotencyMiddleware")


class TestIdempotencyScopeIsolatesSubjects:
    def _client(self) -> TestClient:
        from database.base import Base
        from database.hub import hub
        from services.api_gateway.middleware.idempotency import IdempotencyMiddleware
        from services.api_gateway.middleware.identity import IdentityMiddleware

        Base.metadata.create_all(hub.get_sqlalchemy_engine())

        app = FastAPI()
        app.add_middleware(IdempotencyMiddleware)
        app.add_middleware(IdentityMiddleware)

        @app.post("/api/v1/finance/payments/intent")
        async def intent(request: Request) -> JSONResponse:
            body = await request.json()
            return JSONResponse(status_code=201, content={"status": "created", "body": body})

        return TestClient(app)

    def test_two_users_may_reuse_the_same_key(self):
        """Regression: with a shared 'anonymous' scope this returned 422."""
        client = self._client()
        key = str(uuid.uuid4())
        body = {"amount": 100}

        r1 = client.post(
            "/api/v1/finance/payments/intent",
            json=body,
            headers={"Authorization": f"Bearer {_make_token('user-a')}", "Idempotency-Key": key},
        )
        r2 = client.post(
            "/api/v1/finance/payments/intent",
            json=body,
            headers={"Authorization": f"Bearer {_make_token('user-b')}", "Idempotency-Key": key},
        )

        assert r1.status_code == r2.status_code == 201

    def test_one_user_still_gets_its_own_cached_response(self):
        client = self._client()
        key = str(uuid.uuid4())
        body = {"amount": 100}
        headers = {"Authorization": f"Bearer {_make_token('user-a')}", "Idempotency-Key": key}

        first = client.post("/api/v1/finance/payments/intent", json=body, headers=headers)
        second = client.post("/api/v1/finance/payments/intent", json=body, headers=headers)

        assert first.status_code == second.status_code == 201
        assert first.json() == second.json()

    def test_one_user_still_cannot_reuse_a_key_with_a_different_body(self):
        client = self._client()
        key = str(uuid.uuid4())
        auth = {"Authorization": f"Bearer {_make_token('user-a')}", "Idempotency-Key": key}

        client.post("/api/v1/finance/payments/intent", json={"amount": 100}, headers=auth)
        clash = client.post("/api/v1/finance/payments/intent", json={"amount": 999}, headers=auth)

        assert clash.status_code == 422


class TestAnonymousScopeFingerprint:
    def test_does_not_leak_the_peer_address(self):
        from starlette.requests import Request

        from services.api_gateway.middleware.identity import anonymous_scope

        def scope(client_host: str) -> str:
            raw = {
                "type": "http",
                "method": "POST",
                "scheme": "http",
                "server": ("test", 80),
                "path": "/api/v1/finance/payments/intent",
                "query_string": b"",
                "headers": [],
                "http_version": "1.1",
                "client": (client_host, 8000),
                "root_path": "",
                "app": None,
                "extensions": {},
            }
            return anonymous_scope(Request(raw))

        assert "203.0.113.7" not in scope("203.0.113.7")
        assert scope("203.0.113.7") == scope("203.0.113.7")
        assert scope("203.0.113.7") != scope("203.0.113.8")

    @pytest.mark.parametrize("host", ["203.0.113.7", "198.51.100.1"])
    def test_length_is_bounded(self, host: str) -> None:
        from services.api_gateway.middleware.identity import ANON_FINGERPRINT_LEN, anonymous_scope

        raw = {
            "type": "http",
            "method": "POST",
            "scheme": "http",
            "server": ("test", 80),
            "path": "/x",
            "query_string": b"",
            "headers": [],
            "http_version": "1.1",
            "client": (host, 8000),
            "root_path": "",
            "app": None,
            "extensions": {},
        }
        assert len(anonymous_scope(Request(raw))) == len("anon:") + ANON_FINGERPRINT_LEN
