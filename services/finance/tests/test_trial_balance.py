"""Trial balance regressions using an isolated, in-memory database."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import FinJournalBatch, FinJournalEntry
from services.api_gateway.auth import get_current_user
from services.finance.ledger_service import LedgerService
from services.finance.routers.finance import get_db, router


@pytest.fixture
async def report_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        for table in (FinJournalBatch.__table__, FinJournalEntry.__table__):
            await conn.run_sync(table.create)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add_all(
            [
                FinJournalBatch(
                    id=1, batch_number="posted", batch_date=date(2026, 9, 1), is_posted=True
                ),
                FinJournalBatch(
                    id=2, batch_number="draft", batch_date=date(2026, 9, 1), is_posted=False
                ),
                FinJournalBatch(
                    id=3, batch_number="future", batch_date=date(2026, 10, 1), is_posted=True
                ),
            ]
        )
        for batch, asset, amount in [
            (1, "IRR", "10.1250"),
            (1, "USD", "2.5000"),
            (2, "IRR", "999"),
            (3, "IRR", "500"),
        ]:
            for account, kind in [("cash", "debit"), ("revenue", "credit")]:
                session.add(
                    FinJournalEntry(
                        batch_id=batch,
                        account_id=account,
                        entry_type=kind,
                        asset=asset,
                        amount=Decimal(amount),
                    )
                )
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_posted_balances_are_separate_by_asset_and_cutoff(report_db):
    report = await LedgerService(report_db).trial_balance(as_of=date(2026, 9, 30))
    assert len(report["rows"]) == 4
    assert report["totals"] == [
        {"asset": "IRR", "debit": "10.1250", "credit": "10.1250", "balanced": True},
        {"asset": "USD", "debit": "2.5000", "credit": "2.5000", "balanced": True},
    ]
    cash = next(
        row for row in report["rows"] if row["account_id"] == "cash" and row["asset"] == "IRR"
    )
    assert cash["debit_balance"] == "10.1250"
    assert cash["credit_balance"] == "0.0000"
    filtered = await LedgerService(report_db).trial_balance(asset="USD")
    assert len(filtered["rows"]) == 2


@pytest.mark.asyncio
async def test_imbalance_is_reported_not_hidden(report_db):
    report_db.add(
        FinJournalEntry(
            batch_id=1, account_id="cash", entry_type="debit", asset="USD", amount=Decimal("0.0100")
        )
    )
    await report_db.commit()
    report = await LedgerService(report_db).trial_balance(asset="USD")
    assert report["totals"] == [
        {"asset": "USD", "debit": "2.5100", "credit": "2.5000", "balanced": False},
    ]


@pytest.mark.asyncio
async def test_report_api_rejects_non_admin_and_validates_filters(report_db):
    app = FastAPI()
    app.include_router(router)

    async def database():
        yield report_db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="buyer", role="buyer")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        url = "/api/v1/finance/ledger/trial-balance"
        assert (await client.get(url)).status_code == 403
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="admin", role="admin"
        )
        response = await client.get(url, params={"asset": "USD", "as_of": "2026-09-30"})
        assert response.status_code == 200
        assert response.json()["totals"][0]["debit"] == "2.5000"
        assert (await client.get(url, params={"asset": "INVALID"})).status_code == 422
        assert (await client.get(url, params={"as_of": "invalid"})).status_code == 422
