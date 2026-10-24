"""Regression tests for P0-3 — the five HTTP 500s caused by missing model fields.

Findings repaired and pinned here:

1. ``GET /api/v1/inventory/skus`` filtered on ``InvSKU.is_active``, a column that
   did not exist → ``AttributeError`` escaped the route (500).
2. ``GET /api/v1/inventory/skus/{sku_code}`` serialised ``sku.is_trackable``,
   also a missing column → ``AttributeError`` (500).
3. ``GET /api/v1/commerce/orders/{order_id}`` serialised
   ``ComOrderItem.fulfilled_qty``, a missing column → ``AttributeError`` (500).
   The response value now comes from the line's stock reservation
   (``InvReservation.consumed_qty``, which ``ship_order`` writes) so it reports
   the quantity that actually left stock.
4. ``POST /api/v1/inventory/reservations`` parsed ``expires_at`` through
   ``__import__("datetime").datetime.fromisoformat`` outside any error handling,
   so a malformed timestamp raised ``ValueError`` → 500 instead of 422.
5. ``GET /api/v1/inventory/warehouses`` passed the bare ``InvWarehouse.is_active``
   column as a ``where()`` criterion, which only worked by SQL truthiness; it is
   now an explicit ``is_active IS true`` predicate.

Each test below fails on the pre-repair tree (AttributeError / ValueError escaping
the route, which the gateway's catch-all handler turns into a 500) and passes
after the repair.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import (
    ComOrder,
    ComOrderItem,
    ComPaymentIntent,
    InvInventoryBalance,
    InvReservation,
    InvSKU,
    InvStockMovement,
    InvWarehouse,
)
from services.api_gateway.auth import get_current_user
from services.api_gateway.exceptions import EcoNojinException
from services.commerce.routers.commerce import get_db as commerce_get_db
from services.commerce.routers.commerce import get_order as commerce_get_order
from services.commerce.routers.commerce import router as commerce_router
from services.inventory.routers.inventory import get_db
from services.inventory.routers.inventory import router as inventory_router
from services.inventory.service import StockService

pytestmark = pytest.mark.asyncio

_TABLES = (
    InvSKU.__table__,
    InvWarehouse.__table__,
    InvInventoryBalance.__table__,
    InvStockMovement.__table__,
    InvReservation.__table__,
    ComOrder.__table__,
    ComOrderItem.__table__,
    ComPaymentIntent.__table__,
)

# ``require_user`` is an alias of ``get_current_user`` (services/api_gateway/auth.py).
_USER = SimpleNamespace(id="inv-user", role="user", is_active=True)


async def _global_exception_handler(request: Request, exc: Exception) -> Response:
    """Mirror of the gateway's catch-all handler in services/api_gateway/main.py.

    Without it the ASGI transport re-raises the unhandled ``AttributeError``
    instead of reporting the HTTP 500 the gateway actually returns.
    """
    if isinstance(exc, EcoNojinException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ``raise_app_exceptions=False`` mirrors the gateway: its catch-all handler writes
# the error response first and only then re-raises for the server log, so the
# client observes the status code rather than a transport-level exception.
_TRANSPORT_KWARGS = {"raise_app_exceptions": False}


@pytest.fixture
async def inventory_app():
    """A minimal app mounting the inventory + commerce routers over one session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        for table in _TABLES:
            await conn.run_sync(table.create)

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        app = FastAPI()
        app.include_router(inventory_router)
        app.include_router(commerce_router)
        app.add_exception_handler(Exception, _global_exception_handler)

        async def database_override():
            yield session

        # Each router module declares its own ``get_db``; both must be overridden.
        app.dependency_overrides[get_db] = database_override
        app.dependency_overrides[commerce_get_db] = database_override
        app.dependency_overrides[get_current_user] = lambda: _USER

        service = StockService(session)
        warehouse = await service.create_warehouse("WH-1", "Main Warehouse", city="Tehran")
        active_sku = await service.create_sku("SKU-ACTIVE", "Active Product", standard_cost=1)
        inactive_sku = await service.create_sku("SKU-GONE", "Retired Product", standard_cost=1)
        inactive_sku.is_active = False
        await session.commit()

        # Stock on hand so reservations can be made.
        await service.receipt(
            sku_id=active_sku.id,
            warehouse_id=warehouse.id,
            qty=Decimal("100"),
            created_by="seed",
        )

        yield app, session, {"warehouse": warehouse, "sku": active_sku}
    await engine.dispose()


