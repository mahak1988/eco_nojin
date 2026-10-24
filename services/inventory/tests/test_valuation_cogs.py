"""Tests for P2-15 — weighted-average stock valuation and COGS accounting.

Pins:

1. a goods receipt posts a balanced, **posted** batch
   (debit ``ECO_INVENTORY`` / credit ``ECO_ACCOUNTS_PAYABLE``, or ``ECO_CASH``
   when ``payment_mode`` says cash) at ``qty x unit_cost``;
2. an issue (including the commerce ship consumption) posts
   debit ``ECO_COGS`` / credit ``ECO_INVENTORY`` at the moving average;
3. a transfer preserves value — both legs priced at the source's average and no
   journal batch (the value never leaves ``ECO_INVENTORY``);
4. ``adjust`` / ``scrap`` / ``unblock`` / stocktake approval post against
   ``ECO_INVENTORY_VARIANCE``;
5. a customer return posts the reverse of the issue;
6. ``sku_valuation`` / ``valuation_report`` arithmetic over a multi-step moving
   average, across warehouses;
7. the documented failure rules: a zero-value movement books nothing, a journal
   failure discards the stock mutation with it, and a database without the
   finance tables still values its stock;
8. the existing movement and reservation semantics are unchanged.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import (
    FinJournalBatch,
    FinJournalEntry,
    InvInventoryBalance,
    InvSKU,
    InvStockMovement,
    InvStocktakeLine,
    InvWarehouse,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.chart_of_accounts import (
    ECO_ACCOUNTS_PAYABLE,
    ECO_CASH,
    ECO_COGS,
    ECO_INVENTORY,
    ECO_INVENTORY_VARIANCE,
)
from services.inventory.service import (
    JOURNAL_COGS,
    JOURNAL_RECEIPT,
    JOURNAL_RETURN,
    JOURNAL_VARIANCE,
    StockService,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


async def _batches(db_session, reference_type: str | None = None) -> list[FinJournalBatch]:
    stmt = select(FinJournalBatch)
    if reference_type is not None:
        stmt = stmt.where(FinJournalBatch.reference_type == reference_type)
    result = await db_session.execute(stmt.order_by(FinJournalBatch.id))
    return result.scalars().all()


async def _entries(db_session, batch_id: int) -> list[FinJournalEntry]:
    result = await db_session.execute(
        select(FinJournalEntry)
        .where(FinJournalEntry.batch_id == batch_id)
        .order_by(FinJournalEntry.id)
    )
    return result.scalars().all()


def _legs(entries: list[FinJournalEntry]) -> dict[str, dict[str, Decimal]]:
    """The batch's entries as ``{account_code: {"debit": x, "credit": y}}``."""
    legs: dict[str, dict[str, Decimal]] = {}
    for entry in entries:
        leg = legs.setdefault(entry.account_id, {"debit": Decimal("0"), "credit": Decimal("0")})
        leg[entry.entry_type] += Decimal(str(entry.amount))
    return legs


async def _second_warehouse(stock_service: StockService, code: str = "WH-2") -> InvWarehouse:
    return await stock_service.create_warehouse(code, f"Warehouse {code}")


# ---------------------------------------------------------------------------
# receipts
# ---------------------------------------------------------------------------


