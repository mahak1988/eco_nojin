"""Theis reference test — anchored to published *formulae*, not to a table.

On 2026-10-10 no published numeric drawdown for our input set could be
obtained offline (USGS WSP 1541 → 404; EPA → 403; KGS/TWDB/AQTESOLV/OGS publish
formulae or unrelated fit datasets — the full source list is in
``tests/reference_data/theis_worked_example.md``). Rather than invent a value
(the exact defect that made CANON-005's old card claim 0.018 m), this test
anchors the engine to two independently published relations:

1. the published well-function series ``w(u) = -0.5772 - ln(u) + u - u^2/(2*2!)
   + u^3/(3*3!) - ...`` checked against the engine's ``expi``-based branch;
2. the published Cooper-Jacob approximation ``s = (Q/4*pi*T)*ln(2.25*T*t/(r^2*S))``
   for ``u < 0.05``, cross-checked against the engine's exact and
   Cooper-Jacob branches.

The open gap (G-V3-05) is a published *table value*, which would upgrade this
model from VALIDATED_METHOD_CONFORMANCE to VALIDATED_EXTERNAL.
"""

from __future__ import annotations

import math
from typing import cast

from engine.hydroma.groundwater.models import calculate_theis_drawdown

#: Published well-function series, truncated as published (AQTESOLV / KGS GW3).
_WELL_FUNCTION_SERIES_TERMS = 6


def _published_w(u: float) -> float:
    """The published series expansion of the Theis well function."""
    total = -0.5772 - math.log(u)
    term = u
    for k in range(1, _WELL_FUNCTION_SERIES_TERMS + 1):
        if k > 1:
            term *= -u
        total += term / (k * math.factorial(k))
    return total


def _published_cooper_jacob(T: float, S: float, Q: float, r: float, t: float) -> float:
    """The published Cooper-Jacob approximation (valid for u < 0.05)."""
    return (Q / (4.0 * math.pi * T)) * math.log(2.25 * T * t / (r * r * S))


T = 2000.0
S = 0.0002
Q = 760.0
R = 30.0
TIME_DAYS = 1.0


def _drawdown() -> float:
    return cast(
        "float",
        calculate_theis_drawdown(
        transmissivity_m2day=T,
        storativity=S,
        pumping_rate_m3day=Q,
        distance_from_well_m=R,
            time_since_pumping_start_days=TIME_DAYS,
        ),
    )


def test_engine_matches_the_published_well_function_series() -> None:
    """The engine's exact branch agrees with the published series for this u."""
    engine = _drawdown()
    u = (R * R * S) / (4.0 * T * TIME_DAYS)
    assert u < 0.05, f"the series is published for u < 0.05; got {u}"
    reference = (Q / (4.0 * math.pi * T)) * _published_w(u)
    # 2e-6, not 1e-12: the published series is truncated after six terms and
    # differs from the exact value by 1.5e-6 at u = 2.25e-5. That truncation
    # is what "as published" means, so it is the tolerance being tested.
    assert engine == pytest_approx(reference, rel=2e-6), (
        f"engine {engine!r} vs published series {reference!r}"
    )


def test_exact_and_cooper_jacob_branches_agree() -> None:
    """Both branches stay within the published validity band of the approximation."""
    exact = _drawdown()
    approximation = _published_cooper_jacob(T, S, Q, R, TIME_DAYS)
    assert abs(exact - approximation) / exact < 0.05, (
        f"exact {exact!r} vs published Cooper-Jacob {approximation!r}"
    )


def test_the_wrong_card_value_is_regression_guarded() -> None:
    """The CANON-005 card's old 0.018 m claim must never come back."""
    engine = _drawdown()
    assert abs(engine - 0.018) > 0.1, "the engine reproduces the withdrawn 0.018 m claim"
    assert 0.29 < engine < 0.32, f"expected ~0.306 m, measured {engine!r}"


def pytest_approx(value: float, rel: float):
    """Local stand-in so the file imports only ``math`` beyond the engine."""

    class _Approx:
        def __eq__(self, other: object) -> bool:  # pragma: no cover - trivial
            # ``object`` is what ``object.__eq__`` accepts; comparing against a
            # non-number is False rather than a TypeError (pytest.approx agrees).
            if isinstance(other, bool) or not isinstance(other, (int, float)):
                return False
            return math.isclose(float(other), value, rel_tol=rel)

        def __repr__(self) -> str:  # pragma: no cover - trivial
            return f"â‰ˆ{value!r} (آ±{rel:.0%})"

    return _Approx()
