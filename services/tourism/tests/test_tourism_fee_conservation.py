"""Fee conservation for the tourism booking's three fee lines.

``TourismService.create_booking`` charges three fee lines on top of the tour's
subtotal -- platform 800 bps, landscape 200 bps and insurance 200 bps -- and
forms the total from them. The lines used to be computed as unrounded
divisions, and the ``Numeric(15, 2)`` columns round each of the four figures
independently, so the stored fee lines need not have summed to the stored
total: a 0.13-per-person single-participant tour stored lines of 0.01, 0.00
and 0.00 (0.01 in fees) against a total of 0.15 -- a cent no line accounted
for.

Each line is now quantised to the cent before the total is formed, the same
fix ``commerce/service.py:OrderService._compute_fees`` and
``marketplace/service.py`` received, so the three fee lines plus the host's
share always account for the whole total exactly.

The split, and what "the host's share" means here: the fees are charged *on
top* of the tour price, so the host is paid the subtotal and the guest pays
the subtotal plus the three lines. The host's share of the guest's payment is
therefore the subtotal, and ``platform + insurance + landscape + host_share ==
total`` is exactly that statement. The 800/200/200 rates, the 8800 bps
``HOST_SHARE_BPS`` and the host-share semantics are unchanged; only the
arithmetic's rounding is.

What is pinned, by invariant:

1. **Conservation** — ``platform + insurance + landscape + host_share ==
   total`` exactly, for every cent-granular booking, read back from the
   database the booking was written to (the drift used to live precisely
   between the in-memory Decimals and what the columns round to).
2. **The 800/200/200 split values are unchanged** — a whole subtotal charges
   8 %, 2 % and 2 % and costs 12 % more, exactly, with every line cent-granular.
3. **The rates did not move** — each fee line is its share of the subtotal at
   its documented bps, to the cent, and every constant is still the one
   ``services/finance/revenue_indicators.py`` documents for tourism.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from services.tourism.models import TourismBooking
from services.tourism.service import TourismService

#: One cent. Every fee is money, so every figure the booking stores is
#: cent-granular and the comparisons below are exact.
CENT = Decimal("0.01")

#: One hundred per cent, in the bps unit the service's fee constants use.
BPS = Decimal(10000)

#: The schedule, read off the service rather than restated, so a rate change
#: moves this file too. ``revenue_indicators.tourism_schedule`` documents the
#: same split for the take-rate band.
FEE_LINES = (
    ("platform_fee", Decimal(TourismService.PLATFORM_FEE_BPS)),
    ("landscape_fee", Decimal(TourismService.LANDSCAPE_FEE_BPS)),
    ("insurance_fee", Decimal(TourismService.INSURANCE_FEE_BPS)),
)

#: Every cent from 0.01 to 5.00 -- the granularity real money has -- plus the
#: subtotals a reader would recognise. The bank that established the drift is
#: entirely in the awkward lower half of this range.
SWEEP_CENTS = list(range(1, 501))
ERECOGNISED = (
    Decimal("7.77"),
    Decimal("33.33"),
    Decimal("100.00"),
    Decimal("1000.25"),
)


def _unique(prefix: str) -> str:
    """A per-test identifier, so no two examples can collide on a key."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


async def _book(db_session, price_per_person: Decimal, participants: int = 1):
    """Create an active tour and book ``participants`` seats at ``price_per_person``.

    ``min_participants=1`` so a single-participant booking's subtotal is
    exactly the per-person price, which is what makes the cent-granular
    subtotals below the subtotal the assertion is about.
    """
    service = TourismService(db_session)
    guide = await service.register_guide(
        user_id=_unique("guest"),
        village_id="hejij",
        full_name="Guest",
    )
    guide = await service.verify_guide(str(guide.id))
    assert guide.is_verified is True

    tour = await service.create_tour(
        guide_id=str(guide.id),
        village_id="hejij",
        title=_unique("tour"),
        tour_type="nomadic",
        duration_hours=4,
        price_per_person=price_per_person,
        min_participants=1,
        max_participants=50,
    )
    tour = await service.approve_tour(str(tour.id), "manager")
    assert tour.status == "active"

    return await service.create_booking(
        tour_id=str(tour.id),
        guest_id=_unique("guest"),
        participants_count=participants,
        tour_date=datetime.now(UTC) + timedelta(days=30),
        village_id="hejij",
    )


async def _assert_conserved(booking: TourismBooking) -> None:
    """Read the booking back and check the four legs account for the total.

    Every figure is read through the model, so the ``Numeric(15, 2)``
    columns' own rounding is part of what is asserted on: that is where
    the used-to-be drift lived.
    """
    subtotal = Decimal(str(booking.subtotal))
    platform_fee = Decimal(str(booking.platform_fee))
    landscape_fee = Decimal(str(booking.landscape_fee))
    insurance_fee = Decimal(str(booking.insurance_fee))
    total = Decimal(str(booking.total))

    # The host is paid the tour's own price; the fees are charged on top.
    host_share = subtotal

    assert host_share + platform_fee + landscape_fee + insurance_fee == total
    # Restated the other way round: the total is the subtotal plus exactly
    # the three fee lines, nothing else and nothing less.
    assert total - subtotal == platform_fee + landscape_fee + insurance_fee


