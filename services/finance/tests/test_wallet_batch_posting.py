"""Regression tests: wallet journal batches must be POSTED (P0-1).

``LedgerService.create_journal_batch`` leaves ``is_posted`` at its column
default (False) and ``post_journal_batch`` is reachable only through the admin
route, so batches written by ``WalletService`` used to stay invisible drafts:
``trial_balance`` and ``profit_and_loss`` filter on ``is_posted IS TRUE`` and
therefore never reported wallet movements.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from database.models import FinJournalBatch

pytestmark = pytest.mark.asyncio


class TestWalletBatchesArePosted:
    """earn/redeem/transfer batches must be posted and report-visible."""

    @staticmethod
    async def _batches(db_session, reference_type: str) -> list:
        result = await db_session.execute(
            select(FinJournalBatch).where(FinJournalBatch.reference_type == reference_type)
        )
        return result.scalars().all()

    async def test_earn_batch_appears_in_trial_balance(
        self, fresh_wallet_service, fresh_ledger_service, db_session
    ):
        await fresh_wallet_service.earn(
            user_id="posted-earn-user",
            category="tree_planting",
            quantity=Decimal("1"),
        )

        batches = await self._batches(db_session, "eco_earning")
        assert len(batches) == 1
        assert batches[0].is_posted is True
        assert batches[0].posted_at is not None

        report = await fresh_ledger_service.trial_balance()
        rows = [row for row in report["rows"] if row["asset"] == "ECO"]
        assert {row["account_id"] for row in rows} >= {"ECO_ASSET", "REWARD_LIABILITY"}
        eco_totals = [total for total in report["totals"] if total["asset"] == "ECO"]
        assert len(eco_totals) == 1
        assert eco_totals[0]["balanced"] is True
        assert Decimal(eco_totals[0]["debit"]) == Decimal("50")
        assert Decimal(eco_totals[0]["credit"]) == Decimal("50")

    async def test_redeem_batch_appears_in_trial_balance(
        self, fresh_wallet_service, fresh_ledger_service, db_session
    ):
        await fresh_wallet_service.earn(
            user_id="posted-redeem-user", category="community", quantity=Decimal("10")
        )
        await fresh_wallet_service.redeem(user_id="posted-redeem-user", category="consultation")

        earnings = await self._batches(db_session, "eco_earning")
        redemptions = await self._batches(db_session, "eco_redemption")
        assert len(earnings) == 1
        assert earnings[0].is_posted is True
        assert len(redemptions) == 1
        assert redemptions[0].is_posted is True

        report = await fresh_ledger_service.trial_balance()
        rows = [row for row in report["rows"] if row["asset"] == "ECO"]
        assert {row["account_id"] for row in rows} >= {"ECO_ASSET", "REWARD_LIABILITY"}
        eco_totals = [total for total in report["totals"] if total["asset"] == "ECO"]
        assert len(eco_totals) == 1
        assert eco_totals[0]["balanced"] is True

    async def test_transfer_batch_appears_in_trial_balance(
        self, fresh_wallet_service, fresh_ledger_service, db_session
    ):
        await fresh_wallet_service.earn(
            user_id="posted-transfer-from", category="community", quantity=Decimal("10")
        )
        transferred = await fresh_wallet_service.transfer(
            "posted-transfer-from", "posted-transfer-to", Decimal("10")
        )
        assert transferred is True

        transfers = await self._batches(db_session, "eco_transfer")
        assert len(transfers) == 1
        assert transfers[0].is_posted is True

        report = await fresh_ledger_service.trial_balance()
        rows = [row for row in report["rows"] if row["asset"] == "ECO"]
        account_ids = {row["account_id"] for row in rows}
        assert {"ECO_USER_posted-transfer-from", "ECO_USER_posted-transfer-to"} <= account_ids
