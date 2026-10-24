"""Tests for P2-18 — inventory concurrency and data-integrity hardening.

Pins:
1. one balance row per (sku, warehouse, location, lot): the unique
   constraint exists on ``create_all`` and ``get_or_create_balance``
   cannot fork a second row (the entry point for the future
   Postgres-backed concurrent first-touch test).
2. ``reserve_stock`` locks/updates exactly the requested balance row
   (location- or lot-specific); with several location rows under one
   (sku, warehouse) pair it no longer fans out / raises
   ``MultipleResultsFound``. SQLite cannot prove the ``FOR UPDATE`` lock
   itself (SQLAlchemy no-ops it there) — these tests pin the row
   *selection*, and the mutators' read-modify-write touching only the
   targeted row.
3. ``sweep_expired_reservations`` releases expired reservations
   (partially consumed ones release the remainder), and ``reserve_stock``
   sweeps lazily so ``available`` never counts an expired reservation.
4. ``adjust`` can no longer drive ``on_hand`` negative.
5. ``reconcile_inventory`` applies both transfer legs and groups by
   (sku, warehouse, location, lot).
6. ``unblock_stock`` is the missing decrement path for ``blocked``.
7. ``approve_stocktake`` only approves lines that were counted.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import UniqueConstraint, select
from sqlalchemy.exc import IntegrityError

from database.models import InvInventoryBalance, InvStocktakeLine
from services.api_gateway.exceptions import EcoNojinException
from services.inventory.service import sweep_expired_reservations

pytestmark = pytest.mark.asyncio


async def _location_balances(
    db_session, sku_id: int, warehouse_id: int
) -> dict[int, InvInventoryBalance]:
    """All balance rows of one (sku, warehouse) keyed by ``location_id``."""
    result = await db_session.execute(
        select(InvInventoryBalance).where(
            InvInventoryBalance.sku_id == sku_id,
            InvInventoryBalance.warehouse_id == warehouse_id,
        )
    )
    return {balance.location_id: balance for balance in result.scalars().all()}


class TestBalanceUniqueness:
    """One balance row per (sku_id, warehouse_id, location_id, lot_id)."""

    async def test_model_declares_unique_constraint_on_full_key(self):
        unique = {
            constraint.name: constraint
            for constraint in InvInventoryBalance.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert "uq_inv_balance_sku_wh_loc_lot" in unique
        assert [column.name for column in unique["uq_inv_balance_sku_wh_loc_lot"].columns] == [
            "sku_id",
            "warehouse_id",
            "location_id",
            "lot_id",
        ]

    async def test_location_and_lot_sentinels_are_not_null_with_zero_default(self):
        for column in (InvInventoryBalance.location_id, InvInventoryBalance.lot_id):
            assert column.nullable is False
            assert str(column.server_default.arg) == "0"

    async def test_duplicate_balance_row_rejected_by_create_all(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"))

        db_session.add(
            InvInventoryBalance(
                sku_id=sku.id,
                warehouse_id=warehouse.id,
                location_id=0,
                lot_id=0,
                on_hand=Decimal("5"),
            )
        )
        with pytest.raises(IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    async def test_get_or_create_balance_never_forks_a_second_row(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh

        first = await stock_service.get_or_create_balance(sku.id, warehouse.id, 7, 9)
        second = await stock_service.get_or_create_balance(sku.id, warehouse.id, 7, 9)

        assert first.id == second.id
        rows = (
            await db_session.execute(
                select(InvInventoryBalance).where(
                    InvInventoryBalance.sku_id == sku.id,
                    InvInventoryBalance.warehouse_id == warehouse.id,
                    InvInventoryBalance.location_id == 7,
                    InvInventoryBalance.lot_id == 9,
                )
            )
        ).scalars().all()
        assert len(rows) == 1


class TestReserveStockRowSelection:
    """reserve_stock locks/updates exactly one row, never fanning out."""

    async def test_reserve_on_location_specific_row(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), location_id=1)
        await stock_service.receipt(sku.id, warehouse.id, Decimal("20"), location_id=2)

        reservation = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("5"), "order", "order-loc-1", location_id=1
        )

        assert reservation.status == "active"
        assert reservation.location_id == 1
        balances = await _location_balances(db_session, sku.id, warehouse.id)
        assert balances[1].reserved == Decimal("5")
        assert balances[2].reserved == Decimal("0")

    async def test_reserve_availability_is_per_row_not_aggregate(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), location_id=1)
        await stock_service.receipt(sku.id, warehouse.id, Decimal("20"), location_id=2)

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.reserve_stock(
                sku.id, warehouse.id, Decimal("15"), "order", "order-loc-2", location_id=1
            )
        assert exc_info.value.code == "INSUFFICIENT_AVAILABLE_STOCK"

    async def test_reserve_without_location_picks_sentinel_row_deterministically(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"))
        await stock_service.receipt(sku.id, warehouse.id, Decimal("20"), location_id=5)

        # (sku, warehouse) now holds two balance rows: selection must be
        # deterministic instead of matching both (MultipleResultsFound).
        await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("4"), "order", "order-default"
        )

        balances = await _location_balances(db_session, sku.id, warehouse.id)
        assert balances[0].reserved == Decimal("4")
        assert balances[5].reserved == Decimal("0")

    async def test_reservation_round_trip_on_location_specific_row(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("30"), location_id=4)
        reservation = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("12"), "order", "order-round-trip", location_id=4
        )

        await stock_service.consume_reservation(reservation.id, Decimal("5"))
        balances = await _location_balances(db_session, sku.id, warehouse.id)
        assert balances[4].on_hand == Decimal("25")
        assert balances[4].reserved == Decimal("7")

        await stock_service.release_reservation(reservation.id)
        balances = await _location_balances(db_session, sku.id, warehouse.id)
        assert balances[4].reserved == Decimal("0")
        assert balances[4].on_hand == Decimal("25")

    async def test_mutators_update_only_the_targeted_location_row(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), location_id=1)
        await stock_service.receipt(sku.id, warehouse.id, Decimal("20"), location_id=2)

        await stock_service.issue(sku.id, warehouse.id, Decimal("4"), location_id=1)
        await stock_service.transfer(
            sku.id, warehouse.id, warehouse.id, Decimal("3"),
            from_location_id=1, to_location_id=2,
        )

        balances = await _location_balances(db_session, sku.id, warehouse.id)
        assert balances[1].on_hand == Decimal("3")  # 10 - 4 issued - 3 transferred out
        assert balances[2].on_hand == Decimal("23")  # 20 + 3 transferred in


class TestReservationExpiry:
    """Expired reservations release their reserved quantity."""

    async def test_sweep_releases_expired_reservation(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("100"))
        expired = await stock_service.reserve_stock(
            sku.id,
            warehouse.id,
            Decimal("60"),
            "order",
            "order-expired",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        fresh = await stock_service.reserve_stock(
            sku.id,
            warehouse.id,
            Decimal("10"),
            "order",
            "order-fresh",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.reserved == Decimal("70")

        # Time passes: the first reservation's deadline elapses.
        expired.expires_at = datetime.now(UTC) - timedelta(hours=1)
        await db_session.commit()

        released = await sweep_expired_reservations(db_session)
        assert released == 1

        assert expired.status == "expired"
        assert expired.released_at is not None
        assert fresh.status == "active"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.reserved == Decimal("10")

        releases = await stock_service.get_movements(sku_id=sku.id, movement_type="release")
        assert any(movement.qty == Decimal("60") for movement in releases)

    async def test_sweep_releases_only_the_unconsumed_remainder(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("100"))
        reservation = await stock_service.reserve_stock(
            sku.id,
            warehouse.id,
            Decimal("10"),
            "order",
            "order-partial",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        await stock_service.consume_reservation(reservation.id, Decimal("4"))

        released = await sweep_expired_reservations(db_session)
        assert released == 1
        assert reservation.status == "expired"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.reserved == Decimal("0")
        assert balance.on_hand == Decimal("96")  # 100 - 4 consumed

    async def test_reserve_stock_sweeps_expired_lazily(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("100"))
        expired = await stock_service.reserve_stock(
            sku.id,
            warehouse.id,
            Decimal("60"),
            "order",
            "order-superseded",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        # Without the lazy sweep this second reservation would fail:
        # only 40 would be available against the expired 60.
        fresh = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("60"), "order", "order-after-sweep"
        )

        assert fresh.status == "active"
        assert expired.status == "expired"
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.reserved == Decimal("60")

    async def test_sweep_leaves_unexpired_reservations_alone(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("100"))
        reservation = await stock_service.reserve_stock(
            sku.id,
            warehouse.id,
            Decimal("50"),
            "order",
            "order-still-fresh",
            expires_at=datetime.now(UTC) + timedelta(hours=48),
        )

        assert await sweep_expired_reservations(db_session) == 0
        assert reservation.status == "active"
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.reserved == Decimal("50")


class TestAdjustFloor:
    """adjust has a -0 floor on on_hand."""

    async def test_negative_adjustment_cannot_drive_on_hand_negative(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"))

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.adjust(sku.id, warehouse.id, Decimal("-15"), reason="wrong")
        assert exc_info.value.code == "NEGATIVE_ON_HAND"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("10")

    async def test_adjustment_down_to_exactly_zero_is_allowed(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"))

        await stock_service.adjust(sku.id, warehouse.id, Decimal("-10"), reason="depleted")
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("0")

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.adjust(sku.id, warehouse.id, Decimal("-1"))
        assert exc_info.value.code == "NEGATIVE_ON_HAND"

        await stock_service.adjust(sku.id, warehouse.id, Decimal("3"))
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("3")


class TestBlockedPool:
    """blocked is decremented through unblock_stock; available semantics."""

    async def test_scrap_then_unblock_round_trip(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("50"))
        await stock_service.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.blocked == Decimal("10")
        assert balance.on_hand == Decimal("40")
        # blocked sits outside on_hand (scrap removed it from on_hand
        # when it entered the pool), so available does not subtract it.
        assert balance.available == Decimal("40")

        movement = await stock_service.unblock_stock(
            sku.id, warehouse.id, Decimal("4"), reason="inspection passed"
        )
        assert movement.movement_type == "unblock"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.blocked == Decimal("6")
        assert balance.on_hand == Decimal("44")

    async def test_unblock_refuses_more_than_the_pool_holds(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("50"))
        await stock_service.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.unblock_stock(sku.id, warehouse.id, Decimal("11"))
        assert exc_info.value.code == "INSUFFICIENT_BLOCKED"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.blocked == Decimal("10")


class TestReconciliation:
    """reconcile_inventory applies both transfer legs, grouped by place."""

    async def test_transfer_scenario_reconciles_clean(self, db_session, sku, stock_service):
        source = stock_service._default_wh
        destination = await stock_service.create_warehouse("P218-DEST", "Destination")
        await stock_service.receipt(sku.id, source.id, Decimal("100"))
        await stock_service.transfer(sku.id, source.id, destination.id, Decimal("40"))
        await stock_service.issue(sku.id, source.id, Decimal("20"))

        result = await stock_service.reconcile_inventory()

        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0
        assert result["total_checked"] == 2

    async def test_same_warehouse_location_transfer_reconciles_clean(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), location_id=1)
        await stock_service.receipt(sku.id, warehouse.id, Decimal("20"), location_id=2)
        await stock_service.transfer(
            sku.id, warehouse.id, warehouse.id, Decimal("3"),
            from_location_id=1, to_location_id=2,
        )

        result = await stock_service.reconcile_inventory()

        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0

    async def test_drift_reported_with_location_and_lot_keys(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("50"), location_id=3, lot_id=4)

        balance = (
            await db_session.execute(
                select(InvInventoryBalance).where(
                    InvInventoryBalance.sku_id == sku.id,
                    InvInventoryBalance.warehouse_id == warehouse.id,
                    InvInventoryBalance.location_id == 3,
                    InvInventoryBalance.lot_id == 4,
                )
            )
        ).scalar_one()
        balance.on_hand += Decimal("5")
        await db_session.commit()

        result = await stock_service.reconcile_inventory()

        assert result["overall_ok"] is False
        assert result["discrepancies_count"] == 1
        discrepancy = result["discrepancies"][0]
        assert discrepancy["location_id"] == 3
        assert discrepancy["lot_id"] == 4
        assert Decimal(discrepancy["on_hand"]) == Decimal("55")
        assert Decimal(discrepancy["drift"]) == Decimal("5")


class TestStocktakeApproval:
    """approve_stocktake approves only lines that were counted."""

    async def test_approval_follows_the_counted_gate(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("100"))
        stocktake = await stock_service.create_stocktake(
            warehouse_id=warehouse.id,
            created_by="admin",
            lines=[
                # Variance: adjusted and approved.
                {"sku_id": sku.id, "counted_qty": Decimal("95")},
                # Counted and matches the system quantity: approved with
                # no adjustment (the old blanket raw UPDATE approved every
                # line, counted or not; the per-line counted gate now owns
                # that decision).
                {"sku_id": sku.id, "counted_qty": Decimal("100")},
            ],
        )

        await stock_service.approve_stocktake(stocktake.id, "admin")

        lines = (
            await db_session.execute(
                select(InvStocktakeLine).where(
                    InvStocktakeLine.stocktake_id == stocktake.id
                )
            )
        ).scalars().all()
        assert {line.status for line in lines} == {"approved"}

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("95")

        # Only the variance line produces an adjustment movement.
        adjustments = await stock_service.get_movements(movement_type="adjustment")
        assert len(adjustments) == 1

    async def test_stocktake_variance_cannot_drive_on_hand_negative(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("5"))
        stocktake = await stock_service.create_stocktake(
            warehouse_id=warehouse.id,
            created_by="admin",
            lines=[{"sku_id": sku.id, "counted_qty": Decimal("4")}],
        )
        # Stock leaves after the count, so applying the frozen -1 variance
        # would push on_hand below zero.
        await stock_service.issue(sku.id, warehouse.id, Decimal("5"))

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.approve_stocktake(stocktake.id, "admin")
        assert exc_info.value.code == "NEGATIVE_ON_HAND"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("0")
        await db_session.refresh(stocktake)
        assert stocktake.status == "draft"
