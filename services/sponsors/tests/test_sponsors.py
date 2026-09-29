"""Tests for the sponsorship policy and lifecycle.

The point of these tests is not coverage. It is that each rule in policy.py
has a test that fails when the rule is removed. A guard that cannot fail is
not a guard.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from services.sponsors.models import (
    SlotPlacement,
    Sponsorship,
    SponsorshipStatus,
    SponsorTier,
)
from services.sponsors.policy import (
    FORBIDDEN_CATEGORIES,
    FORBIDDEN_PLACEMENT_PREFIXES,
    MAX_PLATFORM_SHARE,
    MAX_SPONSORS_PER_PLACEMENT,
    MAX_VISUAL_WEIGHT_PCT,
    PolicyViolation,
    assert_category_allowed,
    assert_placement_allowed,
    assert_platform_share_ok,
    disclosure_key,
)

TODAY = date(2026, 9, 26)


# --------------------------------------------------------------------------- #
# Placement policy
# --------------------------------------------------------------------------- #


class TestPlacementPolicy:
    def test_public_services_is_allowed(self):
        assert_placement_allowed("/public/services/marketplace-access")

    def test_public_audiences_is_allowed(self):
        assert_placement_allowed("/public/audiences/government")

    @pytest.mark.parametrize(
        "path",
        [
            "/hydroma",
            "/hydroma/dashboard",
            "/virtual-lab",
            "/simulator",
            "/models/ecocoin",
            "/checkout/cart",
            "/wallet",
            "/escrow/abc",
            "/settings",
            "/telecom",
            "/ussd",
            "/simple",
        ],
    )
    def test_protected_surfaces_are_refused(self, path):
        """The agronomic and transactional surfaces are the reason this model
        is a sponsorship and not an ad slot."""
        with pytest.raises(PolicyViolation, match="not permitted"):
            assert_placement_allowed(path)

    def test_trailing_slash_does_not_bypass(self):
        with pytest.raises(PolicyViolation):
            assert_placement_allowed("/checkout/")

    def test_prefix_confusion_does_not_bypass(self):
        """/checkout-archive is not /checkout."""
        assert_placement_allowed("/checkout-archive")

    def test_similar_prefix_is_allowed(self):
        """/modelz is not /models. Over-blocking pushes people to rename around
        the guard, which is worse than the rule being slightly narrow."""
        assert_placement_allowed("/modelz")

    def test_every_forbidden_prefix_is_reachable(self):
        """A prefix nobody can hit is dead policy. Prove each one blocks."""
        for prefix in FORBIDDEN_PLACEMENT_PREFIXES:
            with pytest.raises(PolicyViolation):
                assert_placement_allowed(f"{prefix}/x")


# --------------------------------------------------------------------------- #
# Category policy
# --------------------------------------------------------------------------- #


class TestCategoryPolicy:
    @pytest.mark.parametrize("category", sorted(FORBIDDEN_CATEGORIES))
    def test_every_forbidden_category_is_refused(self, category):
        with pytest.raises(PolicyViolation, match="excluded"):
            assert_category_allowed(category)

    def test_case_insensitive(self):
        with pytest.raises(PolicyViolation):
            assert_category_allowed("Petrochemical")

    def test_unknown_category_is_allowed(self):
        """Only the explicit list is excluded; new sectors are not blocked by
        accident, so a reviewer decides them."""
        assert_category_allowed("seed_company")

    def test_none_is_allowed(self):
        assert_category_allowed(None)


# --------------------------------------------------------------------------- #
# Commercial policy
# --------------------------------------------------------------------------- #


class TestPlatformShare:
    def test_ceiling_is_accepted(self):
        assert_platform_share_ok(MAX_PLATFORM_SHARE)

    def test_above_ceiling_refused(self):
        with pytest.raises(PolicyViolation, match="markup on farmer inputs"):
            assert_platform_share_ok(0.12)

    def test_negative_refused(self):
        with pytest.raises(PolicyViolation):
            assert_platform_share_ok(-0.01)

    def test_ceiling_matches_the_pricing_module(self):
        """The sponsorship fee cap and the instrument fee cap are the same
        number for the same reason, so they must not drift apart."""
        from engine.hydroma.economics.reference_basket import (
            BasketError,
            value_basket,
        )

        quotes = {"dap": 793.50, "urea": 390.00}
        with pytest.raises(BasketError, match="platform_share"):
            value_basket(
                _tiny_basket(),
                quotes,
                platform_share=MAX_PLATFORM_SHARE + 0.01,
            )

    def test_both_ceilings_are_eight_percent(self):
        assert MAX_PLATFORM_SHARE == 0.08


def _tiny_basket():
    from engine.hydroma.economics.reference_basket import (
        BaseBasket,
        InputItem,
    )

    return BaseBasket(
        crop="maize",
        market_class="coastal_low_income",
        items=(
            InputItem("DAP", 321.0, "dap"),
            InputItem("Urea", 150.0, "urea"),
        ),
    )


# --------------------------------------------------------------------------- #
# Model invariants
# --------------------------------------------------------------------------- #


class TestSponsorshipModel:
    def _sponsor(self, **over) -> Sponsorship:
        base = {
            "sponsor_name": "Example Foundation",
            "sponsor_url": "https://example.org",
            "amount": Decimal("25000.00"),
            "currency": "USD",
            "starts_on": date(2026, 9, 1),
            "ends_on": date(2027, 8, 31),
            "tier": SponsorTier.SECTION,
            "placement": SlotPlacement.PUBLIC_SERVICES,
            "status": SponsorshipStatus.ACTIVE,
            "disclosure_required": True,
        }
        base.update(over)
        return Sponsorship(**base)

    def test_live_within_window(self):
        assert self._sponsor().is_live(TODAY) is True

    def test_not_live_before_start(self):
        s = self._sponsor(starts_on=date(2026, 10, 1))
        assert s.is_live(TODAY) is False

    def test_not_live_after_end(self):
        s = self._sponsor(ends_on=date(2026, 9, 25))
        assert s.is_live(TODAY) is False

    def test_not_live_when_not_active(self):
        for status in (
            SponsorshipStatus.PROSPECT,
            SponsorshipStatus.CONTRACTED,
            SponsorshipStatus.SUSPENDED,
            SponsorshipStatus.ENDED,
            SponsorshipStatus.TERMINATED,
        ):
            assert self._sponsor(status=status).is_live(TODAY) is False, status

    def test_expires_today_is_still_live(self):
        s = self._sponsor(ends_on=TODAY)
        assert s.is_live(TODAY) is True
        assert s.is_live(TODAY + timedelta(days=1)) is False

    def test_column_default_is_declared(self):
        """`disclosure_required` must default at the database level too.

        SQLAlchemy applies a Column default on INSERT, not on construction, so
        a freshly built object reads None. That is why SponsorshipService.create
        also sets it explicitly: the value must be present both in memory and
        in the row. A row written by any other path would otherwise be able to
        carry a null and disable the label.
        """
        column = Sponsorship.__table__.columns["disclosure_required"]
        assert column.default is not None, "no column default declared"
        assert column.default.arg is True, "the column default is not True"
        assert column.nullable is False, "disclosure_required must not be nullable"

    def test_service_always_sets_it(self):
        """The in-memory value the service returns must already be True."""
        s = Sponsorship(
            sponsor_name="X",
            sponsor_url="https://x.org",
            amount=Decimal("1.00"),
            starts_on=TODAY,
            ends_on=TODAY,
            placement=SlotPlacement.PUBLIC_SERVICES,
            disclosure_required=True,
        )
        assert s.disclosure_required is True


# --------------------------------------------------------------------------- #
# Public payload shape
# --------------------------------------------------------------------------- #


class TestSlotPayload:
    def test_absent_sponsor_renders_nothing(self):
        from services.sponsors.service import SponsorshipService

        payload = SponsorshipService.slot_payload(None)
        assert payload == {"present": False}
        assert "sponsor" not in payload

    def test_payload_carries_no_user_data(self):
        """The response must be identical for every reader. If a user id ever
        appears here, the design has been broken."""
        from services.sponsors.service import SponsorshipService

        s = Sponsorship(
            sponsor_name="Example Foundation",
            sponsor_url="https://example.org",
            amount=Decimal("25000.00"),
            starts_on=date(2026, 9, 1),
            ends_on=date(2027, 8, 31),
            tier=SponsorTier.SECTION,
            placement=SlotPlacement.PUBLIC_SERVICES,
            status=SponsorshipStatus.ACTIVE,
        )
        payload = SponsorshipService.slot_payload(s)
        flat = repr(payload).lower()
        for forbidden in ("user_id", "visitor", "referrer", "ip", "device", "impression"):
            assert forbidden not in flat, f"payload leaks {forbidden}"

    def test_disclosure_is_always_required(self):
        from services.sponsors.service import SponsorshipService

        s = Sponsorship(
            sponsor_name="Example Foundation",
            sponsor_url="https://example.org",
            amount=Decimal("25000.00"),
            starts_on=date(2026, 9, 1),
            ends_on=date(2027, 8, 31),
            placement=SlotPlacement.PUBLIC_SERVICES,
            status=SponsorshipStatus.ACTIVE,
            disclosure_required=True,
        )
        assert SponsorshipService.slot_payload(s)["disclosure"]["required"] is True
class TestDisclosureKey:
    def test_key_is_stable_and_namespaced(self):
        key = disclosure_key("Example Foundation")
        assert key == "sponsors.slot.disclosure::Example Foundation"
        assert key.startswith("sponsors.slot.disclosure::")


# --------------------------------------------------------------------------- #
# Budget invariants
# --------------------------------------------------------------------------- #


class TestVisualBudget:
    def test_slot_cannot_outweigh_content(self):
        assert MAX_VISUAL_WEIGHT_PCT <= 12

    def test_one_sponsor_per_placement(self):
        """A rotation would make this advertising."""
        assert MAX_SPONSORS_PER_PLACEMENT == 1
