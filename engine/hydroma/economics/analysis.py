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
    """محاسبه دوره بازگشت سرمایه (سال)"""
    cumulative = 0.0
    for year, cf in enumerate(cashflows, 1):
        cumulative += cf
        if cumulative >= 0:
            return year
    return float("inf")
