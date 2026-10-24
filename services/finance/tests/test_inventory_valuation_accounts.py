"""Chart-of-accounts + reporting regressions for the inventory legs (P2-15).

Before this wave nothing journalled against ``ECO_INVENTORY`` /
``ECO_COGS``, so ``LedgerService.trial_balance`` and ``profit_and_loss`` had
nothing to report for the inventory bounded context and a hypothetical batch
would have landed in ``unclassified`` with ``reason="account_not_found"``.

These tests pin the two halves of the fix:

* the four inventory accounts exist in the canonical chart after seeding (and
  seeding stays idempotent);
* the batches ``services/inventory/service.py`` posts are **posted** rows, so
  they show up in the trial balance and the P&L classifies them as expense —
  never unclassified. The accounting invariant is pinned too: the
  ``ECO_INVENTORY`` trial-balance balance equals the value the inventory
  service reports for the same stock.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select

from database.models import FinAccount, FinJournalBatch, FinJournalEntry
from services.finance.chart_of_accounts import (
    ECO_ACCOUNTS_PAYABLE,
    ECO_CASH,
    ECO_COGS,
    ECO_INVENTORY,
    ECO_INVENTORY_VARIANCE,
    INVENTORY_ACCOUNT_CODES,
    ensure_account,
    ensure_inventory_accounts,
    get_account_spec,
    seed_chart_of_accounts,
)
from services.finance.ledger_service import LedgerService

pytestmark = pytest.mark.asyncio

#: The four codes the inventory service journals against.
EXPECTED = {
    ECO_INVENTORY,
    ECO_ACCOUNTS_PAYABLE,
    ECO_COGS,
    ECO_INVENTORY_VARIANCE,
}


@pytest_asyncio.fixture
async def stock_service(db_session):
    """A StockService over one default warehouse.

    Declared here rather than reused from ``conftest.py`` because the shared
    ``stock_service`` fixture touches a wallet-only attribute the
    inventory service does not carry.
    """
    from services.inventory.service import StockService

    service = StockService(db_session)
    warehouse = await service.create_warehouse("DEFAULT", "Default Warehouse")
    service._default_wh = warehouse
    return service


async def _codes(db_session) -> set[str]:
    result = await db_session.execute(select(FinAccount.code))
    return set(result.scalars().all())


# ---------------------------------------------------------------------------
# (a) the chart carries the inventory accounts
# ---------------------------------------------------------------------------


class TestInventoryAccountsAreSeeded:
    async def test_new_accounts_exist_after_seeding(self, db_session):
        seeded = await seed_chart_of_accounts(db_session)
        await db_session.commit()

        assert EXPECTED <= await _codes(db_session)
        assert {account.code for account in seeded} >= EXPECTED

        accounts = {
            account.code: account
            for account in (
                await db_session.execute(select(FinAccount))
            ).scalars().all()
        }
        inventory = accounts[ECO_INVENTORY]
        assert inventory.type == "asset"
        assert inventory.is_active is True
        assert inventory.asset == "IRR"
        assert inventory.currency == "IRR"

        assert accounts[ECO_ACCOUNTS_PAYABLE].type == "liability"
        # A payable hangs under cash, like the seller payable it settles with.
        assert accounts[ECO_ACCOUNTS_PAYABLE].parent_id == str(accounts[ECO_CASH].id)

        assert accounts[ECO_COGS].type == "expense"
        assert accounts[ECO_INVENTORY_VARIANCE].type == "expense"

    async def test_seeding_the_inventory_accounts_is_idempotent(self, db_session):
        first = await ensure_inventory_accounts(db_session)
        await db_session.commit()
        first_ids = sorted(account.id for account in first)

        second = await ensure_inventory_accounts(db_session)
        await db_session.commit()

        assert sorted(account.id for account in second) == first_ids
        assert len(first_ids) == len(EXPECTED)
        assert INVENTORY_ACCOUNT_CODES == EXPECTED

    async def test_ensure_account_accepts_an_inventory_spec(self, db_session):
        spec = get_account_spec(ECO_INVENTORY)
        assert spec is not None

        account = await ensure_account(
            db_session,
            code=spec.code,
            name=spec.name,
            type=spec.type,
            asset=spec.asset,
            currency=spec.currency,
            parent_code=spec.parent_code,
            description=spec.description,
        )
        await db_session.commit()
        account.name = "Renamed by operator"
        await db_session.commit()

        # A re-seed returns the row unchanged, never rewriting an edited name.
        again = await ensure_account(
            db_session,
            code=spec.code,
            name=spec.name,
            type=spec.type,
            asset=spec.asset,
            currency=spec.currency,
        )
        assert again.id == account.id
        assert again.name == "Renamed by operator"


# ---------------------------------------------------------------------------
# (b) the inventory batches are report-visible
# ---------------------------------------------------------------------------


async def _stock_one_sku(stock_service, sku_code: str, cost: str, qty: str):
    """Receive goods for a brand-new SKU and return the warehouse id."""
    warehouse = stock_service._default_wh
    sku = await stock_service.create_sku(sku_code, sku_code)
    await stock_service.receipt(
        sku.id, warehouse.id, Decimal(qty), unit_cost=Decimal(cost)
    )
    return warehouse.id, sku.id


class TestInventoryBatchesAreReported:
    async def test_a_receipt_batch_reaches_the_trial_balance(
        self, stock_service, db_session
    ):
        await _stock_one_sku(stock_service, "TB-SKU", "100", "10")

        ledger = LedgerService(db_session)
        balance = await ledger.trial_balance(asset="IRR")
        by_account = {row["account_id"]: row for row in balance["rows"]}

        assert {ECO_INVENTORY, ECO_ACCOUNTS_PAYABLE} <= set(by_account)
        assert Decimal(by_account[ECO_INVENTORY]["debit_balance"]) == Decimal("1000.0000")
        assert Decimal(by_account[ECO_ACCOUNTS_PAYABLE]["credit_balance"]) == Decimal("1000.0000")

        totals = [total for total in balance["totals"] if total["asset"] == "IRR"]
        assert len(totals) == 1
        assert totals[0]["balanced"] is True
        assert Decimal(totals[0]["debit"]) == Decimal(totals[0]["credit"]) == Decimal("1000.0000")

    async def test_inventory_batches_are_never_unclassified(
        self, stock_service, db_session
    ):
        warehouse_id, sku_id = await _stock_one_sku(stock_service, "PNL-SKU", "40", "10")
        service = stock_service
        await service.issue(sku_id, warehouse_id, Decimal("4"))
        await service.adjust(sku_id, warehouse_id, Decimal("-1"), reason="damaged")
        await service.scrap(sku_id, warehouse_id, Decimal("1"), reason="rotten")

        report = await LedgerService(db_session).profit_and_loss(asset="IRR")

        account_codes = {row["account_code"] for row in report["expense"]}
        assert {ECO_COGS, ECO_INVENTORY_VARIANCE} <= account_codes
        # Nothing about inventory is hidden in the unclassified bucket.
        assert report["unclassified"] == []

        by_code = {row["account_code"]: row for row in report["expense"]}
        assert Decimal(by_code[ECO_COGS]["amount"]) == Decimal("160.0000")  # 4 @ 40
        # -1 adjustment and 1 scrap, both at the moving average of 40
        assert Decimal(by_code[ECO_INVENTORY_VARIANCE]["amount"]) == Decimal("80.0000")

    async def test_the_inventory_account_equals_the_valued_stock(
        self, stock_service, db_session
    ):
        """The accounting invariant: ledger balance == reported stock value."""
        service = stock_service
        source = service._default_wh
        destination = await service.create_warehouse("DEST", "Destination")
        sku = await service.create_sku("INVARIANT-SKU", "Invariant SKU")

        await service.receipt(sku.id, source.id, Decimal("10"), unit_cost=Decimal("100"))
        await service.receipt(sku.id, source.id, Decimal("10"), unit_cost=Decimal("200"))
        await service.issue(sku.id, source.id, Decimal("5"))
        await service.transfer(sku.id, source.id, destination.id, Decimal("10"))
        await service.receipt(sku.id, destination.id, Decimal("5"), unit_cost=Decimal("400"))
        await service.scrap(sku.id, destination.id, Decimal("2"), reason="damaged")
        await service.return_goods(sku.id, destination.id, Decimal("1"))

        valuation = await service.valuation_report()
        balance = await LedgerService(db_session).trial_balance(asset="IRR")
        by_account = {row["account_id"]: row for row in balance["rows"]}

        debit = Decimal(by_account[ECO_INVENTORY]["debit_balance"])
        credit = Decimal(by_account[ECO_INVENTORY]["credit_balance"])
        # Both are money: the trial balance reports 4 decimals, the valuation
        # 8, so compare on the coarser scale.
        assert (debit - credit).quantize(Decimal("0.0001")) == valuation[
            "total_value"
        ].quantize(Decimal("0.0001"))

        totals = [total for total in balance["totals"] if total["asset"] == "IRR"]
        assert totals[0]["balanced"] is True

    async def test_a_cash_receipt_credits_cash_in_the_trial_balance(
        self, stock_service, db_session
    ):
        warehouse = stock_service._default_wh
        sku = await stock_service.create_sku("CASH-SKU", "Cash SKU")
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("2"),
            unit_cost=Decimal("500"),
            payment_mode="cash",
        )

        balance = await LedgerService(db_session).trial_balance(asset="IRR")
        by_account = {row["account_id"]: row for row in balance["rows"]}
        assert ECO_ACCOUNTS_PAYABLE not in by_account
        assert Decimal(by_account[ECO_CASH]["credit_balance"]) == Decimal("1000.0000")

    async def test_batches_are_posted_and_reference_their_movement(
        self, stock_service, db_session
    ):
        warehouse = stock_service._default_wh
        sku = await stock_service.create_sku("REF-SKU", "Reference SKU")
        receipt = await stock_service.receipt(
            sku.id, warehouse.id, Decimal("3"), unit_cost=Decimal("30")
        )
        issue = await stock_service.issue(sku.id, warehouse.id, Decimal("1"))

        result = await db_session.execute(
            select(FinJournalBatch).order_by(FinJournalBatch.id)
        )
        batches = result.scalars().all()
        assert len(batches) == 2
        assert all(batch.is_posted is True for batch in batches)
        assert all(batch.posted_at is not None for batch in batches)
        assert {batch.reference_id for batch in batches} == {
            str(receipt.id),
            str(issue.id),
        }
        assert {batch.reference_type for batch in batches} == {
            "inventory_receipt",
            "inventory_cogs",
        }

        # Every entry carries a code, not a raw numeric id.
        entries = (
            await db_session.execute(select(FinJournalEntry).order_by(FinJournalEntry.id))
        ).scalars().all()
        assert all(entry.account_id.isupper() for entry in entries)
        assert all(entry.asset == "IRR" for entry in entries)
        assert all(Decimal(str(entry.amount)) > 0 for entry in entries)
