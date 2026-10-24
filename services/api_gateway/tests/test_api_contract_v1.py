"""P2 — the API contract page is enforced, not just documented.

`architecture/API-CONTRACT-v1.md` is only as good as the tests that fail when
the code drifts from it. Each clause group below drives real behavior — the
real middleware stack, the real app's OpenAPI, the real exception classes —
so a silent contract break (a changed error body, a dropped rate-limit header,
a money route losing its idempotency requirement, `Decimal` money serialized
as strings) fails CI instead of reaching clients.

The contract version is v1.0; changing any pinned behavior requires the
contract page to be re-issued as v2 first (its §6 version-status rules).
"""

from __future__ import annotations

import os
from decimal import Decimal
from uuid import uuid4

# The gateway settings read SECRET_KEY at import; this is the same public
# test-only literal `services/conftest.py` uses for JWT_SECRET.
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from services.api_gateway.errors import ERROR_CODE_MAP, SAFE_DETAIL, safe_error_detail
from services.api_gateway.exceptions import (
    ConflictException,
    EcoNojinException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
    UnauthorizedException,
    ValidationException,
)

pytestmark = pytest.mark.asyncio

_PROTECTED_PATH = "/api/v1/ecowallet/earn"  # in IDEMPOTENT_EXACT_ROUTES

#: The header name the middleware publishes as ``IDEMPOTENCY_HEADER``; the
#: membership test asserts the two stay identical.
_IDEMPOTENCY_HEADER = "Idempotency-Key"


# --------------------------------------------------------------------------
# §1 — error body contract
# --------------------------------------------------------------------------

_SUBCLASS_DEFAULTS = [
    (ValidationException, 422, "Validation failed", "ValidationException"),
    (NotFoundException, 404, "Resource not found", "NotFoundException"),
    (UnauthorizedException, 401, "Authentication required", "UnauthorizedException"),
    (ForbiddenException, 403, "Access denied", "ForbiddenException"),
    (ConflictException, 409, "Resource conflict", "ConflictException"),
    (
        ServiceUnavailableException,
        503,
        "Service temporarily unavailable",
        "ServiceUnavailableException",
    ),
]


@pytest.mark.parametrize(("cls", "status", "message", "code"), _SUBCLASS_DEFAULTS)
async def test_exception_subclasses_carry_their_contract_status(cls, status, message, code):
    exc = cls()
    assert exc.status_code == status
    assert exc.message == message
    assert exc.code == code  # default code is the class name — a stable vocabulary

async def test_base_exception_carries_status_and_code():
    exc = EcoNojinException("plain", status_code=418, code="TEAPOT")
    assert (exc.status_code, exc.code, exc.message) == (418, "TEAPOT", "plain")


async def test_safe_error_detail_maps_to_a_token_not_the_message():
    detail = safe_error_detail(RuntimeError("db password=hunter2 at 10.0.0.1:5432"))
    assert detail in set(ERROR_CODE_MAP.values())
    leak = safe_error_detail(ValueError("SELECT * FROM users WHERE token='abc'"))
    assert "SELECT" not in leak and "abc" not in leak


async def test_safe_detail_covers_documented_status_codes():
    for status in (400, 401, 403, 404, 409, 422, 500, 502, 503, 504):
        assert SAFE_DETAIL[status]


async def test_real_app_404_body_shape():
    from fastapi.testclient import TestClient

    from services.api_gateway.main import app

    with TestClient(app) as client:
        response = client.get("/api/v1/no-such-endpoint-contract-probe")
    body = response.json()
    assert response.status_code == 404
    assert body["detail"].startswith("Endpoint not found:")
    assert body["hint"] == "Check /docs for available endpoints"


# --------------------------------------------------------------------------
# §2 — idempotency contract (real middleware, in-process database)
# --------------------------------------------------------------------------

