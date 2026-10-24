"""Revenue indicators, derived from the code rather than asserted about it.

Added 2026-10-03. There is no revenue reporting anywhere in this repository, so
the first question -- "what does the platform earn" -- has no answer that can be
regenerated. This module computes the answers from the fee schedules that
actually exist, and every function here is pure: no database, no network.

The figures it produces:

    COMMERCE_COMMISSION_BPS   400   goods: 300 platform + 100 landscape
    TOURISM_COMMISSION_BPS   1200   stays: 800 platform + 200 landscape + 200 insurance
    TOURISM_HOST_SHARE_BPS   8800

The nominal rates are what the schedules declare. ``realised_bps`` is what a
particular order actually pays, and on cent-granular orders the measured band
depends on the schedule, so no single band describes both: the commerce
schedule measures 0-600 bps (the maximum on a 0.50 subtotal, where 0.015
platform + 0.005 landscape, rounded half up, collects 0.03 on 0.50), and the
tourism schedule measures 0-1600 bps (the maximum on a 0.25 subtotal, where
each of its three half-cent lines rounds up to 0.01, collecting 0.04 on 0.25).
Both bands are re-derived from these functions by
``tests/test_take_rate_band_correction.py`` on every run, so the figures here
cannot drift from the arithmetic. Revenue projections must use ``realised_bps``
for their own schedule, or state their rounding assumption.

Not a take rate: ``MAX_DISCOUNT_BPS`` below carries a 20000 bps figure in its
measurement table. That one is a *discount requested* -- 200 % of the platform
line, probed with the clamp removed -- not a fee rate any order collects.

Added 2026-10-03, the same day: the discounted path. ``redemption.py:69`` sells
``MARKET_FEE_DISCOUNT`` for 50 ECO promising "50% reduction of our own
marketplace commission, 5 listings", and nothing in the repository reads it --
``tests/unit/test_market_fee_discount_gap.py`` pins that with a strict xfail.
This module supplies the arithmetic a future wiring would call. It does not wire
it, and it deliberately contains no database, model, order column or redemption
call, so the xfail stays strict.

Two decisions in here are decisions, not consequences, and both are named
constants rather than hidden assumptions:

* **The discount reaches the platform line only.**
  ``DISCOUNT_COVERS_LANDSCAPE_FEE = False``. See its own comment for the
  evidence.
* **The discount is clamped to 0..100 %.** ``MAX_DISCOUNT_BPS``. See its own
  comment for the measurement that makes the clamp load-bearing.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
BPS = Decimal("10000")
ZERO_CENT = Decimal("0.00")

#: The rounding the services actually charge in. ``Decimal.quantize`` takes
#: ``rounding=ROUND_HALF_EVEN`` by default, and neither ``commerce`` nor
#: ``marketplace`` passes the argument, so the money is banker's-rounded.
#:
#: This is NOT the mode the module-level ``realised_bps`` uses -- that one passes
#: ``ROUND_HALF_UP`` explicitly, because a rate quoted in basis points should
#: round away from zero. The two disagree on 50 of 4999 cent-subtotals (25 of
#: them on the landscape fee alone: at subtotal 0.50 the raw fee is exactly
#: 0.005, which is a tie the service rounds to 0.00 and the other mode rounds
#: to 0.01). Both are pinned in ``tests/unit/test_revenue_indicators.py``; the
#: divergence is recorded, not fixed, for the reason in
#: ``tests/unit/test_take_rate.py``: switching the service's rounding moves real
#: money and belongs to whoever owns the fee schedule.
SERVICE_ROUNDING = ROUND_HALF_EVEN

#: Hard ceiling on a discount: 100 % of the platform line. Load-bearing, not
#: decorative. Measured 2026-10-03 with the clamp removed, over every cent from
#: 0.01 to 49.99:
#:
#:     discount_bps    platform fee goes negative on    most negative
#:            10000                             0 of 4999            0.00
#:            20000                        4983 of 4999           -1.50
#:            25000                        4983 of 4999           -2.25
#:           999999                        4983 of 4999         -148.50
#:
#: At a subtotal of 100.00 an unclamped 25000 bps gives a platform fee of -4.50,
#: i.e. a "discount" that pays the seller 4.50 and books negative revenue. A
#: discount above 100 % is not a bigger discount, it is a sign error, so it is
#: clamped rather than honoured. Values below zero are clamped for the mirror
#: reason: at -500 bps on 100.00 an unclamped fee is 3.15, so a negative discount
#: *surcharges* the buyer 0.15.
MAX_DISCOUNT_BPS = Decimal("10000")

#: Whether the fee discount reaches the landscape line. Measured reading: **no**,
#: and the wording is the evidence rather than the code.
#:
#: ``redemption.py:81`` promises "50% reduction of our own marketplace
#: commission". ``redemption.py:75`` narrows it to commissions "collected by the
#: platform itself". Those two agree on the platform line and are silent on the
#: landscape line, so the reading is a choice. It is made this way:
#:
#: 1. The landscape line is not a commission. It is a per-village restoration
#:    charge: ``LandscapeFund`` (``services/landscape/models/__init__.py:72``)
#:    carries ``fee_bps = 100``, the same 100 bps, one fund per ``village_id``,
#:    and ``LandscapeFundDistribution`` spends it. Discounting a restoration
#:    charge to sell a marketplace commission would under-fund a village.
#: 2. The two lines are separate on the order. ``ComOrder`` has distinct
#:    ``platform_fee`` and ``landscape_fee`` columns and ``ComSettlement``
#:    mirrors them, so "the commission" is addressable as one of them.
#: 3. Cash-wise the two are now separable, which is what makes booking the
#:    waiver against one line possible: ``commerce/service.py:settle_order``
#:    credits ``platform_fee + landscape_fee`` to ``ECO_PLATFORM_REVENUE``
#:    and then credits the order's ``landscape_fee`` to the village's
#:    ``LandscapeFund`` (``OrderService._credit_landscape_fund``), so each
#:    line has an auditable destination. Before 2026-10-10 nothing credited
#:    ``LandscapeFund`` from a commerce settlement and the two were
#:    indistinguishable in cash; a waiver aimed at "our own commission" must
#:    still be *booked* against a specific line or it cannot be reconciled.
#:
#: Changing this constant is a fee-schedule decision. It changes what the buyer
#: pays, and the test that pins it says so.
DISCOUNT_COVERS_LANDSCAPE_FEE = False


def _schedule(platform: Decimal, landscape: Decimal, *extra: Decimal) -> dict[str, Decimal]:
    fees = {"platform": platform, "landscape": landscape}
    for i, e in enumerate(extra):
        fees[f"extra_{i + 1}"] = e
    fees["commission_bps"] = sum(fees.values())
    return fees


def commerce_schedule() -> dict[str, Decimal]:
    """The goods marketplace. 400 bps nominal."""
    from services.commerce.service import OrderService

    return _schedule(OrderService.PLATFORM_FEE_BPS, OrderService.LANDSCAPE_FEE_BPS)


def tourism_schedule() -> dict[str, Decimal]:
    """Stays and bookings. 1200 bps nominal, of which 200 is insurance."""
    from services.tourism.service import TourismService

    return _schedule(
        TourismService.PLATFORM_FEE_BPS,
        TourismService.LANDSCAPE_FEE_BPS,
        TourismService.INSURANCE_FEE_BPS,
    )


def realised_bps(subtotal: Decimal, schedule: dict[str, Decimal]) -> Decimal:
    """The take rate actually collected on ``subtotal``, in basis points.

    Mirrors the services: each fee is quantised to the cent independently and
    then summed, so the realised rate is not ``commission_bps``.
    """
    if subtotal <= 0:
        return Decimal("0")
    collected = sum(
        (subtotal * bps / BPS).quantize(CENT, rounding=ROUND_HALF_UP)
        for name, bps in schedule.items()
        if name != "commission_bps"
    )
    return (collected / subtotal * BPS).quantize(Decimal("1"))


def projected_revenue(gross: Decimal, schedule: dict[str, Decimal]) -> dict[str, Decimal]:
    """Platform revenue on ``gross`` of merchandise value.

    Returns both the nominal and the realised figure so a caller cannot quote the
    nominal one by accident.
    """
    nominal = (gross * schedule["commission_bps"] / BPS).quantize(CENT, rounding=ROUND_HALF_UP)
    realised = gross * realised_bps(gross, schedule) / BPS
    return {
        "gross": gross,
        "nominal_commission": nominal,
        "realised_commission": realised.quantize(CENT, rounding=ROUND_HALF_UP),
        "nominal_bps": schedule["commission_bps"],
        "realised_bps": realised_bps(gross, schedule),
        "rounding_drift": (nominal - realised).quantize(CENT, rounding=ROUND_HALF_UP),
    }


def seller_payout(gross: Decimal, schedule: dict[str, Decimal]) -> Decimal:
    """What the seller receives: the subtotal, since fees are added on top.

    The services add fees to the subtotal rather than deducting them from it --
    ``commerce/service.py`` computes ``total = subtotal + platform_fee +
    landscape_fee`` -- so the seller is not exposed to the commission. This
    function makes that explicit, because "seller gets X minus fees" is the
    natural assumption and it is not what happens.
    """
    return gross


# --------------------------------------------------------------------------
# The discounted path. Pure arithmetic, called by nothing.
# --------------------------------------------------------------------------


def clamped_discount_bps(discount_bps: Decimal) -> Decimal:
    """``discount_bps`` restricted to ``0 .. MAX_DISCOUNT_BPS``.

    Named separately from ``discounted_fees`` so a caller that wants to report
    "this holder was offered 300 % and got 100 %" can, and so the clamp is
    inspectable on its own.
    """
    if discount_bps < 0:
        return Decimal("0")
    if discount_bps > MAX_DISCOUNT_BPS:
        return MAX_DISCOUNT_BPS
    return discount_bps


def _charged_lines(subtotal: Decimal, schedule: dict[str, Decimal]) -> dict[str, Decimal]:
    """The cents each schedule line charges, in the service's own rounding.

    ``OrderService._compute_fees`` calls ``quantize(CENT)`` with no ``rounding``
    argument, which is ``ROUND_HALF_EVEN``. Reproducing that exactly is the point:
    ``platform_before`` below is the number the buyer is actually charged, not a
    model of it. ``tests/unit/test_revenue_indicators.py`` asserts this against
    ``OrderService._compute_fees`` directly.
    """
    if subtotal <= 0:
        return {name: ZERO_CENT for name in schedule if name != "commission_bps"}
    return {
        name: (subtotal * bps / BPS).quantize(CENT, rounding=SERVICE_ROUNDING)
        for name, bps in schedule.items()
        if name != "commission_bps"
    }


#: Which single schedule line ``discount_bps`` reduces. Derived from
#: :data:`DISCOUNT_COVERS_LANDSCAPE_FEE` so there is one decision and one
#: consequence, not a boolean that some other code is free to ignore.
DISCOUNTED_FEE_LINE = "landscape" if DISCOUNT_COVERS_LANDSCAPE_FEE else "platform"


def discounted_fees(
    subtotal: Decimal,
    schedule: dict[str, Decimal],
    discount_bps: Decimal,
) -> dict[str, Decimal]:
    """Fees on ``subtotal`` with ``discount_bps`` off :data:`DISCOUNTED_FEE_LINE`.

    Every value is a ``Decimal``. The order of operations is deliberate and
    load-bearing:

    1. Charge the schedule as the service does, cent by cent. Those are the
       ``*_before`` figures -- the money that would have been collected.
    2. Waive ``discount_bps`` of the discounted line, then quantise the waiver to
       the cent.
    3. Subtract it. Every other line passes through untouched.

    The alternative -- re-deriving the fee at a reduced *rate* and quantising
    once -- is not the same function. Measured 2026-10-03 at a 50 % discount the
    two disagree on **1250 of 4999** cent-subtotals, because they round different
    quantities. This form is chosen so the invariant

        sum(every fee line after) + waived == sum(every fee line before)

    holds exactly: measured on all 4999 cents for every discount from 0 to 10000
    bps in steps of 125, zero exceptions. That is what makes ``waived`` a number
    in its own right rather than the residue of two roundings.

    Clamping, in two layers, both measured:

    * ``discount_bps`` is clamped by :func:`clamped_discount_bps`. This is the
      layer that matters: unclamped, a 25000 bps discount drives the fee to -4.50
      on a 100.00 order and 4983 of 4999 cent-subtotals go negative.
    * The discounted line is floored at zero as well. For any
      ``discount_bps <= MAX_DISCOUNT_BPS`` that floor cannot bind -- the waiver is
      a share of a cent-quantised fee at no more than 100 %, so it can at most
      equal it -- but it is cheap, and it makes "no fee line is negative" a
      property of this function rather than a proof about its caller.

    Extra schedule lines (``tourism``'s 200 bps insurance) pass through
    untouched: the discount names one line, and a discount on a fee nobody reads
    cannot be reconciled against anything.
    """
    lines = _charged_lines(subtotal, schedule)
    target = DISCOUNTED_FEE_LINE if DISCOUNTED_FEE_LINE in lines else "platform"
    target_before = lines.get(target, ZERO_CENT)
    applied = clamped_discount_bps(discount_bps)

    waived = (target_before * applied / BPS).quantize(CENT, rounding=SERVICE_ROUNDING)
    target_after = target_before - waived
    if target_after < ZERO_CENT:
        target_after = ZERO_CENT

    result: dict[str, Decimal] = {
        "subtotal": subtotal,
        "total_before": sum(lines.values(), ZERO_CENT),
        "waived": waived,
    }
    total = subtotal
    for name, amount in lines.items():
        after = target_after if name == target else amount
        result[f"{name}_before"] = amount
        result[f"{name}_after"] = after
        total += after
    result["total"] = total
    result["realised_bps"] = (
        Decimal("0")
        if total == subtotal
        else ((total - subtotal) / subtotal * BPS).quantize(Decimal("1"))
    )
    result["discount_bps_requested"] = discount_bps
    result["discount_bps_applied"] = applied
    return result


#: ``discounted_fees`` returns every fee line twice, as ``<line>_before`` and
#: ``<line>_after``. This is the naming convention, named so that summing the
#: lines -- as :func:`discounted_revenue` does -- cannot quietly pick up the
#: subtotal, the rate or the waiver along with them.
_FEE_LINE_SUFFIXES = ("_before", "_after")


def discounted_revenue(
    subtotal: Decimal,
    schedule: dict[str, Decimal],
    discount_bps: Decimal,
) -> dict[str, Decimal]:
    """What a discounted order earns, and what it does not.

    Two figures, kept apart on purpose:

    ``collected_commission``
        Cash the platform keeps on this order: every fee line after the
        discount. This is revenue.
    ``foregone_commission``
        The waiver. Revenue the platform would have had and does not. It is not
        revenue, not a cost, and not a second revenue line.

    **They must never be added together.** Their sum is the pre-discount fee,
    which no order ever pays. Measured 2026-10-03 by summing every cent from 0.01
    to 49.99 at a 50 % discount: the platform line alone is 3749.25 before, of
    which 1874.79 is collected and 1874.46 is foregone; all fee lines together
    are 4999.00 before, 3124.54 collected. At a 100 % discount the platform
    collects 0.00 and waives the whole 3749.25, so the sum is fixed while the
    revenue is not. This function therefore returns no key holding that sum, and
    ``test_the_waiver_is_not_offered_as_a_second_revenue_line`` pins the key set
    so one cannot be added later by accident.

    The waiver is also not cash in the holder's hands. The holder paid 50 ECO
    (``redemption.py:71``) for the discount; the waiver is denominated in the
    order's currency. There is no ECO-to-currency rate anywhere in
    ``services/ecowallet`` -- searched for one on 2026-10-03 (``eco_rate``,
    ``eco_price``, ``IRR_PER_ECO``, ``conversion``) and found nothing -- so the
    two cannot be summed even in principle, and a report that tried would be
    inventing a rate.
    """
    fees = discounted_fees(subtotal, schedule, discount_bps)
    collected = sum(
        (amount for name, amount in fees.items() if name.endswith(_FEE_LINE_SUFFIXES[1])),
        ZERO_CENT,
    )
    return {
        "gross": subtotal,
        "collected_commission": collected,
        "collected_bps": fees["realised_bps"],
        "foregone_commission": fees["waived"],
        "foregone_bps": (
            Decimal("0")
            if subtotal <= 0
            else (fees["waived"] / subtotal * BPS).quantize(Decimal("1"))
        ),
        "discount_bps_applied": fees["discount_bps_applied"],
    }
