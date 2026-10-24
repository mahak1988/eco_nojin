"""HTTP regression tests for the backend capabilities exposed in wave 5 —
one minimal app per data plane, following the established patterns in
``test_http_inventory_finance.py`` (async engines + ``dependency_overrides``)
and ``test_http_marketplace_commerce.py``.

Coverage:

* Marketplace — ``GET /api/v1/marketplace/orders/{order_id}/items`` returns the
  persisted basket (200, with the seeded ``MarketplaceOrderItem`` rows) and a
  clean 404 for an unknown order;
* Inventory — ``GET /api/v1/inventory/skus`` now includes ``is_trackable`` and
  ``GET /skus/{code}`` 404s cleanly (route-level guard, not the gateway
  catch-all);
* Finance — ``POST /api/v1/finance/payments/intent`` with ``provider=bank_transfer``
  returns a persisted payment intent (registered at finance-router import time);
* Chart of accounts — ``seed_chart_of_accounts`` is idempotent when called twice.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from database.models import ComPaymentIntent
from services.api_gateway.auth import get_current_user
from services.api_gateway.routers.marketplace import get_async_db as marketplace_get_async_db
from services.api_gateway.routers.marketplace import get_db as marketplace_get_db
from services.api_gateway.routers.marketplace import router as marketplace_router
from services.finance.payment_provider import BankTransferProvider, payment_registry
from services.finance.routers.finance import get_db as finance_get_db
from services.finance.routers.finance import router as finance_router
from services.inventory.routers.inventory import get_db as inventory_get_db
from services.inventory.routers.inventory import router as inventory_router
from services.inventory.service import StockService
from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderItem,
    MarketplaceOrderStatus,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _db_override(session):
    async def _override():
        yield session

    return _override


async def _request(app, method: str, path: str, payload: dict | None = None, params=None):
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        return await client.request(method, path, json=payload, params=params)


def _add_500_handlers(app: FastAPI) -> FastAPI:
    """Surface a genuine server error as a 500 response (never a transport crash).

    No ``EcoNojinException`` handler is registered on purpose: that keeps an
    unguarded ``EcoNojinException`` a 500 so the route-level guard is what makes
    the SKU-not-found case a clean 404.
    """

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def _server_error_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    return app


# ===========================================================================
# (a) Marketplace — persisted order basket over HTTP
# ===========================================================================


async def _seed_order_with_items(
    db_session, order_id: str = "ord-items-1", *, items: bool = True
) -> str:
    order = MarketplaceOrder(
        id=order_id,
        order_number=f"ORD-{order_id}",
        buyer_id="buyer-1",
        village_id="village-1",
        subtotal=Decimal("350000.00"),
        total=Decimal("350000.00"),
        status=MarketplaceOrderStatus.PENDING,
        payment_status="pending",
    )
    db_session.add(order)
    if items:
        db_session.add(
            MarketplaceOrderItem(
                id=f"item-{order_id}",
                order_id=order_id,
                product_id="prod-1",
                seller_id="seller-1",
                product_name="Honey",
                quantity=Decimal("2"),
                unit="piece",
                unit_price=Decimal("175000.00"),
                line_total=Decimal("350000.00"),
            )
        )
    await db_session.commit()
    return order_id


def _marketplace_app(db_session) -> FastAPI:
    app = FastAPI()
    app.include_router(marketplace_router)
    # The marketplace routes construct the module-level ``MarketplaceService``
    # singleton through ``get_marketplace_service(db)``; overriding ``get_db``
    # with the isolated async session makes that singleton read the seeded rows.
    app.dependency_overrides[marketplace_get_db] = _db_override(db_session)
    # P12: the order-items route reads through the async plane. The fixture's
    # ``db_session`` is already an async session, so the same object is yielded
    # to the async dependency — no second engine, no dual-plane split.
    app.dependency_overrides[marketplace_get_async_db] = _db_override(db_session)
    # P3 parity: the basket route requires the caller, and the seeded order
    # belongs to ``buyer-1`` (see ``_seed_order_with_items``).
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="buyer-1", role="buyer"
    )
    return app


class TestMarketplaceOrderItems:
    async def test_returns_persisted_basket(self, db_session, monkeypatch):
        monkeypatch.setattr("services.marketplace.service._marketplace_service", None)
        await _seed_order_with_items(db_session)
        app = _marketplace_app(db_session)

        response = await _request(app, "GET", "/api/v1/marketplace/orders/ord-items-1/items")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["order_id"] == "ord-items-1"
        assert body["count"] == 1
        item = body["items"][0]
        assert item["product_id"] == "prod-1"
        assert item["product_name"] == "Honey"
        assert Decimal(item["quantity"]) == Decimal("2")
        assert Decimal(item["unit_price"]) == Decimal("175000.00")
        assert Decimal(item["line_total"]) == Decimal("350000.00")

    async def test_empty_basket_allowed(self, db_session, monkeypatch):
        monkeypatch.setattr("services.marketplace.service._marketplace_service", None)
        await _seed_order_with_items(db_session, order_id="ord-empty", items=False)
        # No MarketplaceOrderItem rows for this order -> empty list, not an error.
        app = _marketplace_app(db_session)
        response = await _request(app, "GET", "/api/v1/marketplace/orders/ord-empty/items")
        assert response.status_code == 200, response.text
        assert response.json() == {"order_id": "ord-empty", "items": [], "count": 0}

    async def test_unknown_order_is_404(self, db_session, monkeypatch):
        monkeypatch.setattr("services.marketplace.service._marketplace_service", None)
        app = _marketplace_app(db_session)
        response = await _request(app, "GET", "/api/v1/marketplace/orders/no-such-order/items")
        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"

    async def test_stranger_cannot_read_another_buyers_basket(self, db_session, monkeypatch):
        """The basket is the buyer's own (same invariant as the order list)."""
        monkeypatch.setattr("services.marketplace.service._marketplace_service", None)
        await _seed_order_with_items(db_session)
        app = _marketplace_app(db_session)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="stranger-1", role="buyer"
        )
        response = await _request(app, "GET", "/api/v1/marketplace/orders/ord-items-1/items")
        assert response.status_code == 403


