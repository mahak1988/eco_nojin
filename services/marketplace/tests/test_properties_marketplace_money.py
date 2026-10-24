"""Property-based tests for the marketplace money invariants.

Every test is a Hypothesis property test on a deterministic profile:
``deadline=None``, a small ``max_examples`` budget, ``database=None`` (no
example database is written) and ``derandomize=True`` (the same examples on
every run). Each example starts from a database the test wipes itself, so no
example can observe another's rows, and no key is shared between examples.

The marketplace carries the same fee-conservation invariant the commerce
service does -- a total is a subtotal plus two fee lines -- and it is now the
*same* fix, not a weaker one:

* ``services/commerce/service.py`` quantises each fee line to the cent and
  builds ``total`` from the *quantised* lines, so
  ``subtotal + platform_fee + landscape_fee == total`` holds exactly.
* ``services/marketplace/service.py`` did the same from 2026-10-10. Before
  that, it computed the lines, added the *raw* divisions to form ``total``, and
  only then handed all four numbers to ``Numeric(15, 2)`` columns, so the
  round-trip rounded each line independently and the parts need not add up to
  the whole -- a 0.13 subtotal at 300 + 100 bps stored fee lines of 0.00 each
  against a total of 0.14.

The tests below pin that invariant from both sides: the rate columns round the
fee lines exactly as the service charges them, and the total is the sum of the
stored parts to the cent.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select, text

from services.marketplace.models import (
    MarketplaceCommissionRule,
    MarketplaceOrder,
)
from services.marketplace.service import MarketplaceService

# ---------------------------------------------------------------------------
# Deterministic Hypothesis profile.
# ---------------------------------------------------------------------------

_HEALTH = [HealthCheck.function_scoped_fixture, HealthCheck.too_slow]

PROPERTY = settings(
    max_examples=12,
    deadline=None,
    database=None,
    derandomize=True,
    suppress_health_check=_HEALTH,
)

BPS = Decimal("10000")

#: The storage scale of every marketplace money column: ``Numeric(15, 2)``.
CENT = Decimal("0.01")

#: Only the tables this file writes, children before parents, so one DELETE
#: pass fully isolates one example from the next.
_OWNED_TABLES = (
    "marketplace_order_items",
    "marketplace_orders",
    "marketplace_products",
    "marketplace_sellers",
    "marketplace_commission_rules",
)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


async def _wipe(db_session) -> None:
    """Empty every table this file touches, so an example starts clean."""
    await db_session.rollback()
    for table in _OWNED_TABLES:
        await db_session.execute(text(f"DELETE FROM {table}"))
    await db_session.commit()
    db_session.expunge_all()


# ---------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------


@st.composite
def marketplace_plan(draw):
    """A random catalogue and basket.

    ``price`` is drawn in whole cents because ``MarketplaceProduct.price`` is
    ``Numeric(12, 2)`` -- a sub-cent price would be rounded on the way in and
    the plan would describe a product that does not exist.
    """
    return {
        "price": draw(
            st.integers(1, 500_000).map(lambda c: Decimal(c) / 100)
        ),
        "quantity": draw(st.integers(1, 5)),
        "platform_bps": draw(st.integers(0, 3000)),
        "landscape_bps": draw(st.integers(0, 2000)),
        "village": draw(st.booleans()),
    }


async def _stock_and_order(db_session, plan) -> MarketplaceOrder:
    """Register a seller, publish and approve a product, then order it."""
    service = MarketplaceService(db_session)
    village_id = _unique("village")

    seller = await service.register_seller(
        user_id=_unique("user"),
        village_id=village_id,
        shop_name=_unique("shop"),
    )
    await service.verify_seller(seller.id, "property-test")

    product = await service.create_product(
        seller_id=seller.id,
        name=_unique("item"),
        price=plan["price"],
        village_id=village_id,
        category="compost",
        stock=100,
    )
    await service.approve_product(product.id, "property-test")

    # Either an explicit per-village rule, or -- when the plan says so -- the
    # service's own default row, so the default bps are covered too.
    if plan["village"]:
        db_session.add(
            MarketplaceCommissionRule(
                village_id=village_id,
                platform_fee_bps=plan["platform_bps"],
                landscape_fee_bps=plan["landscape_bps"],
                is_active=True,
            )
        )
        await db_session.commit()
    else:
        await service._get_commission_rule(_unique("other-village"))

    return await service.create_order(
        buyer_id=_unique("buyer"),
        items=[{"product_id": product.id, "quantity": plan["quantity"]}],
        village_id=village_id,
        shipping_address={"city": "Karaj"},
    )


# ---------------------------------------------------------------------------
# fee conservation
# ---------------------------------------------------------------------------


class TestMarketplaceFeeConservation:
    """The parts add up to the whole, and by how much exactly."""

    @given(plan=marketplace_plan())
    @PROPERTY
    async def test_the_total_is_the_subtotal_plus_both_fee_lines(
        self, db_session, plan
    ):
        await _wipe(db_session)
        order = await _stock_and_order(db_session, plan)

        subtotal = Decimal(str(order.subtotal))
        platform_fee = Decimal(str(order.platform_fee))
        landscape_fee = Decimal(str(order.landscape_fee))
        total = Decimal(str(order.total))

        # The catalogue is the pricing authority, so the subtotal is exactly
        # the price that was published, times the quantity ordered.
        assert subtotal == plan["price"] * plan["quantity"]
        assert isinstance(total, Decimal)
        assert isinstance(platform_fee, Decimal)
        assert isinstance(landscape_fee, Decimal)
        # Fees are never negative and never exceed the total.
        assert platform_fee >= 0
        assert landscape_fee >= 0
        assert total >= subtotal

        # The service quantises each fee line to the cent before forming the
        # total, as commerce does, so the identity holds at the storage scale.
        assert total == subtotal + platform_fee + landscape_fee

    @given(plan=marketplace_plan())
    @PROPERTY
    async def test_each_fee_line_is_its_share_rounded_to_the_storage_scale(
        self, db_session, plan
    ):
        await _wipe(db_session)
        order = await _stock_and_order(db_session, plan)

        subtotal = Decimal(str(order.subtotal))
        platform_fee = Decimal(str(order.platform_fee))
        landscape_fee = Decimal(str(order.landscape_fee))

        rules = (
            (
                await db_session.execute(
                    select(MarketplaceCommissionRule).where(
                        MarketplaceCommissionRule.is_active.is_(True)
                    )
                )
            )
            .scalars()
            .all()
        )
        assert rules
        # A per-village rule beats the default row, exactly as the service
        # resolves it.
        village_id = str(order.village_id)
        rule = next((r for r in rules if r.village_id == village_id), rules[0])

        # The service quantises each line itself, so the stored line is the
        # subtotal's share of the rule to the cent, rounded half to even.
        assert platform_fee == (
            subtotal * Decimal(rule.platform_fee_bps) / BPS
        ).quantize(CENT)
        assert landscape_fee == (
            subtotal * Decimal(rule.landscape_fee_bps) / BPS
        ).quantize(CENT)
        # And the rate the rule carries is what the order was charged.
        assert platform_fee + landscape_fee <= subtotal * Decimal("5000") / BPS

    async def test_a_default_rate_order_adds_up_exactly(self, db_session):
        """A cent-granular subtotal with the default schedule is exact.

        Not every order is, but the majority of them are, and this is the
        shape of one: 300 + 100 bps on a whole-ruble subtotal produces
        fee lines that are already whole cents, so nothing is rounded away
        and the identity holds exactly.
        """
        await _wipe(db_session)
        plan = {
            "price": Decimal("100.00"),
            "quantity": 1,
            "platform_bps": 300,
            "landscape_bps": 100,
            "village": False,
        }
        order = await _stock_and_order(db_session, plan)

        assert Decimal(str(order.subtotal)) == Decimal("100.00")
        assert Decimal(str(order.platform_fee)) == Decimal("3.00")
        assert Decimal(str(order.landscape_fee)) == Decimal("1.00")
        assert Decimal(str(order.total)) == Decimal("104.00")
        assert (
            Decimal(str(order.subtotal))
            + Decimal(str(order.platform_fee))
            + Decimal(str(order.landscape_fee))
            == Decimal(str(order.total))
        )

    async def test_the_default_rates_keep_the_identity_to_the_cent(
        self, db_session
    ):
        """The invariant that used to fail by a cent, now asserted.

        A 0.13 subtotal at the default 300 + 100 bps schedule computes
        ``platform_fee`` as 0.0039 and ``landscape_fee`` as 0.0013. Both used
        to reach the ``Numeric(15, 2)`` columns unrounded while the total was
        built from the *raw* divisions, so the fee columns rounded to 0.00 each
        while the total rounded to 0.14 -- a cent of total that no fee line
        accounted for, in whichever direction the rounding landed.

        ``services/marketplace/service.py`` now quantises each line to the cent
        before summing, exactly as ``services/commerce/service.py`` does, so
        the stored figures are one identity:
        ``subtotal + platform_fee + landscape_fee == total``.
        """
        await _wipe(db_session)
        plan = {
            "price": Decimal("0.13"),
            "quantity": 1,
            "platform_bps": 300,
            "landscape_bps": 100,
            "village": False,
        }
        order = await _stock_and_order(db_session, plan)

        subtotal = Decimal(str(order.subtotal))
        platform_fee = Decimal(str(order.platform_fee))
        landscape_fee = Decimal(str(order.landscape_fee))
        total = Decimal(str(order.total))

        assert subtotal == Decimal("0.13")
        # Both fee lines round down to nothing, each quantised by the service
        # itself rather than by the storage round-trip...
        assert platform_fee == Decimal("0.00")
        assert landscape_fee == Decimal("0.00")
        # ...and the total is the sum of the stored parts, so the cent that
        # used to vanish is no longer there to hold.
        assert total == subtotal + platform_fee + landscape_fee
        assert total == Decimal("0.13")
        assert abs(total - subtotal - platform_fee - landscape_fee) == Decimal("0.00")

    @given(
        price=st.integers(100, 500_000).map(lambda c: Decimal(c) / 100),
        quantity=st.integers(1, 5),
    )
    @PROPERTY
    async def test_a_zero_rate_order_charges_nothing_extra(
        self, db_session, price, quantity
    ):
        """A rule that charges nothing cannot move money at all."""
        await _wipe(db_session)
        plan = {
            "price": price,
            "quantity": quantity,
            "platform_bps": 0,
            "landscape_bps": 0,
            "village": True,
        }
        order = await _stock_and_order(db_session, plan)

        subtotal = Decimal(str(order.subtotal))
        platform_fee = Decimal(str(order.platform_fee))
        landscape_fee = Decimal(str(order.landscape_fee))
        total = Decimal(str(order.total))

        assert platform_fee == Decimal("0.00")
        assert landscape_fee == Decimal("0.00")
        assert total == subtotal
        assert subtotal + platform_fee + landscape_fee == total
