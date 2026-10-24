"""Bank-webhook HMAC + ASVS-aligned access-control regression suite.

Three layers are pinned here, each with the minimal app + dependency-override
pattern used by ``test_security_hardening.py`` and ``test_http_*.py``:

1. **The bank callback's authenticity** (the ``_bank_transfer_webhook`` route
   repaired by the previous wave). It now authenticates the caller with an
   HMAC-SHA256 over the *raw* request body before the body is parsed or
   anything is persisted, and it fails closed when no secret is provisioned.
2. **The access-control matrix** over the application's write surface: every
   mutating route in the key routers must carry an authentication or
   authorization dependency, the admin-only ones must refuse a non-admin
   caller, and the exact inventory of surveyed write routes is pinned so a
   future unguarded addition cannot slip in unnoticed.

OWASP ASVS v5.0.0 chapter map
-----------------------------
* **V3 — Session Management**: a machine-to-machine webhook has no session, so
  the shared secret *is* its authentication. V3 requires the endpoint to
  refuse a request that does not prove possession of that secret, which is
  what the 401/503 cases below assert.
* **V4 — Access Control**: every mutating route must be protected by an
  authorization decision, and a role that is not permitted must be refused
  (``403``) rather than served. ``TestAccessControlMatrix`` enumerates the
  routes from the routers themselves, so the matrix is an audit artifact
  rather than a hand-written list.
* **V6 — Cryptography**: the signature is ``HMAC-SHA256`` (not a bare hash,
  not SHA-1), computed over the exact bytes received, and compared with
  ``hmac.compare_digest`` so the check does not leak its result through
  timing. ``TestBankCallbackSignatureHelpers`` pins that directly.
* **V14 — Configuration**: the secret is deployment configuration read from
  ``BANK_WEBHOOK_SECRET`` at request time, and an absent or whitespace-only
  value is a *closed* endpoint (``503``), never an open one — the
  ``require_api_key`` "admits anyone while the key is empty" behaviour this
  suite exists to stop shipping.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from database.models import AuditEvent, ComPaymentIntent
from services.api_gateway.auth import get_current_user
from services.api_gateway.routers.land import router as land_router
from services.api_gateway.routers.marketplace import get_db as marketplace_get_db
from services.api_gateway.routers.marketplace import router as marketplace_router
from services.api_gateway.routers.village_hub import _get_db as village_hub_get_db
from services.api_gateway.routers.village_hub import router as village_hub_router
from services.commerce.routers.commerce import get_db as commerce_get_db
from services.commerce.routers.commerce import router as commerce_router
from services.finance.payment_provider import (
    bank_callback_signature,
    verify_bank_callback,
)
from services.finance.routers.finance import get_db as finance_get_db
from services.finance.routers.finance import router as finance_router
from services.inventory.routers.inventory import get_db as inventory_get_db
from services.inventory.routers.inventory import router as inventory_router
from services.landscape.api.governance import router as governance_router
from services.landscape.api.territories import _get_db as territories_get_db
from services.landscape.api.territories import router as territories_router
from services.tourism.api.router import get_db as tourism_get_db
from services.tourism.api.router import router as tourism_router

_WEBHOOK_URL = "/api/v1/finance/payments/webhook/bank_transfer"
_SECRET = "test-bank-webhook-secret"

#: Dependencies that constitute an authentication/authorization decision.
#: ``require_user`` is the alias of ``get_current_user`` so both spellings map
#: onto the same callable; ``require_roles`` is a *factory*, so the callable
#: that lands in a route's dependency tree is its closure and is matched by
#: qualname prefix instead.
_GUARD_NAMES = frozenset(
    {
        "get_current_user",
        "require_user",
        "require_admin",
        "require_security_admin",
        "require_content_admin",
        "require_user_admin",
        "require_admin_with_mfa",
        "require_api_key",
        "get_current_user_with_tenant",
    }
)
_ADMIN_GUARD_NAMES = frozenset({"require_admin", "require_security_admin"})

#: HTTP methods that change state and therefore need a guard.
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

#: Routers surveyed by the matrix. "land/territories" is three modules: the
#: DEM/terrain plane, the territory state machine and territory governance.
_SURVEYED_ROUTERS = (
    commerce_router,
    finance_router,
    inventory_router,
    land_router,
    marketplace_router,
    territories_router,
    governance_router,
    tourism_router,
    village_hub_router,
)


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


def _sign(raw: bytes, secret: str = _SECRET) -> str:
    return bank_callback_signature(secret.encode("utf-8"), raw)


async def _post_webhook(app, raw: bytes, *, headers: dict | None = None):
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        return await client.post(_WEBHOOK_URL, content=raw, headers=request_headers)


async def _send(app, method: str, path: str):
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        return await client.request(method, path)


def _walk_dependencies(dependant, seen=None):
    """Yield every dependency node in a route's tree, innermost included."""

    if seen is None:
        seen = set()
    if id(dependant) in seen:
        return
    seen.add(id(dependant))
    yield dependant
    for sub in dependant.dependencies:
        yield from _walk_dependencies(sub, seen)


