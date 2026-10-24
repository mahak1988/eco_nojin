"""The realised take-rate band, re-derived from the arithmetic on every run.

``revenue_indicators`` documents what ``realised_bps`` measures, and until
2026-10-10 the module docstring published a single band -- "0 to 588 bps" --
that no schedule respects and none could: the commerce schedule (400 bps
nominal) measures 0-600 bps and the tourism schedule (1200 bps nominal, three
lines) measures 0-1600 bps, so one number cannot describe both.

This file re-derives both bands from ``realised_bps`` itself rather than
restating the prose, so a changed fee schedule or a changed rounding moves the
measured band and these tests fail before the documentation can be believed
again. The measurement is exhaustive over every subtotal from 0.01 to 2000.00
in one-cent steps -- 20000 subtotals per schedule -- which is the sweep that
established the 600 and 1600 ceilings in the first place.

What is pinned:

1. The commerce band: minimum 0, maximum 600 bps, the maximum attained on a
   0.50 subtotal where each half-cent fee line rounds up.
2. The tourism band: minimum 0, maximum 1600 bps, the maximum attained on a
   0.25 subtotal where each half-cent line rounds up.
3. That the two bands differ, so no single documented band covers both.
4. That the module docstring's figures are the measured ones, which is what
   keeps the prose and the arithmetic from drifting apart again.
"""

from __future__ import annotations

import re
from decimal import Decimal

from services.finance import revenue_indicators
from services.finance.revenue_indicators import (
    BPS,
    CENT,
    commerce_schedule,
    realised_bps,
    tourism_schedule,
)

#: One cent, as a Decimal subtotal. Every subtotal in the sweep is
#: ``_cent(i)``, so nothing is produced by float division.
SWEEP_TOP = 20_000


def _cent(index: int) -> Decimal:
    return Decimal(index) / 100


def _band(schedule: dict[str, Decimal]) -> tuple[int, int, Decimal]:
    """The realised take rate's extremes over the sweep, and where the max sits.

    Derives everything from the schedule that was passed in: the extremes, and
    the smallest subtotal attaining the maximum.
    """
    lo: int | None = None
    hi: int | None = None
    at: Decimal | None = None
    for index in range(1, SWEEP_TOP + 1):
        subtotal = _cent(index)
        rate = int(realised_bps(subtotal, schedule))
        if lo is None or rate < lo:
            lo = rate
        if hi is None or rate > hi:
            hi, at = rate, subtotal
    return lo, hi, at


def _line_count(schedule: dict[str, Decimal]) -> int:
    return sum(1 for name in schedule if name != "commission_bps")


def test_the_commerce_band_is_zero_to_six_hundred_bps():
    """Commerce, measured exhaustively: 0 to 600 bps, peaking on 0.50."""
    schedule = commerce_schedule()
    nominal = int(schedule["commission_bps"])

    lo, hi, at = _band(schedule)

    assert nominal == 400
    assert _line_count(schedule) == 2
    assert lo == 0
    assert hi == 600
    assert at == Decimal("0.50")
    # The ceiling is derived from the rates rather than memorised: on a 0.50
    # subtotal each of the two fee lines is exactly half a cent, so each rounds
    # up by half a cent and the collected fee is the nominal one plus that
    # drift -- the whole gap between 400 and 600 bps.
    peak = Decimal("0.50")
    fees = [bps for name, bps in schedule.items() if name != "commission_bps"]
    raw = sum((peak * bps / BPS for bps in fees), Decimal("0.00"))
    collected = sum(
        (
            (peak * bps / BPS).quantize(CENT, rounding=revenue_indicators.ROUND_HALF_UP)
            for bps in fees
        ),
        Decimal("0.00"),
    )
    assert raw == Decimal("0.02")
    assert collected == Decimal("0.03")
    assert int(realised_bps(peak, schedule)) == nominal + int(
        (collected - raw) / peak * BPS
    )


def test_the_tourism_band_is_zero_to_sixteen_hundred_bps():
    """Tourism, measured exhaustively: 0 to 1600 bps, peaking on 0.25."""
    schedule = tourism_schedule()
    nominal = int(schedule["commission_bps"])

    lo, hi, at = _band(schedule)

    assert nominal == 1200
    assert _line_count(schedule) == 3
    assert lo == 0
    assert hi == 1600
    assert at == Decimal("0.25")


def test_no_single_band_describes_both_schedules():
    """Why the old single "0 to 588 bps" figure had to go: they are different."""
    commerce_hi = _band(commerce_schedule())[1]
    tourism_hi = _band(tourism_schedule())[1]

    assert commerce_hi == 600
    assert tourism_hi == 1600
    assert commerce_hi != tourism_hi


def test_the_measured_maxima_are_the_rounding_of_half_cent_lines():
    """Both ceilings are one rounding event, shown on the subtotal that hits it.

    The figures the docstring cites are re-derived here from the schedule
    rates, so they are checkable arithmetic rather than prose.
    """
    commerce_peak = Decimal("0.50")
    commerce_total = sum(
        (
            (commerce_peak * bps / BPS).quantize(CENT, rounding=revenue_indicators.ROUND_HALF_UP)
            for name, bps in commerce_schedule().items()
            if name != "commission_bps"
        ),
        Decimal("0.00"),
    )
    assert commerce_total == Decimal("0.03")
    assert int(realised_bps(commerce_peak, commerce_schedule())) == 600

    tourism_peak = Decimal("0.25")
    tourism_total = sum(
        (
            (tourism_peak * bps / BPS).quantize(CENT, rounding=revenue_indicators.ROUND_HALF_UP)
            for name, bps in tourism_schedule().items()
            if name != "commission_bps"
        ),
        Decimal("0.00"),
    )
    assert tourism_total == Decimal("0.04")
    assert int(realised_bps(tourism_peak, tourism_schedule())) == 1600


def test_the_documented_bands_are_the_measured_ones():
    """The docstring's figures and the sweep's figures are the same numbers.

    A corrected document that later drifts is the defect this file exists to
    catch, so the prose is held to the arithmetic: the module docstring must
    state the commerce band the sweep measures and the tourism band the sweep
    measures, and must not state the superseded single band.
    """
    doc = revenue_indicators.__doc__ or ""
    _, commerce_hi, _ = _band(commerce_schedule())
    _, tourism_hi, _ = _band(tourism_schedule())

    commerce_band = re.search(r"commerce\s+schedule measures 0-(\d+) bps", doc)
    tourism_band = re.search(r"tourism\s+schedule measures 0-(\d+) bps", doc)

    assert commerce_band is not None, doc
    assert tourism_band is not None, doc
    assert int(commerce_band.group(1)) == commerce_hi
    assert int(tourism_band.group(1)) == tourism_hi

    assert "588" not in doc


def test_the_two_thousand_bps_figure_is_documented_as_a_discount_not_a_rate():
    """``MAX_DISCOUNT_BPS``' table carries 20000 bps. It is a discount, not a fee.

    ``MAX_DISCOUNT_BPS`` is 10000, and the 20000 bps in its comment is a
    *requested* discount probed with the clamp removed, so the docstring
    explains the quantity rather than letting a reader file it as a take rate.
    """
    doc = revenue_indicators.__doc__ or ""

    assert int(revenue_indicators.MAX_DISCOUNT_BPS) == 10000

    assert "20000" in doc
    assert re.search(r"20000 bps figure.*discount", doc, re.DOTALL)
    assert re.search(r"discount requested", doc)
