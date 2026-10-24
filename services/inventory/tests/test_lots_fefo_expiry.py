"""Tests for P2-14 — lots/batches, FEFO expiry picking and the costing duality.

Pins:

1. a receipt carrying ``lot_number``/``expiry_date`` creates (or reuses) an
   :class:`~database.models.InvLot` and stamps ``lot_uuid`` on the balance row
   and the movement, with ``qty_received``/``qty_remaining``/``unit_cost`` on
   the lot; a receipt without them leaves ``lot_uuid`` NULL and behaves
   exactly as before;
2. an issue of lot-tracked stock is allocated **FEFO** — earliest expiry
   first, one leg per lot, each leg costed at *that lot's* ``unit_cost`` and
   carrying its ``lot_uuid``, with ``qty_remaining`` decremented;
3. an expired lot is refused with ``EXPIRED_LOT`` (lazily, without
   ``expire_due_lots`` ever running) and admitted only with
   ``allow_expired=True``;
4. ``expire_due_lots`` flips lots past their expiry and reports how many;
5. **the duality**: non-lot-tracked stock is still valued at the warehouse
   moving average — the P2-15 numbers unchanged — while lot-tracked stock in
   the same warehouse, even on the same SKU, is valued per lot;
6. reservations taken from lot-tracked stock record the FEFO lot and consume
   it at that lot's cost; transfers/adjustments/scraps propagate ``lot_uuid``;
7. the router surface: lot create/list/get/close, expire-due, a receipt with
   lot fields, the valuation read endpoints, 404 on an unknown lot and 422 on
   a malformed ``expiry_date``.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from database.base import Base
from database.models import (
    FinJournalBatch,
    FinJournalEntry,
    InvInventoryBalance,
    InvStockMovement,
)
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.exceptions import EcoNojinException
from services.inventory.routers.inventory import get_db
from services.inventory.routers.inventory import router as inventory_router
from services.inventory.service import JOURNAL_COGS, StockService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def other_sku(stock_service):
    """A second SKU, so lot scoping is provable."""
    return await stock_service.create_sku("LOT-OTHER-SKU", "Other SKU", standard_cost=Decimal("10"))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _in_days(days: int) -> date:
    """A date relative to today, so expiry tests never rot."""
    return date.today() + timedelta(days=days)


async def _lot_issues(stock_service: StockService, sku_id: int) -> list:
    """The lot-tracked issue legs written for one SKU, in ledger order.

    Ordered by id (not by ``get_movements``' newest-first ``created_at``),
    because FEFO writes its legs oldest-first and the order is the assertion.
    """
    result = await stock_service.db.execute(
        select(InvStockMovement)
        .where(
            InvStockMovement.sku_id == sku_id,
            InvStockMovement.movement_type == "issue",
            InvStockMovement.lot_uuid.is_not(None),
        )
        .order_by(InvStockMovement.id)
    )
    return list(result.scalars().all())


async def _balance_of(
    stock_service: StockService, sku_id: int, warehouse_id: int, location_id: int | None = None
):
    result = await stock_service.db.execute(
        select(InvInventoryBalance).where(
            InvInventoryBalance.sku_id == sku_id,
            InvInventoryBalance.warehouse_id == warehouse_id,
            InvInventoryBalance.location_id == (location_id or 0),
        )
    )
    return result.scalar_one_or_none()


async def _cogs_amounts(db_session) -> list[Decimal]:
    """Every posted COGS amount, sorted — the per-lot legs reach the ledger."""
    result = await db_session.execute(
        select(FinJournalEntry.amount)
        .join(FinJournalBatch, FinJournalEntry.batch_id == FinJournalBatch.id)
        .where(
            FinJournalBatch.reference_type == JOURNAL_COGS,
            FinJournalEntry.entry_type == "debit",
        )
    )
    return sorted(Decimal(str(row[0])) for row in result.all())


# ---------------------------------------------------------------------------
# lot entity
# ---------------------------------------------------------------------------


class TestLotEntity:
    """create_lot / get_lot / list_lots / close_lot / lot_valuation."""

    async def test_create_lot_starts_full_and_active(self, stock_service, sku):
        lot = await stock_service.create_lot(
            sku.id,
            "LOT-2026-001",
            expiry_date=_in_days(60),
            unit_cost=Decimal("12.5"),
            qty_received=Decimal("40"),
        )
        assert lot.id and len(lot.id) == 36
        assert lot.sku_id == str(sku.id)
        assert lot.lot_number == "LOT-2026-001"
        assert lot.status == "active"
        assert lot.expiry_date == _in_days(60)
        assert lot.unit_cost == Decimal("12.5")
        assert lot.qty_received == Decimal("40")
        assert lot.qty_remaining == Decimal("40")

    async def test_create_lot_defaults_to_zero_quantity(self, stock_service, sku):
        lot = await stock_service.create_lot(sku.id, "LOT-EMPTY")
        assert lot.qty_received == Decimal("0")
        assert lot.qty_remaining == Decimal("0")
        assert lot.expiry_date is None
        assert lot.status == "active"

    async def test_get_lot_unknown_is_404(self, stock_service):
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.get_lot("no-such-lot")
        assert exc_info.value.code == "LOT_NOT_FOUND"
        assert exc_info.value.status_code == 404

    async def test_create_lot_rejects_unknown_sku(self, stock_service):
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.create_lot(4242, "LOT-ORPHAN")
        assert exc_info.value.code == "SKU_NOT_FOUND"

    async def test_one_active_lot_number_per_sku(self, stock_service, sku):
        """A duplicate active label is refused, not forked into a second lot."""
        await stock_service.create_lot(sku.id, "LOT-DUP", qty_received=Decimal("5"))

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.create_lot(sku.id, "LOT-DUP", qty_received=Decimal("5"))
        assert exc_info.value.code == "LOT_EXISTS"
        assert exc_info.value.status_code == 409

        assert len(await stock_service.list_lots(sku_id=sku.id)) == 1

    async def test_a_closed_label_can_be_re_registered(self, stock_service, sku):
        """Closing a batch frees its number for the next one."""
        first = await stock_service.create_lot(sku.id, "LOT-REUSE", qty_received=Decimal("5"))
        await stock_service.close_lot(first.id, "quarantine")

        second = await stock_service.create_lot(sku.id, "LOT-REUSE", qty_received=Decimal("7"))
        assert second.id != first.id
        assert second.qty_remaining == Decimal("7")
        assert len(await stock_service.list_lots(sku_id=sku.id)) == 2

    async def test_a_repeat_receipt_never_forks_a_lot(self, db_session, stock_service, sku):
        """Two receipts with one label end as one row (no MultipleResultsFound)."""
        warehouse = stock_service._default_wh
        for _ in range(3):
            movement = await stock_service.receipt(
                sku.id, warehouse.id, Decimal("2"), unit_cost=Decimal("9"), lot_number="ONE"
            )
            assert movement.lot_uuid is not None

        lots = await stock_service.list_lots(sku_id=sku.id)
        assert len(lots) == 1
        assert lots[0].qty_received == Decimal("6")
        assert lots[0].qty_remaining == Decimal("6")

    async def test_invalid_expiry_date_is_refused(self, stock_service, sku):
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.create_lot(sku.id, "LOT-BAD-DATE", expiry_date="next tuesday")
        assert exc_info.value.code == "INVALID_EXPIRY_DATE"
        assert exc_info.value.status_code == 400

    async def test_list_lots_scopes_to_the_sku(self, stock_service, sku, other_sku):
        await stock_service.create_lot(sku.id, "LOT-A", qty_received=Decimal("1"))
        await stock_service.create_lot(sku.id, "LOT-B", qty_received=Decimal("1"))
        await stock_service.create_lot(other_sku.id, "LOT-C", qty_received=Decimal("1"))

        assert len(await stock_service.list_lots(sku_id=sku.id)) == 2
        assert len(await stock_service.list_lots(sku_id=other_sku.id)) == 1

    async def test_list_lots_filters_an_expiry_window(self, stock_service, sku):
        soon = await stock_service.create_lot(
            sku.id, "LOT-SOON", expiry_date=_in_days(5), qty_received=Decimal("1")
        )
        later = await stock_service.create_lot(
            sku.id, "LOT-LATER", expiry_date=_in_days(200), qty_received=Decimal("1")
        )
        undated = await stock_service.create_lot(sku.id, "LOT-NO-EXPIRY", qty_received=Decimal("1"))

        # A strictly-earlier window, so an expiry far in the future is excluded.
        expiring = await stock_service.list_lots(sku_id=sku.id, expiry_before=_in_days(30))
        assert [lot.id for lot in expiring] == [soon.id]

        everything = await stock_service.list_lots(sku_id=sku.id, expiry_before=_in_days(4000))
        assert [lot.id for lot in everything] == [soon.id, later.id]
        assert undated.id not in [lot.id for lot in everything]

    async def test_list_lots_filters_by_status(self, stock_service, sku):
        held = await stock_service.create_lot(sku.id, "LOT-HELD", qty_received=Decimal("3"))
        await stock_service.close_lot(held.id, "quarantine")
        free = await stock_service.create_lot(sku.id, "LOT-FREE", qty_received=Decimal("3"))

        active = await stock_service.list_lots(sku_id=sku.id, status="active")
        quarantined = await stock_service.list_lots(sku_id=sku.id, status="quarantine")
        assert [lot.id for lot in active] == [free.id]
        assert [lot.id for lot in quarantined] == [held.id]

    async def test_close_lot_quarantines_without_touching_quantity(self, stock_service, sku):
        lot = await stock_service.create_lot(
            sku.id, "LOT-HOLD", qty_received=Decimal("7"), unit_cost=Decimal("3")
        )
        closed = await stock_service.close_lot(lot.id, "quarantine")
        assert closed.status == "quarantine"
        assert closed.qty_remaining == Decimal("7")

        reopened = await stock_service.close_lot(lot.id, "active")
        assert reopened.status == "active"

    async def test_close_lot_rejects_an_unknown_status(self, stock_service, sku):
        lot = await stock_service.create_lot(sku.id, "LOT-BAD-STATUS", qty_received=Decimal("1"))
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.close_lot(lot.id, "shredded")
        assert exc_info.value.code == "INVALID_LOT_STATUS"

    async def test_close_lot_unknown_is_404(self, stock_service):
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.close_lot("no-such-lot")
        assert exc_info.value.code == "LOT_NOT_FOUND"

    async def test_lot_valuation_reports_remaining_value_per_status(
        self, stock_service, sku, other_sku
    ):
        await stock_service.create_lot(
            sku.id, "LOT-CHEAP", qty_received=Decimal("10"), unit_cost=Decimal("5")
        )
        await stock_service.create_lot(
            sku.id, "LOT-PRICEY", qty_received=Decimal("4"), unit_cost=Decimal("25")
        )
        held = await stock_service.create_lot(
            other_sku.id, "LOT-HELD", qty_received=Decimal("2"), unit_cost=Decimal("10")
        )
        await stock_service.close_lot(held.id, "quarantine")

        valuation = await stock_service.lot_valuation(sku.id)
        assert valuation["lots"] == 2
        assert valuation["qty_remaining"] == Decimal("14")
        # 10 x 5 + 4 x 25
        assert valuation["value"] == Decimal("150.00000000")
        assert [row["status"] for row in valuation["statuses"]] == ["active"]

        other = await stock_service.lot_valuation(other_sku.id)
        assert other["qty_remaining"] == Decimal("2")
        assert other["value"] == Decimal("20.00000000")
        assert [row["status"] for row in other["statuses"]] == ["quarantine"]


# ---------------------------------------------------------------------------
# receipt path
# ---------------------------------------------------------------------------


class TestReceiptWithLots:
    """A lot-tracked receipt stamps lot_uuid on the balance row and movement."""

    async def test_receipt_with_lot_writes_lot_uuid_and_lot_quantities(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        movement = await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("25"),
            unit_cost=Decimal("48"),
            lot_number="BATCH-A",
            expiry_date=_in_days(120),
            created_by="receiver",
        )

        lots = await stock_service.list_lots(sku_id=sku.id)
        assert len(lots) == 1
        lot = lots[0]
        assert lot.lot_number == "BATCH-A"
        assert lot.expiry_date == _in_days(120)
        assert lot.unit_cost == Decimal("48")
        assert lot.qty_received == Decimal("25")
        assert lot.qty_remaining == Decimal("25")

        balance = await _balance_of(stock_service, sku.id, warehouse.id)
        assert balance is not None
        assert balance.lot_uuid == lot.id
        assert balance.on_hand == Decimal("25")

        assert movement.lot_uuid == lot.id
        assert movement.lot_id is None  # the legacy sentinel column is untouched

    async def test_receipt_without_lot_leaves_lot_uuid_null(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        movement = await stock_service.receipt(
            sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("7")
        )

        assert await stock_service.list_lots(sku_id=sku.id) == []
        balance = await _balance_of(stock_service, sku.id, warehouse.id)
        assert balance.lot_uuid is None
        assert movement.lot_uuid is None

    async def test_repeat_receipt_tops_up_the_same_lot(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("30"),
            lot_number="BATCH-A",
            expiry_date=_in_days(60),
        )
        await stock_service.receipt(
            sku.id, warehouse.id, Decimal("5"), unit_cost=Decimal("35"), lot_number="BATCH-A"
        )

        lots = await stock_service.list_lots(sku_id=sku.id)
        assert len(lots) == 1
        lot = lots[0]
        assert lot.qty_received == Decimal("15")
        assert lot.qty_remaining == Decimal("15")
        assert lot.expiry_date == _in_days(60)  # the first receipt defined it
        assert lot.unit_cost == Decimal("35")  # the latest priced receipt wins

    async def test_a_lot_number_is_scoped_per_sku(self, db_session, stock_service, sku, other_sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id, warehouse.id, Decimal("4"), unit_cost=Decimal("10"), lot_number="SHARED-1"
        )
        await stock_service.receipt(
            other_sku.id, warehouse.id, Decimal("6"), unit_cost=Decimal("20"), lot_number="SHARED-1"
        )

        first = await stock_service.list_lots(sku_id=sku.id)
        second = await stock_service.list_lots(sku_id=other_sku.id)
        assert len(first) == 1
        assert len(second) == 1
        assert first[0].id != second[0].id

    async def test_a_non_lot_receipt_does_not_untrack_the_row(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("10"),
            lot_number="BATCH-A",
            expiry_date=_in_days(30),
        )
        await stock_service.receipt(sku.id, warehouse.id, Decimal("5"), unit_cost=Decimal("10"))

        balance = await _balance_of(stock_service, sku.id, warehouse.id)
        assert balance.lot_uuid is not None
        assert balance.on_hand == Decimal("15")


# ---------------------------------------------------------------------------
# FEFO issue
# ---------------------------------------------------------------------------


class TestFefoIssue:
    """Issue picks the earliest-expiry lot first and costs at its price."""

    async def test_issue_picks_the_earliest_expiry_lot_first(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            lot_number="LATE",
            expiry_date=_in_days(90),
        )
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("250"),
            lot_number="EARLY",
            expiry_date=_in_days(30),
        )
        early_lot = next(
            lot for lot in await stock_service.list_lots(sku_id=sku.id)
            if lot.lot_number == "EARLY"
        )

        movement = await stock_service.issue(
            sku.id, warehouse.id, Decimal("4"), created_by="picker"
        )

        assert movement.lot_uuid == early_lot.id
        assert Decimal(str(movement.unit_cost)) == Decimal("250")
        assert Decimal(str(movement.total_cost)) == Decimal("1000")

        refreshed = await stock_service.get_lot(early_lot.id)
        assert refreshed.qty_remaining == Decimal("6")
        assert refreshed.status == "active"

    async def test_issue_spans_lots_fefo_with_per_lot_costing(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            lot_number="FIRST",
            expiry_date=_in_days(10),
        )
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("200"),
            lot_number="SECOND",
            expiry_date=_in_days(80),
        )
        lots = {lot.lot_number: lot for lot in await stock_service.list_lots(sku_id=sku.id)}

        first_leg = await stock_service.issue(
            sku.id, warehouse.id, Decimal("15"), created_by="picker"
        )

        legs = await _lot_issues(stock_service, sku.id)
        assert len(legs) == 2
        # FEFO: the whole of the earliest lot, then the remainder of the next.
        assert legs[0].lot_uuid == lots["FIRST"].id
        assert Decimal(str(legs[0].qty)) == Decimal("10")
        assert Decimal(str(legs[0].unit_cost)) == Decimal("100")
        assert legs[1].lot_uuid == lots["SECOND"].id
        assert Decimal(str(legs[1].qty)) == Decimal("5")
        assert Decimal(str(legs[1].unit_cost)) == Decimal("200")
        assert first_leg.id == legs[0].id

        depleted = await stock_service.get_lot(lots["FIRST"].id)
        assert depleted.status == "depleted"
        assert depleted.qty_remaining == Decimal("0")
        assert (await stock_service.get_lot(lots["SECOND"].id)).qty_remaining == Decimal("5")

        balance = await _balance_of(stock_service, sku.id, warehouse.id)
        assert balance.on_hand == Decimal("5")

    async def test_an_undated_lot_is_picked_after_dated_ones(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"), lot_number="NO-EXPIRY"
        )
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("200"),
            lot_number="DATED",
            expiry_date=_in_days(365),
        )
        lots = {lot.lot_number: lot for lot in await stock_service.list_lots(sku_id=sku.id)}

        movement = await stock_service.issue(
            sku.id, warehouse.id, Decimal("3"), created_by="picker"
        )

        assert movement.lot_uuid == lots["DATED"].id
        assert Decimal(str(movement.unit_cost)) == Decimal("200")

    async def test_issue_of_an_expired_lot_is_refused(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("50"),
            lot_number="STALE",
            expiry_date=_in_days(-1),
        )

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.issue(sku.id, warehouse.id, Decimal("2"), created_by="picker")
        assert exc_info.value.code == "EXPIRED_LOT"
        assert exc_info.value.status_code == 400

        # Nothing moved: no issue leg, no COGS, the lot keeps its quantity.
        assert await _lot_issues(stock_service, sku.id) == []
        balance = await _balance_of(stock_service, sku.id, warehouse.id)
        assert balance.on_hand == Decimal("10")
        assert (await stock_service.list_lots(sku_id=sku.id))[0].qty_remaining == Decimal("10")

    async def test_allow_expired_overrides_the_refusal(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("50"),
            lot_number="STALE",
            expiry_date=_in_days(-1),
        )
        stale_lot = next(
            lot for lot in await stock_service.list_lots(sku_id=sku.id)
            if lot.lot_number == "STALE"
        )

        movement = await stock_service.issue(
            sku.id, warehouse.id, Decimal("2"), created_by="picker", allow_expired=True
        )

        assert movement.lot_uuid == stale_lot.id
        assert Decimal(str(movement.unit_cost)) == Decimal("50")
        assert (await stock_service.get_lot(stale_lot.id)).qty_remaining == Decimal("8")

    async def test_expiry_is_enforced_lazily_without_a_scheduled_sweep(
        self, db_session, stock_service, sku
    ):
        """The FEFO path refuses an expired lot nobody ever swept."""
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("50"),
            lot_number="STALE",
            expiry_date=_in_days(-1),
        )
        lot = (await stock_service.list_lots(sku_id=sku.id))[0]
        assert lot.status == "active"  # expire_due_lots never ran

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.issue(sku.id, warehouse.id, Decimal("1"))

        assert exc_info.value.code == "EXPIRED_LOT"
        # The lazy check records the truth in the same transaction.
        assert (await stock_service.get_lot(lot.id)).status == "expired"

    async def test_a_quarantined_lot_is_never_picked(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("50"),
            lot_number="HELD",
            expiry_date=_in_days(5),
        )
        lot = (await stock_service.list_lots(sku_id=sku.id))[0]
        await stock_service.close_lot(lot.id, "quarantine")

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.issue(sku.id, warehouse.id, Decimal("1"))
        assert exc_info.value.code == "INSUFFICIENT_STOCK"

    async def test_fefo_posts_one_cogs_batch_per_lot_leg(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            lot_number="FIRST",
            expiry_date=_in_days(10),
        )
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("200"),
            lot_number="SECOND",
            expiry_date=_in_days(80),
        )

        await stock_service.issue(sku.id, warehouse.id, Decimal("15"), created_by="picker")

        # 10 x 100 and 5 x 200: the per-lot costing reaches the ledger.
        assert await _cogs_amounts(db_session) == [
            Decimal("1000.00000000"),
            Decimal("1000.00000000"),
        ]


# ---------------------------------------------------------------------------
# expiry sweep
# ---------------------------------------------------------------------------


class TestExpireDueLots:
    """expire_due_lots flips lots past their expiry and reports how many."""

    async def test_expire_due_flips_only_the_due_active_lots(
        self, db_session, stock_service, sku
    ):
        fresh = await stock_service.create_lot(
            sku.id, "LOT-FRESH", expiry_date=_in_days(30), qty_received=Decimal("5")
        )
        stale = await stock_service.create_lot(
            sku.id, "LOT-STALE", expiry_date=_in_days(-1), qty_received=Decimal("5")
        )
        held = await stock_service.create_lot(
            sku.id, "LOT-HELD-STALE", expiry_date=_in_days(-10), qty_received=Decimal("5")
        )
        await stock_service.close_lot(held.id, "quarantine")

        # Only the due *active* lot flips: a manual quarantine hold is a
        # decision, and the sweeper must not override it.
        assert await stock_service.expire_due_lots() == 1
        assert (await stock_service.get_lot(stale.id)).status == "expired"
        assert (await stock_service.get_lot(held.id)).status == "quarantine"
        assert (await stock_service.get_lot(fresh.id)).status == "active"

    async def test_expire_due_reports_zero_when_nothing_is_due(
        self, db_session, stock_service, sku
    ):
        await stock_service.create_lot(
            sku.id, "LOT-FRESH", expiry_date=_in_days(30), qty_received=Decimal("5")
        )
        assert await stock_service.expire_due_lots() == 0

    async def test_expire_due_leaves_undated_lots_alone(self, db_session, stock_service, sku):
        lot = await stock_service.create_lot(sku.id, "LOT-NO-EXPIRY", qty_received=Decimal("5"))
        assert await stock_service.expire_due_lots() == 0
        assert (await stock_service.get_lot(lot.id)).status == "active"


# ---------------------------------------------------------------------------
# the costing duality
# ---------------------------------------------------------------------------


class TestCostingDuality:
    """Lot-tracked stock costs per lot; everything else stays moving-average."""

    async def test_non_lot_stock_keeps_the_moving_average_numbers(
        self, db_session, stock_service, sku
    ):
        """The P2-15 arithmetic, verbatim: 10@100 + 10@200, issue 5 -> 150."""
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("200"))

        movement = await stock_service.issue(sku.id, warehouse.id, Decimal("5"))

        assert movement.lot_uuid is None
        assert Decimal(str(movement.unit_cost)) == Decimal("150")
        assert Decimal(str(movement.total_cost)) == Decimal("750")

    async def test_both_policies_coexist_on_one_sku_in_one_warehouse(
        self, db_session, stock_service, sku
    ):
        """A lot-tracked location and a plain location under one SKU.

        The warehouse moving average still prices the plain leg (10@100 +
        10@200 = 150) while the lot-tracked leg is priced at its own lot's
        100 — neither policy rewrites the other.
        """
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            location_id=1,
            lot_number="BATCH-A",
            expiry_date=_in_days(30),
        )
        lots = {lot.lot_number: lot for lot in await stock_service.list_lots(sku_id=sku.id)}
        await stock_service.receipt(
            sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("200"), location_id=2
        )

        lot_issue = await stock_service.issue(
            sku.id, warehouse.id, Decimal("2"), location_id=1, created_by="picker"
        )
        plain_issue = await stock_service.issue(
            sku.id, warehouse.id, Decimal("2"), location_id=2, created_by="picker"
        )

        assert lot_issue.lot_uuid == lots["BATCH-A"].id
        assert Decimal(str(lot_issue.unit_cost)) == Decimal("100")

        assert plain_issue.lot_uuid is None
        assert Decimal(str(plain_issue.unit_cost)) == Decimal("150")

    async def test_both_policies_coexist_on_different_skus(self, db_session, stock_service, sku):
        tracked = await stock_service.create_sku("DUAL-TRACKED", "Tracked SKU")
        plain = await stock_service.create_sku("DUAL-PLAIN", "Plain SKU")
        warehouse = stock_service._default_wh

        await stock_service.receipt(
            tracked.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            lot_number="BATCH-A",
            expiry_date=_in_days(30),
        )
        await stock_service.receipt(plain.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(plain.id, warehouse.id, Decimal("10"), unit_cost=Decimal("200"))

        plain_issue = await stock_service.issue(plain.id, warehouse.id, Decimal("5"))
        assert Decimal(str(plain_issue.unit_cost)) == Decimal("150")
        assert plain_issue.lot_uuid is None

        tracked_issue = await stock_service.issue(tracked.id, warehouse.id, Decimal("5"))
        assert Decimal(str(tracked_issue.unit_cost)) == Decimal("100")
        assert tracked_issue.lot_uuid is not None

        # The valuation read API is untouched: still weighted averages.
        report = await stock_service.valuation_report()
        assert report["method"] == "weighted_avg"
        by_sku = {row["sku_id"]: row for row in report["skus"]}
        assert by_sku[plain.id]["total_value"] == Decimal("2250.00000000")
        assert by_sku[tracked.id]["total_value"] == Decimal("500.00000000")

    async def test_a_depleted_lot_leaves_the_later_one_pickable(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("5"),
            unit_cost=Decimal("100"),
            lot_number="FIRST",
            expiry_date=_in_days(10),
        )
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("20"),
            unit_cost=Decimal("200"),
            lot_number="SECOND",
            expiry_date=_in_days(80),
        )
        lots = {lot.lot_number: lot for lot in await stock_service.list_lots(sku_id=sku.id)}

        await stock_service.issue(sku.id, warehouse.id, Decimal("5"))
        movement = await stock_service.issue(sku.id, warehouse.id, Decimal("5"))

        assert movement.lot_uuid == lots["SECOND"].id
        assert Decimal(str(movement.unit_cost)) == Decimal("200")
        assert (await stock_service.get_lot(lots["FIRST"].id)).status == "depleted"


# ---------------------------------------------------------------------------
# reservations
# ---------------------------------------------------------------------------


class TestLotTrackedReservations:
    """A reservation on lot-tracked stock records and consumes its lot."""

    async def test_reserve_records_the_fefo_lot(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            lot_number="LATE",
            expiry_date=_in_days(80),
        )
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("300"),
            lot_number="EARLY",
            expiry_date=_in_days(20),
        )
        lots = {lot.lot_number: lot for lot in await stock_service.list_lots(sku_id=sku.id)}

        reservation = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("6"), "order", "order-lots-1", created_by="buyer"
        )

        assert reservation.lot_uuid == lots["EARLY"].id
        assert reservation.status == "active"
        # Reserving holds stock; it does not consume the lot.
        assert (await stock_service.get_lot(lots["EARLY"].id)).qty_remaining == Decimal("10")

    async def test_consume_costs_at_the_lot_and_decrements_it(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("300"),
            lot_number="EARLY",
            expiry_date=_in_days(20),
        )
        lot = (await stock_service.list_lots(sku_id=sku.id))[0]

        reservation = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("6"), "order", "order-lots-2", created_by="buyer"
        )
        movement = await stock_service.consume_reservation(reservation.id)

        assert movement.lot_uuid == lot.id
        assert Decimal(str(movement.unit_cost)) == Decimal("300")
        assert Decimal(str(movement.total_cost)) == Decimal("1800")
        assert (await stock_service.get_lot(lot.id)).qty_remaining == Decimal("4")

    async def test_consume_refuses_an_expired_lot_unless_allowed(
        self, db_session, stock_service, sku
    ):
        """The lot was fine at reserve time and expired before consumption."""
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("300"),
            lot_number="WILL-STALE",
            expiry_date=_in_days(20),
        )
        lot = (await stock_service.list_lots(sku_id=sku.id))[0]

        reservation = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("6"), "order", "order-lots-3", created_by="buyer"
        )
        lot.expiry_date = _in_days(-1)
        await stock_service.db.commit()

        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.consume_reservation(reservation.id)
        assert exc_info.value.code == "EXPIRED_LOT"

        # The refusal left the reservation untouched, so the override can run.
        movement = await stock_service.consume_reservation(reservation.id, allow_expired=True)
        assert movement.lot_uuid == lot.id
        assert Decimal(str(movement.unit_cost)) == Decimal("300")
        assert (await stock_service.get_lot(lot.id)).qty_remaining == Decimal("4")

    async def test_a_non_lot_reservation_keeps_the_moving_average(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await stock_service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("200"))

        reservation = await stock_service.reserve_stock(
            sku.id, warehouse.id, Decimal("5"), "order", "order-plain-1", created_by="buyer"
        )
        assert reservation.lot_uuid is None

        movement = await stock_service.consume_reservation(reservation.id)
        assert movement.lot_uuid is None
        assert Decimal(str(movement.unit_cost)) == Decimal("150")


# ---------------------------------------------------------------------------
# transfer / adjust / scrap propagation
# ---------------------------------------------------------------------------


class TestLotPropagation:
    """Transfer/adjust/scrap carry the lot_uuid the row already has."""

    async def test_transfer_propagates_the_lot_to_both_legs(
        self, db_session, stock_service, sku
    ):
        source = stock_service._default_wh
        destination = await stock_service.create_warehouse("WH-LOT-2", "Second Warehouse")
        await stock_service.receipt(
            sku.id,
            source.id,
            Decimal("10"),
            unit_cost=Decimal("100"),
            lot_number="BATCH-A",
            expiry_date=_in_days(30),
        )
        lot = (await stock_service.list_lots(sku_id=sku.id))[0]

        movement = await stock_service.transfer(
            sku.id, source.id, destination.id, Decimal("4"), created_by="mover"
        )

        assert movement.lot_uuid == lot.id
        destination_balance = await _balance_of(stock_service, sku.id, destination.id)
        assert destination_balance.lot_uuid == lot.id
        source_balance = await _balance_of(stock_service, sku.id, source.id)
        assert source_balance.on_hand == Decimal("6")
        # A transfer moves the batch; the lot still holds every unit.
        assert (await stock_service.get_lot(lot.id)).qty_remaining == Decimal("10")

    async def test_adjust_and_scrap_carry_the_lot_uuid(self, db_session, stock_service, sku):
        warehouse = stock_service._default_wh
        await stock_service.receipt(
            sku.id,
            warehouse.id,
            Decimal("20"),
            unit_cost=Decimal("100"),
            lot_number="BATCH-A",
            expiry_date=_in_days(30),
        )
        lot = (await stock_service.list_lots(sku_id=sku.id))[0]

        adjustment = await stock_service.adjust(
            sku.id, warehouse.id, Decimal("-2"), reason="shrink", created_by="auditor"
        )
        scrap = await stock_service.scrap(
            sku.id, warehouse.id, Decimal("3"), reason="damaged", created_by="auditor"
        )

        assert adjustment.lot_uuid == lot.id
        assert scrap.lot_uuid == lot.id
        # Neither path splits the lot: its quantity is untouched by both.
        assert (await stock_service.get_lot(lot.id)).qty_remaining == Decimal("20")

    async def test_adjust_and_scrap_on_plain_stock_stay_lot_free(
        self, db_session, stock_service, sku
    ):
        warehouse = stock_service._default_wh
        await stock_service.receipt(sku.id, warehouse.id, Decimal("20"), unit_cost=Decimal("100"))

        adjustment = await stock_service.adjust(sku.id, warehouse.id, Decimal("-2"))
        scrap = await stock_service.scrap(sku.id, warehouse.id, Decimal("3"))

        assert adjustment.lot_uuid is None
        assert scrap.lot_uuid is None


# ---------------------------------------------------------------------------
# router
# ---------------------------------------------------------------------------


@pytest.fixture
async def lot_app():
    """A minimal app mounting the inventory router over a full in-memory schema."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        app = FastAPI()
        app.include_router(inventory_router)

        async def database_override():
            yield session

        app.dependency_overrides[get_db] = database_override
        app.dependency_overrides[require_user] = lambda: {"id": "lot-user"}
        app.dependency_overrides[require_admin] = lambda: {"id": "lot-admin"}

        service = StockService(session)
        warehouse = await service.create_warehouse("WH-LOTS", "Lot Warehouse")
        seeded = await service.create_sku(
            "LOT-SKU", "Lot SKU", uom="kg", standard_cost=Decimal("10")
        )
        await session.commit()

        yield app, session, service, warehouse, seeded
    await engine.dispose()


async def _request(app, method: str, path: str, payload: dict | None = None):
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        return await client.request(method, path, json=payload)


class TestLotRouter:
    """POST/GET /lots, close, expire-due, lot receipts and valuation reads."""

    async def test_create_get_list_and_close_a_lot(self, lot_app):
        app, _session, service, _warehouse, sku = lot_app

        created = await _request(
            app,
            "POST",
            "/api/v1/inventory/lots",
            {
                "sku_code": sku.sku_code,
                "lot_number": "BATCH-RT",
                "expiry_date": _in_days(45).isoformat(),
                "unit_cost": "12.50",
                "qty_received": "20",
                "supplier_ref": "SUP-1",
            },
        )
        assert created.status_code == 200, created.text
        lot_id = created.json()["id"]
        assert created.json()["lot_number"] == "BATCH-RT"
        assert created.json()["status"] == "active"
        assert Decimal(created.json()["qty_remaining"]) == Decimal("20")
        assert Decimal(created.json()["qty_received"]) == Decimal("20")
        assert Decimal(created.json()["unit_cost"]) == Decimal("12.50")
        assert created.json()["expiry_date"] == _in_days(45).isoformat()

        fetched = await _request(app, "GET", f"/api/v1/inventory/lots/{lot_id}")
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["id"] == lot_id

        listed = await _request(
            app, "GET", f"/api/v1/inventory/lots?sku_code={sku.sku_code}&status=active"
        )
        assert listed.status_code == 200, listed.text
        assert [row["id"] for row in listed.json()] == [lot_id]

        other = await service.create_sku("LOT-SKU-2", "Other SKU")
        await _request(
            app,
            "POST",
            "/api/v1/inventory/lots",
            {"sku_code": other.sku_code, "lot_number": "BATCH-RT-2"},
        )
        scoped = await _request(app, "GET", f"/api/v1/inventory/lots?sku_code={other.sku_code}")
        assert [row["id"] for row in scoped.json()] == [
            lot.id for lot in await service.list_lots(sku_id=other.id)
        ]

        window = await _request(
            app, "GET", f"/api/v1/inventory/lots?expiry_before={_in_days(60).isoformat()}"
        )
        assert [row["id"] for row in window.json()] == [lot_id]

        closed = await _request(
            app, "POST", f"/api/v1/inventory/lots/{lot_id}/close", {"status": "quarantine"}
        )
        assert closed.status_code == 200, closed.text
        assert closed.json()["status"] == "quarantine"
        assert Decimal(closed.json()["qty_remaining"]) == Decimal("20")

    async def test_unknown_lot_is_404(self, lot_app):
        app, _session, _service, _warehouse, _sku = lot_app
        response = await _request(app, "GET", "/api/v1/inventory/lots/does-not-exist")
        assert response.status_code == 404

    async def test_closing_an_unknown_lot_is_404(self, lot_app):
        app, _session, _service, _warehouse, _sku = lot_app
        response = await _request(
            app, "POST", "/api/v1/inventory/lots/does-not-exist/close", {"status": "quarantine"}
        )
        assert response.status_code == 404

    async def test_malformed_expiry_date_is_422(self, lot_app):
        app, _session, _service, _warehouse, sku = lot_app
        response = await _request(
            app,
            "POST",
            "/api/v1/inventory/lots",
            {"sku_code": sku.sku_code, "lot_number": "BATCH-BAD", "expiry_date": "31-31-2026"},
        )
        assert response.status_code == 422, response.text

    async def test_a_blank_lot_number_is_rejected(self, lot_app):
        app, _session, _service, _warehouse, sku = lot_app
        response = await _request(
            app,
            "POST",
            "/api/v1/inventory/lots",
            {"sku_code": sku.sku_code, "lot_number": "   "},
        )
        assert response.status_code == 400, response.text

    async def test_a_duplicate_active_lot_number_is_409(self, lot_app):
        app, _session, service, _warehouse, sku = lot_app
        await service.create_lot(sku.id, "BATCH-TAKEN", qty_received=Decimal("1"))

        response = await _request(
            app,
            "POST",
            "/api/v1/inventory/lots",
            {"sku_code": sku.sku_code, "lot_number": "BATCH-TAKEN"},
        )
        assert response.status_code == 409, response.text

    async def test_expire_due_reports_how_many(self, lot_app):
        app, _session, service, _warehouse, sku = lot_app
        await service.create_lot(
            sku.id, "LOT-DUE", expiry_date=_in_days(-1), qty_received=Decimal("2")
        )
        await service.create_lot(
            sku.id, "LOT-FUTURE", expiry_date=_in_days(90), qty_received=Decimal("2")
        )

        response = await _request(app, "POST", "/api/v1/inventory/lots/expire-due")
        assert response.status_code == 200, response.text
        assert response.json()["expired"] == 1

    async def test_receipt_accepts_lot_fields_and_stamps_the_lot(self, lot_app):
        app, _session, service, warehouse, sku = lot_app

        receipt = await _request(
            app,
            "POST",
            "/api/v1/inventory/movements/receipt",
            {
                "sku_code": sku.sku_code,
                "warehouse_id": warehouse.id,
                "qty": "15",
                "unit_cost": "60",
                "lot_number": "BATCH-HTTP",
                "expiry_date": _in_days(30).isoformat(),
            },
        )
        assert receipt.status_code == 200, receipt.text

        lots = await service.list_lots(sku_id=sku.id)
        assert len(lots) == 1
        assert lots[0].lot_number == "BATCH-HTTP"
        assert lots[0].qty_remaining == Decimal("15")

        balance = await _balance_of(service, sku.id, warehouse.id)
        assert balance.lot_uuid == lots[0].id

    async def test_a_malformed_receipt_expiry_date_is_422(self, lot_app):
        app, _session, _service, warehouse, sku = lot_app
        response = await _request(
            app,
            "POST",
            "/api/v1/inventory/movements/receipt",
            {
                "sku_code": sku.sku_code,
                "warehouse_id": warehouse.id,
                "qty": "5",
                "lot_number": "BATCH-BAD",
                "expiry_date": "whenever",
            },
        )
        assert response.status_code == 422, response.text

    async def test_receipt_without_lot_fields_behaves_as_before(self, lot_app):
        app, _session, service, warehouse, sku = lot_app

        receipt = await _request(
            app,
            "POST",
            "/api/v1/inventory/movements/receipt",
            {"sku_code": sku.sku_code, "warehouse_id": warehouse.id, "qty": "9"},
        )
        assert receipt.status_code == 200, receipt.text
        assert await service.list_lots(sku_id=sku.id) == []

    async def test_valuation_endpoints_are_wired(self, lot_app):
        app, _session, service, warehouse, sku = lot_app
        await service.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("100"))
        await service.receipt(
            sku.id,
            warehouse.id,
            Decimal("10"),
            unit_cost=Decimal("300"),
            lot_number="BATCH-VAL",
            expiry_date=_in_days(30),
        )

        per_sku = await _request(app, "GET", f"/api/v1/inventory/valuation/{sku.sku_code}")
        assert per_sku.status_code == 200, per_sku.text
        body = per_sku.json()
        assert body["sku_id"] == sku.id
        assert body["method"] == "weighted_avg"
        assert Decimal(body["moving_average_cost"]) == Decimal("200")
        assert Decimal(body["total_value"]) == Decimal("4000")
        assert Decimal(body["warehouses"][0]["total_value"]) == Decimal("4000")

        report = await _request(app, "GET", "/api/v1/inventory/valuation/report")
        assert report.status_code == 200, report.text
        assert report.json()["method"] == "weighted_avg"
        assert Decimal(report.json()["total_value"]) == Decimal("4000")

    async def test_valuation_of_an_unknown_sku_is_404(self, lot_app):
        app, _session, _service, _warehouse, _sku = lot_app
        response = await _request(app, "GET", "/api/v1/inventory/valuation/NO-SUCH-SKU")
        assert response.status_code == 404
