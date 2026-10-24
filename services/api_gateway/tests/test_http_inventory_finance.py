"""HTTP regression tests for the inventory + finance endpoints repaired in
waves 1-3, one minimal app per data plane.

Inventory (P0-3/P2-18) — mounted with in-memory SQLite + overrides (the
``services/inventory/tests/test_p0_3_http500_repair.py`` pattern):

* ``GET /skus`` with and without ``?is_active``, ``GET /skus/{code}``
  exposing ``is_trackable``, ``GET /warehouses``;
* ``POST /reservations`` with a malformed ``expires_at`` returns 422 (not 500),
  and the reserve → consume → release lifecycle over HTTP;
* service-level: the unique balance constraint, the ``adjust`` non-negative
  floor, and the expiry sweep.

Finance (P0-1/P0-2/P2-13/P1-9) — mounted on the same app:

* ``POST /wallet/earn`` / ``/wallet/redeem`` no longer 500 and legacy category
  aliases resolve;
* ``GET /ledger/trial-balance`` and ``/ledger/profit-and-loss`` return real
  rows over posted batches (admin-only);
* ``GET /consolidated/position`` (admin) exposes all five money stores.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from database.models import (
    EcoWallet,
    FinAccount,
    InvInventoryBalance,
    InvSKU,
    LedgerEntry,
)
from services.api_gateway.auth import get_current_user
from services.api_gateway.exceptions import EcoNojinException
from services.api_gateway.routers.finance_consolidation import get_db as cons_get_db
from services.api_gateway.routers.finance_consolidation import router as consolidation_router
from services.finance.ledger_service import LedgerService
from services.finance.routers.finance import get_db as finance_get_db
from services.finance.routers.finance import router as finance_router
from services.inventory.routers.inventory import get_db as inventory_get_db
from services.inventory.routers.inventory import router as inventory_router
from services.inventory.service import StockService, sweep_expired_reservations

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    """One in-memory database shared by every app built in a test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


def _build_app(session, *, role="admin", user_id="user-1"):
    """Mount the inventory + finance + consolidation routers.

    Overriding the single ``get_current_user`` callable covers ``require_user``
    (its alias) and ``require_admin`` (which depends on it), so ``role``
    drives every role gate on this app. A global exception handler plus
    ``raise_app_exceptions=False`` lets a genuine 500 surface as a response so
    the "422 not 500" contract is actually pinned.
    """
    app = FastAPI()
    app.include_router(inventory_router)
    app.include_router(finance_router)
    app.include_router(consolidation_router)

    async def db_override():
        yield session

    app.dependency_overrides[inventory_get_db] = db_override
    app.dependency_overrides[finance_get_db] = db_override
    app.dependency_overrides[cons_get_db] = db_override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id, role=role)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def _server_error_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    @app.exception_handler(EcoNojinException)
    async def _eco_exception_handler(request: Request, exc: EcoNojinException):
        return JSONResponse(status_code=exc.status_code or 400, content={"detail": exc.message})

    return app


async def _request(app, method: str, path: str, payload: dict | None = None, params=None):
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        return await client.request(method, path, json=payload, params=params)


async def _seed_inventory(session) -> tuple[StockService, int, int, int]:
    """A default warehouse, an active+trackable SKU and an inactive SKU."""
    service = StockService(session)
    warehouse = await service.create_warehouse("MAIN", "Main Warehouse", city="Tehran")
    active = await service.create_sku("SKU-A", "Active Trackable SKU", uom="kg")
    inactive = InvSKU(sku_code="SKU-INACTIVE", name="Inactive SKU", is_active=False)
    session.add(inactive)
    await session.commit()
    await service.receipt(active.id, warehouse.id, Decimal("100"))
    return service, warehouse.id, active.id, inactive.id


# ===========================================================================
# Inventory — HTTP
# ===========================================================================


