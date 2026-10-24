"""Regression tests for the finance wallet router routes (P0-2).

``POST /api/v1/finance/wallet/earn`` and ``/wallet/redeem`` used to raise
``TypeError`` inside the route because the router forwarded
``idempotency_key`` to ``WalletService.earn/redeem``, which do not accept it —
a guaranteed HTTP 500. Idempotency is enforced by ``IdempotencyMiddleware``
via the ``Idempotency-Key`` header, not by the service. The request patterns
were also out of sync with ``earning_rates``: legacy names were admitted and
most canonical categories were unreachable.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import (
    DailyEarnings,
    EcoWallet,
    FinAccount,
    FinJournalBatch,
    FinJournalEntry,
)
from services.api_gateway.auth import get_current_user
from services.finance import earning_rates
from services.finance.routers.finance import get_db, router

pytestmark = pytest.mark.asyncio

_WALLET_TABLES = (
    FinAccount.__table__,
    FinJournalBatch.__table__,
    FinJournalEntry.__table__,
    EcoWallet.__table__,
    DailyEarnings.__table__,
)


@pytest.fixture
async def wallet_app():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        for table in _WALLET_TABLES:
            await conn.run_sync(table.create)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        app = FastAPI()
        app.include_router(router)

        async def database_override():
            yield session

        app.dependency_overrides[get_db] = database_override
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="wallet-user")
        yield app, session
    await engine.dispose()


async def _post(app, path, payload):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/finance{path}", json=payload)
    return response


async def test_wallet_earn_returns_200_not_500(wallet_app):
    app, _ = wallet_app
    response = await _post(
        app,
        "/wallet/earn",
        {"category": "tree_planting", "quantity": 1, "idempotency_key": "header-owned"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["category"] == "tree_planting"
    assert Decimal(body["amount_earned"]) == Decimal("50")
    assert Decimal(body["new_balance"]) == Decimal("50")


async def test_wallet_redeem_returns_200_not_500(wallet_app):
    app, _ = wallet_app
    earn = await _post(
        app,
        "/wallet/earn",
        {"category": "biodiversity", "quantity": 1, "idempotency_key": "header-owned"},
    )
    assert earn.status_code == 200, earn.text
    response = await _post(
        app, "/wallet/redeem", {"category": "consultation", "idempotency_key": "header-owned"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["category"] == "consultation"
    assert Decimal(body["amount_redeemed"]) == Decimal("20")
    assert Decimal(body["new_balance"]) == Decimal("20")


@pytest.mark.parametrize("category", sorted(earning_rates.EARNING_RATES))
async def test_every_canonical_earning_category_is_reachable(wallet_app, category):
    app, _ = wallet_app
    response = await _post(app, "/wallet/earn", {"category": category})
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("category", sorted(earning_rates.REDEMPTION_RATES))
async def test_every_canonical_redemption_category_is_reachable(wallet_app, category):
    app, _ = wallet_app
    earn = await _post(app, "/wallet/earn", {"category": "carbon_verification", "quantity": 2})
    assert earn.status_code == 200, earn.text
    response = await _post(app, "/wallet/redeem", {"category": category})
    assert response.status_code == 200, response.text
    assert response.json()["category"] == category


@pytest.mark.parametrize("alias", sorted(earning_rates.LEGACY_CATEGORY_ALIASES))
async def test_legacy_earning_alias_is_resolved_not_rejected(wallet_app, alias):
    app, session = wallet_app
    response = await _post(app, "/wallet/earn", {"category": alias})
    assert response.status_code == 200, response.text
    result = await session.execute(
        select(DailyEarnings).where(DailyEarnings.user_id == "wallet-user")
    )
    sources = {row.source for row in result.scalars().all()}
    assert sources == {earning_rates.resolve_category(alias)}


async def test_unknown_earning_category_returns_4xx(wallet_app):
    app, _ = wallet_app
    response = await _post(app, "/wallet/earn", {"category": "unknown_activity"})
    assert 400 <= response.status_code < 500


async def test_unknown_redemption_category_returns_4xx(wallet_app):
    app, _ = wallet_app
    response = await _post(app, "/wallet/redeem", {"category": "tree_planting"})
    assert 400 <= response.status_code < 500