async def _get(app, path):
    async with AsyncClient(
        transport=ASGITransport(app=app, **_TRANSPORT_KWARGS), base_url="http://test"
    ) as client:
        return await client.get(path)


async def _post(app, path, payload):
    async with AsyncClient(
        transport=ASGITransport(app=app, **_TRANSPORT_KWARGS), base_url="http://test"
    ) as client:
        return await client.post(path, json=payload)


class TestListSKUs:
    async def test_no_filter_returns_active_and_inactive(self, inventory_app):
        app, _session, _ = inventory_app
        response = await _get(app, "/api/v1/inventory/skus")
        assert response.status_code == 200, response.text
        codes = {row["sku_code"] for row in response.json()}
        assert codes == {"SKU-ACTIVE", "SKU-GONE"}

    async def test_is_active_true_filters_to_active(self, inventory_app):
        app, _session, _ = inventory_app
        response = await _get(app, "/api/v1/inventory/skus?is_active=true")
        assert response.status_code == 200, response.text
        codes = {row["sku_code"] for row in response.json()}
        assert codes == {"SKU-ACTIVE"}
        assert all(row["is_active"] is True for row in response.json())

    async def test_is_active_false_filters_to_inactive(self, inventory_app):
        app, _session, _ = inventory_app
        response = await _get(app, "/api/v1/inventory/skus?is_active=false")
        assert response.status_code == 200, response.text
        codes = {row["sku_code"] for row in response.json()}
        assert codes == {"SKU-GONE"}
        assert all(row["is_active"] is False for row in response.json())


class TestGetSKU:
    async def test_sku_exposes_is_trackable(self, inventory_app):
        app, _session, _ = inventory_app
        response = await _get(app, "/api/v1/inventory/skus/SKU-ACTIVE")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["sku_code"] == "SKU-ACTIVE"
        assert body["is_trackable"] is True

    async def test_unknown_sku_is_404_not_500(self, inventory_app):
        app, _session, _ = inventory_app
        response = await _get(app, "/api/v1/inventory/skus/NO-SUCH-SKU")
        assert response.status_code == 404


class TestListWarehouses:
    async def test_warehouses_lists_active_warehouses(self, inventory_app):
        app, _session, _ = inventory_app
        response = await _get(app, "/api/v1/inventory/warehouses")
        assert response.status_code == 200, response.text
        codes = {row["code"] for row in response.json()}
        assert codes == {"WH-1"}

    async def test_inactive_warehouses_are_excluded(self, inventory_app):
        app, session, seeded = inventory_app
        # A deactivated warehouse must not be served by the explicit filter.
        seeded["warehouse"].is_active = False
        await session.commit()
        response = await _get(app, "/api/v1/inventory/warehouses")
        assert response.status_code == 200, response.text
        assert response.json() == []


