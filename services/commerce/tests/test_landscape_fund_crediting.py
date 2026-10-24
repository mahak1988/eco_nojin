"""P1-8: the per-village restoration fund is fed by commerce settlements.

``OrderService.settle_order`` used to compute the 100 bps landscape fee and
book it, together with the 300 bps platform fee, to the single account
``ECO_PLATFORM_REVENUE`` — and nothing ever credited ``LandscapeFund``. The
fund was a model with no money in it. These tests pin the wiring:

* the credit is exactly the fee the settlement charged and booked;
* one ``LandscapeFundCredit`` audit row per settlement, carrying the order,
  the settlement and the journal batch;
* settlements accumulate on the per-village fund row;
* an order with no village behind it is skipped, not crashed on;
* the settlement batch stays posted and balanced with unchanged totals
  (the P0-1 regression this must not revert).
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from database.models import FinJournalBatch, FinJournalEntry
from services.landscape.models import LandscapeFund, LandscapeFundCredit

pytestmark = pytest.mark.asyncio

VILLAGE_ID = "village-p1-8"

# Money is compared by value, never by string form. ``ComOrder``'s fee columns
# are ``Numeric(18, 8)`` while the fund/credit columns and the report are
# ``Numeric(18, 2)``, so the same amount comes back as
# ``Decimal("0.02000000")`` from the order and ``Decimal("0.02")`` from the
# fund — equal as values, different as ``str()``. The scale a row is read back
# with also depends on whether it was re-read from the database or served from
# the session's identity map, which is what made the string form flaky in
# full-suite runs while it stayed green in isolation. ``Decimal.__eq__``
# compares values, so the expected literals below hold at either precision.


async def _deliver_order(order_service, order_id: str) -> None:
    await order_service.confirm_payment(order_id, payment_confirmed=True)
    await order_service.process_order(order_id)
    await order_service.ship_order(order_id, "TRACK-P1-8", "admin")
    await order_service.mark_delivered(order_id)


async def _order_with_village(
    order_service, sku, unit_price: Decimal, shipping_address
):
    """Create, deliver and settle one order; return (order, settlement)."""
    order = await order_service.create_order(
        buyer_id="p1-8-buyer",
        items=[
            {
                "sku_code": sku.sku_code,
                "quantity": 1,
                "unit_price": unit_price,
                "warehouse_id": 1,
            }
        ],
        shipping_address=shipping_address,
    )
    await _deliver_order(order_service, order.id)
    settlement = await order_service.settle_order(order.id)
    return order, settlement


class TestLandscapeFundCrediting:
    async def test_settlement_credits_the_village_fund_by_exactly_landscape_fee(
        self, order_service, sku, db_session
    ):
        order, settlement = await _order_with_village(
            order_service, sku, Decimal("100"), {"village_id": VILLAGE_ID, "city": "Kermanshah"}
        )

        credited = Decimal(str(order.landscape_fee))
        assert credited == Decimal("1.00")

        funds = (
            await db_session.execute(
                select(LandscapeFund).where(LandscapeFund.village_id == VILLAGE_ID)
            )
        ).scalars().all()
        assert len(funds) == 1
        fund = funds[0]
        # fee_bps follows the canonical schedule (100), one row per village.
        assert fund.fee_bps == 100
        assert fund.total_collected == credited
        assert fund.pending_balance == credited
        assert fund.total_distributed == Decimal("0.00")
        assert fund.is_active is True

        # One auditable credit per settlement, traceable to the posted batch.
        credits = (
            await db_session.execute(
                select(LandscapeFundCredit).where(LandscapeFundCredit.order_id == order.id)
            )
        ).scalars().all()
        assert len(credits) == 1
        credit = credits[0]
        assert credit.amount == credited
        assert credit.village_id == VILLAGE_ID
        assert credit.fund_id == fund.id
        assert credit.settlement_id == settlement.id
        assert credit.journal_batch_id == settlement.journal_batch_id
        assert credit.currency == order.currency

    async def test_two_settlements_accumulate_on_the_fund(self, order_service, sku, db_session):
        first, _ = await _order_with_village(
            order_service, sku, Decimal("100"), {"village_id": VILLAGE_ID}
        )
        second, _ = await _order_with_village(
            order_service, sku, Decimal("250"), {"village_id": VILLAGE_ID}
        )

        expected = Decimal(str(first.landscape_fee)) + Decimal(str(second.landscape_fee))
        assert expected == Decimal("3.50")  # 1.00 + 2.50

        fund = (
            await db_session.execute(
                select(LandscapeFund).where(LandscapeFund.village_id == VILLAGE_ID)
            )
        ).scalar_one()
        # Still a single fund row for the village, now holding both credits.
        assert fund.total_collected == expected
        assert fund.pending_balance == expected
        assert fund.total_distributed == Decimal("0.00")

        credits = (
            await db_session.execute(
                select(LandscapeFundCredit).where(
                    LandscapeFundCredit.village_id == VILLAGE_ID
                )
            )
        ).scalars().all()
        # Values, not string forms: the amounts are the two landscape fees
        # actually charged (1.00 on 100, 2.50 on 250).
        assert sorted(credit.amount for credit in credits) == [Decimal("1.00"), Decimal("2.50")]

    async def test_villages_are_funded_independently(self, order_service, sku, db_session):
        await _order_with_village(order_service, sku, Decimal("100"), {"village_id": "village-a"})
        await _order_with_village(order_service, sku, Decimal("100"), {"village_id": "village-b"})

        for village_id in ("village-a", "village-b"):
            fund = (
                await db_session.execute(
                    select(LandscapeFund).where(LandscapeFund.village_id == village_id)
                )
            ).scalar_one()
            assert fund.total_collected == Decimal("1.00")
            assert fund.pending_balance == Decimal("1.00")

    async def test_order_without_village_id_is_skipped_and_does_not_crash(
        self, order_service, sku, db_session
    ):
        order, settlement = await _order_with_village(order_service, sku, Decimal("100"), None)

        # Settlement itself is unaffected: still paid, still referencing its batch.
        assert settlement.status == "paid"
        assert settlement.landscape_fee == order.landscape_fee

        assert (
            await db_session.execute(select(LandscapeFundCredit))
        ).scalars().all() == []
        assert (await db_session.execute(select(LandscapeFund))).scalars().all() == []

    async def test_blank_or_non_mapping_address_is_skipped(self, order_service, sku, db_session):
        for address in ({"village_id": ""}, {"village_id": "   "}, {"city": "Tehran"}, "Tehran"):
            await _order_with_village(order_service, sku, Decimal("100"), address)

        assert (await db_session.execute(select(LandscapeFund))).scalars().all() == []
        assert (
            await db_session.execute(select(LandscapeFundCredit))
        ).scalars().all() == []

    async def test_settlement_in_a_non_fund_currency_is_skipped(
        self, order_service, sku, db_session
    ):
        order = await order_service.create_order(
            buyer_id="p1-8-buyer",
            items=[
                {
                    "sku_code": sku.sku_code,
                    "quantity": 1,
                    "unit_price": Decimal("100"),
                    "warehouse_id": 1,
                }
            ],
            shipping_address={"village_id": VILLAGE_ID},
        )
        order.currency = "ECO"
        await db_session.commit()
        await _deliver_order(order_service, order.id)
        settlement = await order_service.settle_order(order.id)

        assert settlement.landscape_fee == order.landscape_fee
        assert (await db_session.execute(select(LandscapeFund))).scalars().all() == []

    async def test_landscape_fee_that_quantises_to_zero_credits_nothing(
        self, order_service, sku, db_session
    ):
        # 0.50 * 100 bps = 0.005, a tie the service rounds to 0.00. The buyer
        # is charged no landscape fee, so there is nothing to fund — and the
        # divergence from realised_bps (which rounds the tie up) is reported,
        # not silently smoothed over.
        order, _ = await _order_with_village(
            order_service, sku, Decimal("0.50"), {"village_id": VILLAGE_ID}
        )
        assert Decimal(str(order.landscape_fee)) == Decimal("0.00")
        assert (await db_session.execute(select(LandscapeFund))).scalars().all() == []


class TestSettlementBatchUnchanged:
    """P0-1 regression: the settlement batch stays posted and balanced."""

    async def test_full_settle_keeps_posted_balanced_batch_with_same_totals(
        self, order_service, sku, db_session
    ):
        from services.finance.ledger_service import LedgerService

        order, settlement = await _order_with_village(
            order_service, sku, Decimal("100"), {"village_id": VILLAGE_ID}
        )

        batch = (
            await db_session.execute(
                select(FinJournalBatch).where(FinJournalBatch.id == settlement.journal_batch_id)
            )
        ).scalar_one()
        assert batch.is_posted is True
        assert batch.posted_at is not None
        assert batch.reference_type == "settlement"

        entries = (
            await db_session.execute(
                select(FinJournalEntry).where(FinJournalEntry.batch_id == batch.id)
            )
        ).scalars().all()
        debits = {e.account_id: e.amount for e in entries if e.entry_type == "debit"}
        credits = {e.account_id: e.amount for e in entries if e.entry_type == "credit"}
        assert debits == {"ECO_CASH": order.total}
        assert credits == {
            # Both fee lines still land on the platform revenue account; the
            # fund credit is a separate, auditable movement.
            "ECO_PLATFORM_REVENUE": order.platform_fee + order.landscape_fee,
            "ECO_SELLER_PAYABLE": order.total - order.platform_fee - order.landscape_fee,
        }
        assert sum(debits.values()) == sum(credits.values())

        report = await LedgerService(db_session).trial_balance()
        rows = [row for row in report["rows"] if row["asset"] == order.currency]
        assert {"ECO_PLATFORM_REVENUE", "ECO_SELLER_PAYABLE", "ECO_CASH"} <= {
            row["account_id"] for row in rows
        }
        totals = [total for total in report["totals"] if total["asset"] == order.currency]
        assert len(totals) == 1
        assert totals[0]["balanced"] is True

    async def test_reconciliation_still_agrees_with_the_settlement(
        self, order_service, sku, db_session
    ):
        from services.finance.reconciliation import ReconciliationService

        order, _ = await _order_with_village(
            order_service, sku, Decimal("100"), {"village_id": VILLAGE_ID}
        )
        report = await ReconciliationService(db_session).reconcile_orders_payments()
        settlement_flaws = [
            d
            for d in report["discrepancies"]
            if d.get("order_id") == order.id
            and d["type"]
            in (
                "settlement_amount_mismatch",
                "missing_settlement",
                "unposted_settlement_journal_batch",
            )
        ]
        assert settlement_flaws == []


class TestSettlementRevenueReport:
    """The reporting path for the module's realised-vs-nominal figures."""

    async def test_report_reads_the_schedule_from_revenue_indicators(
        self, order_service, sku, db_session
    ):
        order, _ = await _order_with_village(
            order_service, sku, Decimal("100"), {"village_id": VILLAGE_ID}
        )
        report = await order_service.settlement_revenue_report(order.id)

        assert report["order_id"] == order.id
        assert report["schedule_bps"] == {
            "platform": "300",
            "landscape": "100",
            "commission_bps": "400",
        }
        assert Decimal(report["charged_platform_fee"]) == Decimal(str(order.platform_fee))
        assert Decimal(report["charged_landscape_fee"]) == Decimal(str(order.landscape_fee))
        # Compared as values: the report quotes cents (2 decimals) while the
        # stored fee columns carry eight, so the two string forms differ.
        assert Decimal(report["charged_commission"]) == Decimal("4.00")
        assert Decimal(report["nominal_commission"]) == Decimal("4.00")
        assert Decimal(report["realised_commission"]) == Decimal("4.00")
        assert Decimal(report["nominal_bps"]) == Decimal("400")
        assert Decimal(report["realised_bps"]) == Decimal("400")
        assert Decimal(report["rounding_drift"]) == Decimal("0.00")

    async def test_report_shows_the_rounding_drift_without_changing_the_money(
        self, order_service, sku, db_session
    ):
        order, _ = await _order_with_village(
            order_service, sku, Decimal("0.50"), {"village_id": VILLAGE_ID}
        )
        report = await order_service.settlement_revenue_report(order.id)

        # The buyer was charged a 0.02 platform fee and a 0.00 landscape fee
        # (banker's rounding on the 0.005 tie), so the fund was credited
        # nothing. realised_bps rounds the same ties up: 0.02 platform plus
        # 0.01 landscape gives a realised 0.03 against a nominal 0.02. The
        # divergence is documented here rather than fixed by moving money.
        assert Decimal(report["charged_commission"]) == Decimal("0.02")
        assert Decimal(report["realised_commission"]) == Decimal("0.03")
        assert Decimal(report["nominal_bps"]) == Decimal("400")
        assert Decimal(report["realised_bps"]) == Decimal("600")
        assert Decimal(report["rounding_drift"]) == Decimal("-0.01")

    async def test_report_for_a_plain_100_order_matches_the_charged_fees(
        self, order_service, sku, db_session
    ):
        order, _ = await _order_with_village(
            order_service, sku, Decimal("100"), {"village_id": VILLAGE_ID}
        )
        report = await order_service.settlement_revenue_report(order.id)
        charged = Decimal(str(order.platform_fee)) + Decimal(str(order.landscape_fee))
        assert Decimal(str(report["nominal_commission"])) == charged
