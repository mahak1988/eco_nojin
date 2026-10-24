"""Independent consistency checks for HYRUE seasonal computations.

These checks verify that HYRUE's seasonal mode results are mathematically
consistent with the model's own formulas, by independently recomputing
each sub-component and comparing.  They do NOT import the model's internal
methods — they re-derive the formulas from the documented equations:

    f_IPAR  = 1 - exp(-k * min(LAI, lai_max))   (Beer-Lambert)
    f_water = 1 - EWSI
    f_temp  = exp(-((T - T_opt) / 8)^2)         (Gaussian)
    B_day   = PAR * f_IPAR * epsilon * f_water * f_temp
    B_total = sum(B_day)
    Y       = B_total * HI

If the model's output does not match the independent recomputation within
a tight tolerance, the check fails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ConsistencyCheck:
    """Result of a single consistency check."""

    name: str
    passed: bool
    expected: float
    computed: float
    relative_error: float
    tolerance: float
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "expected": self.expected,
            "computed": self.computed,
            "relative_error": self.relative_error,
            "tolerance": self.tolerance,
            "notes": self.notes,
        }


@dataclass
class ConsistencyReport:
    """Results of all consistency checks for a model run."""

    checks: list[ConsistencyCheck] = field(default_factory=list)
    all_passed: bool = True
    model_name: str = "HYRUE"
    params: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def add(self, check: ConsistencyCheck) -> None:
        self.checks.append(check)
        if not check.passed:
            self.all_passed = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "all_passed": self.all_passed,
            "n_checks": len(self.checks),
            "n_passed": sum(1 for c in self.checks if c.passed),
            "params": self.params,
            "checks": [c.to_dict() for c in self.checks],
            "notes": self.notes,
        }


def _rel_err(a: float, b: float, eps: float = 1e-9) -> float:
    return abs(a - b) / (abs(b) + eps)


def _expected_f_ipar(lai: np.ndarray, k: float, lai_max: float) -> np.ndarray:
    """Independent Beer-Lambert: f_IPAR = 1 - exp(-k * min(LAI, lai_max))."""
    canopy = np.clip(lai, 0, lai_max)
    return 1 - np.exp(-k * canopy)


def _expected_f_water(ewsi: np.ndarray) -> np.ndarray:
    """Independent water stress: f_water = 1 - EWSI."""
    return 1 - np.clip(ewsi, 0, 1)


def _expected_f_temp(
    t_mean: np.ndarray, t_opt: float, t_min: float, t_max: float
) -> np.ndarray:
    """Independent Gaussian temperature stress.

    f_temp = exp(-((T - T_opt) / 8)^2) when t_min <= T <= t_max, else 0.
    The Gaussian width of 8 °C is documented in HYRUEParams as a platform
    choice (not from Steduto et al. 2009); we reproduce it exactly here.
    """
    t = np.asarray(t_mean, dtype=float)
    below = t < t_min
    above = t > t_max
    t_clipped = np.where(below | above, t_opt, t)
    f_temp = np.exp(-(((t_clipped - t_opt) / 8.0) ** 2))
    f_temp = np.where(below | above, 0.0, f_temp)
    return f_temp


def _expected_daily_biomass(
    par: np.ndarray,
    lai: np.ndarray,
    ewsi: np.ndarray,
    t_mean: np.ndarray,
    epsilon: float,
    k: float,
    lai_max: float,
    t_opt: float,
    t_min: float,
    t_max: float,
) -> np.ndarray:
    """Independently compute daily biomass per the documented HYRUE formula."""
    f_ipar = _expected_f_ipar(lai, k, lai_max)
    f_water = _expected_f_water(ewsi)
    f_temp = _expected_f_temp(t_mean, t_opt, t_min, t_max)
    return par * f_ipar * epsilon * f_water * f_temp


def verify_seasonal_consistency(
    model_result: dict[str, Any],
    par: np.ndarray,
    lai: np.ndarray,
    ewsi: np.ndarray,
    t_mean: np.ndarray,
    params: dict[str, Any] | None = None,
    tolerance: float = 1e-6,
) -> ConsistencyReport:
    """Verify HYRUE seasonal output against independent formula recomputation.

    Args:
        model_result: The dict returned by ``HYRUE.compute`` in seasonal mode.
        par: Daily PAR array used in the computation.
        lai: Daily LAI array used in the computation.
        ewsi: Daily EWSI array used in the computation.
        t_mean: Daily mean temperature array used in the computation.
        params: Dict of model parameters (epsilon, k, hi, lai_max, t_opt,
            t_min, t_max). If None, defaults are used.
        tolerance: Maximum relative error for each check to pass.

    Returns:
        A :class:`ConsistencyReport` with all checks.
    """
    if params is None:
        params = {}

    epsilon = params.get("epsilon", 2.2)
    k = params.get("k", 0.65)
    hi = params.get("hi", 0.45)
    lai_max = params.get("lai_max", 6.0)
    t_opt = params.get("t_opt", 20.0)
    t_min = params.get("t_min", 5.0)
    t_max = params.get("t_max", 35.0)

    par = np.asarray(par, dtype=float)
    lai = np.asarray(lai, dtype=float)
    ewsi = np.asarray(ewsi, dtype=float)
    t_mean = np.asarray(t_mean, dtype=float)

    report = ConsistencyReport(
        model_name="HYRUE",
        params={
            "epsilon": epsilon,
            "k": k,
            "hi": hi,
            "lai_max": lai_max,
            "t_opt": t_opt,
            "t_min": t_min,
            "t_max": t_max,
            "gaussian_width": 8.0,
        },
        notes=(
            "Independent recomputation of HYRUE seasonal formulas. "
            "Gaussian width = 8.0 is documented in HYRUEParams as a platform choice."
        ),
    )

    # --- Check 1: f_IPAR ---
    expected_f_ipar = _expected_f_ipar(lai, k, lai_max)
    model_f_ipar = np.asarray(model_result.get("f_ipar", []), dtype=float)
    if model_f_ipar.size > 0:
        check = ConsistencyCheck(
            name="f_IPAR (Beer-Lambert)",
            passed=np.allclose(model_f_ipar, expected_f_ipar, rtol=tolerance, atol=tolerance),
            expected=float(np.mean(expected_f_ipar)),
            computed=float(np.mean(model_f_ipar)),
            relative_error=float(np.max(np.abs(model_f_ipar - expected_f_ipar))),
            tolerance=tolerance,
            notes="f_IPAR = 1 - exp(-k * min(LAI, lai_max))",
        )
        report.add(check)

    # --- Check 2: f_water ---
    # f_water = 1 - EWSI; verified indirectly through daily biomass check below.

    # --- Check 3: f_temp ---
    # f_temp = exp(-((T - T_opt) / 8)^2); verified indirectly through daily biomass check.

    # --- Check 4: daily biomass ---
    expected_daily_biomass = _expected_daily_biomass(
        par, lai, ewsi, t_mean, epsilon, k, lai_max, t_opt, t_min, t_max,
    )

    model_daily_biomass = np.asarray(
        model_result.get("daily_biomass_g_m2", []), dtype=float,
    )
    if model_daily_biomass.size > 0:
        check = ConsistencyCheck(
            name="daily_biomass_g_m2",
            passed=np.allclose(
                model_daily_biomass, expected_daily_biomass, rtol=tolerance, atol=tolerance
            ),
            expected=float(np.sum(expected_daily_biomass)),
            computed=float(np.sum(model_daily_biomass)),
            relative_error=_rel_err(
                float(np.sum(model_daily_biomass)),
                float(np.sum(expected_daily_biomass)),
            ),
            tolerance=tolerance,
            notes=(
                "B_daily = PAR * f_IPAR * epsilon * f_water * f_temp"
            ),
        )
        report.add(check)

    # --- Check 5: total biomass (seasonal sum) ---
    expected_total = float(np.sum(expected_daily_biomass))
    model_total = float(model_result.get("total_biomass_g_m2", 0.0))
    check = ConsistencyCheck(
        name="total_biomass_g_m2 (seasonal sum)",
        passed=_rel_err(model_total, expected_total) <= tolerance,
        expected=expected_total,
        computed=model_total,
        relative_error=_rel_err(model_total, expected_total),
        tolerance=tolerance,
        notes="B_total = sum(B_daily)",
    )
    report.add(check)

    # --- Check 6: yield ---
    expected_yield = expected_total * hi
    model_yield = float(model_result.get("yield_g_m2", 0.0))
    check = ConsistencyCheck(
        name="yield_g_m2",
        passed=_rel_err(model_yield, expected_yield) <= tolerance,
        expected=expected_yield,
        computed=model_yield,
        relative_error=_rel_err(model_yield, expected_yield),
        tolerance=tolerance,
        notes="Y = B_total * HI",
    )
    report.add(check)

    # --- Check 7: yield in t/ha ---
    expected_yield_tha = expected_yield / 100.0
    model_yield_tha = float(model_result.get("yield_t_ha", 0.0))
    check = ConsistencyCheck(
        name="yield_t_ha",
        passed=_rel_err(model_yield_tha, expected_yield_tha) <= tolerance,
        expected=expected_yield_tha,
        computed=model_yield_tha,
        relative_error=_rel_err(model_yield_tha, expected_yield_tha),
        tolerance=tolerance,
        notes="Y_t_ha = Y_g_m2 / 100",
    )
    report.add(check)

    # --- Check 8: season length ---
    n_days = len(par)
    model_season_length = model_result.get("season_length_days", n_days)
    check = ConsistencyCheck(
        name="season_length_days",
        passed=model_season_length == n_days,
        expected=float(n_days),
        computed=float(model_season_length),
        relative_error=_rel_err(float(model_season_length), float(n_days)),
        tolerance=tolerance,
        notes="season_length_days should equal number of input days",
    )
    report.add(check)

    return report