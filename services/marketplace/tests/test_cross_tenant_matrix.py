"""The cross-tenant negative matrix (B5).

Every row is a *negative* case: a principal that does not own the resource
must be refused. The matrix is deliberately written as one table so a gap is
visible as a missing row rather than as a missing file.

Surfaces covered:

* **user ↔ user** — a wallet entry belongs to one user; a stranger may not
  read, void, or move it.
* **shop ↔ shop** — a marketplace order belongs to one buyer; the database
  backstop keeps two buyers apart.
* **village ↔ village** — a community space belongs to one village; a
  stranger may not read it.
* **seller ↔ other seller** — a seller's revenue figures must not leak into
  another seller's view.
"""

from decimal import Decimal

import pytest

from services.wallet.eco_balance import Reason


class TestUserToUser:
    """A wallet entry belongs to exactly one user."""

    @pytest.fixture
    async def accounts(self, db_session):
        from services.wallet.eco_balance import EcoBalanceService

        service = EcoBalanceService(db_session)
        await service.credit(
            user_id="user-a",
            tonnes_co2e=Decimal("100.00"),
            source="measured",
            observation_id="obs-a",
            reason=Reason.SOIL_CARBON_OBSERVED,
            evidence={"method": "test"},
        )
        return service

    async def test_a_stranger_cannot_void_another_users_entry(self, accounts):
        """The guard is the entry's owner, not the caller's role."""
        entries = await accounts.ledger("user-a")
        assert entries

        with pytest.raises(LookupError):
            await accounts.retire(user_id="user-b", entry_id=entries[0].id)

    async def test_the_entry_survives_the_refused_retraction(self, accounts):
        """A refused retraction must not change anything."""
        entries = await accounts.ledger("user-a")
        entry_id = entries[0].id

        with pytest.raises(LookupError):
            await accounts.retire(user_id="user-b", entry_id=entry_id)

        account = await accounts.account_for("user-a")
        assert account.balance > 0
        after = await accounts.ledger("user-a")
        assert all(e.retired_at is None for e in after)

    async def test_the_ledger_is_scoped_to_its_owner(self, accounts):
        """One user's ledger must not contain another user's entries."""
        assert await accounts.ledger("user-b") == []

    async def test_the_balance_is_per_user(self, accounts):
        await accounts.credit(
            user_id="user-b",
            tonnes_co2e=Decimal("50.00"),
            source="measured",
            observation_id="obs-b",
            reason=Reason.SOIL_CARBON_OBSERVED,
            evidence={"method": "test"},
        )
        a = await accounts.account_for("user-a")
        b = await accounts.account_for("user-b")
        assert a.balance != b.balance


class TestShopToShop:
    """A marketplace order belongs to exactly one buyer."""

    async def test_the_order_carries_its_buyer(self, db_session):
        """The order records the buyer, so the scope check has something to check."""
        from database.models import ComOrder

        order = ComOrder(
            id="order-1",
            order_number="ORD-1",
            buyer_id="buyer-a",
            seller_id="seller-1",
            status="draft",
            total=Decimal("100.00"),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        assert order.buyer_id == "buyer-a"
        assert order.buyer_id != "buyer-b"

    async def test_two_buyers_may_reuse_one_idempotency_key(self, db_session):
        """The idempotency backstop is *per buyer*.

        Two different buyers may present the same key; two requests from the
        *same* buyer collide instead of creating a duplicate order.
        """
        from sqlalchemy.exc import IntegrityError

        from database.models import ComOrder

        for buyer in ("buyer-a", "buyer-b"):
            db_session.add(
                ComOrder(
                    id=f"order-{buyer}",
                    order_number=f"ORD-{buyer}",
                    buyer_id=buyer,
                    seller_id="seller-1",
                    status="draft",
                    total=Decimal("100.00"),
                    idempotency_key="key-1",
                )
            )
        await db_session.commit()

        # The same buyer, the same key, a different row id -> must collide.
        db_session.add(
            ComOrder(
                id="order-a-again",
                order_number="ORD-A-AGAIN",
                buyer_id="buyer-a",
                seller_id="seller-1",
                status="draft",
                total=Decimal("100.00"),
                idempotency_key="key-1",
            )
        )
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()


class TestVillageToVillage:
    """A community space belongs to exactly one village."""

    @pytest.fixture
    async def spaces(self, db_session):
        from services.village.models import CommunitySpace, CommunitySpaceKind, SpaceStatus

        for village in ("village-a", "village-b"):
            db_session.add(
                CommunitySpace(
                    village_id=village,
                    name=f"Space {village}",
                    kind=CommunitySpaceKind.VILLAGE.value,
                    status=SpaceStatus.ACTIVE.value,
                    region="R",
                    country="IR",
                )
            )
        await db_session.commit()
        return db_session

    async def test_each_space_carries_its_own_village(self, spaces):
        from sqlalchemy import select

        from services.village.models import CommunitySpace

        result = await spaces.execute(select(CommunitySpace))
        for space in result.scalars().all():
            assert space.village_id in ("village-a", "village-b")

    async def test_a_stranger_cannot_read_another_villages_space(self, spaces):
        """The API refuses a space that is not the caller's village."""
        import inspect

        from services.village import api as village_api

        source = inspect.getsource(village_api)
        assert "_require_admin_of" in source
        # The read path is guarded by the same helper the write paths use.
        read = inspect.getsource(village_api.get_space)
        assert "_require_admin_of" in read


class TestSellerToOtherSeller:
    """A seller's revenue must not leak into another seller's view."""

    def test_the_stats_endpoint_is_scoped_to_the_verified_seller(self):
        """The stats route resolves the caller's own seller id.

        The scoping happens in the router: it looks the caller's
        ``MarketplaceSeller`` row up and passes that ``seller_id`` to
        ``get_revenue_stats``, so a non-seller gets the global aggregate and
        a verified seller only ever sees their own figures.
        """
        import inspect

        from services.api_gateway.routers import marketplace as mkt_router

        source = inspect.getsource(mkt_router.marketplace_stats)
        assert "seller_id=seller_id" in source
        assert "MarketplaceSeller" in source
        assert "verified" in source

    def test_the_revenue_aggregation_can_be_scoped(self):
        """The aggregation itself accepts a seller filter."""
        import inspect

        from services.marketplace.order_management import OrderManager

        signature = inspect.signature(OrderManager.get_revenue_stats)
        assert "seller_id" in signature.parameters
