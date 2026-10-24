"""Profit & loss regressions using an isolated, in-memory database."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import FinAccount, FinJournalBatch, FinJournalEntry
from services.api_gateway.auth import get_current_user
from services.finance.ledger_service import LedgerService
from services.finance.routers.finance import get_db, router


@pytest.fixture
async def pnl_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        for table in (FinAccount.__table__, FinJournalBatch.__table__, FinJournalEntry.__table__):
            await conn.run_sync(table.create)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add_all(
            [
                FinAccount(
                    id=1, code="SALES_INCOME", name="Sales Income", type="income", asset="IRR"
                ),
                FinAccount(
                    id=2,
                    code="LOGISTICS_EXPENSE",
                    name="Logistics Expense",
                    type="expense",
                    asset="IRR",
                ),
                FinAccount(id=3, code="CASH", name="Cash", type="asset", asset="IRR"),
                FinJournalBatch(
                    id=1, batch_number="sep", batch_date=date(2026, 9, 10), is_posted=True
                ),
                FinJournalBatch(
                    id=2, batch_number="oct", batch_date=date(2026, 10, 10), is_posted=True
                ),
                FinJournalBatch(
                    id=3, batch_number="draft", batch_date=date(2026, 9, 11), is_posted=False
                ),
            ]
        )
        # September: 100 income, 40 expense, plus balance-sheet leg and an orphan account.
        session.add_all(
            [
                FinJournalEntry(
                    batch_id=1,
                    account_id="1",
                    entry_type="credit",
                    asset="IRR",
                    amount=Decimal("100"),
                ),
                FinJournalEntry(
                    batch_id=1,
                    account_id="2",
                    entry_type="debit",
                    asset="IRR",
                    amount=Decimal("40"),
                ),
                FinJournalEntry(
                    batch_id=1,
                    account_id="3",
                    entry_type="debit",
                    asset="IRR",
                    amount=Decimal("60"),
                ),
                FinJournalEntry(
                    batch_id=1,
                    account_id="GHOST",
                    entry_type="credit",
                    asset="IRR",
                    amount=Decimal("7"),
                ),
                # October: 25 income.
                FinJournalEntry(
                    batch_id=2,
                    account_id="1",
                    entry_type="credit",
                    asset="IRR",
                    amount=Decimal("25"),
                ),
                # Draft batch must never be reported.
                FinJournalEntry(
                    batch_id=3,
                    account_id="1",
                    entry_type="credit",
                    asset="IRR",
                    amount=Decimal("999"),
                ),
            ]
        )
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_pnl_classifies_accounts_and_respects_date_range(pnl_db):
    report = await LedgerService(pnl_db).profit_and_loss(
        from_date=date(2026, 9, 1), to_date=date(2026, 9, 30)
    )
    assert report["from_date"] == "2026-09-01"
    assert report["to_date"] == "2026-09-30"
    assert [row["account_id"] for row in report["income"]] == ["1"]
    assert report["income"][0]["account_name"] == "Sales Income"
    assert report["income"][0]["amount"] == "100.0000"
    assert [row["account_id"] for row in report["expense"]] == ["2"]
    assert report["expense"][0]["amount"] == "40.0000"
    assert report["totals"] == [
        {
            "asset": "IRR",
            "income": "100.0000",
            "expense": "40.0000",
            "net": "60.0000",
            "profitable": True,
        }
    ]


@pytest.mark.asyncio
async def test_pnl_excludes_balance_sheet_and_reports_unknown_accounts(pnl_db):
    report = await LedgerService(pnl_db).profit_and_loss()
    reported_ids = {row["account_id"] for row in report["income"]} | {
        row["account_id"] for row in report["expense"]
    }
    assert "3" not in reported_ids  # asset account is not a P&L line
    assert report["unclassified"] == [
        {
            "account_id": "GHOST",
            "account_code": None,
            "account_name": None,
            "asset": "IRR",
            "amount": "7.0000",
            "reason": "account_not_found",
        }
    ]
    assert (
        report["totals"][0]["net"] == "85.0000"
    )  # 125 income - 40 expense (GHOST is excluded, not guessed)


@pytest.mark.asyncio
async def test_pnl_reports_loss_and_filters_by_asset(pnl_db):
    pnl_db.add(
        FinJournalEntry(
            batch_id=1, account_id="2", entry_type="debit", asset="USD", amount=Decimal("15")
        )
    )
    await pnl_db.commit()
    usd = await LedgerService(pnl_db).profit_and_loss(asset="USD")
    assert usd["totals"] == [
        {
            "asset": "USD",
            "income": "0.0000",
            "expense": "15.0000",
            "net": "-15.0000",
            "profitable": False,
        }
    ]
    assert usd["income"] == []


@pytest.mark.asyncio
async def test_pnl_api_rejects_non_admin_and_validates_filters(pnl_db):
    app = FastAPI()
    app.include_router(router)

    async def database():
        yield pnl_db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="buyer", role="buyer")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        url = "/api/v1/finance/ledger/profit-and-loss"
        assert (await client.get(url)).status_code == 403
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="admin", role="admin"
        )
        response = await client.get(
            url, params={"from_date": "2026-09-01", "to_date": "2026-09-30", "asset": "IRR"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["totals"][0]["net"] == "60.0000"
        assert body["income"][0]["account_code"] == "SALES_INCOME"
        assert (await client.get(url, params={"asset": "INVALID"})).status_code == 422
        assert (await client.get(url, params={"from_date": "not-a-date"})).status_code == 422
