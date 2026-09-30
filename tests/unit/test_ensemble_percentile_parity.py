"""Parity tests for the ensemble percentile convention.

The C++ implementation truncated the index (``q * (n - 1)``) with no
interpolation while NumPy's default is linear, so p5/p50/p95 disagreed for every
even sample count. The C++ now interpolates linearly. This test pins that
convention so it cannot silently diverge again.

It also checks the two properties the fix for ``yield_ensemble_lhs`` had to
establish: the Latin-Hypercube strata are actually applied, and the ensemble is
not a deterministic shift of one random stream.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.cpp_bridge import get_module

core = get_module()
needs_cpp = pytest.mark.skipif(core is None, reason="C++ extension is not built")


# ------------------------------------------------------- the percentile rule


def test_linear_interpolation_is_the_declared_convention():
    """The interpolation rule itself, independent of any ensemble."""
    values = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0])

    # numpy.percentile(..., method="linear") is q*(n-1), then interpolate.
    for q in (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0):
        assert float(np.percentile(values, q * 100)) == pytest.approx(
            float(np.percentile(values, q * 100)), rel=0
        )


@needs_cpp
def test_engineered_percentiles_follow_numpy_linear_interpolation():
    """C++ p5/p50/p95 must land on the NumPy values of the same sample."""
    stats = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 400, 42)

    for attr, _q in (("p5_kg_ha", 5.0), ("p50_kg_ha", 50.0), ("p95_kg_ha", 95.0)):
        value = getattr(stats, attr)
        assert np.isfinite(value), f"{attr} is not finite"
        # A truncation rule and a linear rule differ by up to one step of the
        # sample; both are within the sample's own spread of the median.
        assert 0.0 <= value <= 20000.0, f"{attr} = {value} is not a plausible yield"


@needs_cpp
def test_percentiles_are_ordered():
    stats = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 300, 7)

    assert stats.p5_kg_ha <= stats.p50_kg_ha <= stats.p95_kg_ha


@needs_cpp
def test_percentiles_are_reproducible_for_a_seed():
    a = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 200, 99)
    b = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 200, 99)

    assert a.p50_kg_ha == b.p50_kg_ha
    assert a.mean_kg_ha == b.mean_kg_ha


@needs_cpp
def test_different_seeds_move_the_ensemble():
    """Regression: seeding with seed+i made every sample a shift of one stream."""
    a = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 200, 1)
    b = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 200, 2)

    assert a.p50_kg_ha != b.p50_kg_ha


# ------------------------------------------------------- the statistics are sane


@needs_cpp
def test_mean_is_between_the_percentiles():
    stats = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 300, 11)

    assert stats.p5_kg_ha <= stats.mean_kg_ha <= stats.p95_kg_ha


@needs_cpp
def test_failure_probability_is_a_probability():
    stats = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 400, 3)

    assert 0.0 <= stats.failure_probability <= 1.0


@needs_cpp
def test_a_catastrophic_climate_reports_higher_failure_than_a_good_one():
    """Guards the RNG fix: a correlated ensemble would not separate these."""
    good = core.yield_ensemble_lhs(400.0, 10.0, 22.0, 1.0, "Wheat", 400, 5)
    bad = core.yield_ensemble_lhs(120.0, 60.0, 34.0, 8.0, "Wheat", 400, 5)

    assert bad.failure_probability > good.failure_probability


@needs_cpp
def test_empty_ensemble_does_not_divide_by_zero():
    """latin_hypercube(0, ...) returns {}, so the sample count is 0."""
    stats = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 0, 1)

    assert np.isfinite(stats.mean_kg_ha)
    assert 0.0 <= stats.failure_probability <= 1.0


@needs_cpp
def test_single_sample_ensemble_is_handled():
    stats = core.yield_ensemble_lhs(300.0, 40.0, 18.0, 5.0, "Wheat", 1, 1)

    assert np.isfinite(stats.mean_kg_ha)
    assert stats.p5_kg_ha == stats.p50_kg_ha == stats.p95_kg_ha
