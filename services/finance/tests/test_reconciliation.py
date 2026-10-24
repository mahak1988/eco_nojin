"""Tests for the real reconciliation checks (P1-12).

``ReconciliationService.reconcile_orders_payments`` and
``reconcile_inventory`` used to return hardcoded zero-discrepancy
payloads, so ``run_full_reconciliation`` was always green. These tests
pin the real behaviour: clean seeded states stay ``ok``, and seeded
discrepancies (orphaned intents, missing/unconfirmed payments, missing
settlements, unposted settlement journals, balance/ledger drift and
warehouse transfers) are reported with item-level detail.
"""

import uuid
from collections import Counter
from decimal import Decimal

import pytest
from sqlalchemy import select

from database.models import (
    ComOrder,
    ComPaymentIntent,
    ComSettlement,
    InvInventoryBalance,
)
from services.finance.ledger_service import LedgerService
from services.finance.reconciliation import ReconciliationService
from services.inventory.service import StockService

pytestmark = pytest.mark.asyncio


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


async def _seed_posted_batch(db_session) -> int:
    """Create and post a balanced journal batch; return its id."""
    ledger = LedgerService(db_session)
    batch = await ledger.create_journal_batch(
        reference_type="settlement",
        reference_id=_unique("ref"),
        entries=[
            {
                "account_id": "ECO_CASH",
                "entry_type": "debit",
                "asset": "IRR",
                "amount": "1000",
            },
            {
                "account_id": "ECO_SELLER_PAYABLE",
                "entry_type": "credit",
                "asset": "IRR",
                "amount": "1000",
            },
        ],
        description="Reconciliation test batch",
        created_by="recon-test",
    )
    posted = await ledger.post_journal_batch(batch.id)
    return posted.id


async def _seed_order(
    db_session,
    *,
    total: Decimal,
    status: str = "paid",
    payment_status: str = "paid",
) -> ComOrder:
    order = ComOrder(
        id=_unique("order"),
        order_number=_unique("ORD"),
        buyer_id="buyer-recon",
        seller_id="seller-recon",
        status=status,
        payment_status=payment_status,
        currency="IRR",
        subtotal=total,
        platform_fee=Decimal("0"),
        landscape_fee=Decimal("0"),
        total=total,
    )
    db_session.add(order)
    await db_session.commit()
    return order


async def _seed_payment_intent(
    db_session,
    *,
    order_id: str,
    amount: Decimal,
    status: str = "succeeded",
) -> ComPaymentIntent:
    intent = ComPaymentIntent(
        id=_unique("pi"),
        order_id=order_id,
        buyer_id="buyer-recon",
        provider="bank_transfer",
        amount=amount,
        currency="IRR",
        status=status,
    )
    db_session.add(intent)
    await db_session.commit()
    return intent


async def _seed_settlement(
    db_session,
    *,
    order_id: str,
    amount: Decimal,
    journal_batch_id: int | None,
) -> ComSettlement:
    settlement = ComSettlement(
        id=_unique("stl"),
        order_id=order_id,
        seller_id="seller-recon",
        amount=amount,
        currency="IRR",
        commission_fee=Decimal("0"),
        landscape_fee=Decimal("0"),
        status="paid",
        journal_batch_id=journal_batch_id,
    )
    db_session.add(settlement)
    await db_session.commit()
    return settlement


async def _load_balance(db_session, sku_id: int, warehouse_id: int) -> InvInventoryBalance:
    result = await db_session.execute(
        select(InvInventoryBalance).where(
            InvInventoryBalance.sku_id == sku_id,
            InvInventoryBalance.warehouse_id == warehouse_id,
        )
    )
    return result.scalar_one()


