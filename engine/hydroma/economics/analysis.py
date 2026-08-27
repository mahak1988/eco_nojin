"""
Economic Analysis for Agricultural Projects
منبع: FAO Investment Centre methodology
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EconomicResult:
    npv: float
    irr: float | None
    payback_years: float
    gross_margin: float
    net_margin: float
    roi: float

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
