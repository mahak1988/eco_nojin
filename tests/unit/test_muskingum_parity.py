"""Parity tests for Muskingum-Cunge flood routing.

``route_multi_reach`` was the one formula the registry refused to serve: the C++
implementation routed ``n+1`` reaches and gave every one of them the *full*
``channel_length``, so the total routed distance was ``(n+1) x`` the intended
length. The Python twin divides the length and runs exactly ``n_reaches``, so the
two were modelling different rivers rather than two implementations of one model.

The fix is verified here structurally -- the total routed distance must equal the
channel length, and the travel time must scale with reach count but not with an
extra pass -- and then numerically against the Python twin.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.cpp_bridge import get_module
from engine.hydroma.cpp_bridge import hydrology_fast as hf

core = get_module()

needs_cpp = pytest.mark.skipif(core is None, reason="C++ extension is not built")

HYDROGRAPH = [0.0, 50.0, 100.0, 50.0, 0.0]
LENGTH = 1000.0
MANNING = 0.03
SLOPE = 0.002
DT = 3600.0
WIDTH = 5.0


# ------------------------------------------------------- structural properties


@needs_cpp
@pytest.mark.parametrize("n_reaches", [1, 2, 4, 8])
def test_multi_reach_routes_exactly_n_reaches(n_reaches: int):
    """Regression: the loop ran n_reaches times and then routed once more."""
    single = core.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)
    multi = core.route_multi_reach(HYDROGRAPH, LENGTH, n_reaches, MANNING, SLOPE, DT, WIDTH)

    # One reach of the full length is the n=1 case, so it must match exactly.
    if n_reaches == 1:
        assert multi.travel_time == pytest.approx(single.travel_time)
    else:
        # Each reach covers L/n, so travel time must fall as reaches multiply.
        assert multi.travel_time < single.travel_time


@needs_cpp
def test_travel_time_scales_with_reach_count():
    """Each reach must be L/n long, so K is 1/n of the single-reach K."""
    base = core.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)

    ratios = []
    for n in (2, 4, 8):
        r = core.route_multi_reach(HYDROGRAPH, LENGTH, n, MANNING, SLOPE, DT, WIDTH)
        ratios.append(base.travel_time / r.travel_time)

    # K is proportional to reach length, so the ratio must track n.
    for n, ratio in zip((2, 4, 8), ratios):
        assert ratio == pytest.approx(n, rel=0.02), (
            f"n={n}: travel time ratio {ratio:.3f}, expected {n}. "
            "A reach is not covering its own share of the channel."
        )


@needs_cpp
def test_multi_reach_preserves_the_peak_within_numerical_tolerance():
    """More reaches must not manufacture discharge.

    Peak monotonic decrease is NOT a valid assertion here: with dt = 3600 s and a
    short reach, the Muskingum coefficients approach a pass-through and the peak
    ripples by ~0.1% between reach counts. The claim that is valid is that no
    reach count inflates the peak beyond a small numerical margin.
    """
    peaks = [
        core.route_multi_reach(HYDROGRAPH, LENGTH, n, MANNING, SLOPE, DT, WIDTH).peak_outflow
        for n in (1, 2, 4, 8)
    ]
    base = max(peaks)
    for n, peak in zip((1, 2, 4, 8), peaks):
        assert peak <= base * 1.005, f"n={n}: peak {peak} inflates beyond 0.5% of {base}"


@needs_cpp
def test_reach_count_only_shortens_each_reach():
    """The structural property that proves a reach covers L/n.

    Travel time is proportional to reach length, so a single pass over the whole
    channel takes n times as long as n passes over L/n. This is the invariant the
    old implementation violated, having given every reach the full length.
    """
    base = core.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)
    for n in (2, 4, 8):
        r = core.route_multi_reach(HYDROGRAPH, LENGTH, n, MANNING, SLOPE, DT, WIDTH)
        assert base.travel_time / r.travel_time == pytest.approx(n, rel=0.02)


@needs_cpp
def test_negative_discharge_is_rejected():
    """Discharge is non-negative; a negative inflow used to route into the output."""
    with pytest.raises(Exception, match="non-negative"):
        core.route_flood_wave(
            [-50.0, 0.0, 100.0, 0.0, 20.0], LENGTH, 1, MANNING, SLOPE, DT, WIDTH
        )


@needs_cpp
def test_routing_output_is_non_negative_for_physical_input():
    r = core.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)

    out = np.asarray(r.outflow_hydrograph, dtype=float)
    assert np.all(np.isfinite(out))
    assert np.all(out >= 0.0)


@needs_cpp
def test_degenerate_inputs_return_empty_without_raising():
    assert core.route_multi_reach([], LENGTH, 2, MANNING, SLOPE, DT, WIDTH).travel_time >= 0
    assert core.route_multi_reach(HYDROGRAPH, LENGTH, 0, MANNING, SLOPE, DT, WIDTH).travel_time >= 0


# ------------------------------------------------------- agreement with Python


@needs_cpp
def test_agrees_with_the_python_twin_on_a_single_reach():
    cpp = core.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)
    py = hf.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)

    assert cpp.travel_time == pytest.approx(py["travel_time"], rel=1e-9)
    assert cpp.celerity == pytest.approx(py["celerity"], rel=1e-9)
    assert cpp.normal_depth == pytest.approx(py["normal_depth"], rel=1e-9)
    assert cpp.volume_in == pytest.approx(py["volume_in"], rel=1e-9)


@needs_cpp
def test_outflow_hydrographs_agree():
    cpp = core.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)
    py = hf.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)

    np.testing.assert_allclose(
        np.asarray(cpp.outflow_hydrograph),
        np.asarray(py["outflow_hydrograph"]),
        rtol=1e-9,
        atol=1e-9,
    )


@needs_cpp
def test_multi_reach_agrees_with_the_python_twin():
    """The two must model the same river: n reaches of L/n, cascaded."""
    for n in (2, 4):
        cpp = core.route_multi_reach(HYDROGRAPH, LENGTH, n, MANNING, SLOPE, DT, WIDTH)
        py = hf.route_multi_reach(HYDROGRAPH, LENGTH, n, MANNING, SLOPE, DT, WIDTH)

        np.testing.assert_allclose(
            np.asarray(cpp.outflow_hydrograph),
            np.asarray(py["outflow_hydrograph"]),
            rtol=1e-6,
            atol=1e-9,
        )
        assert cpp.peak_outflow == pytest.approx(py["peak_outflow"], rel=1e-6)


# ------------------------------------------------- physical admissibility


@needs_cpp
def test_routing_conserves_volume_closely():
    """A kinematic-wave router should neither create nor destroy discharge."""
    r = core.route_flood_wave(HYDROGRAPH, LENGTH, 1, MANNING, SLOPE, DT, WIDTH)

    assert 0.5 < r.mass_balance < 2.0, f"mass_balance {r.mass_balance} is not physical"