class TestOrdersPaymentsReconciliation:
    """Order/payment/settlement reconciliation checks."""

    async def test_clean_state_ok(self, db_session):
        service = ReconciliationService(db_session)
        batch_id = await _seed_posted_batch(db_session)

        paid_order = await _seed_order(db_session, total=Decimal("1000"))
        await _seed_payment_intent(
            db_session, order_id=paid_order.id, amount=Decimal("1000")
        )

        settled_order = await _seed_order(db_session, total=Decimal("2500"), status="settled")
        await _seed_payment_intent(
            db_session, order_id=settled_order.id, amount=Decimal("2500")
        )
        await _seed_settlement(
            db_session,
            order_id=settled_order.id,
            amount=Decimal("2500"),
            journal_batch_id=batch_id,
        )

        # A draft order legitimately carries no payment intent yet.
        await _seed_order(
            db_session, total=Decimal("5"), status="draft", payment_status="pending"
        )

        result = await service.reconcile_orders_payments()

        assert result["total_orders_checked"] == 3
        assert result["discrepancies_count"] == 0
        assert result["discrepancies"] == []
        assert result["overall_ok"] is True

    async def test_response_shape_keys_unchanged(self, db_session):
        service = ReconciliationService(db_session)

        orders = await service.reconcile_orders_payments()
        inventory = await service.reconcile_inventory()

        assert set(orders) == {
            "checked_at",
            "total_orders_checked",
            "discrepancies_count",
            "discrepancies",
            "overall_ok",
        }
        assert set(inventory) == {
            "checked_at",
            "total_balances_checked",
            "discrepancies_count",
            "discrepancies",
            "overall_ok",
        }

    async def test_discrepancies_detected_with_item_detail(self, db_session):
        service = ReconciliationService(db_session)
        batch_id = await _seed_posted_batch(db_session)

        # Payment intent without an order (orphan).
        await _seed_payment_intent(
            db_session, order_id=_unique("missing-order"), amount=Decimal("500")
        )

        # Paid order with an unconfirmed intent whose amount drifts.
        unconfirmed_order = await _seed_order(db_session, total=Decimal("1000"))
        await _seed_payment_intent(
            db_session,
            order_id=unconfirmed_order.id,
            amount=Decimal("900"),
            status="awaiting_transfer",
        )

        # Settled order without any settlement.
        unsettled_order = await _seed_order(db_session, total=Decimal("750"), status="settled")
        await _seed_payment_intent(
            db_session, order_id=unsettled_order.id, amount=Decimal("750")
        )

        # Settled order whose settlement amount does not fold back to the
        # order total and whose journal batch id is missing.
        short_settled_order = await _seed_order(db_session, total=Decimal("300"), status="settled")
        await _seed_payment_intent(
            db_session, order_id=short_settled_order.id, amount=Decimal("300")
        )
        await _seed_settlement(
            db_session,
            order_id=short_settled_order.id,
            amount=Decimal("100"),
            journal_batch_id=None,
        )

        # Control: fully healthy settled order.
        healthy_order = await _seed_order(db_session, total=Decimal("200"), status="settled")
        await _seed_payment_intent(
            db_session, order_id=healthy_order.id, amount=Decimal("200")
        )
        await _seed_settlement(
            db_session,
            order_id=healthy_order.id,
            amount=Decimal("200"),
            journal_batch_id=batch_id,
        )

        result = await service.reconcile_orders_payments()

        assert result["overall_ok"] is False
        assert result["total_orders_checked"] == 4
        counts = Counter(item["type"] for item in result["discrepancies"])
        assert counts == {
            "orphaned_payment_intent": 1,
            "unconfirmed_payment_intent": 1,
            "payment_amount_mismatch": 1,
            "missing_settlement": 1,
            "settlement_amount_mismatch": 1,
            "unposted_settlement_journal_batch": 1,
        }
        assert result["discrepancies_count"] == 6

        mismatch = next(
            item
            for item in result["discrepancies"]
            if item["type"] == "payment_amount_mismatch"
        )
        assert mismatch["order_id"] == unconfirmed_order.id
        assert mismatch["payment_intent_id"] is not None
        assert Decimal(mismatch["order_total"]) == Decimal("1000")
        assert Decimal(mismatch["payment_amount"]) == Decimal("900")

        orphan = next(
            item
            for item in result["discrepancies"]
            if item["type"] == "orphaned_payment_intent"
        )
        assert Decimal(orphan["payment_amount"]) == Decimal("500")
        assert orphan["order_id"] not in {
            unconfirmed_order.id,
            unsettled_order.id,
            short_settled_order.id,
            healthy_order.id,
        }


