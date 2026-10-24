"""
Economic Analysis for Agricultural Projects
منبع: FAO Investment Centre methodology
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EconomicResult:
    # The provenance fields were added above the required ones, and in a
    # dataclass a field without a default may not follow one that has it. The
    # module then failed at import with
    # `TypeError: non-default argument 'npv' follows default argument`, which
    # took down `app.openapi()` and therefore every contract check in the
    # repository — the failure looked like a routing problem and was a field
    # order. Required fields first, defaults after, keeps both intents.
    npv: float | None = None
    irr: float | None = None
    payback_years: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None
    roi: float | None = None
    data_source: str = "simulated"
    model: str = ""
    computed: bool = True


def calculate_npv(cashflows: list[float], discount_rate: float) -> float:
    """محاسبه NPV (Net Present Value)"""
    return sum(cf / ((1 + discount_rate) ** t) for t, cf in enumerate(cashflows))


def calculate_payback(cashflows: list[float]) -> float:
    """محاسبه دوره بازگشت سرمایه (سال)

    Convention: the cumulative-cash convention, counting **full periods**.
    Years are 1-based and every flow in ``cashflows`` is treated as a
    year-end flow, so the period count at which the running sum first
    turns non-negative is the payback period. This is the convention the
    service contract pins: ``calculate_payback([-100, 50, 50, 50]) == 3``
    (``services/validation/formula_checks.py`` "payback_convention"), and
    ``[-1000, 250, 250, 250, 250]`` therefore returns 5, not the 4.0 of a
    t=0-investment reading. Callers needing the fractional form should
    interpolate the crossing period themselves; both readings are valid in
    the literature and this module publishes only the one it implements.
    """
    cumulative = 0.0
    for year, cf in enumerate(cashflows, 1):
        cumulative += cf
        if cumulative >= 0:
            return year
    return float("inf")
