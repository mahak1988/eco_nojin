"""Regression tests for the chart-of-accounts join.

``FinJournalEntry.account_id`` is a String column, and writers disagreed about
its contents: ``services/finance/wallet_service.py`` wrote ``FinAccount.id``
(an integer) while ``services/commerce/service.py`` wrote the account code.
``services/finance/reconciliation.py`` joined it against ``FinAccount.id``,
comparing a string to an integer primary key, so the join matched nothing and
every wallet reconciled against a ledger balance of zero.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import (
    EcoWallet,
    FinAccount,
    FinJournalBatch,
    FinJournalEntry,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.reconciliation import ReconciliationService


@pytest.fixture
async def ledger_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        for table in (
            EcoWallet.__table__,
            FinAccount.__table__,
            FinJournalBatch.__table__,
            FinJournalEntry.__table__,
        ):
            await conn.run_sync(table.create)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        liability = FinAccount(
            id=7, code="REWARD_LIABILITY", name="Rewards payable", type="liability", asset="ECO"
        )
        asset = FinAccount(id=8, code="ECO_ASSET", name="ECO pool", type="asset", asset="ECO")
        session.add_all([liability, asset])
        session.add(EcoWallet(user_id="user-1", balance=Decimal("100")))
        await session.commit()
        yield session, liability, asset
    await engine.dispose()


def _batch(session, created_by: str, number: str) -> FinJournalBatch:
    batch = FinJournalBatch(
        batch_number=number,
        batch_date=date(2026, 9, 1),
        is_posted=True,
        created_by=created_by,
        created_at=datetime.now(UTC),
    )
    session.add(batch)
    return batch


class TestReconciliationJoinsTheChartOfAccounts:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("use_code", [True, False], ids=["code", "legacy_integer_id"])
    async def test_ledger_balance_is_found_under_both_conventions(self, ledger_db, use_code: bool):
        """Regression: the join never matched, so the balance was always zero."""
        session, liability, asset = ledger_db
        batch = _batch(session, "user-1", "JB-CODE")
        await session.flush()

        account_ref = liability.code if use_code else str(liability.id)
        session.add(
            FinJournalEntry(
                batch_id=batch.id,
                account_id=account_ref,
                entry_type="credit",
                asset="ECO",
                amount=Decimal("100"),
            )
        )
        # A second, unrelated account must not be swept in.
        session.add(
            FinJournalEntry(
                batch_id=batch.id,
                account_id=asset.code if use_code else str(asset.id),
                entry_type="credit",
                asset="ECO",
                amount=Decimal("999"),
            )
        )
        await session.commit()

        svc = ReconciliationService(session)
        balance = await svc._get_ledger_balance("user-1", "ECO")
        assert balance == Decimal("100")

    @pytest.mark.asyncio
    async def test_wallet_reconciles_clean_against_its_ledger(self, ledger_db):
        session, liability, _asset = ledger_db
        batch = _batch(session, "user-1", "JB-CLEAN")
        await session.flush()
        session.add(
            FinJournalEntry(
                batch_id=batch.id,
                account_id=liability.code,
                entry_type="credit",
                asset="ECO",
                amount=Decimal("100"),
            )
        )
        await session.commit()

        report = await ReconciliationService(session).reconcile_wallet_ledger()
        assert report["total_wallets"] == 1
        assert report["discrepancies_count"] == 0
        assert report["overall_ok"] is True

    @pytest.mark.asyncio
    async def test_a_mismatched_balance_is_still_reported(self, ledger_db):
        """The fix must not turn reconciliation into a rubber stamp."""
        session, liability, _asset = ledger_db
        batch = _batch(session, "user-1", "JB-OFF")
        await session.flush()
        session.add(
            FinJournalEntry(
                batch_id=batch.id,
                account_id=liability.code,
                entry_type="credit",
                asset="ECO",
                amount=Decimal("40"),
            )
        )
        await session.commit()

        report = await ReconciliationService(session).reconcile_wallet_ledger()
        assert report["discrepancies_count"] == 1
        assert report["overall_ok"] is False
        assert report["discrepancies"][0]["user_id"] == "user-1"


class TestWalletWritesCanonicalCodes:
    @pytest.mark.asyncio
    async def test_earning_posts_account_codes_not_ids(self, ledger_db):
        from services.finance.ledger_service import LedgerService
        from services.finance.wallet_service import WalletService

        session, _liability, _asset = ledger_db

        from sqlalchemy import select

        rows = (
            (
                await session.execute(
                    select(FinJournalEntry).where(FinJournalEntry.batch_id.is_not(None))
                )
            )
            .scalars()
            .all()
        )
        assert rows == []

        # Drive the batch builder directly: it is the function that chooses the
        # account reference. The ledger it writes through is the canonical one —
        # wallet_service no longer defines its own (phase 4 group 3).
        wallet = WalletService(session)
        assert isinstance(wallet.ledger, LedgerService), (
            "the wallet must post through the validating canonical ledger, not a local copy"
        )
        await wallet._create_earning_batch("user-1", Decimal("5"), "soil_restoration")

        posted = (
            (await session.execute(select(FinJournalEntry).order_by(FinJournalEntry.entry_type)))
            .scalars()
            .all()
        )
        assert {row.account_id for row in posted} == {"ECO_ASSET", "REWARD_LIABILITY"}
        # Codes, not the decimal string of an integer id.
        assert all(not row.account_id.isdigit() for row in posted)

    @pytest.mark.asyncio
    async def test_the_wallet_refuses_an_unbalanced_batch(self, ledger_db):
        """The removed local ledger had no balance check, so an unbalanced
        journal was creatable straight through the wallet path."""
        from services.finance.ledger_service import LedgerService

        session, _liability, _asset = ledger_db
        ledger = LedgerService(session)

        with pytest.raises(EcoNojinException) as exc:
            await ledger.create_journal_batch(
                reference_type="eco_earning",
                reference_id="r1",
                entries=[
                    {
                        "account_id": "ECO_ASSET",
                        "entry_type": "debit",
                        "asset": "ECO",
                        "amount": "100.00",
                    },
                    {
                        "account_id": "REWARD_LIABILITY",
                        "entry_type": "credit",
                        "asset": "ECO",
                        "amount": "99.99",
                    },
                ],
                description="unbalanced on purpose",
                created_by="user-1",
            )
        assert "UNBALANCED_JOURNAL" in str(exc.value) or "not balanced" in str(exc.value).lower()
