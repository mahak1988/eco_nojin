"""Pilot error analysis for Stage 35 HY-RUE benchmark pilot run.

Analyses the Stage 35 pilot result (engine/reports/data/stage35_pilot_single.json)
to identify the source of the 63% yield overestimation.

Pilot record:
  - Field: pilot_1, District: Buxar, Year: 2016-17
  - Coordinates: 26.33 N, 83.54 E
  - Season: 2016-11-01 to 2017-04-21 (172 days)
  - Observed yield: 6.68 t/ha
  - Predicted yield: 10.899 t/ha
  - Absolute error: +4.219 t/ha
  - Relative error: +63.16%
  - EWSI mean: 0.4592

Key computation inputs (from Stage 35):
  - PAR: Open-Meteo shortwave_radiation_sum (MJ/m^2/day)
    - NOT converted to PAR (no 0.5 factor applied)
    - Shortwave radiation includes UV + visible + NIR
    - PAR is only ~45-50% of shortwave
    - Using shortwave directly as PAR overestimates PAR by ~2x
  - LAI: Fixed at 3.0 m^2/m^2 (default, not crop-stage dependent)
  - EWSI: mean 0.4592 (calculated from real NDMI + VPD + soil moisture)
  - epsilon: 2.2 g/MJ IPAR (wheat preset)
  - HI: 0.45 (wheat preset)
  - k: 0.65 (light extinction coefficient)
  - t_opt: 20.0 C (wheat)

These inputs flow through HYRUE:
  f_IPAR = 1 - exp(-k * min(LAI, lai_max))
  f_water = 1 - EWSI
  f_temp = exp(-((T - t_opt) / 8)^2)
  B_day = PAR * f_IPAR * epsilon * f_water * f_temp
  Y = B_season * HI / 100  (g/m^2 -> t/ha)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

PILOT_RESULT_PATH = Path(
    "engine/reports/data/stage35_pilot_single.json"
)


@dataclass
class PilotErrorDiagnosis:
    """Diagnosis of the Stage 35 pilot yield overestimation.

    Attributes:
        observed_yield: Observed grain yield (t/ha).
        predicted_yield: Predicted grain yield (t/ha).
        absolute_error: predicted - observed (t/ha).
        relative_error_percent: absolute_error / observed * 100.
        component_issues: List of identified issues affecting each model
            component (PAR, LAI, EWSI, epsilon, HI).
        primary_drivers: Ranked list of likely primary error sources.
        recommendations: Recommended corrective actions.
    """

    observed_yield: float
    predicted_yield: float
    absolute_error: float
    relative_error_percent: float
    component_issues: list[str] = field(default_factory=list)
    primary_drivers: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def load_pilot_result() -> dict[str, Any]:
    """Load the Stage 35 pilot result JSON."""
    with open(PILOT_RESULT_PATH, encoding="utf-8") as f:
        return json.load(f)


def analyze_pilot_error() -> PilotErrorDiagnosis:
    """Analyze the Stage 35 pilot error and identify likely sources.

    Returns:
        A :class:`PilotErrorDiagnosis` with the error breakdown and
        recommended corrective actions.
    """
    result = load_pilot_result()
    observed = float(result["observed_yield"])
    predicted = float(result["predicted_yield"])
    abs_error = predicted - observed
    rel_error_pct = abs_error / observed * 100.0

    diagnosis = PilotErrorDiagnosis(
        observed_yield=observed,
        predicted_yield=predicted,
        absolute_error=abs_error,
        relative_error_percent=rel_error_pct,
    )

    # --- Component-level issue identification ---

    # PAR issue: shortwave radiation used directly as PAR
    # Shortwave radiation (~20-25 MJ/m^2/day) is roughly 2x PAR (~10-12 MJ/m^2/day)
    # No 0.5 conversion factor was applied in Stage 35
    diagnosis.component_issues.append(
        "PAR: Open-Meteo shortwave_radiation_sum (MJ/m^2/day) was used directly "
        "as PAR without the 0.5 shortwave->PAR conversion factor. Shortwave "
        "radiation includes UV + visible + NIR; PAR (~400-700 nm) is roughly "
        "45-50% of shortwave. Using shortwave as PAR overestimates PAR by ~2x, "
        "directly scaling biomass upward by ~2x."
    )

    # LAI issue: fixed at default 3.0
    # Wheat LAI varies through the season (near zero at planting, peaks at
    # ~4-6 at anthesis, senesces before harvest). A constant LAI=3.0:
    # - Underestimates early-season interception (LAI near zero)
    # - Overestimates mid-season if actual LAI < 3.0
    # - Underestimates late-season if actual LAI > 3.0
    # Net effect depends on season, but a constant LAI misrepresents the
    # canopy development curve.
    diagnosis.component_issues.append(
        "LAI: Fixed at 3.0 m^2/m^2 (default) for the entire season. Wheat "
        "LAI follows a sigmoid development curve (near zero at emergence, "
        "peaking around anthesis, senescing before harvest). Constant LAI "
        "misrepresents f_IPAR through the season."
    )

    # EWSI issue: uncalibrated weights and anchors
    # EWSI weights (0.4/0.3/0.3) and VPD anchors (0.5/4.0 kPa) are project
    # defaults with no published source. NDMI reference/critical values
    # (0.3/-0.2) are also unsourced. EWSI mean of 0.4592 gives f_water = 0.5408.
    diagnosis.component_issues.append(
        "EWSI: Weights (0.4/0.3/0.3), NDMI anchors (0.3/-0.2), VPD anchors "
        "(0.5/4.0 kPa), and field capacity (0.35 m^3/m^3) are uncalibrated "
        "project defaults with no published source for wheat in eastern "
        "India. EWSI mean of 0.4592 implies moderate water stress "
        "(f_water = 0.5408), but the stress magnitude is unverified."
    )

    # epsilon issue: wheat preset 2.2 g/MJ IPAR
    diagnosis.component_issues.append(
        "RUE (epsilon): 2.2 g/MJ IPAR from wheat crop preset. This is a "
        "literature value, not calibrated to the CIMMYT dataset or the "
        "specific varieties/agronomy in the records."
    )

    # HI issue: 0.45 from wheat preset
    diagnosis.component_issues.append(
        "Harvest index: 0.45 from wheat crop preset. Actual HI varies by "
        "variety, agronomy, and year. Not calibrated to CIMMYT data."
    )

    # Temperature issue: t_opt = 20.0 C for wheat, Gaussian width = 8 (hard-coded)
    diagnosis.component_issues.append(
        "Temperature stress: t_opt = 20.0 C (wheat preset) with hard-coded "
        "Gaussian width of 8 C. No published source for this specific crop-"
        "location combination. Winter wheat in Bihar experiences Nov-Feb "
        "cooling then Mar-Apr warming; the thermal response may not match."
    )

    # --- Primary drivers (ranked by likely impact) ---

    # PAR conversion is the largest likely factor (~2x overestimation of PAR
    # -> ~2x overestimation of biomass -> ~2x yield overestimation)
    diagnosis.primary_drivers.append(
        "1. PAR unit error: shortwave radiation used directly as PAR without "
        "the 0.5 conversion factor. This alone can explain ~100% overestimation "
        "of biomass (and thus yield) before other factors compensate."
    )
    diagnosis.primary_drivers.append(
        "2. LAI misrepresentation: constant LAI=3.0 instead of crop-stage-"
        "dependent LAI. f_IPAR = 1 - exp(-0.65 * 3.0) = 0.858 is near the "
        "asymptote; actual seasonal average f_IPAR is likely lower."
    )
    diagnosis.primary_drivers.append(
        "3. Uncalibrated EWSI parameters: weights, NDMI/VPD anchors, and "
        "field capacity are project defaults. EWSI mean 0.4592 may over- or "
        "under-estimate water stress."
    )

    # --- Recommendations ---

    diagnosis.recommendations.append(
        "Apply shortwave->PAR conversion factor of 0.5 (documented as "
        "estimated, not measured) before passing PAR to HYRUE."
    )
    diagnosis.recommendations.append(
        "Replace constant LAI with crop-stage-dependent LAI (GDD model or "
        "empirical NDVI-based LAI)."
    )
    diagnosis.recommendations.append(
        "Calibrate EWSI weights and anchors on development-district data "
        "only; never on test-district data."
    )
    diagnosis.recommendations.append(
        "Do not tune parameters to reduce the pilot error on this single "
        "record. The pilot error analysis is diagnostic, not a calibration "
        "target."
    )

    return diagnosis


def compute_hyrue_component_breakdown() -> dict[str, float]:
    """Compute the HYRUE component values for the pilot record.

    Uses the Stage 35 pilot inputs to show how each component contributes
    to the final yield estimate. This is a diagnostic computation, not a
    calibration target.

    Returns:
        Dict of component name -> value with interpretation notes.
    """
    # Stage 35 pilot inputs
    lai = 3.0  # constant LAI (default)
    k = 0.65
    lai_max = 6.0
    epsilon = 2.2  # wheat preset (g/MJ IPAR)
    hi = 0.45  # wheat preset
    ewsi_mean = 0.4591508361932881  # from pilot result

    # f_IPAR
    f_ipar = 1.0 - np.exp(-k * min(lai, lai_max))

    # f_water
    f_water = 1.0 - ewsi_mean

    # f_temp (approximate: use t_opt so f_temp = 1.0 for illustration;
    # actual season has varying temperatures)
    f_temp_at_opt = 1.0  # T == t_opt

    # PAR estimate: shortwave radiation ~450 MJ/m^2/day average (Jan_Srad +
    # Feb_Srad / 2), but used directly as PAR in Stage 35
    shortwave_avg = 450.0  # MJ/m^2/day (rough estimate from CIMMYT data)
    par_as_shortwave = shortwave_avg  # what Stage 35 used (WRONG)
    par_converted = shortwave_avg * 0.5  # what should be used (shortwave -> PAR)

    n_days = 172

    # Biomass with PAR used as shortwave (Stage 35 approach)
    b_day_wrong = par_as_shortwave * f_ipar * epsilon * f_water * f_temp_at_opt
    b_season_wrong = b_day_wrong * n_days
    y_wrong = b_season_wrong * hi / 100  # t/ha

    # Biomass with PAR converted from shortwave
    b_day_right = par_converted * f_ipar * epsilon * f_water * f_temp_at_opt
    b_season_right = b_day_right * n_days
    y_right = b_season_right * hi / 100  # t/ha

    return {
        "f_ipar": float(f_ipar),
        "f_water": float(f_water),
        "f_temp_at_opt": float(f_temp_at_opt),
        "par_as_shortwave_mj_m2_day": float(par_as_shortwave),
        "par_converted_mj_m2_day": float(par_converted),
        "n_days": n_days,
        "yield_with_shortwave_as_par_t_ha": float(y_wrong),
        "yield_with_converted_par_t_ha": float(y_right),
        "observed_yield_t_ha": 6.68,
        "error_if_shortwave_used_as_par_pct": float(
            (y_wrong - 6.68) / 6.68 * 100
        ),
        "error_if_par_converted_pct": float((y_right - 6.68) / 6.68 * 100),
    }


if __name__ == "__main__":
    diagnosis = analyze_pilot_error()
    breakdown = compute_hyrue_component_breakdown()

    print("=" * 60)
    print("Stage 35 Pilot Error Analysis")
    print("=" * 60)
    print(f"Observed yield:  {diagnosis.observed_yield:.3f} t/ha")
    print(f"Predicted yield: {diagnosis.predicted_yield:.3f} t/ha")
    print(f"Absolute error:  {diagnosis.absolute_error:+.3f} t/ha")
    print(f"Relative error:  {diagnosis.relative_error_percent:+.1f}%")
    print()
    print("Component issues identified:")
    for i, issue in enumerate(diagnosis.component_issues, 1):
        print(f"  {i}. {issue}")
    print()
    print("Primary drivers (ranked):")
    for driver in diagnosis.primary_drivers:
        print(f"  {driver}")
    print()
    print("Recommendations:")
    for rec in diagnosis.recommendations:
        print(f"  - {rec}")
    print()
    print("Component breakdown (diagnostic computation):")
    for key, val in breakdown.items():
        print(f"  {key}: {val}")