class TestReceiptAccounting:
    """A goods receipt is balanced, posted and priced."""

    async def test_receipt_posts_inventory_against_payable(
        self, db_session, sku, stock_service
    ):
        movement = await stock_service.receipt(
            sku.id,
            stock_service._default_wh.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            created_by="buyer",
        )

        assert Decimal(str(movement.unit_cost)) == Decimal("100")
        assert Decimal(str(movement.total_cost)) == Decimal("1000")

        batches = await _batches(db_session, JOURNAL_RECEIPT)
        assert len(batches) == 1
        batch = batches[0]
        assert batch.is_posted is True
        assert batch.posted_at is not None
        assert batch.created_by == "buyer"
        # The batch points back at the movement that caused it.
        assert batch.reference_id == str(movement.id)

        legs = _legs(await _entries(db_session, batch.id))
        assert legs == {
            ECO_INVENTORY: {"debit": Decimal("1000"), "credit": Decimal("0")},
            ECO_ACCOUNTS_PAYABLE: {"debit": Decimal("0"), "credit": Decimal("1000")},
        }
        debits = sum(leg["debit"] for leg in legs.values())
        credits = sum(leg["credit"] for leg in legs.values())
        assert debits == credits == Decimal("1000")

    async def test_cash_payment_mode_credits_cash_instead_of_payable(
        self, db_session, sku, stock_service
    ):
        movement = await stock_service.receipt(
            sku.id,
            stock_service._default_wh.id,
            Decimal("4"),
            unit_cost=Decimal("25"),
            payment_mode=" CASH ",
        )

        batch = (await _batches(db_session, JOURNAL_RECEIPT))[0]
        legs = _legs(await _entries(db_session, batch.id))
        assert ECO_ACCOUNTS_PAYABLE not in legs
        assert legs[ECO_INVENTORY]["debit"] == Decimal("100")
        assert legs[ECO_CASH]["credit"] == Decimal("100")
        assert Decimal(str(movement.total_cost)) == Decimal("100")

    @pytest.mark.parametrize("payment_mode", [None, "credit", "on_account", "cash_cheque"])
    async def test_every_other_payment_mode_is_on_account(
        self, db_session, sku, stock_service, payment_mode
    ):
        await stock_service.receipt(
            sku.id,
            stock_service._default_wh.id,
            Decimal("1"),
            unit_cost=Decimal("10"),
            payment_mode=payment_mode,
        )
        batch = (await _batches(db_session, JOURNAL_RECEIPT))[0]
        legs = _legs(await _entries(db_session, batch.id))
        assert set(legs) == {ECO_INVENTORY, ECO_ACCOUNTS_PAYABLE}

    async def test_receipt_without_unit_cost_falls_back_to_standard_cost(
        self, db_session, stock_service
    ):
        warehoused = await stock_service.create_sku("P215-FALLBACK", "Fallback SKU")
        priced = await stock_service.create_sku(
            "P215-STANDARD", "Standard-cost SKU", standard_cost=Decimal("7")
        )

        standard_movement = await stock_service.receipt(
            priced.id, stock_service._default_wh.id, Decimal("10")
        )
        zero_movement = await stock_service.receipt(
            warehoused.id, stock_service._default_wh.id, Decimal("10")
        )

        assert Decimal(str(standard_movement.unit_cost)) == Decimal("7")
        assert Decimal(str(zero_movement.unit_cost)) == Decimal("0")

        # The priced fallback books its value; the unpriced one books nothing.
        batches = await _batches(db_session, JOURNAL_RECEIPT)
        assert len(batches) == 1
        legs = _legs(await _entries(db_session, batches[0].id))
        assert legs[ECO_INVENTORY]["debit"] == Decimal("70")

    async def test_zero_value_movement_books_nothing(self, db_session, stock_service):
        unpriced = await stock_service.create_sku("P215-FREE", "Free SKU")
        await stock_service.receipt(unpriced.id, stock_service._default_wh.id, Decimal("5"))

        assert await _batches(db_session, JOURNAL_RECEIPT) == []
        movements = await stock_service.get_movements(sku_id=unpriced.id)
        assert len(movements) == 1
        assert Decimal(str(movements[0].unit_cost)) == Decimal("0")


# ---------------------------------------------------------------------------
# issues / COGS
# ---------------------------------------------------------------------------


class TestIssueAccounting:
    """An issue recognises COGS at the moving average."""

    async def test_issue_posts_cogs_at_moving_average(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("200"))

        movement = await stock_service.issue(sku.id, warehouse.id, Decimal("5"))

        assert Decimal(str(movement.unit_cost)) == Decimal("150")
        assert Decimal(str(movement.total_cost)) == Decimal("750")

        batches = await _batches(db_session, JOURNAL_COGS)
        assert len(batches) == 1
        batch = batches[0]
        assert batch.is_posted is True
        assert batch.reference_id == str(movement.id)
        legs = _legs(await _entries(db_session, batch.id))
        assert legs == {
            ECO_COGS: {"debit": Decimal("750"), "credit": Decimal("0")},
            ECO_INVENTORY: {"debit": Decimal("0"), "credit": Decimal("750")},
        }

    async def test_issue_all_stock_then_re_receipt_re_bases_the_average(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.issue(sku.id, warehouse.id, Decimal("10"))

        valuation = await stock_service.sku_valuation(sku.id, warehouse.id)
        assert valuation["on_hand"] == Decimal("0")
        assert valuation["total_value"] == Decimal("0")

        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("300"))
        valuation = await stock_service.sku_valuation(sku.id, warehouse.id)
        assert valuation["moving_average_cost"] == Decimal("300")
        assert valuation["total_value"] == Decimal("3000")