def _guard_qualnames(route: APIRoute) -> frozenset[str]:
    """Qualified names of every auth/authorization dependency on ``route``."""

    names = set()
    for node in _walk_dependencies(route.dependant):
        qualname = getattr(node.call, "__qualname__", "") or ""
        if qualname in _GUARD_NAMES or qualname.startswith("require_roles"):
            names.add(qualname)
    return frozenset(names)


def _role_guards(route: APIRoute) -> list:
    """Every ``require_roles`` closure on a route, in dependency order."""

    return [
        node.call
        for node in _walk_dependencies(route.dependant)
        if (getattr(node.call, "__qualname__", "") or "").startswith("require_roles")
    ]


def _api_routes(routes):
    """Flatten ``include_router`` branches into their ``APIRoute`` leaves.

    FastAPI 0.141 keeps an included router as a lazy ``_IncludedRouter`` branch
    on ``app.routes`` instead of copying its routes across, so iterating
    ``app.routes`` directly finds one opaque entry per mounted router and none
    of the endpoints. ``effective_candidates()`` expands that branch; the
    ``original_route`` fallback keeps this working on a FastAPI that flattens
    eagerly instead.
    """

    found = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
        elif callable(getattr(route, "effective_candidates", None)):
            found.extend(_api_routes(route.effective_candidates()))
        elif getattr(route, "original_route", None) is not None:
            found.extend(_api_routes([route.original_route]))
    return found


def _write_routes(app: FastAPI) -> list[tuple[str, str, APIRoute]]:
    """Every ``(METHOD, path, route)`` on ``app`` that changes state."""

    surveyed = []
    for route in _api_routes(app.routes):
        for method in sorted(set(route.methods) & _WRITE_METHODS):
            surveyed.append((method, route.path, route))
    return sorted(surveyed, key=lambda item: (item[1], item[0]))


@pytest.fixture
def matrix_app() -> FastAPI:
    """One app mounting every router the matrix surveys."""
    app = FastAPI()
    for router in _SURVEYED_ROUTERS:
        app.include_router(router)
    return app


@pytest.fixture
async def webhook_app(db_session, monkeypatch):
    """The finance router alone, with the webhook secret provisioned."""
    monkeypatch.setenv("BANK_WEBHOOK_SECRET", _SECRET)
    app = FastAPI()
    app.include_router(finance_router)
    app.dependency_overrides[finance_get_db] = _db_override(db_session)
    _add_error_handlers(app)
    yield app, db_session