class TestInventoryReadEndpoints:
    async def test_list_skus_without_filter_returns_all(self, session):
        await _seed_inventory(session)
        app = _build_app(session)
        response = await _request(app, "GET", "/api/v1/inventory/skus")
        assert response.status_code == 200, response.text
        body = response.json()
        codes = {item["sku_code"] for item in body}
        assert codes == {"SKU-A", "SKU-INACTIVE"}
        assert all("is_active" in item for item in body)

    @pytest.mark.parametrize("active,expected", [("true", {"SKU-A"}), ("false", {"SKU-INACTIVE"})])
    async def test_list_skus_is_active_filter(self, session, active, expected):
        await _seed_inventory(session)
        app = _build_app(session)
        response = await _request(
            app, "GET", "/api/v1/inventory/skus", params={"is_active": active}
        )
        assert response.status_code == 200, response.text
        assert {item["sku_code"] for item in response.json()} == expected

    async def test_get_sku_exposes_is_trackable(self, session):
        await _seed_inventory(session)
        app = _build_app(session)
        response = await _request(app, "GET", "/api/v1/inventory/skus/SKU-A")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["is_trackable"] is True
        assert data["sku_code"] == "SKU-A"
        assert data["uom"] == "kg"

    async def test_get_unknown_sku_returns_404(self, session):
        app = _build_app(session)
        assert (await _request(app, "GET", "/api/v1/inventory/skus/NOPE")).status_code == 404

    async def test_list_warehouses(self, session):
        await _seed_inventory(session)
        app = _build_app(session)
        response = await _request(app, "GET", "/api/v1/inventory/warehouses")
        assert response.status_code == 200, response.text
        body = response.json()
        assert any(w["code"] == "MAIN" for w in body)
        assert all({"id", "code", "name", "city"} <= set(w) for w in body)

    async def test_inactive_warehouse_excluded_from_listing(self, session):
        service = StockService(session)
        warehouse = await service.create_warehouse("MAIN", "Main")
        warehouse.is_active = False
        await session.commit()
        app = _build_app(session)
        response = await _request(app, "GET", "/api/v1/inventory/warehouses")
        assert response.status_code == 200, response.text
        assert response.json() == []

    async def test_read_endpoints_require_auth(self, session):
        app = _build_app(session)
        app.dependency_overrides.pop(get_current_user, None)
        # No overriding user without a bearer token → genuine 401.
        assert (await _request(app, "GET", "/api/v1/inventory/skus")).status_code == 401