class TestReserveStockExpiresAt:
    async def test_malformed_expires_at_is_422_not_500(self, inventory_app):
        app, _session, seeded = inventory_app
        response = await _post(
            app,
            "/api/v1/inventory/reservations",
            {
                "sku_code": seeded["sku"].sku_code,
                "warehouse_id": seeded["warehouse"].id,
                "qty": 2,
                "reference_id": "order-1",
                "expires_at": "not-a-timestamp",
            },
        )
        assert response.status_code == 422, response.text
        assert "expires_at" in response.json()["detail"]

    @pytest.mark.parametrize("expires_at", ["", "2026-01-01T00:00:00+00:00", "2026-01-01"])
    async def test_valid_expires_at_still_reserves(self, inventory_app, expires_at):
        app, _session, seeded = inventory_app
        response = await _post(
            app,
            "/api/v1/inventory/reservations",
            {
                "sku_code": seeded["sku"].sku_code,
                "warehouse_id": seeded["warehouse"].id,
                "qty": 2,
                "reference_id": f"order-{expires_at or 'none'}",
                "expires_at": expires_at,
            },
        )
        assert response.status_code == 200, response.text
        assert Decimal(response.json()["qty"]) == Decimal("2")

    async def test_malformed_expires_at_writes_no_reservation(self, inventory_app):
        app, session, seeded = inventory_app
        await _post(
            app,
            "/api/v1/inventory/reservations",
            {
                "sku_code": seeded["sku"].sku_code,
                "warehouse_id": seeded["warehouse"].id,
                "qty": 2,
                "reference_id": "order-bad",
                "expires_at": "31/31/2026",
            },
        )
        result = await session.execute(select(InvReservation))
        assert result.scalars().all() == []


class TestOrderLineFulfilledQty:
    """``GET /orders/{order_id}`` must report the reservation's consumed qty."""

    async def _seed_order(self, session, consumed_qty):
        order = ComOrder(
            id="order-1",
            order_number="ORD-1",
            buyer_id="inv-user",
            seller_id=None,
            status="processing",
            payment_status="pending",
            subtotal=Decimal("10"),
            platform_fee=Decimal("0"),
            landscape_fee=Decimal("0"),
            total=Decimal("10"),
            version=0,
            created_at=datetime.now(UTC),
        )
        session.add(order)
        await session.flush()
        session.add(
            ComOrderItem(
                id="line-1",
                order_id="order-1",
                sku_id=1,
                sku_code="SKU-1",
                name="Product",
                quantity=Decimal("5"),
                unit_price=Decimal("2"),
                line_total=Decimal("10"),
                warehouse_id=1,
                reservation_id=42,
            )
        )
        session.add(
            InvReservation(
                id=42,
                sku_id=1,
                warehouse_id=1,
                qty=Decimal("5"),
                consumed_qty=Decimal(consumed_qty),
                status="active",
                reference_type="order",
                reference_id="order-1",
                created_by="inv-user",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()

    async def test_fulfilled_qty_reflects_consumed_reservation(self, inventory_app):
        _app, session, _seeded = inventory_app
        await self._seed_order(session, "3.5")
        body = await commerce_get_order("order-1", db=session, user=_USER)
        assert Decimal(body["items"][0]["fulfilled_qty"]) == Decimal("3.5")

    async def test_unconsumed_reservation_reports_zero(self, inventory_app):
        _app, session, _seeded = inventory_app
        await self._seed_order(session, "0")
        body = await commerce_get_order("order-1", db=session, user=_USER)
        assert Decimal(body["items"][0]["fulfilled_qty"]) == Decimal("0")

    async def test_line_without_reservation_reports_zero(self, inventory_app):
        _app, session, _seeded = inventory_app
        await self._seed_order(session, "3.5")
        result = await session.execute(select(ComOrderItem).where(ComOrderItem.id == "line-1"))
        result.scalars().one().reservation_id = None
        await session.commit()
        body = await commerce_get_order("order-1", db=session, user=_USER)
        assert Decimal(body["items"][0]["fulfilled_qty"]) == Decimal("0")

    async def test_fulfilled_qty_never_exceeds_the_reserved_quantity(self, inventory_app):
        _app, session, _seeded = inventory_app
        await self._seed_order(session, "3.5")
        body = await commerce_get_order("order-1", db=session, user=_USER)
        line = body["items"][0]
        assert Decimal(line["fulfilled_qty"]) <= Decimal(line["quantity"])
