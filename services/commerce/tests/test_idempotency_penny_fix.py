"""Surgical regression tests for the two money/security fixes.

Both bugs were found by the ``test_properties_order_money`` wave and pinned
there as INTENTIONAL; these tests nail the fixed behaviour directly, without
Hypothesis, so a regression fails loudly and alone:

1. **Cross-tenant idempotency** — an idempotency key is scoped to its buyer.
   Buyer B reusing buyer A's key is rejected with ``IDEMPOTENCY_KEY_CONFLICT``
   and is never mapped to A's order, while A's own replay stays idempotent.
2. **Penny-order settlement** — an order whose two fee lines both round to
   0.00 settles with a zero-leg-free, still balanced batch (cash in, seller
   out), leaving the ledger's trial balance even.

Normal-fee orders keep their exact three-line settlement lineup.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from database.models import (
    ComOrder,
    ComOrderItem,
    ComSettlement,
    FinJournalBatch,
    FinJournalEntry,
    InvInventoryBalance,
    InvReservation,
)
from services.api_gateway.exceptions import EcoNojinException
from services.commerce.service import OrderService
from services.finance.chart_of_accounts import (
    ECO_CASH,
    ECO_PLATFORM_REVENUE,
    ECO_SELLER_PAYABLE,
)
from services.finance.ledger_service import LedgerService
from services.inventory.service import StockService

pytestmark = pytest.mark.asyncio

#: Only the tables this file writes, children before parents, so one DELETE
#: pass fully isolates one test from the next.
_OWNED_TABLES = (
    "com_order_items",
    "com_payment_intents",
    "com_settlements",
    "com_orders",
    "inv_reservations",
    "inv_stock_movements",
    "inv_inventory_balances",
    "inv_lots",
    "inv_locations",
    "inv_warehouses",
    "inv_skus",
    "landscape_fund_credits",
    "landscape_funds",
    "fin_journal_entries",
    "fin_journal_batches",
    "fin_accounts",
    "audit_events",
)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


async def _wipe(db_session) -> None:
    """Empty every table this file touches, so a test starts clean."""
    await db_session.rollback()
    for table in _OWNED_TABLES:
        await db_session.execute(text(f"DELETE FROM {table}"))
    await db_session.commit()
    db_session.expunge_all()


async def _stock(db_session, on_hand: str = "100", cost: str = "1"):
    """A warehouse with one SKU and ``on_hand`` units on the shelf."""
    stock = StockService(db_session)
    warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
    sku = await stock.create_sku(
        _unique("SKU"), _unique("item"), standard_cost=Decimal(cost)
    )
    await stock.receipt(
        sku.id, warehouse.id, Decimal(on_hand), unit_cost=Decimal(cost), created_by="fix"
    )
    return stock, warehouse, sku


def _item(sku, warehouse, *, qty: str = "1", unit_price: str | None = None) -> list[dict]:
    entry = {
        "sku_code": sku.sku_code,
        "quantity": Decimal(qty),
        "warehouse_id": warehouse.id,
    }
    if unit_price is not None:
        entry["unit_price"] = Decimal(unit_price)
    return [entry]


async def _deliver(service: OrderService, order_id: str) -> None:
    await service.confirm_payment(order_id, payment_confirmed=True)
    await service.process_order(order_id)
    await service.ship_order(order_id, _unique("TRK"), "fix")
    await service.mark_delivered(order_id)


async def _reserved_qty(db_session, sku, warehouse) -> Decimal:
    balance = (
        (
            await db_session.execute(
                select(InvInventoryBalance).where(
                    InvInventoryBalance.sku_id == sku.id,
                    InvInventoryBalance.warehouse_id == warehouse.id,
                )
            )
        )
        .scalar_one()
    )
    return Decimal(str(balance.reserved))


async def _order_reservations(db_session) -> list:
    return (
        (
            await db_session.execute(
                select(InvReservation).where(InvReservation.reference_type == "order")
            )
        )
        .scalars()
        .all()
    )


# ---------------------------------------------------------------------------
# (a) + (b) idempotency is scoped to its buyer
# ---------------------------------------------------------------------------


class TestIdempotencyKeyIsScopedToItsBuyer:
    async def test_second_buyer_with_same_key_is_rejected_not_mapped(self, db_session):
        """Buyer B reusing buyer A's key is refused, never handed A's order.

        The rejection happens before any stock is held, so the order does not
        double-hold, and A's own later replay still resolves to A's order.
        """
        await _wipe(db_session)
        _, warehouse, sku = await _stock(db_session)
        service = OrderService(db_session)
        key = _unique("shared-key")
        alice = _unique("alice")
        bob = _unique("bob")

        alice_order = await service.create_order(
            buyer_id=alice, items=_item(sku, warehouse), idempotency_key=key
        )
        alice_id = alice_order.id
        assert alice_order.buyer_id == alice
        assert await _reserved_qty(db_session, sku, warehouse) == Decimal("1")

        # The second buyer, reusing the key, is rejected — not mapped to A.
        with pytest.raises(EcoNojinException) as raised:
            await service.create_order(
                buyer_id=bob, items=_item(sku, warehouse), idempotency_key=key
            )
        assert raised.value.code == "IDEMPOTENCY_KEY_CONFLICT"

        # Never mapped: still exactly one order, and it is A's.
        rows = (await db_session.execute(select(ComOrder))).scalars().all()
        assert len(rows) == 1
        assert rows[0].id == alice_id
        assert rows[0].buyer_id == alice

        # Stock is not double-held: one order reservation, one unit reserved.
        assert len(await _order_reservations(db_session)) == 1
        assert await _reserved_qty(db_session, sku, warehouse) == Decimal("1")

        # The rejection did not poison A's own namespace: A still replays.
        replayed = await service.create_order(
            buyer_id=alice, items=_item(sku, warehouse), idempotency_key=key
        )
        assert replayed.id == alice_id
        assert len((await db_session.execute(select(ComOrder))).scalars().all()) == 1

    async def test_same_buyer_replay_is_still_idempotent(self, db_session):
        """A legitimate replay by the key's own buyer returns the same order.

        Stock is reserved once, one order and one order-item row survive, and
        every replay returns the identical order id.
        """
        await _wipe(db_session)
        _, warehouse, sku = await _stock(db_session, on_hand="50")
        service = OrderService(db_session)
        buyer = _unique("buyer")
        key = _unique("own-key")

        created = [
            await service.create_order(
                buyer_id=buyer, items=_item(sku, warehouse), idempotency_key=key
            )
            for _ in range(3)
        ]

        assert len({order.id for order in created}) == 1
        assert len((await db_session.execute(select(ComOrder))).scalars().all()) == 1
        item_rows = (await db_session.execute(select(ComOrderItem))).scalars().all()
        assert len(item_rows) == 1
        assert len(await _order_reservations(db_session)) == 1
        assert await _reserved_qty(db_session, sku, warehouse) == Decimal("1")


# ---------------------------------------------------------------------------
# (c) a penny order settles with a balanced batch and an even trial balance
# ---------------------------------------------------------------------------


class TestPennyOrderSettles:
    async def test_one_cent_order_settles_balanced_with_a_trial_balance(self, db_session):
        await _wipe(db_session)
        _, warehouse, sku = await _stock(db_session, on_hand="10")
        service = OrderService(db_session)

        order = await service.create_order(
            buyer_id=_unique("buyer"),
            items=_item(sku, warehouse, unit_price="0.01"),
            shipping_address={"city": "Karaj"},
        )
        # A one-cent subtotal charges no fee at all.
        assert Decimal(str(order.subtotal)) == Decimal("0.01")
        assert Decimal(str(order.platform_fee)) == Decimal("0.00")
        assert Decimal(str(order.landscape_fee)) == Decimal("0.00")
        assert Decimal(str(order.total)) == Decimal("0.01")

        await _deliver(service, order.id)
        settlement = await service.settle_order(order.id)

        # A settlement row exists and folds the whole total to the seller.
        assert order.status == "settled"
        settlements = (
            (await db_session.execute(select(ComSettlement))).scalars().all()
        )
        assert len(settlements) == 1
        assert Decimal(str(settlement.amount)) == Decimal("0.01")

        # The batch is posted, and carries exactly the two live legs: the zero
        # fee leg was omitted, so there is no ``ECO_PLATFORM_REVENUE`` line.
        batch = (
            await db_session.execute(
                select(FinJournalBatch).where(
                    FinJournalBatch.id == settlement.journal_batch_id
                )
            )
        ).scalar_one()
        assert batch.is_posted is True

        entries = (
            (
                await db_session.execute(
                    select(FinJournalEntry).where(
                        FinJournalEntry.batch_id == settlement.journal_batch_id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(entries) == 2
        debits = {e.account_id: e.amount for e in entries if e.entry_type == "debit"}
        credits = {e.account_id: e.amount for e in entries if e.entry_type == "credit"}
        assert debits == {ECO_CASH: Decimal("0.01")}
        assert credits == {ECO_SELLER_PAYABLE: Decimal("0.01")}
        # Every leg is positive and the batch balances (0.01 in == 0.01 out).
        assert all(Decimal(str(e.amount)) > 0 for e in entries)
        assert sum(debits.values()) == sum(credits.values()) == Decimal("0.01")

        # The ledger's posted trial balance for the order currency still evens.
        report = await LedgerService(db_session).trial_balance(asset=order.currency)
        row = next(r for r in report["totals"] if r["asset"] == order.currency)
        assert Decimal(row["debit"]) == Decimal(row["credit"])


# ---------------------------------------------------------------------------
# (d) a normal-fee order keeps its byte-identical three-line lineup
# ---------------------------------------------------------------------------


class TestNormalOrderSettlementLineupUnchanged:
    async def test_normal_order_keeps_three_legs_with_the_same_amounts(self, db_session):
        await _wipe(db_session)
        _, warehouse, sku = await _stock(db_session, on_hand="100")
        service = OrderService(db_session)

        # 100 * 300 bps = 3.00 platform, 100 * 100 bps = 1.00 landscape,
        # total 104.00, seller 100.00 — all three legs positive, so none is
        # dropped and the settlement lineup is exactly what it was before.
        order = await service.create_order(
            buyer_id=_unique("buyer"),
            items=_item(sku, warehouse, unit_price="100"),
            shipping_address={"village_id": _unique("village")},
        )
        assert Decimal(str(order.platform_fee)) == Decimal("3.00")
        assert Decimal(str(order.landscape_fee)) == Decimal("1.00")
        assert Decimal(str(order.total)) == Decimal("104.00")

        await _deliver(service, order.id)
        settlement = await service.settle_order(order.id)

        entries = (
            (
                await db_session.execute(
                    select(FinJournalEntry).where(
                        FinJournalEntry.batch_id == settlement.journal_batch_id
                    )
                )
            )
            .scalars()
            .all()
        )
        # The three-line lineup, in creation order, unchanged.
        assert len(entries) == 3
        lineup = [
            (e.account_id, e.entry_type, Decimal(str(e.amount)))
            for e in sorted(entries, key=lambda e: e.id)
        ]
        assert lineup == [
            (ECO_PLATFORM_REVENUE, "credit", Decimal("4.00")),
            (ECO_SELLER_PAYABLE, "credit", Decimal("100.00")),
            (ECO_CASH, "debit", Decimal("104.00")),
        ]

        debits = {e.account_id: e.amount for e in entries if e.entry_type == "debit"}
        credits = {e.account_id: e.amount for e in entries if e.entry_type == "credit"}
        assert sum(debits.values()) == sum(credits.values()) == Decimal("104.00")

        report = await LedgerService(db_session).trial_balance(asset=order.currency)
        row = next(r for r in report["totals"] if r["asset"] == order.currency)
        assert row["balanced"] is True
