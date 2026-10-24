"""Property-based tests for the order-money invariants of the commerce service.

Every test is a Hypothesis property test on a deterministic profile:
``deadline=None``, a small ``max_examples`` budget, ``database=None`` (no
example database is written) and ``derandomize=True`` (the same examples on
every run). Each example starts from a database the test wipes itself, so no
example can observe another's rows, and no key is shared between examples.

What is pinned, by invariant:

1. **Fee conservation** — for cent-granular subtotals,
   ``platform_fee + landscape_fee + subtotal == total`` exactly, all in
   Decimal, no fee line negative, and each line within cent rounding of its
   share of the documented schedule.
2. **The seller receives the subtotal** — ``settle_order`` credits
   ``seller_amount == order.total - platform_fee - landscape_fee``, which is
   ``subtotal``: fees are added on top of the price, never taken out of it.
3. **The settlement folds to the order total** — ``amount + commission_fee +
   landscape_fee == total``, and the settlement journal's own rows balance and
   credit the exact fee lines.
4. **The take-rate band** — ``settlement_revenue_report``'s realised bps stay
   in the same measured band ``revenue_indicators`` documents.
5. **Idempotency** — replaying an order creation intent with the same
   ``idempotency_key`` returns the same order and reserves the stock once.
6. **The reservation lifecycle end to end** — creating an order holds stock,
   shipping it consumes it, cancelling it releases it, and
   ``available + reserved == on_hand`` throughout.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select, text

from database.models import (
    ComOrder,
    ComOrderItem,
    ComSettlement,
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
from services.finance.revenue_indicators import commerce_schedule, realised_bps
from services.inventory.service import StockService
from services.landscape.models import LandscapeFund, LandscapeFundCredit

# ---------------------------------------------------------------------------
# Deterministic Hypothesis profile.
# ---------------------------------------------------------------------------

_HEALTH = [HealthCheck.function_scoped_fixture, HealthCheck.too_slow]

PROPERTY = settings(
    max_examples=12,
    deadline=None,
    database=None,
    derandomize=True,
    suppress_health_check=_HEALTH,
)

#: Only the tables this file writes, children before parents, so one DELETE
#: pass fully isolates one example from the next.
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

MONEY_SCALE = Decimal("0.00000001")
#: The take-rate ceiling measured over ``revenue_indicators``' own arithmetic:
#: the nominal 400 bps plus one cent of rounding per line on a one-cent order.
MEASURED_BPS_CEILING = 600


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _cents(low: int, high: int) -> st.SearchStrategy[Decimal]:
    return st.integers(min_value=low, max_value=high).map(lambda c: Decimal(c) / 100)


async def _wipe(db_session) -> None:
    """Empty every table this file touches, so an example starts clean."""
    await db_session.rollback()
    for table in _OWNED_TABLES:
        await db_session.execute(text(f"DELETE FROM {table}"))
    await db_session.commit()
    db_session.expunge_all()


# ---------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------


@st.composite
def priced_plan(draw):
    """A random purchase: how much stock is received, and at what price.

    ``qty`` is drawn first so ``received_qty`` can be bounded below by it —
    otherwise the plan could ask for more than the receipt put on the shelf
    and ``create_order`` would refuse it, which is a property about the
    generator, not about the money.

    ``unit_price`` starts at one full unit so that both fee lines are
    non-zero: a subtotal of a few cents rounds both fees to nothing, and a
    settlement then keeps only the cash/seller legs (the zero fee leg is
    omitted — see :class:`TestPennyOrders`). Drawing above a cent keeps these
    property tests on the normal three-line settlement.
    """
    qty = draw(st.integers(1, 4))
    extra = draw(st.integers(0, 20))
    return {
        "received_qty": qty + extra,
        "received_cost": draw(_cents(1, 5000)),
        "unit_price": draw(_cents(100, 5000)),
        "qty": qty,
        "hold": draw(st.sampled_from(["settle", "cancel"])),
        "village": draw(st.booleans()),
    }


async def _place_order(db_session, plan) -> tuple[ComOrder, StockService]:
    """Build stock, then run one order through the reserved state."""
    stock = StockService(db_session)
    warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
    sku = await stock.create_sku(
        _unique("SKU"), _unique("item"), standard_cost=plan["received_cost"]
    )
    await stock.receipt(
        sku.id,
        warehouse.id,
        Decimal(plan["received_qty"]),
        unit_cost=plan["received_cost"],
        created_by="prop",
    )

    shipping = (
        {"village_id": _unique("village")} if plan["village"] else {"city": "Karaj"}
    )
    service = OrderService(db_session)
    order = await service.create_order(
        buyer_id=_unique("buyer"),
        items=[
            {
                "sku_code": sku.sku_code,
                "quantity": Decimal(plan["qty"]),
                "unit_price": plan["unit_price"],
                "warehouse_id": warehouse.id,
            }
        ],
        shipping_address=shipping,
        idempotency_key=_unique("idem"),
    )
    return order, stock


# ---------------------------------------------------------------------------
# 1. fee conservation
# ---------------------------------------------------------------------------


class TestFeeConservation:
    """``platform_fee + landscape_fee + subtotal == total``, exactly."""

    @given(subtotal=_cents(1, 200_000))
    @PROPERTY
    async def test_the_three_fee_lines_conserve_the_total(
        self, db_session, subtotal
    ):
        await _wipe(db_session)
        service = OrderService(db_session)

        platform_fee, landscape_fee, total = service._compute_fees(subtotal)

        assert platform_fee + landscape_fee + subtotal == total
        assert all(
            isinstance(value, Decimal) for value in (platform_fee, landscape_fee, total)
        )
        # Fees are never negative and never exceed the total.
        assert platform_fee >= 0
        assert landscape_fee >= 0
        assert total >= subtotal
        # Every figure is cent-granular, because every figure is money.
        for value in (platform_fee, landscape_fee, total):
            assert value == value.quantize(Decimal("0.01"))

    @given(subtotal=_cents(1, 200_000))
    @PROPERTY
    async def test_each_fee_line_is_one_cent_of_rounding_from_its_rate(
        self, db_session, subtotal
    ):
        await _wipe(db_session)
        service = OrderService(db_session)
        schedule = commerce_schedule()

        platform_fee, landscape_fee, _ = service._compute_fees(subtotal)

        for fee, name in ((platform_fee, "platform"), (landscape_fee, "landscape")):
            exact = subtotal * schedule[name] / Decimal("10000")
            # The line is the schedule's share, to the cent.
            assert abs(fee - exact) <= Decimal("0.01"), name

    @given(subtotal=_cents(1, 200_000))
    @PROPERTY
    async def test_fee_conservation_holds_for_any_subtotal(
        self, db_session, subtotal
    ):
        """The same property, restated as a sum of parts.

        Whatever the subtotal, the seller is paid the subtotal and the two
        fee lines are the only thing added on top of it.
        """
        await _wipe(db_session)
        service = OrderService(db_session)

        platform_fee, landscape_fee, total = service._compute_fees(subtotal)
        seller_amount = total - platform_fee - landscape_fee

        assert seller_amount == subtotal
        assert platform_fee + landscape_fee == total - subtotal

    async def test_a_zero_subtotal_costs_nothing(self, db_session):
        await _wipe(db_session)
        service = OrderService(db_session)

        platform_fee, landscape_fee, total = service._compute_fees(Decimal("0"))

        assert platform_fee == Decimal("0")
        assert landscape_fee == Decimal("0")
        assert total == Decimal("0")


# ---------------------------------------------------------------------------
# 2-4. the settlement split, its journal, and the take rate
# ---------------------------------------------------------------------------


class TestSettlementSplit:
    """One settled order: the split folds to the total and balances the books."""

    @given(plan=priced_plan())
    @PROPERTY
    async def test_the_seller_receives_the_subtotal_exactly(self, db_session, plan):
        await _wipe(db_session)
        order, _ = await _place_order(db_session, plan)
        service = OrderService(db_session)

        subtotal = Decimal(str(order.subtotal))
        total = Decimal(str(order.total))
        platform_fee = Decimal(str(order.platform_fee))
        landscape_fee = Decimal(str(order.landscape_fee))

        await service.confirm_payment(order.id)
        await service.process_order(order.id)
        await service.ship_order(order.id, _unique("TRK"), "prop")
        await service.mark_delivered(order.id)
        settlement = await service.settle_order(order.id)

        seller_amount = Decimal(str(settlement.amount))
        assert seller_amount == total - platform_fee - landscape_fee
        # Fees are added on top, so the seller gets exactly the subtotal.
        assert seller_amount == subtotal
        # The three settlement figures fold to what the buyer paid.
        assert (
            seller_amount
            + Decimal(str(settlement.commission_fee))
            + Decimal(str(settlement.landscape_fee))
            == total
        )
        assert Decimal(str(settlement.commission_fee)) == platform_fee
        assert Decimal(str(settlement.landscape_fee)) == landscape_fee
        assert Decimal(str(order.total)) == total

    @given(plan=priced_plan())
    @PROPERTY
    async def test_the_settlement_journal_balances_and_names_the_lines(
        self, db_session, plan
    ):
        await _wipe(db_session)
        order, _ = await _place_order(db_session, plan)
        service = OrderService(db_session)

        await service.confirm_payment(order.id)
        await service.process_order(order.id)
        await service.ship_order(order.id, _unique("TRK"), "prop")
        await service.mark_delivered(order.id)
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
        by_account: dict[str, Decimal] = {}
        for entry in entries:
            by_account.setdefault(entry.account_id, Decimal("0"))
            by_account[entry.account_id] += (
                Decimal(str(entry.amount))
                if entry.entry_type == "debit"
                else -Decimal(str(entry.amount))
            )

        total = Decimal(str(order.total))
        platform_fee = Decimal(str(order.platform_fee))
        landscape_fee = Decimal(str(order.landscape_fee))
        seller_amount = Decimal(str(settlement.amount))

        # Every reported account balances, and the three lines are the split.
        assert sum(by_account.values(), Decimal("0")) == 0
        assert by_account[ECO_CASH] == total
        assert by_account[ECO_SELLER_PAYABLE] == -seller_amount
        assert by_account[ECO_PLATFORM_REVENUE] == -(platform_fee + landscape_fee)
        # ``ECO_PLATFORM_REVENUE`` carries both fee lines, so the split folds.
        assert -by_account[ECO_PLATFORM_REVENUE] + seller_amount == total

        # And the whole ledger reports the batch balanced per asset.
        report = await LedgerService(db_session).trial_balance(asset=order.currency)
        row = next(
            r
            for r in report["totals"]
            if r["asset"] == order.currency
        )
        assert Decimal(row["debit"]) == Decimal(row["credit"])

    @given(plan=priced_plan())
    @PROPERTY
    async def test_the_take_rate_stays_inside_the_measured_band(
        self, db_session, plan
    ):
        await _wipe(db_session)
        order, _ = await _place_order(db_session, plan)
        service = OrderService(db_session)

        await service.confirm_payment(order.id)
        await service.process_order(order.id)
        await service.ship_order(order.id, _unique("TRK"), "prop")
        await service.mark_delivered(order.id)
        await service.settle_order(order.id)

        report = await service.settlement_revenue_report(order.id)
        subtotal = Decimal(str(order.subtotal))
        schedule = commerce_schedule()

        realised = int(report["realised_bps"])
        assert realised == realised_bps(subtotal, schedule)
        assert 0 <= realised <= MEASURED_BPS_CEILING, subtotal
        # The report quotes what the service charged, not a re-derivation.
        assert Decimal(report["charged_platform_fee"]) == Decimal(
            str(order.platform_fee)
        ).quantize(Decimal("0.01"))
        assert Decimal(report["charged_commission"]) == Decimal(
            str(order.platform_fee + order.landscape_fee)
        ).quantize(Decimal("0.01"))
        # The drift is the nominal minus the realised, rounded half up.
        assert Decimal(report["rounding_drift"]) == (
            Decimal(report["nominal_commission"])
            - Decimal(report["realised_commission"])
        )

    @given(plan=priced_plan())
    @PROPERTY
    async def test_the_landscape_fund_receives_exactly_the_landscape_fee(
        self, db_session, plan
    ):
        await _wipe(db_session)
        order, _ = await _place_order(db_session, plan)
        service = OrderService(db_session)

        await service.confirm_payment(order.id)
        await service.process_order(order.id)
        await service.ship_order(order.id, _unique("TRK"), "prop")
        await service.mark_delivered(order.id)
        await service.settle_order(order.id)

        credits = (
            (await db_session.execute(select(LandscapeFundCredit))).scalars().all()
        )
        funds = (await db_session.execute(select(LandscapeFund))).scalars().all()

        landscape_fee = Decimal(str(order.landscape_fee)).quantize(Decimal("0.01"))
        if plan["village"]:
            assert landscape_fee > 0
            assert len(credits) == 1
            assert len(funds) == 1
            # The credit is the fee that was actually charged and booked --
            # never a re-derivation from the rate.
            assert Decimal(str(credits[0].amount)) == landscape_fee
            assert Decimal(str(funds[0].total_collected)) == landscape_fee
            assert Decimal(str(funds[0].pending_balance)) == landscape_fee
            # One credit per settlement, naming where the money came from.
            assert credits[0].order_id == order.id
            assert credits[0].journal_batch_id is not None
        else:
            # No village to fund: the fee stays in platform revenue rather
            # than vanishing or being credited twice.
            assert credits == []
            assert funds == []


# ---------------------------------------------------------------------------
# 5. idempotency of an order-creation intent
# ---------------------------------------------------------------------------


class TestOrderIdempotency:
    """A replayed order-creation intent is not a second order."""

    @given(plan=priced_plan(), replays=st.integers(1, 4))
    @PROPERTY
    async def test_a_replayed_intent_reserves_the_stock_once(
        self, db_session, plan, replays
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(
            _unique("SKU"), _unique("item"), standard_cost=plan["received_cost"]
        )
        await stock.receipt(
            sku.id,
            warehouse.id,
            Decimal(plan["received_qty"]),
            unit_cost=plan["received_cost"],
            created_by="prop",
        )
        on_hand = Decimal(plan["received_qty"])

        service = OrderService(db_session)
        key = _unique("idem")
        # A replay is the *same* buyer submitting the same intent again; a
        # different buyer reusing the key is a cross-tenant collision that
        # ``create_order`` now refuses (see
        # ``test_the_same_idempotency_key_does_not_leak_between_buyers``).
        buyer = _unique("buyer")
        items = [
            {
                "sku_code": sku.sku_code,
                "quantity": Decimal(plan["qty"]),
                "unit_price": plan["unit_price"],
                "warehouse_id": warehouse.id,
            }
        ]

        created = [
            await service.create_order(
                buyer_id=buyer, items=items, idempotency_key=key
            )
            for _ in range(replays)
        ]

        # One order, one id, one order item row, one reservation per replay.
        assert len({order.id for order in created}) == 1
        rows = (
            (await db_session.execute(select(ComOrder))).scalars().all()
        )
        assert len(rows) == 1
        items_rows = (await db_session.execute(select(ComOrderItem))).scalars().all()
        assert len(items_rows) == 1
        reservations = (
            (
                await db_session.execute(
                    select(InvReservation).where(
                        InvReservation.reference_type == "order"
                    )
                )
            )
            .scalars()
            .all()
        )
        # One live reservation, however many times the client retried.
        assert len(reservations) == 1

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
        held = Decimal(plan["qty"])
        assert Decimal(str(balance.reserved)) == held
        assert Decimal(str(balance.on_hand)) == on_hand
        assert Decimal(str(balance.available)) == on_hand - held

    async def test_the_same_idempotency_key_does_not_leak_between_buyers(
        self, db_session
    ):
        """A key is scoped to its buyer; a cross-buyer reuse is rejected.

        ``OrderService._check_order_idempotency`` looks a key up within the
        caller's own buyer, and ``create_order`` refuses a key another buyer
        has taken rather than silently mapping the second buyer onto the
        first's order. The result is one order (the first buyer's), one hold
        (nothing double-held) and an explicit ``IDEMPOTENCY_KEY_CONFLICT`` for
        the second buyer — never a shared, paid-for order handed across
        tenants.
        """
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        await stock.receipt(
            sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1")
        )

        service = OrderService(db_session)
        key = _unique("shared-key")
        alice = _unique("alice")
        bob = _unique("bob")

        alice_order = await service.create_order(
            buyer_id=alice,
            items=[
                {
                    "sku_code": sku.sku_code,
                    "quantity": Decimal("1"),
                    "warehouse_id": warehouse.id,
                }
            ],
            idempotency_key=key,
        )
        alice_id = alice_order.id
        assert alice_order.buyer_id == alice

        # The second buyer, reusing the first's key, is refused outright.
        with pytest.raises(EcoNojinException) as raised:
            await service.create_order(
                buyer_id=bob,
                items=[
                    {
                        "sku_code": sku.sku_code,
                        "quantity": Decimal("1"),
                        "warehouse_id": warehouse.id,
                    }
                ],
                idempotency_key=key,
            )
        assert raised.value.code == "IDEMPOTENCY_KEY_CONFLICT"

        # One order exists, and it is the first buyer's — bob was not handed it.
        rows = (await db_session.execute(select(ComOrder))).scalars().all()
        assert len(rows) == 1
        assert rows[0].id == alice_id
        assert rows[0].buyer_id == alice

        # The stock is held once (alice's), not double-held.
        reservations = (
            (
                await db_session.execute(
                    select(InvReservation).where(
                        InvReservation.reference_type == "order"
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(reservations) == 1

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
        assert Decimal(str(balance.reserved)) == Decimal("1")
        assert Decimal(str(balance.on_hand)) == Decimal("100")


# ---------------------------------------------------------------------------
# 6. the reservation lifecycle through the order flow
# ---------------------------------------------------------------------------


class TestPennyOrders:
    """A subtotal small enough that both fee lines round to nothing.

    Such an order can be created, paid, shipped and delivered, and it must be
    settleable. ``settle_order`` builds a batch whose ``ECO_PLATFORM_REVENUE``
    leg is ``platform_fee + landscape_fee``; when both fees round to 0.00 that
    leg has amount ``0``, which ``LedgerService.create_journal_batch`` rightly
    refuses (``INVALID_AMOUNT`` — amounts must be positive). The fix is to
    omit zero legs rather than weaken that guard: a penny order settles with
    ``debit ECO_CASH / credit ECO_SELLER_PAYABLE`` — both legs positive and
    equal — and the zero fee leg is dropped as a no-op. The buyer's money and
    the seller's goods, both already committed at delivery, now reach a
    settlement row and a balanced, posted ledger batch.
    """

    @pytest.mark.parametrize("cents", [1, 2, 5, 9])
    async def test_a_penny_order_settles_with_a_balanced_batch(
        self, db_session, cents
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        await stock.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("1"))

        service = OrderService(db_session)
        order = await service.create_order(
            buyer_id=_unique("buyer"),
            items=[
                {
                    "sku_code": sku.sku_code,
                    "quantity": Decimal("1"),
                    "unit_price": Decimal(cents) / 100,
                    "warehouse_id": warehouse.id,
                }
            ],
            shipping_address={"city": "Karaj"},
        )

        subtotal = Decimal(str(order.subtotal))
        assert subtotal == Decimal(cents) / 100
        assert Decimal(str(order.platform_fee)) == Decimal("0.00")
        assert Decimal(str(order.landscape_fee)) == Decimal("0.00")
        assert Decimal(str(order.total)) == subtotal

        await service.confirm_payment(order.id)
        await service.process_order(order.id)
        await service.ship_order(order.id, _unique("TRK"), "prop")
        await service.mark_delivered(order.id)
        assert order.status == "delivered"

        # It settles now — no INVALID_AMOUNT, no stuck delivered order.
        settlement = await service.settle_order(order.id)
        assert order.status == "settled"

        # One settlement row, folding the whole total to the seller (fees 0.00).
        settlements = (
            (await db_session.execute(select(ComSettlement))).scalars().all()
        )
        assert len(settlements) == 1
        assert Decimal(str(settlement.amount)) == subtotal
        assert Decimal(str(settlement.commission_fee)) == Decimal("0.00")
        assert Decimal(str(settlement.landscape_fee)) == Decimal("0.00")

        # The zero fee leg is omitted; the two live legs are positive and
        # balance. ``ECO_CASH`` now carries the settlement's cash debit.
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
        by_account: dict[str, Decimal] = {}
        for entry in entries:
            signed = (
                Decimal(str(entry.amount))
                if entry.entry_type == "debit"
                else -Decimal(str(entry.amount))
            )
            by_account[entry.account_id] = (
                by_account.get(entry.account_id, Decimal("0")) + signed
            )
            assert Decimal(str(entry.amount)) > 0

        assert ECO_PLATFORM_REVENUE not in by_account
        assert by_account[ECO_CASH] == subtotal
        assert by_account[ECO_SELLER_PAYABLE] == -subtotal
        assert sum(by_account.values(), Decimal("0")) == 0

        # The posted batch leaves the ledger's trial balance even.
        report = await LedgerService(db_session).trial_balance(asset=order.currency)
        row = next(r for r in report["totals"] if r["asset"] == order.currency)
        assert Decimal(row["debit"]) == Decimal(row["credit"])


class TestOrderReservationLifecycle:
    """Creating holds, shipping consumes, cancelling releases."""

    @given(plan=priced_plan())
    @PROPERTY
    async def test_a_settled_order_conserves_stock_end_to_end(
        self, db_session, plan
    ):
        await _wipe(db_session)
        order, stock = await _place_order(db_session, plan)
        service = OrderService(db_session)

        received = Decimal(plan["received_qty"])
        ordered = Decimal(plan["qty"])

        after_create = await stock.get_balance(
            await _sku_id(db_session, order), await _warehouse_id(db_session, order)
        )
        assert Decimal(str(after_create.on_hand)) == received
        assert Decimal(str(after_create.reserved)) == ordered
        assert Decimal(str(after_create.available)) == received - ordered

        await service.confirm_payment(order.id)
        await service.process_order(order.id)
        await service.ship_order(order.id, _unique("TRK"), "prop")
        await service.mark_delivered(order.id)
        await service.settle_order(order.id)

        after = await stock.get_balance(
            await _sku_id(db_session, order), await _warehouse_id(db_session, order)
        )
        # The hold became a consumption: on hand and reserved both dropped.
        assert Decimal(str(after.on_hand)) == received - ordered
        assert Decimal(str(after.reserved)) == Decimal("0")
        assert Decimal(str(after.available)) == received - ordered
        assert Decimal(str(after.on_hand)) >= 0

    @given(plan=priced_plan())
    @PROPERTY
    async def test_cancelling_releases_the_hold(self, db_session, plan):
        await _wipe(db_session)
        order, stock = await _place_order(db_session, plan)

        received = Decimal(plan["received_qty"])
        sku_id = await _sku_id(db_session, order)
        warehouse_id = await _warehouse_id(db_session, order)

        service = OrderService(db_session)
        await service.cancel_order(order.id, reason="property test")

        after = await stock.get_balance(sku_id, warehouse_id)
        # Nothing was issued, so nothing left; the hold is back.
        assert Decimal(str(after.on_hand)) == received
        assert Decimal(str(after.reserved)) == Decimal("0")
        assert Decimal(str(after.available)) == received

        reservations = (
            (
                await db_session.execute(
                    select(InvReservation).where(
                        InvReservation.reference_type == "order"
                    )
                )
            )
            .scalars()
            .all()
        )
        assert all(row.status == "released" for row in reservations)
        # Whatever happened to the hold, quantity was conserved.
        assert Decimal(str(after.on_hand)) + Decimal(str(after.reserved)) == received

    @given(plan=priced_plan())
    @PROPERTY
    async def test_an_unpaid_order_still_holds_stock_and_cannot_ship(
        self, db_session, plan
    ):
        await _wipe(db_session)
        order, _ = await _place_order(db_session, plan)
        sku_id = await _sku_id(db_session, order)
        warehouse_id = await _warehouse_id(db_session, order)

        # An unpaid order still holds stock, and shipping it is refused.
        with pytest.raises(EcoNojinException) as raised:
            await OrderService(db_session).ship_order(
                order.id, _unique("TRK"), "prop"
            )
        # ``ship_order`` checks the status before the payment gate, and the
        # reserved state fails there. The payment gate itself
        # (``ORDER_NOT_PAID``) is reachable only through the placeholder
        # payment-intent path, which is what the note is about; what matters
        # here is that no shipment went out either way.
        assert raised.value.code in {"INVALID_SHIP_STATE", "ORDER_NOT_PAID"}

        stock = StockService(db_session)
        balance = await stock.get_balance(sku_id, warehouse_id)
        assert Decimal(str(balance.reserved)) == Decimal(plan["qty"])
        assert Decimal(str(balance.on_hand)) == Decimal(plan["received_qty"])
        assert Decimal(str(balance.on_hand)) >= Decimal(str(balance.reserved))
        assert Decimal(str(balance.available)) >= 0


async def _sku_id(db_session, order: ComOrder) -> int:
    item = (
        (
            await db_session.execute(
                select(ComOrderItem).where(ComOrderItem.order_id == order.id)
            )
        )
        .scalars()
        .one()
    )
    return int(item.sku_id)


async def _warehouse_id(db_session, order: ComOrder) -> int:
    item = (
        (
            await db_session.execute(
                select(ComOrderItem).where(ComOrderItem.order_id == order.id)
            )
        )
        .scalars()
        .one()
    )
    return int(item.warehouse_id)
