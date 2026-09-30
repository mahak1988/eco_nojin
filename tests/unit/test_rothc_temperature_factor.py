"""Tests for the RothC-26.3 temperature rate modifier.

The coefficients are pinned to the primary source, not to this repository's
history. Coleman, Prout & Milne (2024), Rothamsted model description section
1.6.1 equation (1):

    RM_Tmp = 47.91 / (1 + e^(106.06 / (T + 18.27)))

Two claims made earlier in this file's history were wrong and are withdrawn here
so they cannot be reintroduced:

* that a reciprocal exponent made the shape invalid. RothC's temperature
  response is intentionally monotonically increasing, with no optimum and no
  supra-optimal decline, so "the shape is wrong" was never a valid objection;
* that the numerator might be a site-dependent ``2C``. It is not: 47.91 is a hard
  constant in the published equation and in the official Fortran, Python and R.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from engine.hydroma.simulation.runners.rothc_runner import (
    TEMP_FACTOR_A,
    TEMP_FACTOR_B,
    TEMP_FACTOR_NUMERATOR,
    TEMP_FACTOR_ZERO_BELOW_C,
    temp_factor,
)


def test_coefficients_match_the_published_equation():
    """47.91 / 106.06 / 18.27, verbatim from section 1.6.1."""
    assert TEMP_FACTOR_NUMERATOR == 47.91
    assert TEMP_FACTOR_A == 106.06
    assert TEMP_FACTOR_B == 18.27
    assert TEMP_FACTOR_ZERO_BELOW_C == -5.0


@pytest.mark.parametrize(
    ("t", "expected"),
    [
        (-5.0, 0.0162),
        (-4.99, 0.0163),
        (0.0, 0.1439),
        (5.0, 0.4971),
        (9.291, 1.0000),
        (10.0, 1.0987),
        (15.0, 1.8979),
        (20.0, 2.8215),
        (25.0, 3.8019),
        (30.0, 4.7910),
    ],
)
def test_values_against_the_published_coefficients(t: float, expected: float):
    got = temp_factor(t)

    assert got == pytest.approx(expected, rel=2e-3), f"T={t}: {got} vs {expected}"


def test_the_numerator_normalises_to_one_at_the_rothamsted_mean():
    """47.91 exists so that RM_Tmp = 1.0 at the Rothamsted mean annual temperature.

    Figure 2 of the model description marks that point, and it is the only
    normalisation in the model.
    """
    # 47.91 / (1 + e^(a/(t+b))) = 1  =>  e^(a/(t+b)) = 46.91  =>  t = a/ln(46.91) - b
    t_star = TEMP_FACTOR_A / np.log(TEMP_FACTOR_NUMERATOR - 1.0) - TEMP_FACTOR_B
    assert t_star == pytest.approx(9.291, abs=5e-3)

    assert temp_factor(float(t_star)) == pytest.approx(1.0, rel=1e-9)


def test_monotonically_increasing_with_no_optimum():
    """RothC has no supra-optimal decline. Assert the increase so the shape is pinned."""
    temps = np.arange(-5.0, 40.1, 0.5)
    vals = [temp_factor(float(t)) for t in temps]

    for prev, nxt in itertools.pairwise(vals):
        assert nxt > prev, "the response must be increasing; RothC has no optimum"


def test_exceeding_one_is_correct_not_a_defect():
    """The factor multiplies the rate constant k and is not normalised to a maximum."""
    assert temp_factor(20.0) > 1.0
    assert temp_factor(30.0) > temp_factor(20.0) > temp_factor(10.0)


def test_below_minus_five_is_zeroed_as_the_official_code_does():
    """RothC_Code hard-zeros below -5 C; it does not raise and it does not extrapolate."""
    assert temp_factor(-5.0001) == 0.0
    assert temp_factor(-10.0) == 0.0
    assert temp_factor(-40.0) == 0.0


def test_frozen_soil_stops_decomposition_rather_than_raising():
    """Regression: the previous version raised at -18.3 C, which the model does not do."""
    assert temp_factor(-18.3) == 0.0
    assert temp_factor(-18.27) == 0.0
    assert temp_factor(-100.0) == 0.0


def test_no_singularity_in_the_evaluated_range():
    """The pole at T = -18.27 C must never be reached."""
    for t in np.arange(TEMP_FACTOR_ZERO_BELOW_C, 60.0, 0.25):
        v = temp_factor(float(t))
        assert np.isfinite(v)
        assert v >= 0.0


def test_matches_a_direct_evaluation_of_the_published_equation():
    for t in (-4.9, 0.0, 12.3, 20.0, 33.0):
        expected = 47.91 / (1.0 + np.exp(106.06 / (t + 18.27)))
        assert temp_factor(t) == pytest.approx(expected, rel=1e-12)


def test_the_withdrawn_objections_stay_withdrawn():
    """The docstring must not reassert either retracted claim."""
    import inspect

    doc = inspect.getdoc(temp_factor) or ""

    assert "withdrawn" in doc.lower()
    assert "no optimum" in doc.lower(), "the monotonic-no-optimum shape must be stated"
    assert "increasing" in doc.lower()
    # The site-dependent-constant question is settled, so it must not be listed
    # as an open question any more.
    assert "cannot be settled" not in doc