# ===========================================================================
# (b) Inventory — is_trackable on the list + clean 404 for an unknown SKU
# ===========================================================================


async def _seed_sku(db_session) -> None:
    service = StockService(db_session)
    await service.create_sku("SKU-A", "Active Trackable SKU", uom="kg")


def _inventory_app(db_session) -> FastAPI:
    app = FastAPI()
    app.include_router(inventory_router)
    app.dependency_overrides[inventory_get_db] = _db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="user-1", role="admin")
    return _add_500_handlers(app)


class TestInventorySkuEndpoints:
    async def test_list_exposes_is_trackable(self, db_session):
        await _seed_sku(db_session)
        app = _inventory_app(db_session)
        response = await _request(app, "GET", "/api/v1/inventory/skus")
        assert response.status_code == 200, response.text
        rows = response.json()
        assert all("is_trackable" in row for row in rows)
        sku_a = next(row for row in rows if row["sku_code"] == "SKU-A")
        assert sku_a["is_trackable"] is True

    async def test_unknown_sku_is_clean_404(self, db_session):
        # No EcoNojinException handler on this app: the route-level guard is
        # what turns ``StockService.get_sku``'s EcoNojinException into a 404.
        app = _inventory_app(db_session)
        response = await _request(app, "GET", "/api/v1/inventory/skus/NOPE")
        assert response.status_code == 404, response.text

    async def test_known_sku_still_returns_detail(self, db_session):
        await _seed_sku(db_session)
        app = _inventory_app(db_session)
        response = await _request(app, "GET", "/api/v1/inventory/skus/SKU-A")
        assert response.status_code == 200, response.text
        assert response.json()["sku_code"] == "SKU-A"
        assert response.json()["is_trackable"] is True


# ===========================================================================
# (c) Finance — bank_transfer payment intent registered at import time
# ===========================================================================


class TestFinanceBankTransferIntent:
    async def test_registered_without_commerce(self):
        # Import-time registration (mirrors OrderService.__init__) is what makes
        # the provider reachable before any order flow has been constructed.
        assert isinstance(payment_registry.get("bank_transfer"), BankTransferProvider)

    async def test_intent_persisted_over_http(self, db_session):
        app = FastAPI()
        app.include_router(finance_router)
        app.dependency_overrides[finance_get_db] = _db_override(db_session)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="u1", role="user")
        _add_500_handlers(app)

        # Bind a fresh provider on the isolated session so the route + provider
        # share the same engine; restore the module-level binding afterwards.
        original = payment_registry.get("bank_transfer")
        payment_registry.register(BankTransferProvider(db_session))
        try:
            response = await _request(
                app,
                "POST",
                "/api/v1/finance/payments/intent",
                {
                    "amount": 150000,
                    "currency": "IRR",
                    "order_id": "ord-bt-1",
                    "provider": "bank_transfer",
                },
            )
        finally:
            payment_registry.register(original)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["provider"] == "bank_transfer"
        assert body["status"] == "awaiting_transfer"
        assert Decimal(body["amount"]) == Decimal("150000")

        row = await db_session.get(ComPaymentIntent, body["id"])
        assert row is not None
        assert row.provider == "bank_transfer"
        assert row.status == "awaiting_transfer"
        assert Decimal(str(row.amount)) == Decimal("150000")


# ===========================================================================
# (d) Chart of accounts — the startup seeder is idempotent (no app boot)
# ===========================================================================


class TestSeedChartOfAccountsIdempotent:
    async def test_seeding_twice_is_idempotent(self, db_session):
        from services.finance.chart_of_accounts import seed_chart_of_accounts

        first = await seed_chart_of_accounts(db_session)
        await db_session.commit()
        first_ids = sorted(account.id for account in first)

        second = await seed_chart_of_accounts(db_session)
        await db_session.commit()
        second_ids = sorted(account.id for account in second)

        assert first_ids  # something was seeded
        assert len(first) == len({account.code for account in first})
        assert first_ids == second_ids
