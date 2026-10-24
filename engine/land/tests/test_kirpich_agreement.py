"""P1-5 (bounded) -- one Kirpich implementation, and both paths agree.

``engine/land/drainage.py`` carried a second copy of the Kirpich time-of-
concentration equation with two unit errors: the slope entered as a percent
(``tan(deg) * 100``) where the canonical implementation takes m/m, and the
minute-scale result was labelled hours. For a 1000 m catchment at 1 % the copy
answered 3.98 "hours" where
``engine/hydroma/watershed/calculator.calculate_kirpich_tc`` answers 23.44
minutes (0.39 h) -- the percent-for-m/m substitution alone is worth a factor of
100^-0.385 = 0.098.

The duplicate now delegates to the canonical function; the arithmetic lives in
one place and the wrapper only converts the slope from degrees to m/m and the
result from minutes to hours, so both published callers keep their
``time_of_concentration_hours`` contract.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.watershed.calculator import calculate_kirpich_tc
from engine.land.drainage import (
    DrainageAnalyzer,
    _calculate_time_of_concentration,
    calculate_drainage_metrics,
)

#: A 1000 m flow path on a 1 % catchment.
CANONICAL_LENGTH_M = 1000.0
CANONICAL_SLOPE_M_M = 0.01
#: 0.0195 * 1000^0.77 * 0.01^-0.385 minutes.
CANONICAL_TC_MIN = 23.44415647503955
CELL_SIZE_M = 30.0


def _one_kilometre_accumulation() -> np.ndarray:
    """A D8 accumulation grid whose longest path is exactly 1000 m.

    The wrapper derives ``L = cell_size * sqrt(max_acc) / 2``, so with a 30 m
    cell a max accumulation of 4444.444... gives L = 30 * 66.667 / 2 = 1000 m.
    """
    return np.array([[1.0, 1.0], [40000.0 / 9.0, 1.0]])


def _slope_of(m_per_m: float) -> float:
    """The degree angle whose tangent is ``m_per_m``."""
    return float(np.degrees(np.arctan(m_per_m)))


class TestKirpichSingleImplementation:
    def test_canonical_value_for_1000m_at_1_percent(self) -> None:
        """The canonical path itself: 23.44 minutes for 1000 m at 1 %."""
        got = calculate_kirpich_tc(CANONICAL_LENGTH_M, CANONICAL_SLOPE_M_M)
        assert got == pytest.approx(CANONICAL_TC_MIN, rel=1e-9)

    def test_duplicate_delegates_to_the_canonical_implementation(self) -> None:
        """Both paths must print the same number for the same catchment."""
        hours = _calculate_time_of_concentration(
            _one_kilometre_accumulation(),
            None,
            CELL_SIZE_M,
            _slope_of(CANONICAL_SLOPE_M_M),
        )
        assert hours * 60.0 == pytest.approx(CANONICAL_TC_MIN, rel=1e-9)
        assert hours == pytest.approx(
            calculate_kirpich_tc(CANONICAL_LENGTH_M, CANONICAL_SLOPE_M_M) / 60.0,
            rel=1e-9,
        )

    def test_the_percent_scale_factor_is_what_was_wrong(self) -> None:
        """The old copy answered 3.98 'hours'; the factor it was off by is
        100^-0.385 applied to the slope term. Pinning that factor documents
        the repair rather than silently changing a number."""
        old_wrong = 0.0195 * (CANONICAL_LENGTH_M**0.77) * 1.0  # slope as percent
        assert old_wrong == pytest.approx(3.982, abs=0.01)
        assert CANONICAL_TC_MIN / 60.0 / old_wrong == pytest.approx(
            0.098, rel=0.01
        )

    def test_public_callers_still_report_hours(self) -> None:
        """``calculate_drainage_metrics`` and ``DrainageAnalyzer.analyze`` keep
        their ``time_of_concentration_hours`` field, so no downstream consumer
        sees a unit change."""
        dem = np.zeros((10, 10), dtype=float)
        dem[0, :] = 100.0
        dem[9, :] = 0.0

        metrics = calculate_drainage_metrics(dem, resolution=CELL_SIZE_M)
        analysis = DrainageAnalyzer(resolution=CELL_SIZE_M).analyze(dem, profile_id="k")

        for tc in (
            metrics["time_of_concentration_hours"],
            analysis.time_of_concentration_hours,
        ):
            assert tc is not None
            assert 0.1 <= tc <= 24.0, tc

    def test_steeper_catchment_has_the_smaller_tc(self) -> None:
        """Kirpich is monotone decreasing in slope; the delegation must not
        have inverted it."""
        acc = _one_kilometre_accumulation()
        gentle = _calculate_time_of_concentration(acc, None, CELL_SIZE_M, _slope_of(0.01))
        steep = _calculate_time_of_concentration(acc, None, CELL_SIZE_M, _slope_of(0.05))
        assert steep < gentle

    def test_zero_slope_is_guarded_not_fatal(self) -> None:
        acc = _one_kilometre_accumulation()
        got = _calculate_time_of_concentration(acc, None, CELL_SIZE_M, 0.0)
        assert np.isfinite(got) and got > 0.0
