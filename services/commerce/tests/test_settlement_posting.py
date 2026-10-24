"""Regression tests: settlement journal batches must be POSTED (P0-1).

``OrderService.settle_order`` writes its settlement journal batch through
``LedgerService.create_journal_batch``, which leaves ``is_posted`` at its column
default (False). Because ``trial_balance`` and ``profit_and_loss`` filter on
``is_posted IS TRUE``, marketplace settlements used to stay invisible drafts and
both report endpoints came back empty.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from database.models import FinJournalBatch

pytestmark = pytest.mark.asyncio


async def _deliver_order(order_service, order_id: str) -> None:
    await order_service.confirm_payment(order_id, payment_confirmed=True)
    await order_service.process_order(order_id)
    await order_service.ship_order(order_id, "TRACK-P0-1", "admin")
    await order_service.mark_delivered(order_id)


class TestSettlementBatchIsPosted:
    async def test_settle_order_batch_appears_in_trial_balance(
        self, order_service, sku, db_session
    ):
        from services.finance.ledger_service import LedgerService

        order = await order_service.create_order(
            buyer_id="settled-buyer",
            items=[
                {
                    "sku_code": sku.sku_code,
                    "quantity": 1,
                    "unit_price": Decimal("100"),
                    "warehouse_id": 1,
                }
            ],
        )
        await _deliver_order(order_service, order.id)
        settlement = await order_service.settle_order(order.id)

        result = await db_session.execute(
            select(FinJournalBatch).where(FinJournalBatch.id == settlement.journal_batch_id)
        )
        batch = result.scalar_one()
        assert batch.is_posted is True
        assert batch.posted_at is not None

        report = await LedgerService(db_session).trial_balance()
        rows = [row for row in report["rows"] if row["asset"] == order.currency]
        assert {"ECO_PLATFORM_REVENUE", "ECO_SELLER_PAYABLE", "ECO_CASH"} <= {
            row["account_id"] for row in rows
        }
        totals = [total for total in report["totals"] if total["asset"] == order.currency]
        assert len(totals) == 1
        assert totals[0]["balanced"] is True