class TestInventoryReconciliation:
    """Balance-vs-ledger reconciliation checks."""

    async def test_clean_state_ok(self, db_session):
        service = ReconciliationService(db_session)
        stock = StockService(db_session)
        wh_a = await stock.create_warehouse("RECON-A", "Warehouse A", city="Tehran")
        wh_b = await stock.create_warehouse("RECON-B", "Warehouse B", city="Shiraz")
        sku = await stock.create_sku(sku_code=_unique("SKU"), name="Compost")

        await stock.receipt(sku.id, wh_a.id, Decimal("100"), created_by="recon-test")
        await stock.reserve_stock(
            sku.id,
            wh_a.id,
            Decimal("30"),
            "order",
            "order-clean",
            created_by="recon-test",
        )
        await stock.issue(sku.id, wh_a.id, Decimal("20"), created_by="recon-test")
        await stock.transfer(
            sku.id, wh_a.id, wh_b.id, Decimal("10"), created_by="recon-test"
        )
        await stock.scrap(
            sku.id, wh_b.id, Decimal("5"), reason="damaged", created_by="recon-test"
        )

        result = await service.reconcile_inventory()

        assert result["total_balances_checked"] == 2
        assert result["discrepancies_count"] == 0
        assert result["overall_ok"] is True

    async def test_transfer_between_warehouses_not_double_counted(self, db_session):
        service = ReconciliationService(db_session)
        stock = StockService(db_session)
        wh_a = await stock.create_warehouse("TRF-A", "Warehouse A")
        wh_b = await stock.create_warehouse("TRF-B", "Warehouse B")
        sku = await stock.create_sku(sku_code=_unique("SKU"), name="Compost")

        await stock.receipt(sku.id, wh_a.id, Decimal("100"), created_by="recon-test")
        await stock.transfer(
            sku.id, wh_a.id, wh_b.id, Decimal("30"), created_by="recon-test"
        )

        result = await service.reconcile_inventory()

        # The transfer moves stock: 70 stays at the source, 30 lands at the
        # destination. Counting it as a pure inbound movement (the
        # StockService SQL bug) would flag both warehouses as drifted.
        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0

    async def test_consumed_reservation_keeps_reserved_in_sync(self, db_session):
        service = ReconciliationService(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse("CONS-WH", "Warehouse")
        sku = await stock.create_sku(sku_code=_unique("SKU"), name="Compost")

        await stock.receipt(sku.id, warehouse.id, Decimal("100"), created_by="recon-test")
        reservation = await stock.reserve_stock(
            sku.id,
            warehouse.id,
            Decimal("50"),
            "order",
            "order-consume",
            created_by="recon-test",
        )
        await stock.consume_reservation(reservation.id)

        result = await service.reconcile_inventory()

        # on_hand: 100 receipt - 50 consume-issue; reserved: the reservation
        # is consumed, so nothing stays reserved.
        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0

    async def test_balance_ledger_drift_detected(self, db_session):
        service = ReconciliationService(db_session)
        stock = StockService(db_session)
        wh_a = await stock.create_warehouse("DRIFT-A", "Warehouse A")
        wh_b = await stock.create_warehouse("DRIFT-B", "Warehouse B")
        sku = await stock.create_sku(sku_code=_unique("SKU"), name="Compost")

        await stock.receipt(sku.id, wh_a.id, Decimal("100"), created_by="recon-test")
        await stock.transfer(
            sku.id, wh_a.id, wh_b.id, Decimal("30"), created_by="recon-test"
        )

        clean = await service.reconcile_inventory()
        assert clean["overall_ok"] is True

        balance_a = await _load_balance(db_session, sku.id, wh_a.id)
        balance_a.on_hand += Decimal("7")
        await db_session.commit()

        balance_b = await _load_balance(db_session, sku.id, wh_b.id)
        balance_b.reserved += Decimal("4")
        await db_session.commit()

        result = await service.reconcile_inventory()

        assert result["overall_ok"] is False
        assert result["discrepancies_count"] == 2
        by_key = {
            (item["sku_id"], item["warehouse_id"]): item
            for item in result["discrepancies"]
        }

        drift_a = by_key[(sku.id, wh_a.id)]
        assert Decimal(drift_a["on_hand"]) == Decimal("77")
        assert Decimal(drift_a["ledger_on_hand"]) == Decimal("70")
        assert Decimal(drift_a["on_hand_drift"]) == Decimal("7")
        assert Decimal(drift_a["reserved_drift"]) == Decimal("0")

        drift_b = by_key[(sku.id, wh_b.id)]
        assert Decimal(drift_b["on_hand"]) == Decimal("30")
        assert Decimal(drift_b["on_hand_drift"]) == Decimal("0")
        assert Decimal(drift_b["reserved"]) == Decimal("4")
        assert Decimal(drift_b["expected_reserved"]) == Decimal("0")
        assert Decimal(drift_b["reserved_drift"]) == Decimal("4")


class TestFullReconciliation:
    """run_full_reconciliation folds the real results into overall_ok."""

    async def test_empty_database_is_ok(self, db_session):
        result = await ReconciliationService(db_session).run_full_reconciliation()

        assert result["overall_ok"] is True
        assert set(result["checks"]) == {"wallet_ledger", "orders_payments", "inventory"}
        for check in result["checks"].values():
            assert check["overall_ok"] is True

    async def test_discrepancies_make_overall_not_ok(self, db_session):
        await _seed_payment_intent(
            db_session, order_id=_unique("missing-order"), amount=Decimal("500")
        )

        stock = StockService(db_session)
        warehouse = await stock.create_warehouse("FULL-WH", "Warehouse")
        sku = await stock.create_sku(sku_code=_unique("SKU"), name="Compost")
        await stock.receipt(sku.id, warehouse.id, Decimal("10"), created_by="recon-test")
        balance = await _load_balance(db_session, sku.id, warehouse.id)
        balance.on_hand += Decimal("3")
        await db_session.commit()

        result = await ReconciliationService(db_session).run_full_reconciliation()

        assert result["overall_ok"] is False
        orders = result["checks"]["orders_payments"]
        inventory = result["checks"]["inventory"]
        assert orders["overall_ok"] is False
        assert inventory["overall_ok"] is False
        assert any(
            item["type"] == "orphaned_payment_intent" for item in orders["discrepancies"]
        )
        assert Decimal(inventory["discrepancies"][0]["on_hand_drift"]) == Decimal("3")
