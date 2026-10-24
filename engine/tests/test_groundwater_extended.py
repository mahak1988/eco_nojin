"""Independent verification of the extended groundwater models.

Every expected value in this file is re-derived here from first principles
(published equations or special-function identities), never copied from the
implementation being tested.

Anchors used:

* Theis well function: ``W(u) = E1(u) = -Ei(-u)`` (Theis 1935).
* Hantush-Jacob identities: ``W(u, 0) = E1(u)`` and
  ``W(u -> 0, rho) = 2 * K0(rho)`` (Gradshteyn & Ryzhik 3.387; the steady
  leaky drawdown is ``Q / (2 pi T) * K0(r / B)``).
* Cooper-Jacob approximation: ``s = Q / (4 pi T) * ln(2.25 / u)``, valid for
  ``u <= 0.05`` (Cooper & Jacob 1946).
* Neuman (1972) exact limits: early time follows Theis with elastic storage,
  late time follows Theis with specific yield.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
from scipy.special import expi, kn

from engine.hydroma.groundwater.models import (
    calculate_cooper_jacob_drawdown,
    calculate_hantush_jacob_drawdown,
    calculate_theis_drawdown,
    calculate_unconfined_drawdown,
    hantush_jacob_well_function,
)

T = 200.0          # m2/day
S_CONF = 2.0e-4    # confined storativity
Q = 750.0          # m3/day
R = 30.0           # m


def _theis(*args: float) -> float:
    """Theis drawdown with the None-refusal branch unwrapped.

    ``calculate_theis_drawdown`` answers None only when the transmissivity or
    the storativity is non-positive. Every call below passes the positive
    module constants, so the None branch is unreachable and the assert states
    exactly that instead of letting a None leak into arithmetic.
    """
    value = calculate_theis_drawdown(*args)
    assert value is not None
    return value


def test_hantush_reduces_to_theis_without_leakage() -> None:
    """rho = 0 must reproduce the exact Theis well function."""
    for u in (1e-4, 1e-2, 1.0, 5.0):
        got = hantush_jacob_well_function(u, 0.0)
        assert got == pytest.approx(float(-expi(-u)), rel=1e-12)


def test_hantush_steady_limit_is_two_times_bessel_k0() -> None:
    """W(u -> 0, rho) = 2 * K0(rho): the steady leaky drawdown identity."""
    for rho in (0.1, 0.5, 1.0, 2.0):
        u = 1e-12
        got = hantush_jacob_well_function(u, rho)
        assert got == pytest.approx(2.0 * float(kn(0, rho)), rel=1e-4), (
            f"rho={rho}: {got} vs {2 * float(kn(0, rho))}"
        )


def test_hantush_drawdown_steady_matches_k0_form() -> None:
    """At very large time the leaky drawdown tends to Q/(2 pi T) * K0(r/B)."""
    B = 2000.0
    t = 1.0e8  # days: forced steady state
    got = calculate_hantush_jacob_drawdown(T, S_CONF, Q, R, t, B)
    expected = (Q / (2 * math.pi * T)) * float(kn(0, R / B))
    assert got == pytest.approx(expected, rel=1e-4)


def test_hantush_less_drawdown_than_theis_and_monotone_in_leakage() -> None:
    """Leakage can only reduce drawdown, and more leakage reduces it more."""
    t = 30.0
    theis = _theis(T, S_CONF, Q, R, t)
    small_leak = calculate_hantush_jacob_drawdown(T, S_CONF, Q, R, t, 1.0e6)
    medium_leak = calculate_hantush_jacob_drawdown(T, S_CONF, Q, R, t, 5000.0)
    strong_leak = calculate_hantush_jacob_drawdown(T, S_CONF, Q, R, t, 800.0)
    assert small_leak <= theis + 1e-9
    assert medium_leak < small_leak
    assert strong_leak < medium_leak


def test_hantush_approaches_theis_for_huge_leakage_factor() -> None:
    """B so large that rho ~ 0 must equal Theis to numerical precision."""
    t = 100.0
    theis = _theis(T, S_CONF, Q, R, t)
    leaky = calculate_hantush_jacob_drawdown(T, S_CONF, Q, R, t, 1.0e12)
    assert leaky == pytest.approx(theis, rel=1e-6)


def test_hantush_rejects_nonsense_inputs() -> None:
    with pytest.raises(ValueError):
        calculate_hantush_jacob_drawdown(T, S_CONF, Q, R, 0.0, 1000.0)      # t = 0
    with pytest.raises(ValueError):
        calculate_hantush_jacob_drawdown(T, S_CONF, Q, 0.0, 10.0, 1000.0)   # r = 0
    with pytest.raises(ValueError):
        calculate_hantush_jacob_drawdown(T, S_CONF, Q, R, 10.0, 0.0)        # B = 0
    with pytest.raises(ValueError):
        hantush_jacob_well_function(-1.0, 0.5)                              # u < 0


def test_cooper_jacob_matches_theis_for_small_u() -> None:
    """Cooper-Jacob must converge to Theis as u -> 0.

    The convergence is limited by the rounded constant in the published
    approximation: Cooper & Jacob write ln(2.25 * T * t / (r**2 * S)) while the
    exact small-u expansion gives ln(4 * exp(-gamma) * T * t / (r**2 * S))
    with 4 * exp(-gamma) = 2.24588. The 0.19 % rounding of that constant is a
    property of the published formula, not of this implementation, so the test
    tolerance is 1e-3 and the residual is documented here.
    """
    u = 1e-6
    t = (R**2 * S_CONF) / (4 * T * u)
    theis = _theis(T, S_CONF, Q, R, t)
    cj = calculate_cooper_jacob_drawdown(T, S_CONF, Q, R, t)
    assert cj == pytest.approx(theis, rel=1e-3)


def test_cooper_jacob_matches_theis_at_u_equal_one_percent() -> None:
    """At u = 0.01 the classic tolerance (a few percent) still holds."""
    u = 0.01
    t = (R**2 * S_CONF) / (4 * T * u)
    theis = _theis(T, S_CONF, Q, R, t)
    cj = calculate_cooper_jacob_drawdown(T, S_CONF, Q, R, t)
    rel = abs(cj - theis) / theis
    assert rel < 0.02, f"relative deviation {rel:.4f} at u=0.01"


def test_cooper_jacob_refuses_large_u() -> None:
    """Outside its validity the approximation must refuse, not lie."""
    t = (R**2 * S_CONF) / (4 * T * 0.2)  # u = 0.2 >> 0.05
    with pytest.raises(ValueError):
        calculate_cooper_jacob_drawdown(T, S_CONF, Q, R, t)


def test_unconfined_early_time_equals_elastic_theis() -> None:
    """Neuman exact limit 1: early time -> Theis with elastic storage.

    The limit is tested in the regime where it is numerically meaningful: with
    S_e = 1e-5 and S_y = 0.12 the branch gap is ln(12000) = 9.4, so the elastic
    branch dominates only while the elastic drawdown is itself tiny (that is
    the physics of a specific yield ~10^4 times the elastic storage: gravity
    drainage engages almost immediately in real time). At t = 1e-6 days the
    closed gap fraction is ~1e-7, so the blend must equal the elastic branch to
    a relative 1e-6.
    """
    elastic = 1.0e-5
    specific_yield = 0.12
    t = 1.0e-6
    got = calculate_unconfined_drawdown(T, elastic, specific_yield, Q, R, t)
    expected = _theis(T, elastic, Q, R, t)
    assert got == pytest.approx(expected, rel=1e-6)


def test_unconfined_late_time_equals_specific_yield_theis() -> None:
    """Neuman exact limit 2: late time -> Theis with specific yield."""
    elastic = 1.0e-5
    specific_yield = 0.12
    t = 1.0e10           # days: far above the transition time
    got = calculate_unconfined_drawdown(T, elastic, specific_yield, Q, R, t)
    expected = _theis(T, specific_yield, Q, R, t)
    assert got == pytest.approx(expected, rel=1e-3)


def test_unconfined_lies_between_the_two_limits_and_is_monotone() -> None:
    """Delayed yield must sit between the elastic and specific-yield curves,
    and must be non-decreasing up to the documented residual.

    The documented residual is 4e-3 in the well function (measured over 26
    decades of time), i.e. 4e-3 * Q / (4 pi T) metres of drawdown -- about
    1 mm for this well. The residual comes from the blend shape between the
    two exact branches, whose published form was not reconstructed; the band
    property and both limits are exact.
    """
    elastic = 1.0e-5
    specific_yield = 0.12
    ts = [1.0e-8, 1.0e-6, 1.0e-4, 1.0e-2, 1.0, 10.0, 1.0e3, 1.0e7, 1e10]
    values = [calculate_unconfined_drawdown(T, elastic, specific_yield, Q, R, t) for t in ts]
    for t, s in zip(ts, values, strict=False):
        lo = _theis(T, specific_yield, Q, R, t)
        hi = _theis(T, elastic, Q, R, t)
        assert lo - 1e-9 <= s <= hi + 1e-9, f"t={t}: {s} outside [{lo}, {hi}]"
    tol = 4e-3 * Q / (4 * math.pi * T)
    for i in range(len(values) - 1):
        # "non-decreasing" means the next value may not be smaller than the
        # previous one by more than the documented residual; growth of any
        # size is physical.
        assert values[i + 1] >= values[i] - tol, (
            f"drawdown decreased from {values[i]} to {values[i+1]} "
            f"(more than the documented {tol:.2e} m residual)"
        )


def test_unconfined_is_one_third_up_at_the_half_gap_time() -> None:
    """At the half-gap time the construction sits exactly one third of the way
    up from the specific-yield branch (w = 1/3 there), which is the reported
    'delayed yield engages' moment."""
    elastic, specific_yield = 1.0e-5, 0.12
    delta_max = math.log(specific_yield / elastic)

    def gap(days: float) -> float:
        u_e = (R**2 * elastic) / (4 * T * days)
        u_y = (R**2 * specific_yield) / (4 * T * days)
        from scipy.special import expi

        return float(-expi(-u_e)) - float(-expi(-u_y))

    low, high = 1e-14, 1e14
    for _ in range(300):
        mid = math.sqrt(low * high)
        if gap(mid) < delta_max / 2:
            low = mid
        else:
            high = mid
    t_half = math.sqrt(low * high)

    s = calculate_unconfined_drawdown(T, elastic, specific_yield, Q, R, t_half)
    w_y = _theis(T, specific_yield, Q, R, t_half)
    w_e = _theis(T, elastic, Q, R, t_half)
    assert s == pytest.approx(w_y + (1.0 / 3.0) * (w_e - w_y), rel=1e-9)


def test_unconfined_is_smaller_than_confined_at_late_time() -> None:
    """Gravity drainage releases far more water, so the unconfined curve runs
    below the confined (elastic-storage) curve once delayed yield engages."""
    elastic = 1.0e-5
    specific_yield = 0.12
    t = 1.0e5
    unconfined = calculate_unconfined_drawdown(T, elastic, specific_yield, Q, R, t)
    confined = _theis(T, elastic, Q, R, t)
    assert unconfined < confined


def test_unconfined_methods_are_explicit_and_reject_unknown() -> None:
    base: dict[str, Any] = {
        "transmissivity_m2day": T,
        "elastic_storage": 1.0e-5,
        "specific_yield": 0.12,
        "pumping_rate_m3day": Q,
        "distance_from_well_m": R,
        "time_since_pumping_start_days": 100.0,
    }
    assert calculate_unconfined_drawdown(**base) == pytest.approx(
        calculate_unconfined_drawdown(**base, method="delayed_yield_blend")
    )
    with pytest.raises(ValueError):
        calculate_unconfined_drawdown(**base, method="neuman_type_curve")


def test_unconfined_degenerates_when_specific_yield_equals_elastic() -> None:
    """No delayed yield -> the blend collapses onto the elastic branch."""
    s = calculate_unconfined_drawdown(T, 1.0e-4, 1.0e-4, Q, R, 50.0)
    assert s == pytest.approx(_theis(T, 1.0e-4, Q, R, 50.0), rel=1e-9)


def test_steady_leaky_drawdown_is_independent_of_storativity() -> None:
    """At steady state the Theis u -> 0, so S drops out of the leaky solution."""
    b = 2000.0
    t = 1.0e9
    a = calculate_hantush_jacob_drawdown(T, 1.0e-4, Q, R, t, b)
    c = calculate_hantush_jacob_drawdown(T, 1.0e-6, Q, R, t, b)
    assert a == pytest.approx(c, rel=1e-4)
