"""Tests for the read-only cross-store consolidation (P2-13).

Seeds each of the five independent money stores through the shared ``db_session``
fixture (an isolated in-memory SQLite database built by ``services/conftest.py``
via ``Base.metadata.create_all``) and asserts the consolidated per-asset
aggregation, plus the empty-store zero behaviour.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from database.models import (
    EcoWallet,
    FinAccount,
    FinJournalBatch,
    FinJournalEntry,
    LedgerEntry,
)
from services.api_gateway.auth import get_current_user
from services.api_gateway.routers.finance_consolidation import get_db, router
from services.finance.consolidation import SOURCE_KEYS, ConsolidatedPositionService
from services.marketplace.models.marketplace_payment import MarketplaceEscrowEntry

pytestmark = pytest.mark.asyncio

_ECOCOIN_DDL = """
CREATE TABLE ecocoin_balances (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    balance NUMERIC,
    total_earned NUMERIC,
    total_spent NUMERIC,
    total_burned NUMERIC
)
"""


async def _seed_all_stores(db_session) -> None:
    """Seed a known value into each of the five stores.

    Deliberately uses different numbers per store so the consolidation reports
    them side by side (they are independent representations, never summed).
    """
    # 1) double-entry: posted batch, ECO_ASSET debit 200 / REWARD_LIABILITY
    #    credit 200 — reported per account, grouped by asset.
    batch = FinJournalBatch(
        batch_number="JB-SEED", batch_date=date(2026, 9, 1), is_posted=True
    )
    db_session.add(batch)
    await db_session.flush()
    db_session.add_all(
        [
            FinJournalEntry(
                batch_id=batch.id,
                account_id="ECO_ASSET",
                entry_type="debit",
                asset="ECO",
                amount=Decimal("200"),
            ),
            FinJournalEntry(
                batch_id=batch.id,
                account_id="REWARD_LIABILITY",
                entry_type="credit",
                asset="ECO",
                amount=Decimal("200"),
            ),
        ]
    )

    # 2) single-entry: ECO credit 30 / debit 10 -> signed +20; IRR credit 100.
    db_session.add_all(
        [
            LedgerEntry(
                account_id="esc_buyer", entry_type="credit", asset="ECO", amount=Decimal("30")
            ),
            LedgerEntry(
                account_id="esc_buyer", entry_type="debit", asset="ECO", amount=Decimal("10")
            ),
            LedgerEntry(
                account_id="esc_seller", entry_type="credit", asset="IRR", amount=Decimal("100")
            ),
        ]
    )

    # 3) marketplace escrow (IRR): hold 50, release 30, refund 20 -> total 100.
    db_session.add_all(
        [
            MarketplaceEscrowEntry(
                payment_id="p1",
                order_id="o1",
                entry_type="hold",
                amount=Decimal("50"),
                currency="IRR",
            ),
            MarketplaceEscrowEntry(
                payment_id="p1",
                order_id="o1",
                entry_type="release",
                amount=Decimal("30"),
                currency="IRR",
            ),
            MarketplaceEscrowEntry(
                payment_id="p1",
                order_id="o1",
                entry_type="refund",
                amount=Decimal("20"),
                currency="IRR",
            ),
        ]
    )

    # 4) eco_wallets: two ECO wallets, 100 + 50 -> 150.
    db_session.add_all(
        [
            EcoWallet(
                user_id="u1",
                balance=Decimal("100"),
                total_earned=Decimal("120"),
                total_redeemed=Decimal("20"),
            ),
            EcoWallet(
                user_id="u2",
                balance=Decimal("50"),
                total_earned=Decimal("50"),
                total_redeemed=Decimal("0"),
            ),
        ]
    )
    await db_session.commit()

    # 5) ecocoin: raw table with no ORM model — created + seeded via text() SQL.
    await db_session.execute(text(_ECOCOIN_DDL))
    await db_session.execute(
        text(
            "INSERT INTO ecocoin_balances "
            "(id, user_id, balance, total_earned, total_spent, total_burned) "
            "VALUES (:id, :uid, :bal, :earned, :spent, :burned)"
        ),
        {"id": "e1", "uid": "c1", "bal": 40, "earned": 40, "spent": 0, "burned": 0},
    )
    await db_session.commit()


async def test_seeded_position_matches_expected_per_asset(db_session):
    await _seed_all_stores(db_session)
    report = await ConsolidatedPositionService(db_session).position(as_of=date(2026, 10, 10))

    assert list(report["sources"].keys()) == list(SOURCE_KEYS)

    fin = report["sources"]["fin_double_entry"]["assets"]
    assert Decimal(fin["ECO"]["total_debits"]) == Decimal("200")
    assert Decimal(fin["ECO"]["total_credits"]) == Decimal("200")
    assert {a["account_id"] for a in fin["ECO"]["accounts"]} == {
        "ECO_ASSET",
        "REWARD_LIABILITY",
    }

    single = report["sources"]["ledger_single_entry"]["assets"]
    assert Decimal(single["ECO"]["total"]) == Decimal("20")
    assert Decimal(single["IRR"]["total"]) == Decimal("100")

    mkt = report["sources"]["marketplace_escrow"]["assets"]
    assert Decimal(mkt["IRR"]["total"]) == Decimal("100")
    assert {k: Decimal(v) for k, v in mkt["IRR"]["by_state"].items()} == {
        "hold": Decimal("50"),
        "release": Decimal("30"),
        "refund": Decimal("20"),
    }

    wallets = report["sources"]["eco_wallets"]["assets"]["ECO"]
    assert Decimal(wallets["total"]) == Decimal("150")
    assert Decimal(wallets["total_earned"]) == Decimal("170")
    assert report["sources"]["eco_wallets"]["row_count"] == 2

    eco = report["sources"]["ecocoin"]["assets"]["ECO"]
    assert report["sources"]["ecocoin"]["available"] is True
    assert report["sources"]["ecocoin"]["row_count"] == 1
    assert Decimal(eco["total"]) == Decimal("40")

    # Gaps: two wallets, neither with a matching per-user REWARD_LIABILITY ledger.
    recon = report["gaps"]["wallet_vs_reward_liability"]
    assert recon["overall_ok"] is False
    assert recon["discrepancies_count"] == 2

    overall = report["overall"]
    assert overall["source_count"] == 5
    assert set(overall["assets"]) == {"ECO", "IRR"}
    assert set(overall["non_empty_sources"]) == set(SOURCE_KEYS)


async def test_double_entry_as_of_cutoff_is_applied(db_session):
    await _seed_all_stores(db_session)
    service = ConsolidatedPositionService(db_session)

    before = await service.position(as_of=date(2026, 1, 1))
    assert before["sources"]["fin_double_entry"]["row_count"] == 0
    # Non-dated stores are not date-filtered, so they keep their current totals.
    wallet_total = before["sources"]["eco_wallets"]["assets"]["ECO"]["total"]
    assert Decimal(wallet_total) == Decimal("150")


async def test_empty_db_returns_zero_for_every_source(db_session):
    report = await ConsolidatedPositionService(db_session).position()

    assert list(report["sources"].keys()) == list(SOURCE_KEYS)
    for source in report["sources"].values():
        assert source["row_count"] == 0
        for bucket in source["assets"].values():
            assert Decimal(bucket["total"]) == 0

    # eco_wallets / ecocoin always carry an ECO bucket even when empty.
    wallets_total = report["sources"]["eco_wallets"]["assets"]["ECO"]["total"]
    assert Decimal(wallets_total) == Decimal("0")
    ecocoin_total = report["sources"]["ecocoin"]["assets"]["ECO"]["total"]
    assert Decimal(ecocoin_total) == Decimal("0")
    assert report["sources"]["ecocoin"]["available"] is False
    # The variable-asset stores have nothing to attribute, so no buckets.
    assert report["sources"]["fin_double_entry"]["assets"] == {}
    assert report["sources"]["ledger_single_entry"]["assets"] == {}
    assert report["sources"]["marketplace_escrow"]["assets"] == {}

    assert report["overall"]["non_empty_sources"] == []
    recon = report["gaps"]["wallet_vs_reward_liability"]
    assert recon["overall_ok"] is True
    assert recon["total_wallets"] == 0


async def test_wallet_matching_reward_liability_reports_no_gap(db_session):
    # The reconciliation joins journal entries to the chart of accounts, so the
    # REWARD_LIABILITY account must exist for the wallet balance to reconcile.
    db_session.add(
        FinAccount(
            code="REWARD_LIABILITY",
            name="Reward Liability",
            type="liability",
            asset="ECO",
            currency="ECO",
        )
    )
    wallet = EcoWallet(user_id="u9", balance=Decimal("75"), total_earned=Decimal("75"))
    db_session.add(wallet)
    batch = FinJournalBatch(
        batch_number="JB-RL", batch_date=date(2026, 9, 1), is_posted=True, created_by="u9"
    )
    db_session.add(batch)
    await db_session.flush()
    db_session.add(
        FinJournalEntry(
            batch_id=batch.id,
            account_id="REWARD_LIABILITY",
            entry_type="credit",
            asset="ECO",
            amount=Decimal("75"),
        )
    )
    await db_session.commit()

    report = await ConsolidatedPositionService(db_session).position()
    recon = report["gaps"]["wallet_vs_reward_liability"]
    assert recon["overall_ok"] is True
    assert recon["discrepancies_count"] == 0


async def test_consolidated_position_endpoint_admin_only(db_session):
    await _seed_all_stores(db_session)
    app = FastAPI()
    app.include_router(router)

    async def database():
        yield db_session

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="buyer", role="buyer"
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        url = "/api/v1/finance/consolidated/position"
        assert (await client.get(url)).status_code == 403

        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="admin", role="admin"
        )
        response = await client.get(url, params={"as_of": "2026-10-10"})
        assert response.status_code == 200
        body = response.json()
        assert list(body["sources"].keys()) == list(SOURCE_KEYS)
        wallet_total = body["sources"]["eco_wallets"]["assets"]["ECO"]["total"]
        assert Decimal(wallet_total) == Decimal("150")
