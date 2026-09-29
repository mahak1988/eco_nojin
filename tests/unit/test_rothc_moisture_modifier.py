"""Regression tests for the RothC moisture rate modifier.

``water_factor`` is the shared root of ``run_rothc`` and the ECSI model, so a
defect here reached both. The two segments were computed independently, and at the
breakpoint the lower branch returned 0.6448 while the upper branch returned 0.3597
for the same soil moisture: the modifier fell by 0.285 as the soil dried, which
is a non-monotonic response over the range the modifier spends most of its time
in. A pixel or a month straddling the breakpoint decomposed at a materially
different rate.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.simulation.runners.rothc_runner import (
    _MOISTURE_BREAKPOINT,
    _MOISTURE_FLOOR,
    water_factor,
)

MAX_SMD = 60.0
BREAKPOINT_MM = _MOISTURE_BREAKPOINT * MAX_SMD


def test_no_discontinuity_at_the_breakpoint():
    """The regression: a 0.285 downward jump as the soil dried."""
    before = water_factor(BREAKPOINT_MM - 1e-9, MAX_SMD)
    after = water_factor(BREAKPOINT_MM + 1e-9, MAX_SMD)

    assert abs(after - before) < 1e-6, (
        f"discontinuity at the breakpoint: {before:.6f} -> {after:.6f}"
    )


def test_monotonically_decreasing_across_the_whole_range():
    """A drying soil must never speed decomposition up."""
    smd = np.linspace(0.0, MAX_SMD, 2001)
    values = [water_factor(float(s), MAX_SMD) for s in smd]

    for prev, nxt in zip(values, values[1:]):
        assert nxt <= prev + 1e-12, f"moisture modifier increased while drying: {prev} -> {nxt}"


def test_endpoints():
    assert water_factor(0.0, MAX_SMD) == pytest.approx(1.0)
    assert water_factor(MAX_SMD, MAX_SMD) == pytest.approx(_MOISTURE_FLOOR)


def test_bounded_in_the_documented_range():
    for s in (0.0, 1.0, 13.0, BREAKPOINT_MM, 45.0, 60.0, 200.0):
        v = water_factor(s, MAX_SMD)
        assert _MOISTURE_FLOOR - 1e-12 <= v <= 1.0 + 1e-12


def test_stays_continuous_for_several_max_deficits():
    for max_smd in (10.0, 30.0, 60.0, 120.0):
        bp = _MOISTURE_BREAKPOINT * max_smd
        before = water_factor(bp - 1e-9, max_smd)
        after = water_factor(bp + 1e-9, max_smd)
        assert abs(after - before) < 1e-6, f"discontinuity at max_smd={max_smd}"


def test_negative_deficit_is_clamped_not_extrapolated():
    assert water_factor(-10.0, MAX_SMD) == pytest.approx(1.0)


def test_deficit_beyond_maximum_is_clamped():
    assert water_factor(500.0, MAX_SMD) == pytest.approx(_MOISTURE_FLOOR)


def test_zero_max_smd_returns_one():
    assert water_factor(5.0, 0.0) == 1.0
    assert water_factor(0.0, 0.0) == 1.0


def test_both_branches_ordered():
    """The pre-existing ordering assertion still holds."""
    w1 = water_factor(10.0, MAX_SMD)
    w2 = water_factor(40.0, MAX_SMD)

    assert 0.0 <= w2 < w1 <= 1.0


def test_joins_the_two_segments_at_the_breakpoint():
    """A small step either side of the join changes the value by < 1%."""
    step = 0.5
    left = water_factor(BREAKPOINT_MM - step, MAX_SMD)
    right = water_factor(BREAKPOINT_MM + step, MAX_SMD)
    base = water_factor(BREAKPOINT_MM, MAX_SMD)

    assert abs(left - base) < 0.01
    assert abs(right - base) < 0.01
