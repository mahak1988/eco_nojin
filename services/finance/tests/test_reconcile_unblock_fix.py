"""Regression tests for the ``unblock`` leg in ``reconcile_inventory``.

``StockService.unblock_stock`` is the mirror of ``scrap``: it restores
``on_hand`` (and decrements ``blocked``), and the weighted-average
valuation prices the leg as inbound. The finance reconciliation's signed
movement sum used to omit that leg, so a scrap-then-unblock sequence
reconciled clean at the scrap and then reported the whole restored
quantity as phantom ``on_hand_drift`` — the exact defect this file pins
shut.

These tests also prove the fix did not dull the check: a real off-ledger
``on_hand`` mutation is still reported, a scrap without an unblock still
reconciles, and ``run_full_reconciliation`` folds the corrected
inventory result into ``overall_ok``.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from database.models import InvInventoryBalance
from services.finance.reconciliation import ReconciliationService
from services.inventory.service import StockService

pytestmark = pytest.mark.asyncio


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


async def _load_balance(db_session, sku_id: int, warehouse_id: int) -> InvInventoryBalance:
    result = await db_session.execute(
        select(InvInventoryBalance).where(
            InvInventoryBalance.sku_id == sku_id,
            InvInventoryBalance.warehouse_id == warehouse_id,
        )
    )
    return result.scalar_one()


class TestUnblockLegReconciles:
    """A scrap-then-unblock round trip must reconcile with zero drift."""

    async def test_response_shape_keys_unchanged(self, db_session):
        # The fix folds ``unblock`` into the on_hand sum but must not
        # change the response shape or any other key.
        result = await ReconciliationService(db_session).reconcile_inventory()
        assert set(result) == {
            "checked_at",
            "total_balances_checked",
            "discrepancies_count",
            "discrepancies",
            "overall_ok",
        }

    async def test_scrap_then_unblock_reports_no_drift(self, db_session):
        """The exact reproduction from the finding, now green.

        receipt 100 @ 1 -> scrap 10 leaves 90 on hand and reconciles; the
        unblock restores on_hand to 100 and must now be summed as an
        inbound leg, so the balance and the ledger agree (drift 0).
        """
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        service = ReconciliationService(db_session)

        await stock.receipt(sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1"))
        await stock.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")

        between = await service.reconcile_inventory()
        assert between["overall_ok"] is True

        await stock.unblock_stock(sku.id, warehouse.id, Decimal("10"))

        result = await service.reconcile_inventory()

        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0
        assert result["discrepancies"] == []
        assert result["total_balances_checked"] == 1
        # The on_hand was genuinely restored to 100 on both sides.
        balance = await _load_balance(db_session, sku.id, warehouse.id)
        assert Decimal(str(balance.on_hand)) == Decimal("100")

    async def test_off_ledger_on_hand_tamper_is_still_detected(self, db_session):
        """A drift that should be caught still is (the check is not dulled)."""
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        service = ReconciliationService(db_session)

        await stock.receipt(sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1"))
        await stock.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")
        await stock.unblock_stock(sku.id, warehouse.id, Decimal("10"))

        # Clean once the unblock leg is summed correctly.
        assert (await service.reconcile_inventory())["overall_ok"] is True

        # A genuine off-ledger mutation must still surface as drift.
        balance = await _load_balance(db_session, sku.id, warehouse.id)
        balance.on_hand += Decimal("7")
        await db_session.commit()

        result = await service.reconcile_inventory()

        assert result["overall_ok"] is False
        assert result["discrepancies_count"] == 1
        drift = result["discrepancies"][0]
        # ledger: 100 receipt - 10 scrap + 10 unblock = 100; on_hand 107.
        assert Decimal(drift["on_hand"]) == Decimal("107")
        assert Decimal(drift["ledger_on_hand"]) == Decimal("100")
        assert Decimal(drift["on_hand_drift"]) == Decimal("7")

    async def test_scrap_alone_without_unblock_still_reconciles(self, db_session):
        """Scrap alone (no unblock) is unchanged: 100 -> 90 on both sides."""
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        service = ReconciliationService(db_session)

        await stock.receipt(sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1"))
        await stock.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")

        result = await service.reconcile_inventory()

        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0


class TestFullReconciliationFoldsUnblockFix:
    """``run_full_reconciliation`` reflects the corrected inventory check."""

    async def test_scrap_then_unblock_is_ok_end_to_end(self, db_session):
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))

        await stock.receipt(sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1"))
        await stock.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")
        await stock.unblock_stock(sku.id, warehouse.id, Decimal("10"))

        result = await ReconciliationService(db_session).run_full_reconciliation()

        assert set(result["checks"]) == {"wallet_ledger", "orders_payments", "inventory"}
        inventory = result["checks"]["inventory"]
        assert inventory["overall_ok"] is True
        assert inventory["discrepancies_count"] == 0
        assert result["overall_ok"] is True

    async def test_on_hand_tamper_makes_overall_not_ok_via_inventory(self, db_session):
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))

        await stock.receipt(sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1"))
        await stock.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")
        await stock.unblock_stock(sku.id, warehouse.id, Decimal("10"))

        balance = await _load_balance(db_session, sku.id, warehouse.id)
        balance.on_hand += Decimal("5")
        await db_session.commit()

        result = await ReconciliationService(db_session).run_full_reconciliation()

        inventory = result["checks"]["inventory"]
        assert inventory["overall_ok"] is False
        assert result["overall_ok"] is False
        assert Decimal(inventory["discrepancies"][0]["on_hand_drift"]) == Decimal("5")
