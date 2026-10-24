"""Chart-of-accounts regressions (P1-9).

``settle_order`` and the wallet batches wrote ``FinJournalEntry.account_id``
with account **codes** while nothing ever created the ``FinAccount`` rows those
codes name, so every settlement and wallet batch referenced accounts that did
not exist and ``LedgerService.profit_and_loss`` reported them as
``unclassified`` (``reason="account_not_found"``). These tests pin the seeder
that fixes it: ``ECO_PLATFORM_REVENUE`` must be classified as income after a
real commerce settlement.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from database.models import FinAccount, FinJournalBatch, FinJournalEntry
from services.api_gateway.auth import get_current_user
from services.finance.chart_of_accounts import (
    ECO_ASSET,
    ECO_CASH,
    ECO_PLATFORM_REVENUE,
    ECO_SELLER_PAYABLE,
    REWARD_LIABILITY,
    WALLET_ACCOUNT_PREFIX,
    ensure_account,
    get_account_spec,
    seed_chart_of_accounts,
    wallet_account_code,
)
from services.finance.ledger_service import LedgerService
from services.finance.routers.finance import get_db, router

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def sku(db_session):
    """A stocked SKU, so an order can be created and settled."""
    from services.inventory.service import StockService

    stock = StockService(db_session)
    warehouse = await stock.create_warehouse("DEFAULT", "Default Warehouse", city="Tehran")
    stock._default_wh = warehouse
    created = await stock.create_sku(
        "CHART-SKU", "Chart Product", uom="kg", standard_cost=Decimal("10")
    )
    await stock.receipt(
        sku_id=created.id,
        warehouse_id=warehouse.id,
        qty=Decimal("100"),
        reference_type="test-setup",
        reference_id="test-initial",
        created_by="test-setup",
    )
    return created


async def _codes(db_session) -> set[str]:
    result = await db_session.execute(select(FinAccount.code))
    return set(result.scalars().all())


# ---------------------------------------------------------------------------
# (a) the seeder is idempotent
# ---------------------------------------------------------------------------


class TestSeedingIsIdempotent:
    async def test_seeding_twice_creates_one_row_per_code(self, db_session):
        first = await seed_chart_of_accounts(db_session)
        await db_session.commit()
        first_ids = sorted(account.id for account in first)
        first_codes = await _codes(db_session)

        second = await seed_chart_of_accounts(db_session)
        await db_session.commit()
        second_ids = sorted(account.id for account in second)

        assert first_ids == second_ids
        assert first_codes == await _codes(db_session)
        assert len(first_ids) == len(first_codes)
        assert len(first_ids) == len({account.code for account in first})

    async def test_seeded_rows_are_active_and_hierarchical(self, db_session):
        await seed_chart_of_accounts(db_session)
        await db_session.commit()

        result = await db_session.execute(select(FinAccount))
        accounts = {account.code: account for account in result.scalars().all()}

        assert accounts[ECO_PLATFORM_REVENUE].type == "income"
        assert accounts[ECO_PLATFORM_REVENUE].is_active is True
        assert accounts[ECO_SELLER_PAYABLE].parent_id == str(accounts[ECO_CASH].id)
        assert accounts[ECO_CASH].parent_id is None

    async def test_ensure_account_reuses_an_edited_row(self, db_session):
        spec = get_account_spec(ECO_CASH)
        account = await ensure_account(
            db_session,
            code=ECO_CASH,
            name=spec.name,
            type=spec.type,
            asset=spec.asset,
            currency=spec.currency,
        )
        await db_session.commit()
        account.name = "Renamed by operator"
        await db_session.commit()

        again = await ensure_account(
            db_session,
            code=ECO_CASH,
            name=spec.name,
            type=spec.type,
            asset=spec.asset,
            currency=spec.currency,
        )
        assert again.id == account.id
        assert again.name == "Renamed by operator"

    async def test_ensure_account_rejects_unknown_parent(self, db_session):
        with pytest.raises(LookupError):
            await ensure_account(
                db_session,
                code="ORPHAN_ACCOUNT",
                name="Orphan",
                type="asset",
                asset="IRR",
                currency="IRR",
                parent_code="NO_SUCH_PARENT",
            )

    async def test_ensure_account_seeds_a_canonical_parent_on_demand(self, db_session):
        code = wallet_account_code("user-without-seeding")
        account = await ensure_account(
            db_session,
            code=code,
            name="ECO Wallet — user-without-seeding",
            type="asset",
            asset="ECO",
            currency="ECO",
            parent_code=ECO_ASSET,
        )
        await db_session.commit()

        result = await db_session.execute(select(FinAccount).where(FinAccount.code == ECO_ASSET))
        parent = result.scalar_one()
        assert account.parent_id == str(parent.id)


# ---------------------------------------------------------------------------
# (b) acceptance criterion: settlement classifies as income
# ---------------------------------------------------------------------------


class TestSettlementIsClassified:
    async def test_settled_order_reports_platform_revenue_as_income(
        self, fresh_order_service, sku, db_session
    ):
        order_service = fresh_order_service
        order = await order_service.create_order(
            buyer_id="chart-buyer",
            items=[
                {
                    "sku_code": sku.sku_code,
                    "quantity": 1,
                    "unit_price": Decimal("100"),
                    "warehouse_id": 1,
                }
            ],
        )
        await order_service.confirm_payment(order.id, payment_confirmed=True)
        await order_service.process_order(order.id)
        await order_service.ship_order(order.id, "TRACK-CHART", "admin")
        await order_service.mark_delivered(order.id)
        await order_service.settle_order(order.id)

        ledger = LedgerService(db_session)
        report = await ledger.profit_and_loss(asset=order.currency)
        income_codes = {row["account_code"] for row in report["income"]}
        assert income_codes == {ECO_PLATFORM_REVENUE}
        assert report["income"][0]["account_name"] == "Platform Revenue"
        assert Decimal(report["income"][0]["amount"]) == Decimal(str(order.platform_fee)) + Decimal(
            str(order.landscape_fee)
        )
        assert not [
            row
            for row in report["unclassified"]
            if row["account_id"] in {ECO_CASH, ECO_PLATFORM_REVENUE, ECO_SELLER_PAYABLE}
        ]
        assert report["totals"][0]["income"] == report["income"][0]["amount"]

        balance = await ledger.trial_balance(asset=order.currency)
        assert {ECO_CASH, ECO_PLATFORM_REVENUE, ECO_SELLER_PAYABLE} <= {
            row["account_id"] for row in balance["rows"]
        }
        totals = [total for total in balance["totals"] if total["asset"] == order.currency]
        assert len(totals) == 1
        assert totals[0]["balanced"] is True

    async def test_settlement_accounts_exist_before_the_batch(
        self, fresh_order_service, sku, db_session
    ):
        """The seeder runs inside settle_order, so no chart pre-seeding is needed."""
        order = await fresh_order_service.create_order(
            buyer_id="chart-buyer-2",
            items=[
                {
                    "sku_code": sku.sku_code,
                    "quantity": 2,
                    "unit_price": Decimal("100"),
                    "warehouse_id": 1,
                }
            ],
        )
        await fresh_order_service.confirm_payment(order.id, payment_confirmed=True)
        await fresh_order_service.process_order(order.id)
        await fresh_order_service.ship_order(order.id, "TRACK-CHART-2", "admin")
        await fresh_order_service.mark_delivered(order.id)
        await fresh_order_service.settle_order(order.id)

        assert {ECO_CASH, ECO_PLATFORM_REVENUE, ECO_SELLER_PAYABLE} <= await _codes(db_session)

    async def test_settlement_batch_is_posted_and_balanced(
        self, fresh_order_service, sku, db_session
    ):
        order = await fresh_order_service.create_order(
            buyer_id="chart-buyer-3",
            items=[
                {
                    "sku_code": sku.sku_code,
                    "quantity": 1,
                    "unit_price": Decimal("250"),
                    "warehouse_id": 1,
                }
            ],
        )
        await fresh_order_service.confirm_payment(order.id, payment_confirmed=True)
        await fresh_order_service.process_order(order.id)
        await fresh_order_service.ship_order(order.id, "TRACK-CHART-3", "admin")
        await fresh_order_service.mark_delivered(order.id)
        settlement = await fresh_order_service.settle_order(order.id)

        result = await db_session.execute(
            select(FinJournalBatch).where(FinJournalBatch.id == settlement.journal_batch_id)
        )
        batch = result.scalar_one()
        assert batch.is_posted is True
        entries = await db_session.execute(
            select(FinJournalEntry).where(FinJournalEntry.batch_id == batch.id)
        )
        rows = entries.scalars().all()
        debits = sum(Decimal(str(row.amount)) for row in rows if row.entry_type == "debit")
        credits = sum(Decimal(str(row.amount)) for row in rows if row.entry_type == "credit")
        assert debits == credits == Decimal(str(order.total))


# ---------------------------------------------------------------------------
# (c) the wallet earns against chart rows
# ---------------------------------------------------------------------------


class TestWalletAccounts:
    async def test_earn_creates_and_then_reuses_its_accounts(
        self, fresh_wallet_service, db_session
    ):
        amount, balance = await fresh_wallet_service.earn(
            user_id="chart-wallet-user", category="tree_planting"
        )
        assert amount == Decimal("50")
        assert balance == Decimal("50")

        result = await db_session.execute(select(FinAccount))
        accounts = {account.code: account for account in result.scalars().all()}
        assert accounts[ECO_ASSET].type == "asset"
        assert accounts[REWARD_LIABILITY].type == "liability"

        again = await fresh_wallet_service.earn(
            user_id="chart-wallet-user", category="tree_planting"
        )
        assert again[0] == Decimal("50")

        result = await db_session.execute(select(FinAccount))
        after = {account.code: account.id for account in result.scalars().all()}
        assert after[ECO_ASSET] == accounts[ECO_ASSET].id
        assert after[REWARD_LIABILITY] == accounts[REWARD_LIABILITY].id
        assert await _codes(db_session) >= {ECO_ASSET, REWARD_LIABILITY}

    async def test_transfer_creates_per_user_wallet_accounts(
        self, fresh_wallet_service, db_session
    ):
        await fresh_wallet_service.earn(
            user_id="chart-sender", category="tree_planting", quantity=4
        )
        await fresh_wallet_service.transfer("chart-sender", "chart-recipient", Decimal("10"))

        codes = await _codes(db_session)
        sender = wallet_account_code("chart-sender")
        recipient = wallet_account_code("chart-recipient")
        assert sender in codes
        assert recipient in codes
        assert sender.startswith(WALLET_ACCOUNT_PREFIX)

        result = await db_session.execute(select(FinAccount))
        accounts = {account.code: account for account in result.scalars().all()}
        assert accounts[sender].parent_id == str(accounts[ECO_ASSET].id)

    async def test_earning_batch_resolves_against_the_chart(
        self, fresh_wallet_service, db_session
    ):
        await fresh_wallet_service.earn(user_id="chart-earner", category="biodiversity")
        report = await LedgerService(db_session).profit_and_loss(asset="ECO")
        assert report["unclassified"] == []
        assert report["income"] == []


# ---------------------------------------------------------------------------
# (d) the /accounts routes work
# ---------------------------------------------------------------------------


@pytest.fixture
async def accounts_app(db_session):
    app = FastAPI()
    app.include_router(router)

    async def database_override():
        yield db_session

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="admin", role="admin", is_active=True
    )
    return app


async def _get(app, path, params=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(f"/api/v1/finance{path}", params=params)


async def _post(app, path, params=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/api/v1/finance{path}", params=params)


class TestAccountsRoutes:
    async def test_get_accounts_lists_the_seeded_chart(self, accounts_app, db_session):
        await seed_chart_of_accounts(db_session)
        await db_session.commit()

        response = await _get(accounts_app, "/accounts")
        assert response.status_code == 200, response.text
        body = response.json()
        assert ECO_PLATFORM_REVENUE in {row["code"] for row in body}
        assert all(row["is_active"] is True for row in body)

    async def test_get_accounts_honours_is_active_and_parent_filters(
        self, accounts_app, db_session
    ):
        await seed_chart_of_accounts(db_session)
        await db_session.commit()
        await ensure_account(
            db_session,
            code="RETIRED_ACCOUNT",
            name="Retired",
            type="asset",
            asset="IRR",
            currency="IRR",
            parent_code=ECO_CASH,
        )
        retired = (
            await db_session.execute(select(FinAccount).where(FinAccount.code == "RETIRED_ACCOUNT"))
        ).scalar_one()
        retired.is_active = False
        await db_session.commit()
        cash = (
            await db_session.execute(select(FinAccount).where(FinAccount.code == ECO_CASH))
        ).scalar_one()

        inactive = await _get(accounts_app, "/accounts", params={"is_active": "false"})
        assert inactive.status_code == 200, inactive.text
        assert {row["code"] for row in inactive.json()} == {"RETIRED_ACCOUNT"}

        active = await _get(accounts_app, "/accounts", params={"is_active": "true"})
        assert "RETIRED_ACCOUNT" not in {row["code"] for row in active.json()}

        children = await _get(accounts_app, "/accounts", params={"parent_id": cash.id})
        assert children.status_code == 200
        assert "RETIRED_ACCOUNT" in {row["code"] for row in children.json()}

    async def test_post_account_creates_and_resolves_parent(self, accounts_app, db_session):
        response = await _post(
            accounts_app,
            "/accounts",
            params={
                "code": "CHILD_ACCOUNT",
                "name": "Child Account",
                "type": "expense",
                "asset": "IRR",
                "currency": "IRR",
                "parent_code": ECO_PLATFORM_REVENUE,
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == "CHILD_ACCOUNT"
        assert body["is_active"] is True

        result = await db_session.execute(
            select(FinAccount).where(FinAccount.code == "CHILD_ACCOUNT")
        )
        account = result.scalar_one()
        revenue = (
            await db_session.execute(
                select(FinAccount).where(FinAccount.code == ECO_PLATFORM_REVENUE)
            )
        ).scalar_one()
        assert account.parent_id == str(revenue.id)

    async def test_post_account_can_be_created_inactive(self, accounts_app, db_session):
        response = await _post(
            accounts_app,
            "/accounts",
            params={
                "code": "DORMANT_ACCOUNT",
                "name": "Dormant",
                "type": "asset",
                "asset": "IRR",
                "is_active": "false",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["is_active"] is False

        inactive = await _get(accounts_app, "/accounts", params={"is_active": "false"})
        assert "DORMANT_ACCOUNT" in {row["code"] for row in inactive.json()}

    async def test_post_account_is_a_repeatable_get_or_create(self, accounts_app):
        params = {"code": "STABLE_ACCOUNT", "name": "Stable", "type": "asset", "asset": "ECO"}
        first = await _post(accounts_app, "/accounts", params=params)
        assert first.status_code == 200, first.text
        second = await _post(accounts_app, "/accounts", params=params)
        assert second.status_code == 200, second.text
        assert first.json()["id"] == second.json()["id"]

    async def test_post_account_rejects_non_admin(self, accounts_app):
        accounts_app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="buyer", role="buyer", is_active=True
        )
        response = await _post(
            accounts_app,
            "/accounts",
            params={"code": "NOT_ALLOWED", "name": "Not Allowed", "type": "asset", "asset": "IRR"},
        )
        assert response.status_code == 403

    async def test_post_account_validates_input(self, accounts_app):
        unknown_type = await _post(
            accounts_app,
            "/accounts",
            params={"code": "BAD_TYPE", "name": "Bad", "type": "profit", "asset": "IRR"},
        )
        assert unknown_type.status_code == 422

        unknown_asset = await _post(
            accounts_app,
            "/accounts",
            params={"code": "BAD_ASSET", "name": "Bad", "type": "asset", "asset": "GOLD"},
        )
        assert unknown_asset.status_code == 422

        unknown_parent = await _post(
            accounts_app,
            "/accounts",
            params={
                "code": "BAD_PARENT",
                "name": "Bad",
                "type": "asset",
                "asset": "IRR",
                "parent_code": "NO_SUCH_PARENT",
            },
        )
        assert unknown_parent.status_code == 422

        bad_code = await _post(
            accounts_app,
            "/accounts",
            params={"code": "not upper", "name": "Bad", "type": "asset", "asset": "IRR"},
        )
        assert bad_code.status_code == 422