# ---------------------------------------------------------------------------
# transfers, adjustments, scraps, returns
# ---------------------------------------------------------------------------


class TestTransferValuation:
    """A transfer keeps the value inside ECO_INVENTORY."""

    async def test_transfer_prices_both_legs_at_the_source_average(
        self, db_session, sku, stock_service
    ):
        source = stock_service._default_wh
        destination = await _second_warehouse(stock_service)
        await stock_service.receipt(sku.id, source.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(sku.id, source.id, Decimal("10"), unit_cost=Decimal("200"))

        movement = await stock_service.transfer(sku.id, source.id, destination.id, Decimal("10"))

        assert Decimal(str(movement.unit_cost)) == Decimal("150")
        assert Decimal(str(movement.total_cost)) == Decimal("1500")

        # Value moves between warehouses, not in or out of inventory: the
        # transfer itself posts no batch (the two receipts are the only ones).
        assert len(await _batches(db_session)) == 2

        source_value = await stock_service.sku_valuation(sku.id, source.id)
        destination_value = await stock_service.sku_valuation(sku.id, destination.id)
        assert source_value["on_hand"] == Decimal("10")
        assert source_value["total_value"] == Decimal("1500")
        assert destination_value["on_hand"] == Decimal("10")
        assert destination_value["total_value"] == Decimal("1500")
        assert destination_value["moving_average_cost"] == Decimal("150")

    async def test_destination_pool_blends_a_transfer_with_its_own_receipts(
        self, db_session, sku, stock_service
    ):
        source = stock_service._default_wh
        destination = await _second_warehouse(stock_service)
        await stock_service.receipt(sku.id, source.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.transfer(sku.id, source.id, destination.id, Decimal("10"))
        await stock_service.receipt(
            sku.id, destination.id, Decimal("10"), unit_cost=Decimal("300")
        )

        valuation = await stock_service.sku_valuation(sku.id, destination.id)
        # (10 x 100 + 10 x 300) / 20
        assert valuation["moving_average_cost"] == Decimal("200")
        assert valuation["total_value"] == Decimal("4000")


class TestVarianceAccounting:
    """Adjustments, scraps, unblocks and stocktakes book the variance account."""

    async def test_negative_adjustment_writes_off_the_variance(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))

        movement = await stock_service.adjust(
            sku.id, warehouse.id, Decimal("-2"), reason="damaged", created_by="auditor"
        )

        assert Decimal(str(movement.unit_cost)) == Decimal("100")
        batch = (await _batches(db_session, JOURNAL_VARIANCE))[0]
        assert batch.created_by == "auditor"
        legs = _legs(await _entries(db_session, batch.id))
        assert legs == {
            ECO_INVENTORY_VARIANCE: {"debit": Decimal("200"), "credit": Decimal("0")},
            ECO_INVENTORY: {"debit": Decimal("0"), "credit": Decimal("200")},
        }

    async def test_positive_adjustment_debits_inventory(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))

        await stock_service.adjust(sku.id, warehouse.id, Decimal("2"), reason="found")

        batch = (await _batches(db_session, JOURNAL_VARIANCE))[0]
        legs = _legs(await _entries(db_session, batch.id))
        assert legs == {
            ECO_INVENTORY: {"debit": Decimal("200"), "credit": Decimal("0")},
            ECO_INVENTORY_VARIANCE: {"debit": Decimal("0"), "credit": Decimal("200")},
        }

    async def test_scrap_and_unblock_are_mirror_images(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("50"), unit_cost=Decimal("10"))

        await stock_service.scrap(sku.id, warehouse.id, Decimal("5"), reason="rotten")
        await stock_service.unblock_stock(sku.id, warehouse.id, Decimal("5"), reason="inspected")

        batches = await _batches(db_session, JOURNAL_VARIANCE)
        assert len(batches) == 2
        scrap_legs = _legs(await _entries(db_session, batches[0].id))
        unblock_legs = _legs(await _entries(db_session, batches[1].id))
        assert scrap_legs == {
            ECO_INVENTORY_VARIANCE: {"debit": Decimal("50"), "credit": Decimal("0")},
            ECO_INVENTORY: {"debit": Decimal("0"), "credit": Decimal("50")},
        }
        assert unblock_legs == {
            ECO_INVENTORY: {"debit": Decimal("50"), "credit": Decimal("0")},
            ECO_INVENTORY_VARIANCE: {"debit": Decimal("0"), "credit": Decimal("50")},
        }

        # The write-off was fully reversed, so the variance account nets to zero.
        variance_batches = await _batches(db_session, JOURNAL_VARIANCE)
        variance_entries = []
        for batch in variance_batches:
            variance_entries.extend(await _entries(db_session, batch.id))
        variance_net = sum(
            (
                Decimal(str(entry.amount))
                if entry.account_id == ECO_INVENTORY_VARIANCE and entry.entry_type == "debit"
                else Decimal("0")
            )
            - (
                Decimal(str(entry.amount))
                if entry.account_id == ECO_INVENTORY_VARIANCE and entry.entry_type == "credit"
                else Decimal("0")
            )
            for entry in variance_entries
        )
        assert variance_net == Decimal("0")

    async def test_return_posts_the_reverse_of_the_issue(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.issue(sku.id, warehouse.id, Decimal("4"))

        movement = await stock_service.return_goods(sku.id, warehouse.id, Decimal("4"))

        assert Decimal(str(movement.unit_cost)) == Decimal("100")
        batch = (await _batches(db_session, JOURNAL_RETURN))[0]
        legs = _legs(await _entries(db_session, batch.id))
        assert legs == {
            ECO_INVENTORY: {"debit": Decimal("400"), "credit": Decimal("0")},
            ECO_COGS: {"debit": Decimal("0"), "credit": Decimal("400")},
        }

        # The issue and its return net out on the COGS account.
        cogs_entries = (
            await db_session.execute(
                select(FinJournalEntry).where(FinJournalEntry.account_id == ECO_COGS)
            )
        ).scalars().all()
        cogs_net = sum(
            (
                Decimal(str(entry.amount))
                if entry.entry_type == "debit"
                else -Decimal(str(entry.amount))
            )
            for entry in cogs_entries
        )
        assert cogs_net == Decimal("0")


# ---------------------------------------------------------------------------
# stocktake
# ---------------------------------------------------------------------------


class TestStocktakeValuation:
    """A count is valued when taken and booked when approved."""

    async def test_count_records_variance_value(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("30"))

        stocktake = await stock_service.create_stocktake(
            warehouse_id=warehouse.id,
            created_by="counter",
            lines=[{"sku_id": sku.id, "counted_qty": Decimal("7")}],
        )

        lines = (
            await db_session.execute(
                select(InvStocktakeLine).where(InvStocktakeLine.stocktake_id == stocktake.id)
            )
        ).scalars().all()
        assert len(lines) == 1
        line = lines[0]
        assert line.variance_qty == Decimal("-3")
        assert Decimal(str(line.variance_value)) == Decimal("-90")

    async def test_approval_posts_the_variance(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("30"))

        stocktake = await stock_service.create_stocktake(
            warehouse_id=warehouse.id,
            created_by="counter",
            lines=[{"sku_id": sku.id, "counted_qty": Decimal("8")}],
        )
        await stock_service.approve_stocktake(stocktake.id, "manager")

        batch = (await _batches(db_session, JOURNAL_VARIANCE))[0]
        assert batch.is_posted is True
        assert batch.created_by == "manager"
        legs = _legs(await _entries(db_session, batch.id))
        assert legs == {
            ECO_INVENTORY_VARIANCE: {"debit": Decimal("60"), "credit": Decimal("0")},
            ECO_INVENTORY: {"debit": Decimal("0"), "credit": Decimal("60")},
        }

        lines = (
            await db_session.execute(
                select(InvStocktakeLine).where(InvStocktakeLine.stocktake_id == stocktake.id)
            )
        ).scalars().all()
        assert Decimal(str(lines[0].variance_value)) == Decimal("-60")

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("8")
        valuation = await stock_service.sku_valuation(sku.id, warehouse.id)
        assert valuation["total_value"] == Decimal("240")

    async def test_a_found_stocktake_surplus_debits_inventory(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("30"))

        stocktake = await stock_service.create_stocktake(
            warehouse_id=warehouse.id,
            created_by="counter",
            lines=[{"sku_id": sku.id, "counted_qty": Decimal("12")}],
        )
        await stock_service.approve_stocktake(stocktake.id, "manager")

        batch = (await _batches(db_session, JOURNAL_VARIANCE))[0]
        legs = _legs(await _entries(db_session, batch.id))
        assert legs[ECO_INVENTORY]["debit"] == Decimal("60")
        assert legs[ECO_INVENTORY_VARIANCE]["credit"] == Decimal("60")


# ---------------------------------------------------------------------------
# valuation read API
# ---------------------------------------------------------------------------


class TestValuationReadApi:
    """sku_valuation / valuation_report arithmetic."""

    async def test_multi_step_moving_average(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("200"))
        await stock_service.issue(sku.id, warehouse.id, Decimal("5"))
        await stock_service.receipt(sku.id, warehouse.id, Decimal("5"), unit_cost=Decimal("400"))
        await stock_service.issue(sku.id, warehouse.id, Decimal("5"))

        valuation = await stock_service.sku_valuation(sku.id, warehouse.id)
        # Step 1: 10 @100 -> avg 100, pool (10, 1000)
        # Step 2: +10 @200 -> pool (20, 3000), avg 150
        # Step 3: -5 @150 -> pool (15, 2250), avg 150
        # Step 4: +5 @400 -> pool (20, 4250), avg 212.50
        # Step 5: -5 @212.50 -> pool (15, 3187.50), avg 212.50
        assert valuation["on_hand"] == Decimal("15")
        assert valuation["moving_average_cost"] == Decimal("212.50000000")
        assert valuation["total_value"] == Decimal("3187.50000000")
        assert valuation["method"] == "weighted_avg"
        assert valuation["warehouses"] == [
            {
                "warehouse_id": warehouse.id,
                "on_hand": Decimal("15"),
                "moving_average_cost": Decimal("212.50000000"),
                "total_value": Decimal("3187.50000000"),
            }
        ]

    async def test_sku_valuation_spans_every_warehouse(self, db_session, sku, stock_service):
        source = stock_service._default_wh
        destination = await _second_warehouse(stock_service)
        await stock_service.receipt(sku.id, source.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(
            sku.id, destination.id, Decimal("10"), unit_cost=Decimal("300")
        )
        await stock_service.issue(sku.id, source.id, Decimal("5"))

        valuation = await stock_service.sku_valuation(sku.id)
        assert valuation["warehouse_id"] is None
        assert valuation["on_hand"] == Decimal("15")
        assert valuation["total_value"] == Decimal("3500")
        # (5 x 100 + 10 x 300) / 15
        assert valuation["moving_average_cost"] == Decimal("233.33333333")
        assert [row["warehouse_id"] for row in valuation["warehouses"]] == sorted(
            [source.id, destination.id]
        )

    async def test_unknown_sku_raises_not_found(self, db_session, stock_service):
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.sku_valuation(4242)
        assert exc_info.value.code == "SKU_NOT_FOUND"

    async def test_unimplemented_methods_are_rejected(self, db_session, sku, stock_service):
        for method in ("fifo", "standard"):
            with pytest.raises(EcoNojinException) as exc_info:
                await stock_service.sku_valuation(sku.id, method=method)
            assert exc_info.value.code == "UNSUPPORTED_VALUATION_METHOD"

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.sku_valuation(sku.id, method="magic")
        assert exc_info.value.code == "INVALID_VALUATION_METHOD"

    async def test_valuation_report_aggregates_skus_and_warehouses(
        self, db_session, sku, stock_service
    ):
        source = stock_service._default_wh
        destination = await _second_warehouse(stock_service)
        other = await stock_service.create_sku("P215-OTHER", "Other SKU")

        await stock_service.receipt(sku.id, source.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(sku.id, destination.id, Decimal("5"), unit_cost=Decimal("200"))
        await stock_service.receipt(other.id, source.id, Decimal("3"), unit_cost=Decimal("50"))

        report = await stock_service.valuation_report()
        assert report["method"] == "weighted_avg"
        assert report["total_value"] == Decimal("2150")

        by_sku = {row["sku_id"]: row for row in report["skus"]}
        assert Decimal(str(by_sku[sku.id]["total_value"])) == Decimal("2000")
        assert Decimal(str(by_sku[other.id]["total_value"])) == Decimal("150")
        assert by_sku[sku.id]["sku_code"] == "TEST-SKU"

        by_warehouse = {row["warehouse_id"]: row for row in report["warehouses"]}
        assert Decimal(str(by_warehouse[source.id]["total_value"])) == Decimal("1150")
        assert Decimal(str(by_warehouse[destination.id]["total_value"])) == Decimal("1000")

    async def test_report_sums_to_the_per_sku_valuations(
        self, db_session, sku, stock_service
    ):
        """The report is the sum of the per-SKU valuations, not a second model."""
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("7"), unit_cost=Decimal("13"))
        await stock_service.issue(sku.id, warehouse.id, Decimal("2"))
        await stock_service.adjust(sku.id, warehouse.id, Decimal("-1"), reason="shrink")

        per_sku = await stock_service.sku_valuation(sku.id, warehouse.id)
        report = await stock_service.valuation_report()
        assert report["total_value"] == per_sku["total_value"]


# ---------------------------------------------------------------------------
# failure semantics
# ---------------------------------------------------------------------------


class TestFailureSemantics:
    """The documented rules: book nothing on zero, roll back both on failure."""

    async def test_a_journal_failure_discards_the_movement_too(
        self, db_session, sku, stock_service, monkeypatch
    ):
        """The batch is posted before the mutator commits, so neither survives."""
        sku_id = sku.id

        async def _ledger_down(*_args, **_kwargs):
            raise EcoNojinException("ledger unavailable", code="LEDGER_DOWN")

        monkeypatch.setattr("services.inventory.service._post_journal", _ledger_down)

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.receipt(
                sku_id,
                stock_service._default_wh.id,
                Decimal("10"),
                unit_cost=Decimal("100"),
            )
        assert exc_info.value.code == "LEDGER_DOWN"

        # Nothing was persisted: no movement, no journal batch, and the on_hand
        # quantity is back to zero (``get_or_create_balance`` commits its own
        # savepoint, so a zero-quantity placeholder row may survive the
        # caller's rollback — the mutation itself never lands).
        await db_session.rollback()
        assert await stock_service.get_movements(sku_id=sku_id) == []
        assert await _batches(db_session) == []
        valuation = await stock_service.sku_valuation(sku_id)
        assert valuation["on_hand"] == Decimal("0")
        assert valuation["total_value"] == Decimal("0")

    async def test_a_rejected_mutation_books_nothing(self, db_session, sku, stock_service):
        """A rejected movement never reaches the posting path at all."""
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("5"), unit_cost=Decimal("10"))

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.scrap(sku.id, warehouse.id, Decimal("6"), reason="too much")
        assert exc_info.value.code == "INSUFFICIENT_STOCK"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("5")
        assert await _batches(db_session, JOURNAL_VARIANCE) == []

    @pytest.fixture
    async def inventory_only_session(self):
        """A database carrying the inventory tables but no finance ones."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            for table in (
                InvSKU.__table__,
                InvWarehouse.__table__,
                InvInventoryBalance.__table__,
                InvStockMovement.__table__,
            ):
                await conn.run_sync(table.create)
        session = async_sessionmaker(engine, expire_on_commit=False)()
        try:
            yield session
            await session.rollback()
        finally:
            await session.close()
            await engine.dispose()

    async def test_missing_finance_tables_do_not_break_valuation(
        self, inventory_only_session
    ):
        service = StockService(inventory_only_session)
        warehouse = await service.create_warehouse("PARTIAL", "Partial schema")
        sku = await service.create_sku("PARTIAL-SKU", "Partial SKU", standard_cost=Decimal("12"))

        movement = await service.receipt(sku.id, warehouse.id, Decimal("10"))
        assert Decimal(str(movement.unit_cost)) == Decimal("12")
        assert Decimal(str(movement.total_cost)) == Decimal("120")

        valuation = await service.sku_valuation(sku.id, warehouse.id)
        assert valuation["on_hand"] == Decimal("10")
        assert valuation["moving_average_cost"] == Decimal("12")
        assert valuation["total_value"] == Decimal("120")

        # The service now knows the ledger is unavailable and stays quiet.
        assert service._ledger_ready is False


# ---------------------------------------------------------------------------
# unchanged behaviour
# ---------------------------------------------------------------------------


class TestExistingFlowsAreUnchanged:
    """The commerce reserve/consume lifecycle keeps its semantics."""

    async def test_reserve_consume_release_round_trip(self, db_session, sku, stock_service):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("10")
        )
        reservation = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("50"), "order", "order-p215"
        )
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert (balance.on_hand, balance.reserved) == (Decimal("100"), Decimal("50"))

        await stock_service.consume_reservation(reservation.id, Decimal("20"))
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert (balance.on_hand, balance.reserved) == (Decimal("80"), Decimal("30"))

        await stock_service.release_reservation(reservation.id)
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert (balance.on_hand, balance.reserved) == (Decimal("80"), Decimal("0"))

        # Only the consumed 20 recognised COGS; the release moves no value.
        batches = await _batches(db_session, JOURNAL_COGS)
        assert len(batches) == 1
        legs = _legs(await _entries(db_session, batches[0].id))
        assert legs[ECO_COGS]["debit"] == Decimal("200")
        assert legs[ECO_INVENTORY]["credit"] == Decimal("200")
        assert len(await _batches(db_session)) == 2  # receipt + COGS only

        valuation = await stock_service.sku_valuation(sku.id, warehouse.id)
        assert valuation["on_hand"] == Decimal("80")
        assert valuation["total_value"] == Decimal("800")

    async def test_movement_quantities_are_untouched_by_valuation(
        self, db_session, sku, stock_service
    ):
        """Every mutator still writes exactly the quantities it used to."""
        warehouse = stock_service._default_wh
        destination = await _second_warehouse(stock_service)

        await stock_service.receipt(sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("10"))
        await stock_service.issue(sku.id, warehouse.id, Decimal("20"))
        await stock_service.transfer(sku.id, warehouse.id, destination.id, Decimal("30"))
        await stock_service.adjust(sku.id, warehouse.id, Decimal("-10"), reason="count")
        await stock_service.scrap(sku.id, warehouse.id, Decimal("5"), reason="waste")
        await stock_service.return_goods(sku.id, warehouse.id, Decimal("15"))
        await stock_service.unblock_stock(sku.id, warehouse.id, Decimal("5"))

        movements = await stock_service.get_movements(sku_id=sku.id, limit=50)
        by_type = {movement.movement_type: movement for movement in movements}
        assert Decimal(str(by_type["receipt"].qty)) == Decimal("100")
        assert Decimal(str(by_type["issue"].qty)) == Decimal("20")
        assert Decimal(str(by_type["transfer"].qty)) == Decimal("30")
        assert Decimal(str(by_type["adjustment"].qty)) == Decimal("10")
        assert Decimal(str(by_type["scrap"].qty)) == Decimal("5")
        assert Decimal(str(by_type["return"].qty)) == Decimal("15")
        assert Decimal(str(by_type["unblock"].qty)) == Decimal("5")

        # 100 - 20 - 30 - 10 - 5 + 15 + 5
        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("55")

    async def test_adjust_still_rejects_a_negative_on_hand(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("5"), unit_cost=Decimal("10"))
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.adjust(sku.id, warehouse.id, Decimal("-6"))
        assert exc_info.value.code == "NEGATIVE_ON_HAND"

        balance = await stock_service.get_balance(sku.id, warehouse.id)
        assert balance.on_hand == Decimal("5")
        assert await _batches(db_session, JOURNAL_VARIANCE) == []

    async def test_reconciliation_is_unaffected_by_journaling(
        self, db_session, sku, stock_service
    ):
        warehouse = stock_service._default_wh
        destination = await _second_warehouse(stock_service)
        await stock_service.receipt(sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("10"))
        await stock_service.transfer(sku.id, warehouse.id, destination.id, Decimal("40"))
        await stock_service.issue(sku.id, warehouse.id, Decimal("20"))

        result = await stock_service.reconcile_inventory()
        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0
