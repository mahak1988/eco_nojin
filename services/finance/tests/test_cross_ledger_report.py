"""P5 — the cross-ledger report is honest under the shared key (D-10)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from database.models import EcoBalanceAccount, EcoBalanceEntry, EcoWallet, User
from services.finance.cross_ledger_report import reconcile_ledgers_by_user

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def test_report_refuses_an_unknown_user(session):
    from services.api_gateway.exceptions import NotFoundException

    with pytest.raises(NotFoundException):
        await reconcile_ledgers_by_user(session, "nobody")


async def test_report_places_the_stores_side_by_side(session):
    session.add(
        User(
            id="user-1",
            email="a@example.test",
            password_hash="x",
            full_name="A",
        )
    )
    session.add(
        EcoWallet(
            user_id="user-1",
            balance=Decimal("12.5"),
            total_earned=Decimal("20"),
            total_redeemed=Decimal("0"),
        )
    )
    session.add(
        EcoBalanceAccount(id=1, user_id="user-1", balance=Decimal("3"))
    )
    session.add(
        EcoBalanceEntry(
            user_id="user-1",
            sequence=1,
            amount=Decimal("3"),
            reason="grant",
            observation_id="obs-1",
            evidence_digest="d",
        )
    )
    await session.commit()

    report = await reconcile_ledgers_by_user(session, "user-1")

    assert report["shared_key"] == "users.id"
    sources = report["sources"]
    assert sources["wallet"]["present"] is True
    assert sources["wallet"]["balance"] == "12.5"
    assert sources["ecosystem"]["entries"] == 1
    assert sources["ecosystem"]["entry_sum"] == "3"
    # an empty store is absent, never a fabricated zero
    assert sources["ledger"]["entries"] == 0
    assert "not merged" in report["note"]