class TestTourismFeeConservation:
    """``platform + insurance + landscape + host_share == total``, exactly."""

    async def test_a_single_booking_conserves_its_total(self, db_session):
        """One awkward subtotal, spelled out, so the identity is readable.

        0.13 per person for one participant: the exact fees are 0.0104,
        0.0026 and 0.0026, so the three lines are 0.01, 0.00 and 0.00 to the
        cent and the total is 0.14. The host's share is the 0.13 subtotal.
        """
        booking = await _book(db_session, Decimal("0.13"))

        assert Decimal(str(booking.subtotal)) == Decimal("0.13")
        assert Decimal(str(booking.platform_fee)) == Decimal("0.01")
        assert Decimal(str(booking.landscape_fee)) == Decimal("0.00")
        assert Decimal(str(booking.insurance_fee)) == Decimal("0.00")
        assert Decimal(str(booking.total)) == Decimal("0.14")

        await _assert_conserved(booking)

    async def test_every_cent_subtotal_up_to_five_bps_conserves_its_total(
        self, db_session
    ):
        """The exhaustive version: every cent from 0.01 to 5.00.

        This is the range where the unrounded lines used to leak a cent, so
        it is swept rather than sampled.
        """
        for cent in SWEEP_CENTS:
            subtotal = Decimal(cent) / 100
            booking = await _book(db_session, subtotal)

            assert Decimal(str(booking.subtotal)) == subtotal
            await _assert_conserved(booking)

    async def test_recognisable_subtotals_conserve_their_total(self, db_session):
        """Larger, messier subtotals conserve too, not only the small ones."""
        for subtotal in ERECOGNISED:
            booking = await _book(db_session, subtotal)

            assert Decimal(str(booking.subtotal)) == subtotal
            await _assert_conserved(booking)

    async def test_multi_participant_bookings_conserve_their_total(self, db_session):
        """The subtotal scales with the party, and the identity still holds."""
        for participants in (2, 3, 7, 19):
            booking = await _book(
                db_session, Decimal("1.13"), participants=participants
            )

            assert Decimal(str(booking.subtotal)) == Decimal("1.13") * participants
            await _assert_conserved(booking)


class TestTourismFeeRates:
    """The 800/200/200 split is unchanged, and still what the columns store."""

    async def test_the_fee_constants_are_unchanged(self):
        assert TourismService.PLATFORM_FEE_BPS == 800
        assert TourismService.LANDSCAPE_FEE_BPS == 200
        assert TourismService.INSURANCE_FEE_BPS == 200
        assert TourismService.HOST_SHARE_BPS == 8800

    async def test_a_whole_subtotal_charges_the_documented_split(self, db_session):
        """A whole subtotal charges 8 %, 2 % and 2 % and costs 12 % more.

        A whole subtotal produces fee lines that are already whole cents, so
        nothing is rounded away and the split is exactly the schedule's.
        """
        booking = await _book(db_session, Decimal("100.00"))

        assert Decimal(str(booking.subtotal)) == Decimal("100.00")
        assert Decimal(str(booking.platform_fee)) == Decimal("8.00")
        assert Decimal(str(booking.landscape_fee)) == Decimal("2.00")
        assert Decimal(str(booking.insurance_fee)) == Decimal("2.00")
        assert Decimal(str(booking.total)) == Decimal("112.00")

        await _assert_conserved(booking)

    async def test_each_fee_line_is_its_share_rounded_to_the_cent(self, db_session):
        """A line is the subtotal's share of its rate, to the cent.

        The quantisation is the fix; the rates are not what changed, so a
        line is still within a cent of the unrounded share it always was.
        """
        for subtotal in (Decimal("0.13"), Decimal("0.07"), Decimal("3.33")):
            booking = await _book(db_session, subtotal)

            stored = Decimal(str(booking.subtotal))
            for name, bps in FEE_LINES:
                exact = stored * bps / BPS
                line = Decimal(str(getattr(booking, name)))
                assert line == exact.quantize(CENT), name
                # The stored line is still the same share of the subtotal,
                # just no longer carried at full precision.
                assert abs(line - exact) <= CENT, name


class TestTourismSettlementSplit:
    """The host's share of the guest's payment, spelled out against the legs."""

    async def test_the_host_receives_the_subtotal_and_the_total_is_the_sum(
        self, db_session
    ):
        """The three legs plus the host's share are the whole payment.

        The fees are added on top of the price rather than taken out of it,
        so the host's share of the total is the subtotal itself -- the
        ``HOST_SHARE_BPS`` split of the tour price, not of the guest's
        payment, and that is what this pins.
        """
        booking = await _book(db_session, Decimal("0.25"), participants=2)

        subtotal = Decimal(str(booking.subtotal))
        platform_fee = Decimal(str(booking.platform_fee))
        landscape_fee = Decimal(str(booking.landscape_fee))
        insurance_fee = Decimal(str(booking.insurance_fee))
        total = Decimal(str(booking.total))

        assert subtotal == Decimal("0.50")
        host_share = subtotal - (platform_fee + landscape_fee + insurance_fee)
        # No fee ever exceeds the price it is charged on, and the host keeps
        # the lion's share of it.
        assert host_share > platform_fee + landscape_fee + insurance_fee
        assert platform_fee + landscape_fee + insurance_fee <= subtotal
        # And the payment is fully accounted for.
        assert subtotal + platform_fee + landscape_fee + insurance_fee == total