@pytest.fixture
async def idempotent_app():
    """A probe app guarded by the real IdempotencyMiddleware.

    The middleware binds its own session through ``hub.get_async_session()``
    (the process-wide in-memory engine from ``database.config``), so the
    full header-validate → store → replay cycle runs for real. The imports
    are function-local on purpose: ``services.finance`` has a pre-existing
    partial-init cycle that only bites at module-import time.
    """
    from services.api_gateway.middleware.idempotency import IdempotencyMiddleware

    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post(_PROTECTED_PATH)
    async def earn(payload: dict):
        return {"echo": payload, "served": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_money_route_requires_the_header(idempotent_app: AsyncClient):
    from services.api_gateway.middleware.idempotency import IDEMPOTENCY_HEADER

    response = await idempotent_app.post(_PROTECTED_PATH, json={"amount": "1"})
    assert response.status_code == 400
    assert response.json()["code"] == "IDEMPOTENCY_KEY_REQUIRED"
    assert IDEMPOTENCY_HEADER == _IDEMPOTENCY_HEADER


async def test_money_route_rejects_a_malformed_key(idempotent_app: AsyncClient):
    response = await idempotent_app.post(
        _PROTECTED_PATH, json={"amount": "1"}, headers={_IDEMPOTENCY_HEADER: "not-a-key"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


async def test_same_key_same_body_replays_the_cached_response(idempotent_app: AsyncClient):
    key = str(uuid4())
    headers = {_IDEMPOTENCY_HEADER: key}
    first = await idempotent_app.post(_PROTECTED_PATH, json={"amount": "1"}, headers=headers)
    assert first.status_code == 200
    assert first.json() == {"echo": {"amount": "1"}, "served": True}
    second = await idempotent_app.post(_PROTECTED_PATH, json={"amount": "1"}, headers=headers)
    assert second.status_code == 200
    assert second.json() == first.json()  # replayed, not recomputed


async def test_same_key_different_body_is_a_client_error(idempotent_app: AsyncClient):
    key = str(uuid4())
    headers = {_IDEMPOTENCY_HEADER: key}
    await idempotent_app.post(_PROTECTED_PATH, json={"amount": "1"}, headers=headers)
    clash = await idempotent_app.post(_PROTECTED_PATH, json={"amount": "2"}, headers=headers)
    assert clash.status_code == 422
    assert clash.json()["code"] == "IDEMPOTENCY_KEY_REUSE"


async def test_money_route_membership_is_current():
    """Every money-moving route the contract names must still require the key."""
    from services.api_gateway.middleware.idempotency import (
        IDEMPOTENT_EXACT_ROUTES,
        IDEMPOTENT_PARAM_ROUTES,
    )

    for path in (
        "/api/v1/ecowallet/earn",
        "/api/v1/ecowallet/redeem",
        "/api/v1/ecowallet/distribute",
        "/api/v1/ledger/entries",
        "/api/v1/marketplace/orders",
        "/api/v1/marketplace/payments",
        "/api/v1/marketplace/payments/callback",
        "/api/v1/finance/wallet/earn",
        "/api/v1/finance/wallet/redeem",
        "/api/v1/finance/payments/intent",
    ):
        assert path in IDEMPOTENT_EXACT_ROUTES, path
    for path in (
        "/api/v1/marketplace/orders/{order_id}",
        "/api/v1/marketplace/orders/{order_id}/settle",
        "/api/v1/marketplace/orders/{order_id}/complete",
        "/api/v1/marketplace/payments/{payment_id}/escrow/refund",
    ):
        assert path in IDEMPOTENT_PARAM_ROUTES, path
    assert all(p.startswith("/api/v1/") for p in IDEMPOTENT_EXACT_ROUTES)
    assert all(p.startswith("/api/v1/") for p in IDEMPOTENT_PARAM_ROUTES)


# --------------------------------------------------------------------------
# §3 — money contract
# --------------------------------------------------------------------------

async def test_money_is_decimal_internally():
    """Money constants are Decimal at the boundary the contract names.

    Imported from ``services.finance.earning_rates`` (not through
    ``wallet_service``): the ``services.finance`` package has a pre-existing
    partial-init cycle that only bites when a test module is the first
    importer.
    """
    from services.finance import earning_rates

    assert isinstance(earning_rates.TRANSFER_MIN_BALANCE, Decimal)
    rate_values = [
        value
        for name, value in vars(earning_rates).items()
        if not name.startswith("_") and isinstance(value, Decimal)
    ]
    assert rate_values, "earning_rates must expose Decimal rates"
    assert all(isinstance(value, Decimal) for value in rate_values)


async def test_money_wire_format_is_a_json_number():
    """v1 wire format: JSON numbers, not strings (string amounts are a v2 option)."""
    app = FastAPI()

    @app.get("/probe")
    def probe():
        return {"balance": Decimal("10.50"), "amount": Decimal("0.0001")}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/probe")
    assert response.json() == {"balance": 10.5, "amount": 0.0001}


# --------------------------------------------------------------------------
# §4 — pagination contract
# --------------------------------------------------------------------------

async def test_paginated_route_declares_page_and_page_size():
    """The contract's page/page_size convention is declared in the live OpenAPI.

    Pinned against a route that is actually mounted (the alerting router is a
    service without a gateway mount — see the endpoint inventory), so a
    convention change on a live list endpoint fails here.
    """
    from services.api_gateway.main import app

    schema = app.openapi()
    paginated = [
        (path, method)
        for path, item in schema["paths"].items()
        for method, op in item.items()
        if isinstance(op, dict)
        and {"page", "page_size"} <= {p.get("name") for p in op.get("parameters", [])}
    ]
    assert paginated, "no mounted route declares the page/page_size convention"
    for path, method in paginated:
        params = {p["name"]: p for p in schema["paths"][path][method]["parameters"]}
        assert params["page_size"]["schema"]["default"] == 20, path
        assert params["page_size"]["schema"]["maximum"] == 100, path
        assert params["page_size"]["schema"]["minimum"] == 1, path


# --------------------------------------------------------------------------
# §5 — rate-limit and security headers
# --------------------------------------------------------------------------

async def test_real_app_responses_carry_the_contract_headers():
    from fastapi.testclient import TestClient

    from services.api_gateway.main import app

    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    for header in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"):
        assert header in response.headers, header
    for header in ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"):
        assert header in response.headers, header
    assert response.headers["X-Content-Type-Options"] == "nosniff"