class TestInventoryReservationEndpoint:
    async def test_malformed_expires_at_returns_422_not_500(self, session):
        await _seed_inventory(session)
        app = _build_app(session)
        response = await _request(
            app,
            "POST",
            "/api/v1/inventory/reservations",
            {
                "sku_code": "SKU-A",
                "warehouse_id": 1,
                "qty": 5,
                "reference_id": "ord-malformed",
                "expires_at": "not-a-date",
            },
        )
        assert response.status_code == 422, response.text

    async def test_malformed_expires_at_writes_nothing(self, session):
        await _seed_inventory(session)
        app = _build_app(session)
        await _request(
            app,
            "POST",
            "/api/v1/inventory/reservations",
            {
                "sku_code": "SKU-A",
                "warehouse_id": 1,
                "qty": 5,
                "reference_id": "ord-malformed",
                "expires_at": "not-a-date",
            },
        )
        service = StockService(session)
        sku = await service.get_sku("SKU-A")
        movements = await service.get_movements(sku_id=sku.id, movement_type="reservation")
        assert movements == []

    async def test_reserve_valid_iso_expires_at(self, session):
        _service, warehouse_id, active_id, _inactive = await _seed_inventory(session)
        app = _build_app(session)
        response = await _request(
            app,
            "POST",
            "/api/v1/inventory/reservations",
            {
                "sku_code": "SKU-A",
                "warehouse_id": warehouse_id,
                "qty": 5,
                "reference_id": "ord-ok",
                "expires_at": "2030-01-01T00:00:00",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "active"
        assert Decimal(response.json()["qty"]) == Decimal("5")

    async def test_reserve_reduce_available_then_release(self, session):
        service, warehouse_id, active_id, _inactive = await _seed_inventory(session)
        app = _build_app(session)
        reserve = await _request(
            app,
            "POST",
            "/api/v1/inventory/reservations",
            {"sku_code": "SKU-A", "warehouse_id": warehouse_id, "qty": 40, "reference_id": "ord-r"},
        )
        assert reserve.status_code == 200, reserve.text
        reservation_id = reserve.json()["reservation_id"]

        balance = await service.get_balance(active_id, warehouse_id)
        assert balance.reserved == Decimal("40")
        assert balance.available == Decimal("60")

        release = await _request(
            app, "POST", f"/api/v1/inventory/reservations/{reservation_id}/release"
        )
        assert release.status_code == 200, release.text
        balance = await service.get_balance(active_id, warehouse_id)
        assert balance.reserved == Decimal("0")
        assert balance.available == Decimal("100")

    async def test_reserve_then_consume_partial(self, session):
        service, warehouse_id, active_id, _inactive = await _seed_inventory(session)
        app = _build_app(session)
        reserve = await _request(
            app,
            "POST",
            "/api/v1/inventory/reservations",
            {"sku_code": "SKU-A", "warehouse_id": warehouse_id, "qty": 10, "reference_id": "ord-c"},
        )
        reservation_id = reserve.json()["reservation_id"]

        consume = await _request(
            app,
            "POST",
            f"/api/v1/inventory/reservations/{reservation_id}/consume",
            params={"qty": 4},
        )
        assert consume.status_code == 200, consume.text

        balance = await service.get_balance(active_id, warehouse_id)
        assert balance.on_hand == Decimal("96")  # 100 - 4 consumed
        assert balance.reserved == Decimal("6")  # 10 reserved - 4 consumed

    async def test_reserve_insufficient_stock_returns_400(self, session):
        await _seed_inventory(session)
        app = _build_app(session)
        response = await _request(
            app,
            "POST",
            "/api/v1/inventory/reservations",
            {"sku_code": "SKU-A", "warehouse_id": 1, "qty": 500, "reference_id": "ord-big"},
        )
        assert response.status_code == 400, response.text


# ===========================================================================
# Inventory — service-level integrity
# ===========================================================================


class TestInventoryServiceIntegrity:
    async def test_duplicate_balance_row_rejected(self, session):
        service, warehouse_id, active_id, _inactive = await _seed_inventory(session)
        session.add(
            InvInventoryBalance(
                sku_id=active_id,
                warehouse_id=warehouse_id,
                location_id=0,
                lot_id=0,
                on_hand=Decimal("5"),
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

    async def test_adjust_cannot_drive_on_hand_negative(self, session):
        service, warehouse_id, active_id, _inactive = await _seed_inventory(session)
        with pytest.raises(EcoNojinException) as exc_info:
            await service.adjust(active_id, warehouse_id, Decimal("-500"), reason="wrong")
        assert exc_info.value.code == "NEGATIVE_ON_HAND"
        balance = await service.get_balance(active_id, warehouse_id)
        assert balance.on_hand == Decimal("100")

    async def test_expiry_sweep_releases_expired_reservation(self, session):
        service, warehouse_id, active_id, _inactive = await _seed_inventory(session)
        reservation = await service.reserve_stock(
            active_id,
            warehouse_id,
            Decimal("60"),
            "order",
            "ord-expiry",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert (await service.get_balance(active_id, warehouse_id)).reserved == Decimal("60")

        reservation.expires_at = datetime.now(UTC) - timedelta(hours=1)
        await session.commit()

        released = await sweep_expired_reservations(session)
        assert released == 1
        await session.refresh(reservation)
        assert reservation.status == "expired"
        assert (await service.get_balance(active_id, warehouse_id)).reserved == Decimal("0")

    async def test_reservation_consume_release_round_trip(self, session):
        service, warehouse_id, active_id, _inactive = await _seed_inventory(session)
        reservation = await service.reserve_stock(
            active_id, warehouse_id, Decimal("20"), "order", "ord-round"
        )
        await service.consume_reservation(reservation.id, Decimal("7"))
        balance = await service.get_balance(active_id, warehouse_id)
        assert balance.on_hand == Decimal("93")
        assert balance.reserved == Decimal("13")
        await service.release_reservation(reservation.id)
        balance = await service.get_balance(active_id, warehouse_id)
        assert balance.reserved == Decimal("0")
        assert balance.on_hand == Decimal("93")


# ===========================================================================
# Finance — HTTP
# ===========================================================================


class TestWallet:
    async def test_earn_posts_batch_and_returns_balance(self, session):
        app = _build_app(session)
        response = await _request(
            app, "POST", "/api/v1/finance/wallet/earn", {"category": "tree_planting", "quantity": 2}
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert Decimal(body["amount_earned"]) == Decimal("100")  # 50 * 2
        assert Decimal(body["new_balance"]) == Decimal("100")

    async def test_earn_resolves_legacy_category_alias(self, session):
        app = _build_app(session)
        response = await _request(
            app, "POST", "/api/v1/finance/wallet/earn", {"category": "soil_health"}
        )
        assert response.status_code == 200, response.text
        assert Decimal(response.json()["amount_earned"]) == Decimal("30")  # soil_restoration

    async def test_earn_unknown_category_is_rejected(self, session):
        app = _build_app(session)
        response = await _request(app, "POST", "/api/v1/finance/wallet/earn", {"category": "bogus"})
        assert response.status_code == 422, response.text

    async def test_redeem_after_earn(self, session):
        app = _build_app(session)
        await _request(
            app, "POST", "/api/v1/finance/wallet/earn", {"category": "carbon_verification"}
        )
        response = await _request(
            app, "POST", "/api/v1/finance/wallet/redeem", {"category": "training"}
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert Decimal(body["amount_redeemed"]) == Decimal("15")
        assert Decimal(body["new_balance"]) == Decimal("85")  # 100 earned - 15

    async def test_redeem_insufficient_balance_is_rejected(self, session):
        app = _build_app(session)
        response = await _request(
            app, "POST", "/api/v1/finance/wallet/redeem", {"category": "certification"}
        )
        assert response.status_code in (400, 409), response.text

    async def test_wallet_balance_endpoint_persists_earn(self, session):
        app = _build_app(session)
        await _request(app, "POST", "/api/v1/finance/wallet/earn", {"category": "biodiversity"})
        response = await _request(app, "GET", "/api/v1/finance/wallet")
        assert response.status_code == 200, response.text
        assert Decimal(response.json()["balance"]) == Decimal("40")


async def _seed_posted_profit_and_loss(session) -> None:
    """A balanced, POSTED batch touching an income and an expense account."""
    for account in (
        FinAccount(code="REV_TEST", name="Revenue", type="income", asset="ECO", currency="ECO"),
        FinAccount(code="EXP_TEST", name="Expense", type="expense", asset="ECO", currency="ECO"),
        FinAccount(code="CASH_TEST", name="Cash", type="asset", asset="ECO", currency="ECO"),
    ):
        session.add(account)
    await session.commit()
    ledger = LedgerService(session)
    batch = await ledger.create_journal_batch(
        reference_type="test",
        reference_id="pl-seed",
        entries=[
            {"account_id": "REV_TEST", "entry_type": "credit", "asset": "ECO", "amount": "300"},
            {"account_id": "EXP_TEST", "entry_type": "debit", "asset": "ECO", "amount": "100"},
            {"account_id": "CASH_TEST", "entry_type": "debit", "asset": "ECO", "amount": "200"},
        ],
    )
    await ledger.post_journal_batch(batch.id)


class TestLedgerReports:
    async def test_trial_balance_returns_posted_rows(self, session):
        app = _build_app(session)
        await _request(app, "POST", "/api/v1/finance/wallet/earn", {"category": "tree_planting"})
        response = await _request(app, "GET", "/api/v1/finance/ledger/trial-balance")
        assert response.status_code == 200, response.text
        body = response.json()
        accounts = {row["account_id"] for row in body["rows"]}
        assert {"ECO_ASSET", "REWARD_LIABILITY"} <= accounts
        eco = next(t for t in body["totals"] if t["asset"] == "ECO")
        assert eco["balanced"] is True

    async def test_trial_balance_ignores_draft_batches(self, session):
        # A balanced but unposted (draft) batch contributes no rows.
        ledger = LedgerService(session)
        await ledger.create_journal_batch(
            reference_type="test",
            reference_id="draft-only",
            entries=[
                {"account_id": "REV_TEST", "entry_type": "credit", "asset": "ECO", "amount": "10"},
                {"account_id": "CASH_TEST", "entry_type": "debit", "asset": "ECO", "amount": "10"},
            ],
        )
        app = _build_app(session)
        response = await _request(app, "GET", "/api/v1/finance/ledger/trial-balance")
        assert response.status_code == 200
        assert response.json()["rows"] == []

    async def test_profit_and_loss_returns_income_and_expense(self, session):
        await _seed_posted_profit_and_loss(session)
        app = _build_app(session)
        response = await _request(app, "GET", "/api/v1/finance/ledger/profit-and-loss")
        assert response.status_code == 200, response.text
        body = response.json()
        eco_income = {row["account_code"]: row for row in body["income"]}
        assert Decimal(eco_income["REV_TEST"]["amount"]) == Decimal("300")
        eco_expense = {row["account_code"]: row for row in body["expense"]}
        assert Decimal(eco_expense["EXP_TEST"]["amount"]) == Decimal("100")
        totals = next(t for t in body["totals"] if t["asset"] == "ECO")
        assert Decimal(totals["net"]) == Decimal("200")
        assert totals["profitable"] is True

    async def test_reports_reject_non_admin(self, session):
        app = _build_app(session, role="buyer")
        assert (
            await _request(app, "GET", "/api/v1/finance/ledger/trial-balance")
        ).status_code == 403
        assert (
            await _request(app, "GET", "/api/v1/finance/ledger/profit-and-loss")
        ).status_code == 403


class TestConsolidatedPosition:
    async def test_admin_receives_all_five_sources(self, session):
        app = _build_app(session)
        response = await _request(app, "GET", "/api/v1/finance/consolidated/position")
        assert response.status_code == 200, response.text
        body = response.json()
        assert set(body["sources"]) == {
            "fin_double_entry",
            "ledger_single_entry",
            "marketplace_escrow",
            "eco_wallets",
            "ecocoin",
        }
        assert body["overall"]["source_count"] == 5
        # A missing raw EcoCoin table is an empty store, not a crash.
        assert body["sources"]["ecocoin"]["available"] is False

    async def test_non_admin_rejected(self, session):
        app = _build_app(session, role="buyer")
        assert (
            await _request(app, "GET", "/api/v1/finance/consolidated/position")
        ).status_code == 403

    async def test_reflects_seeded_single_entry_and_wallet(self, session):
        session.add(
            LedgerEntry(
                account_id="acct-single", asset="ECO", entry_type="credit", amount=Decimal("25.00")
            )
        )
        session.add(
            EcoWallet(
                user_id="wallet-1", balance=Decimal("50"), total_earned=Decimal("50"),
                total_redeemed=Decimal("0"), is_active=True, version=1,
            )
        )
        await session.commit()
        app = _build_app(session)
        body = (await _request(app, "GET", "/api/v1/finance/consolidated/position")).json()
        wallet_total = body["sources"]["eco_wallets"]["assets"]["ECO"]["total"]
        assert Decimal(wallet_total) == Decimal("50")
        single_total = body["sources"]["ledger_single_entry"]["assets"]["ECO"]["total"]
        assert Decimal(single_total) == Decimal("25")
        assert "ECO" in body["overall"]["assets"]
        assert "eco_wallets" in body["overall"]["non_empty_sources"]

    async def test_fin_double_entry_sees_posted_journal_wave1_fix(self, session):
        # Wave 1-3 posts the batch at its call site, so the wave2 style POST
        # endpoint is visible to consolidation without a separate post step.
        await _seed_posted_profit_and_loss(session)
        app = _build_app(session)
        body = (await _request(app, "GET", "/api/v1/finance/consolidated/position")).json()
        de = body["sources"]["fin_double_entry"]
        assert de["row_count"] == 3
        assert Decimal(de["assets"]["ECO"]["total_debits"]) == Decimal("300")