async def _seed_intent(session, payment_id: str, amount: str = "150000") -> None:
    session.add(
        ComPaymentIntent(
            id=payment_id,
            order_id="ord-hmac-1",
            provider="bank_transfer",
            amount=Decimal(amount),
            currency="IRR",
            status="awaiting_transfer",
            provider_reference="BT-hmac-1",
            payment_metadata={"idempotency_key": "hmac-key"},
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


# ===========================================================================
# 1. HMAC-SHA256 over the raw body — ASVS V6 (cryptography)
# ===========================================================================


class TestBankCallbackSignatureHelpers:
    def test_signature_is_hex_hmac_sha256_of_the_raw_body(self):
        import hashlib
        import hmac as hmac_module

        body = b'{"payment_id":"pay-1","amount":150000}'
        expected = hmac_module.new(_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()

        assert bank_callback_signature(_SECRET.encode("utf-8"), body) == expected
        assert len(expected) == 64  # SHA-256, hex-encoded

    def test_signature_covers_the_bytes_not_a_reserialisation(self):
        # Whitespace and key order are part of the signed material: the bank
        # signs its own bytes, so re-serialising the parsed JSON would produce
        # a different digest and the check would fail on a genuine callback.
        compact = b'{"payment_id":"pay-1","amount":150000}'
        padded = b'{ "payment_id" : "pay-1" , "amount" : 150000 }'

        assert bank_callback_signature(_SECRET.encode("utf-8"), compact) != (
            bank_callback_signature(_SECRET.encode("utf-8"), padded)
        )

    def test_an_empty_secret_is_refused_rather_than_used_as_a_key(self):
        with pytest.raises(ValueError):
            bank_callback_signature(b"", b"{}")

    def test_verify_accepts_a_matching_signature(self):
        body = b'{"payment_id":"pay-1"}'
        signature = bank_callback_signature(_SECRET.encode("utf-8"), body)

        assert verify_bank_callback(_SECRET.encode("utf-8"), body, signature) is True

    def test_verify_rejects_a_signature_over_a_different_body(self):
        body = b'{"payment_id":"pay-1"}'
        other = b'{"payment_id":"pay-2"}'

        assert verify_bank_callback(
            _SECRET.encode("utf-8"),
            other,
            bank_callback_signature(_SECRET.encode("utf-8"), body),
        ) is False

    def test_verify_rejects_a_signature_under_a_different_secret(self):
        body = b'{"payment_id":"pay-1"}'
        attacker_signature = bank_callback_signature(b"attacker-secret", body)

        assert verify_bank_callback(_SECRET.encode("utf-8"), body, attacker_signature) is False

    def test_verify_rejects_an_empty_secret_without_raising(self):
        body = b'{"payment_id":"pay-1"}'
        signature = bank_callback_signature(_SECRET.encode("utf-8"), body)

        assert verify_bank_callback(b"", body, signature) is False

    def test_verify_rejects_a_missing_or_empty_signature(self):
        body = b'{"payment_id":"pay-1"}'

        assert verify_bank_callback(_SECRET.encode("utf-8"), body, "") is False
        assert verify_bank_callback(_SECRET.encode("utf-8"), body, "   ") is False

    def test_verify_accepts_the_sha256_prefix_and_either_hex_case(self):
        # GitHub's header spells the algorithm explicitly; hex case carries no
        # information, so neither spelling may be why a genuine callback is
        # refused.
        body = b'{"payment_id":"pay-1"}'
        signature = bank_callback_signature(_SECRET.encode("utf-8"), body)

        assert verify_bank_callback(_SECRET.encode("utf-8"), body, f"sha256={signature}") is True
        assert verify_bank_callback(_SECRET.encode("utf-8"), body, signature.upper()) is True

    def test_verify_rejects_a_non_ascii_or_short_signature(self):
        body = b'{"payment_id":"pay-1"}'

        assert verify_bank_callback(_SECRET.encode("utf-8"), body, "\u06f3\u06f2\u06f6") is False
        assert verify_bank_callback(_SECRET.encode("utf-8"), body, "abc") is False


# ===========================================================================
# 2. The bank webhook route — ASVS V3 + V6 + V14
# ===========================================================================


@pytest.mark.asyncio
class TestBankWebhookHmac:
    async def test_valid_signature_is_processed(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-hmac-ok")
        raw = json.dumps(
            {"event_id": "evt-hmac-1", "payment_id": "pay-hmac-ok", "amount": 150000}
        ).encode("utf-8")

        response = await _post_webhook(app, raw, headers={"X-Signature": _sign(raw)})

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["processed"] is True
        assert body["event_id"] == "evt-hmac-1"
        assert body["outcome"]["status"] == "succeeded"
        assert body["outcome"]["duplicate"] is False
        row = await session.get(ComPaymentIntent, "pay-hmac-ok")
        assert row.status == "succeeded"

    async def test_redelivery_with_a_valid_signature_is_still_idempotent(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-hmac-dup")
        raw = json.dumps(
            {"event_id": "evt-hmac-2", "payment_id": "pay-hmac-dup", "amount": 150000}
        ).encode("utf-8")
        headers = {"X-Signature": _sign(raw)}

        first = await _post_webhook(app, raw, headers=headers)
        second = await _post_webhook(app, raw, headers=headers)

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert second.json()["outcome"]["duplicate"] is True
        audits = await session.execute(
            select(AuditEvent).where(AuditEvent.resource_id == "pay-hmac-dup")
        )
        assert len(audits.scalars().all()) == 1  # verified exactly once

    async def test_wrong_signature_is_401_and_nothing_is_persisted(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-hmac-bad")
        raw = json.dumps(
            {"event_id": "evt-hmac-3", "payment_id": "pay-hmac-bad", "amount": 150000}
        ).encode("utf-8")

        response = await _post_webhook(app, raw, headers={"X-Signature": "0" * 64})

        assert response.status_code == 401, response.text
        assert "signature" in response.json()["detail"].lower()
        row = await session.get(ComPaymentIntent, "pay-hmac-bad")
        assert row.status == "awaiting_transfer"
        audits = await session.execute(
            select(AuditEvent).where(AuditEvent.resource_id == "pay-hmac-bad")
        )
        assert audits.scalars().all() == []

    async def test_missing_signature_is_401(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-hmac-nosig")
        raw = json.dumps(
            {"event_id": "evt-hmac-4", "payment_id": "pay-hmac-nosig", "amount": 150000}
        ).encode("utf-8")

        response = await _post_webhook(app, raw)

        assert response.status_code == 401, response.text
        row = await session.get(ComPaymentIntent, "pay-hmac-nosig")
        assert row.status == "awaiting_transfer"

    async def test_tampered_body_is_401(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-hmac-tamper")
        signed = json.dumps(
            {"event_id": "evt-hmac-5", "payment_id": "pay-hmac-tamper", "amount": 150000}
        ).encode("utf-8")
        tampered = json.dumps(
            {"event_id": "evt-hmac-5", "payment_id": "pay-hmac-tamper", "amount": 1}
        ).encode("utf-8")

        response = await _post_webhook(app, tampered, headers={"X-Signature": _sign(signed)})

        assert response.status_code == 401, response.text
        row = await session.get(ComPaymentIntent, "pay-hmac-tamper")
        assert row.status == "awaiting_transfer"

    async def test_x_hub_signature_256_header_is_accepted(self, webhook_app):
        app, session = webhook_app
        await _seed_intent(session, "pay-hmac-alias")
        raw = json.dumps(
            {"event_id": "evt-hmac-6", "payment_id": "pay-hmac-alias", "amount": 150000}
        ).encode("utf-8")

        response = await _post_webhook(
            app, raw, headers={"X-Hub-Signature-256": f"sha256={_sign(raw)}"}
        )

        assert response.status_code == 200, response.text
        assert response.json()["processed"] is True

    async def test_unconfigured_secret_fails_closed(self, webhook_app, monkeypatch):
        app, session = webhook_app
        monkeypatch.delenv("BANK_WEBHOOK_SECRET", raising=False)
        await _seed_intent(session, "pay-hmac-unset")
        raw = json.dumps(
            {"event_id": "evt-hmac-7", "payment_id": "pay-hmac-unset", "amount": 150000}
        ).encode("utf-8")

        response = await _post_webhook(app, raw, headers={"X-Signature": _sign(raw)})

        assert response.status_code == 503, response.text
        assert "BANK_WEBHOOK_SECRET" in response.json()["detail"]
        row = await session.get(ComPaymentIntent, "pay-hmac-unset")
        assert row.status == "awaiting_transfer"

    async def test_whitespace_only_secret_fails_closed(self, webhook_app, monkeypatch):
        app, session = webhook_app
        monkeypatch.setenv("BANK_WEBHOOK_SECRET", "   ")
        await _seed_intent(session, "pay-hmac-blank")
        raw = json.dumps(
            {"event_id": "evt-hmac-8", "payment_id": "pay-hmac-blank", "amount": 150000}
        ).encode("utf-8")

        response = await _post_webhook(app, raw, headers={"X-Signature": _sign(raw)})

        assert response.status_code == 503, response.text
        row = await session.get(ComPaymentIntent, "pay-hmac-blank")
        assert row.status == "awaiting_transfer"

    async def test_valid_signature_over_a_bad_payload_is_still_400(self, webhook_app):
        # The signature gates the route; it does not make a malformed payload
        # acceptable, and it must not turn into a 500 either.
        app, _ = webhook_app
        raw = b"not-json"

        response = await _post_webhook(app, raw, headers={"X-Signature": _sign(raw)})

        assert response.status_code == 400, response.text

    async def test_valid_signature_for_an_unknown_payment_is_404(self, webhook_app):
        app, _ = webhook_app
        raw = json.dumps(
            {"event_id": "evt-hmac-9", "payment_id": "pay-hmac-missing", "amount": 150000}
        ).encode("utf-8")

        response = await _post_webhook(app, raw, headers={"X-Signature": _sign(raw)})

        assert response.status_code == 404, response.text

    async def test_signature_over_a_reserialised_body_is_rejected(self, webhook_app):
        # A caller that signs its own re-serialisation of the parsed JSON does
        # not sign the bytes the server received.
        app, _ = webhook_app
        raw = json.dumps(
            {"event_id": "evt-hmac-10", "payment_id": "pay-hmac-x", "amount": 150000}
        ).encode("utf-8")
        reserialised = json.dumps(
            {"amount": 150000, "event_id": "evt-hmac-10", "payment_id": "pay-hmac-x"}
        ).encode("utf-8")

        response = await _post_webhook(app, raw, headers={"X-Signature": _sign(reserialised)})

        assert response.status_code == 401, response.text


# ===========================================================================
# 3. Access-control matrix — ASVS V4
# ===========================================================================

#: Every mutating route in the surveyed routers. The list is data, not prose:
#: ``test_write_route_inventory_is_pinned`` compares the routers' own route
#: objects against it, so adding, renaming or re-mounting a write route fails
#: the suite until it has been reviewed here.
SURVEYED_WRITE_ROUTES = (
    ("POST", "/api/v1/commerce/orders"),
    ("POST", "/api/v1/commerce/orders/{order_id}/cancel"),
    ("POST", "/api/v1/commerce/orders/{order_id}/confirm-payment"),
    ("POST", "/api/v1/commerce/orders/{order_id}/mark-delivered"),
    ("POST", "/api/v1/commerce/orders/{order_id}/pay"),
    ("POST", "/api/v1/commerce/orders/{order_id}/settle"),
    ("POST", "/api/v1/commerce/orders/{order_id}/ship"),
    ("POST", "/api/v1/finance/accounts"),
    ("POST", "/api/v1/finance/ledger/batch"),
    ("POST", "/api/v1/finance/ledger/batch/{batch_id}/post"),
    ("POST", "/api/v1/finance/payments/intent"),
    ("POST", "/api/v1/finance/payments/webhook/{provider_name}"),
    ("POST", "/api/v1/finance/reconciliation/full"),
    ("POST", "/api/v1/finance/reconciliation/wallet-ledger"),
    ("POST", "/api/v1/finance/wallet/earn"),
    ("POST", "/api/v1/finance/wallet/redeem"),
    ("POST", "/api/v1/inventory/locations"),
    ("POST", "/api/v1/inventory/lots"),
    ("POST", "/api/v1/inventory/lots/expire-due"),
    ("POST", "/api/v1/inventory/lots/{lot_id}/close"),
    ("POST", "/api/v1/inventory/movements/adjust"),
    ("POST", "/api/v1/inventory/movements/issue"),
    ("POST", "/api/v1/inventory/movements/receipt"),
    ("POST", "/api/v1/inventory/movements/return"),
    ("POST", "/api/v1/inventory/movements/scrap"),
    ("POST", "/api/v1/inventory/movements/transfer"),
    ("POST", "/api/v1/inventory/reconcile"),
    ("POST", "/api/v1/inventory/reservations"),
    ("POST", "/api/v1/inventory/reservations/{reservation_id}/consume"),
    ("POST", "/api/v1/inventory/reservations/{reservation_id}/release"),
    ("POST", "/api/v1/inventory/skus"),
    ("POST", "/api/v1/inventory/stocktakes"),
    ("POST", "/api/v1/inventory/stocktakes/{stocktake_id}/approve"),
    ("POST", "/api/v1/inventory/warehouses"),
    ("POST", "/api/v1/land/profiles"),
    ("DELETE", "/api/v1/land/profiles/{profile_id}"),
    ("POST", "/api/v1/land/profiles/{profile_id}/capability-assessment"),
    ("POST", "/api/v1/land/profiles/{profile_id}/drainage-analysis"),
    ("POST", "/api/v1/land/profiles/{profile_id}/terrain-analysis"),
    ("POST", "/api/v1/landscape/villages/{village_id}/governance"),
    ("DELETE", "/api/v1/landscape/villages/{village_id}/governance/{user_id}"),
    ("PATCH", "/api/v1/landscape/villages/{village_id}/governance/{user_id}/deactivate"),
    ("PATCH", "/api/v1/landscape/villages/{village_id}/governance/{user_id}/reactivate"),
    ("PATCH", "/api/v1/landscape/villages/{village_id}/governance/{user_id}/term"),
    ("PATCH", "/api/v1/marketplace/admin/products/{product_id}/approve"),
    ("PATCH", "/api/v1/marketplace/admin/vendors/{vendor_id}/approve"),
    ("POST", "/api/v1/marketplace/cart"),
    ("DELETE", "/api/v1/marketplace/cart/{product_id}"),
    ("PATCH", "/api/v1/marketplace/cart/{product_id}"),
    ("POST", "/api/v1/marketplace/checkout/orders"),
    ("POST", "/api/v1/marketplace/checkout/products"),
    ("POST", "/api/v1/marketplace/marketplaces"),
    ("POST", "/api/v1/marketplace/marketplaces/{marketplace_id}/approve"),
    ("POST", "/api/v1/marketplace/marketplaces/{marketplace_id}/members"),
    ("POST", "/api/v1/marketplace/marketplaces/{marketplace_id}/shops"),
    ("POST", "/api/v1/marketplace/orders"),
    ("POST", "/api/v1/marketplace/orders/{order_id}/complete"),
    ("POST", "/api/v1/marketplace/orders/{order_id}/confirm"),
    ("POST", "/api/v1/marketplace/orders/{order_id}/dispute"),
    ("POST", "/api/v1/marketplace/orders/{order_id}/settle"),
    ("POST", "/api/v1/marketplace/payments"),
    ("POST", "/api/v1/marketplace/payments/{payment_id}/confirm"),
    ("POST", "/api/v1/marketplace/payments/{payment_id}/escrow/refund"),
    ("POST", "/api/v1/marketplace/payments/{payment_id}/escrow/release"),
    ("POST", "/api/v1/marketplace/payments/{payment_id}/verify-bank"),
    ("POST", "/api/v1/marketplace/products"),
    ("POST", "/api/v1/marketplace/products/{product_id}/images"),
    ("POST", "/api/v1/marketplace/products/{product_id}/tokenize"),
    ("POST", "/api/v1/marketplace/vendors"),
    ("POST", "/api/v1/marketplace/villages/b2b/demands"),
    ("POST", "/api/v1/marketplace/villages/engagements"),
    ("PUT", "/api/v1/marketplace/villages/entrepreneurs/me"),
    ("POST", "/api/v1/marketplace/villages/events/{event_id}/register"),
    ("POST", "/api/v1/marketplace/villages/festivals"),
    ("POST", "/api/v1/marketplace/villages/investments"),
    ("POST", "/api/v1/marketplace/villages/nomadic-communities"),
    ("DELETE", "/api/v1/marketplace/villages/nomadic-communities/{community_id}"),
    ("PUT", "/api/v1/marketplace/villages/nomadic-communities/{community_id}"),
    ("PATCH", "/api/v1/marketplace/villages/nomadic-communities/{community_id}/approve"),
    ("POST", "/api/v1/marketplace/villages/opportunities/{opportunity_id}/interest"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/ai-recommendations"),
    ("PUT", "/api/v1/marketplace/villages/{village_id}/brand"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/capabilities"),
    ("DELETE", "/api/v1/marketplace/villages/{village_id}/capabilities/{capability_id}"),
    ("PUT", "/api/v1/marketplace/villages/{village_id}/capabilities/{capability_id}"),
    ("PUT", "/api/v1/marketplace/villages/{village_id}/destination"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/events"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/experiences"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/gaps"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/needs"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/opportunities"),
    ("PUT", "/api/v1/marketplace/villages/{village_id}/opportunities/{opportunity_id}"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/projects"),
    ("PUT", "/api/v1/marketplace/villages/{village_id}/projects/{project_id}/progress"),
    ("POST", "/api/v1/marketplace/villages/{village_id}/tourism"),
    ("POST", "/api/v1/marketplace/wishlist"),
    ("DELETE", "/api/v1/marketplace/wishlist/{product_id}"),
    ("POST", "/api/v1/territories/{village_id}/archive"),
    ("POST", "/api/v1/territories/{village_id}/resubmit"),
    ("POST", "/api/v1/territories/{village_id}/review"),
    ("POST", "/api/v1/territories/{village_id}/submit"),
    ("PATCH", "/api/v1/territories/{village_id}/verify"),
    ("POST", "/api/v1/tourism/bookings"),
    ("POST", "/api/v1/tourism/bookings/{booking_id}/complete"),
    ("POST", "/api/v1/tourism/bookings/{booking_id}/confirm-payment"),
    ("POST", "/api/v1/tourism/guides"),
    ("POST", "/api/v1/tourism/guides/{guide_id}/verify"),
    ("POST", "/api/v1/tourism/tours"),
    ("POST", "/api/v1/tourism/tours/{tour_id}/approve"),
)

#: Write routes with no authentication dependency at all. This is the audit
#: artifact: the routes are *reported*, not hidden, and the allowlist is
#: deliberately closed, so guarding one of them is a test change while adding
#: a new unguarded one is a failure.
#:
#: Empty as of 2026-10-11. The last sixteen entries were closed when the
#: territory state machine, the council-membership routes, the DEM/terrain
#: plane and the read-only recommendation route each gained an authentication
#: dependency:
#:
#: * ``PATCH /api/v1/territories/{village_id}/verify`` and
#:   ``POST /api/v1/territories/{village_id}/review`` — ``require_roles(admin,
#:   landscape_manager, council_member)``: an approver role, so an arbitrary
#:   authenticated caller can no longer drive a village's territory to
#:   ``verified``.
#: * ``POST /api/v1/territories/{village_id}/{submit,resubmit,archive}`` —
#:   ``require_user``: the village-side half of the state machine still needs
#:   an authenticated actor.
#: * ``/api/v1/landscape/villages/{id}/governance/**`` —
#:   ``require_roles`` over the same write vocabulary
#:   ``services.marketplace.hub_service._GOVERNANCE_WRITE_ROLES`` uses, so
#:   council membership is a governance decision rather than an open write.
#: * ``/api/v1/land/**`` — ``require_user``. Compute over a caller-supplied
#:   ``dem_array`` with no tenant data, but ``POST`` and ``DELETE`` still
#:   mutate an in-process ``LandService`` singleton.
#: * ``POST /api/v1/marketplace/villages/{id}/ai-recommendations`` —
#:   ``require_user`` for consistency; it changes no state but was the only
#:   unauthenticated ``POST`` left in the surveyed surface.
KNOWN_UNGUARDED_WRITE_ROUTES = frozenset()

#: Write routes that require the ``admin`` role. Each is exercised with a
#: non-admin principal in ``test_admin_only_write_routes_refuse_a_non_admin``.
ADMIN_ONLY_WRITE_ROUTES = frozenset(
    {
        ("PATCH", "/api/v1/marketplace/admin/products/{product_id}/approve"),
        ("PATCH", "/api/v1/marketplace/admin/vendors/{vendor_id}/approve"),
        ("POST", "/api/v1/marketplace/marketplaces/{marketplace_id}/approve"),
        ("POST", "/api/v1/marketplace/payments/{payment_id}/escrow/refund"),
        ("POST", "/api/v1/marketplace/payments/{payment_id}/escrow/release"),
        ("POST", "/api/v1/marketplace/payments/{payment_id}/verify-bank"),
        ("POST", "/api/v1/commerce/orders/{order_id}/settle"),
        ("POST", "/api/v1/finance/accounts"),
        ("POST", "/api/v1/finance/ledger/batch/{batch_id}/post"),
        ("POST", "/api/v1/finance/reconciliation/full"),
        ("POST", "/api/v1/finance/reconciliation/wallet-ledger"),
        ("POST", "/api/v1/inventory/locations"),
        ("POST", "/api/v1/inventory/lots"),
        ("POST", "/api/v1/inventory/lots/expire-due"),
        ("POST", "/api/v1/inventory/lots/{lot_id}/close"),
        ("POST", "/api/v1/inventory/movements/adjust"),
        ("POST", "/api/v1/inventory/movements/scrap"),
        ("POST", "/api/v1/inventory/reconcile"),
        ("POST", "/api/v1/inventory/skus"),
        ("POST", "/api/v1/inventory/stocktakes"),
        ("POST", "/api/v1/inventory/stocktakes/{stocktake_id}/approve"),
        ("POST", "/api/v1/inventory/warehouses"),
    }
)

_NON_ADMIN = SimpleNamespace(id="non-admin-1", role="farmer")
_ADMIN = SimpleNamespace(id="admin-1", role="admin")


class TestAccessControlMatrix:
    def test_write_route_inventory_is_pinned(self, matrix_app):
        surveyed = {(method, path) for method, path, _ in _write_routes(matrix_app)}

        assert surveyed == set(SURVEYED_WRITE_ROUTES), (
            "The write surface moved. Review the diff, then update "
            "SURVEYED_WRITE_ROUTES and KNOWN_UNGUARDED_WRITE_ROUTES together.\n"
            f"  added:   {sorted(surveyed - set(SURVEYED_WRITE_ROUTES))}\n"
            f"  removed: {sorted(set(SURVEYED_WRITE_ROUTES) - surveyed)}"
        )

    def test_every_write_route_carries_an_auth_dependency(self, matrix_app):
        unguarded = sorted(
            (method, path)
            for method, path, route in _write_routes(matrix_app)
            if not _guard_qualnames(route)
        )

        # The allowlist is closed in both directions: a route that is now
        # unguarded fails, and a *recorded* exception that no longer exists
        # means the list has gone stale relative to the routers.
        assert set(unguarded) <= KNOWN_UNGUARDED_WRITE_ROUTES, (
            "Unguarded mutating route(s). Add an authentication dependency, or "
            "record the exception in KNOWN_UNGUARDED_WRITE_ROUTES with a reason.\n"
            f"  unguarded: {unguarded}"
        )
        assert set(KNOWN_UNGUARDED_WRITE_ROUTES) <= set(unguarded), (
            "Stale KNOWN_UNGUARDED_WRITE_ROUTES: every listed route is now "
            "guarded, so the exception list is obsolete and must be emptied.\n"
            f"  no longer unguarded: {sorted(set(KNOWN_UNGUARDED_WRITE_ROUTES) - set(unguarded))}"
        )

    def test_the_bank_webhook_is_api_key_guarded(self, matrix_app):
        routes = {(method, path): route for method, path, route in _write_routes(matrix_app)}
        route = routes[("POST", "/api/v1/finance/payments/webhook/{provider_name}")]

        # The shared-secret header guard stays as the second factor; the HMAC
        # check inside the handler is the first.
        assert "require_api_key" in _guard_qualnames(route)

    def test_admin_only_write_routes_are_pinned(self, matrix_app):
        admin_routes = {
            (method, path)
            for method, path, route in _write_routes(matrix_app)
            if _guard_qualnames(route) & _ADMIN_GUARD_NAMES
        }

        assert admin_routes == ADMIN_ONLY_WRITE_ROUTES, (
            "The admin-only write surface moved. Update ADMIN_ONLY_WRITE_ROUTES.\n"
            f"  added:   {sorted(admin_routes - ADMIN_ONLY_WRITE_ROUTES)}\n"
            f"  removed: {sorted(ADMIN_ONLY_WRITE_ROUTES - admin_routes)}"
        )

    def test_admin_only_write_routes_refuse_a_non_admin(self, matrix_app):
        # The guard is invoked directly with a non-admin principal, so the
        # assertion is about the authorization decision itself and not about
        # any one router's session wiring.
        by_route = {(method, path): route for method, path, route in _write_routes(matrix_app)}
        for method, path in sorted(ADMIN_ONLY_WRITE_ROUTES):
            route = by_route[(method, path)]
            guards = _role_guards(route)
            assert guards, f"{method} {path} lost its admin dependency"
            with pytest.raises(HTTPException) as exc_info:
                guards[-1](_NON_ADMIN)
            assert exc_info.value.status_code == 403, f"{method} {path}: {exc_info.value.detail}"
            # The same guard admits an admin: a guard that refuses everyone is
            # not access control, it is an outage.
            assert guards[-1](_ADMIN) is _ADMIN

    def test_role_guarded_write_routes_refuse_a_non_admin(self, matrix_app):
        # Routes gated by require_roles (rather than require_admin) still have
        # to refuse a caller without a permitted role.
        checked = 0
        for method, path, route in _write_routes(matrix_app):
            for guard in _role_guards(route):
                with pytest.raises(HTTPException) as exc_info:
                    guard(_NON_ADMIN)
                assert exc_info.value.status_code == 403, f"{method} {path}"
                checked += 1
        assert checked, "no role-guarded write route found; the survey is stale"

    def test_unguarded_write_routes_are_reported_as_an_audit_artifact(self, matrix_app):
        unguarded = sorted(
            (method, path)
            for method, path, route in _write_routes(matrix_app)
            if not _guard_qualnames(route)
        )
        guarded = len(SURVEYED_WRITE_ROUTES) - len(unguarded)

        # Report, not assert: this is the artifact a reader takes away from the
        # matrix. The assertion that keeps it honest lives in
        # test_every_write_route_carries_an_auth_dependency.
        print(
            f"\nASVS V4 write-route matrix: {len(SURVEYED_WRITE_ROUTES)} surveyed, "
            f"{guarded} guarded, {len(unguarded)} unguarded:"
        )
        for method, path in unguarded:
            print(f"  UNGUARDED {method:6s} {path}")


@pytest.mark.asyncio
class TestAdminOnlyRoutesOverHttp:
    async def test_admin_routes_reject_a_non_admin_caller(self, db_session):
        """The 403 is produced by the stack, not just by the guard callable."""

        app = FastAPI()
        for router in _SURVEYED_ROUTERS:
            app.include_router(router)

        async def db_override():
            yield db_session

        for dependency in (
            commerce_get_db,
            finance_get_db,
            inventory_get_db,
            tourism_get_db,
            marketplace_get_db,
            territories_get_db,
            village_hub_get_db,
        ):
            app.dependency_overrides[dependency] = db_override
        app.dependency_overrides[get_current_user] = lambda: _NON_ADMIN
        _add_error_handlers(app)

        # Routes chosen because they carry no required request parameter, so
        # the 403 cannot be a 422 from parameter validation arriving first.
        cases = [
            ("POST", "/api/v1/finance/reconciliation/full"),
            ("POST", "/api/v1/inventory/reconcile"),
            ("POST", "/api/v1/commerce/orders/ord-1/settle"),
            ("PATCH", "/api/v1/marketplace/admin/products/prod-1/approve"),
        ]
        for method, path in cases:
            response = await _send(app, method, path)
            assert response.status_code == 403, f"{method} {path} -> {response.status_code}"
            assert "Role" in response.json()["detail"]
