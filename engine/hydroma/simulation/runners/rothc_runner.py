"""RothC (Rothamsted Carbon Model) — in-house Python port (Phase 3, sprint 1).

Implements the monthly RothC-26.3 scheme: four active pools (DPM, RPM, BIO,
HUM) + inert IOM, temperature and moisture rate modifiers, and the
clay-dependent stabilization split (Coleman & Jenkinson 1996).

This is the **canonical, reference implementation** of RothC-26.3 in the engine.
All other carbon modules should delegate to this implementation for
process-based, monthly-step simulations.

Role: **Core process model** — monthly time step, requires climate series,
supports residue/manure inputs, calibrated for soil carbon turnover studies.

See also:
    - engine.hydroma.models.ecsi.ECSI — annual interface, delegates here
    - engine.hydroma.carbon.calculator — IPCC/Verra project-level estimates

HONESTY / VALIDATION STATUS:
    Parameter values follow Coleman & Jenkinson (1996). This port must be
    validated against the official RothC-26.3 reference outputs before
    it is used for reporting; results are labeled
    data_source="simulated" with model="RothC (in-house port, ...)".
"""

from __future__ import annotations

import math

import numpy as np

from engine.hydroma.simulation.contracts import MonthClimate

# Annual rate constants (yr^-1) for the reference state: ~10 C (temperature
# modifier = 1), optimal moisture, bare soil (RothC-26.3 standard values).
RATES: dict[str, float] = {"DPM": 10.0, "RPM": 0.3, "BIO": 0.66, "HUM": 0.02}
# Split of the stabilized C between microbial biomass and humified OM.
BIO_FRAC: float = 0.46
HUM_FRAC: float = 0.54
# Default partition of plant-residue inputs between DPM and RPM.
RESIDUE_SPLIT: dict[str, float] = {"DPM": 0.59, "RPM": 0.41}
# Default initial split of the active (non-IOM) SOC across pools.
INITIAL_SPLIT: dict[str, float] = {"DPM": 0.022, "RPM": 0.075, "BIO": 0.039, "HUM": 0.864}
# Default plant-retainment / soil-cover modifier (no grazing).
PLANT_RETAINMENT: float = 0.6
# Carbon fraction used to convert fresh residue mass to carbon.
RESIDUE_C_FRACTION: float = 0.45


def stabilization_split(clay_pct: float) -> tuple[float, float]:
    """RothC-26.3 partition of decomposed carbon.

    The proportion routed to CO2 versus (BIO + HUM) depends on the soil clay
    content through
        x = 1.67 * (1.85 + 1.60 * exp(-0.0786 * clay%))
        CO2 = x / (1 + x);  BIO + HUM = 1 / (1 + x)
    (Coleman & Jenkinson 1996). For typical soils this keeps ~15-24% of the
    decomposed carbon in the soil; a constant 0.46 would double the
    stabilisation and over-state sequestration.

    Returns:
        (co2_fraction, stabilized_fraction)
    """
    if clay_pct < 0.0:
        raise ValueError("clay_pct must be non-negative")
    x = 1.67 * (1.85 + 1.60 * math.exp(-0.0786 * clay_pct))
    return x / (1.0 + x), 1.0 / (1.0 + x)


#: Lowest soil temperature the RothC temperature response is defined for.
#: RothC-26.3 temperature rate modifier, verified against the primary source.
#:
#: Coleman, K., Prout, J.M. & Milne, A.E. (2024), "RothC - A model for the
#: turnover of carbon in soil", Rothamsted Research, section 1.6.1, equation (1):
#:
#:     RM_Tmp = 47.91 / (1 + e^(106.06 / (T + 18.27)))
#:
#: where T is the average monthly air temperature in degrees Celsius. The same
#: triple is hard-coded in the official Fortran, Python and R releases of
#: RothC_Code / RothC_Py / RothC_R, so it is a constant, not a site calibration.
#:
#: The "47.9" and "106.27 / 18.06" variants seen in search snippets, and the
#: "2C" numerator, are all PDF text-layer extraction artefacts: the Word OMML
#: equation is emitted as separate glyph runs and a naive reflow merges
#: "18" + "." + "27" into "18.06" and drops the trailing "1" of "47.91".
#:
#: 47.91 is not arbitrary. It is the value that normalises the modifier to
#: exactly 1.0 at T = 9.291 C, the Rothamsted mean annual temperature marked on
#: Figure 2 of the model description. That is the only normalisation in the
#: model, and the curve is then monotonically increasing with NO optimum and no
#: supra-optimal decline: the official code comments give the range as
#: "rate modifying fator for temperature (0.0 - ~5.0)" and Figure 2 is still
#: climbing at 30 C. So the factor legitimately exceeds 1.0 -- it multiplies the
#: compartment rate constant k directly and is not a normalised modifier.
TEMP_FACTOR_NUMERATOR = 47.91
TEMP_FACTOR_A = 106.06
TEMP_FACTOR_B = 18.27

#: The official Fortran, Python and R all hard-zero the factor below -5 C:
#:     IF(TEMP.LT.-5.0) RM_TMP = 0.0
#: This is a numerical guard rather than a physiological threshold -- the curve
#: is already about 0.016 at -5 C -- and it is absent from the published equation,
#: so it belongs in the implementation. It also means frozen soils return 0.0 and
#: decomposition simply stops, rather than raising.
TEMP_FACTOR_ZERO_BELOW_C = -5.0


def temp_factor(tmean_c: float) -> float:
    """RothC-26.3 temperature rate modifier (dimensionless, >= 0).

    Implements the published equation exactly, including the official low
    temperature cut-off. See the module-level constants for the citation and for
    why 47.91 is a constant rather than a site calibration.

    Two earlier claims in this file's history were wrong and are withdrawn:

    * that the reciprocal exponent made the shape invalid -- it does not. RothC's
      temperature response is intentionally monotonically increasing, with
      **no optimum and no supra-optimal decline**. Figure 2 of the model
      description plots 0 to 5 over -10 to 30 C and the curve is still climbing
      at 30 C, and the official code comments give the range as
      "rate modifying fator for temperature (0.0 - ~5.0)". The factor
      multiplies the compartment rate constant k directly and is not normalised
      to a maximum, so exceeding 1.0 is correct;
    * that the numerator might be a site-dependent ``2C`` -- it is not. Every
      authoritative rendering carries 47.91.

    Measured values with the published coefficients:

        T (C)   -5      0      5    9.291     10     20     30
        RM_Tmp  0.016  0.144  0.497   1.000  1.099  2.822  4.791

    A prior version used 47.9, which puts the normalisation point at 9.247 C
    instead of 9.291 C, and refused at -18.3 C instead of zeroing below -5 C.
    """
    t = float(tmean_c)
    if t < TEMP_FACTOR_ZERO_BELOW_C:
        return 0.0
    return float(TEMP_FACTOR_NUMERATOR / (1.0 + np.exp(TEMP_FACTOR_A / (t + TEMP_FACTOR_B))))


#: Soil-moisture deficit at which the moisture response changes slope, as a
#: fraction of the maximum deficit.
_MOISTURE_BREAKPOINT = 0.444

#: Rate modifier at the wettest end (no deficit) and at maximum deficit.
_MOISTURE_MAX = 1.0
_MOISTURE_FLOOR = 0.2


def water_factor(smd_mm: float, max_smd_mm: float) -> float:
    """RothC moisture rate modifier (piecewise linear, dimensionless, 0.2..1.0).

    Two linear segments meeting at ``_MOISTURE_BREAKPOINT * max_smd_mm``. The
    value at the join is derived once and shared by both segments, so the join is
    continuous *by construction* rather than by coincidence.

    The previous version computed each segment independently. At the breakpoint
    the lower branch returned 0.6448 and the upper branch 0.3597 for the same
    soil moisture, so the modifier dropped by 0.285 as the soil dried. That made
    the moisture response non-monotonic over its most-used range, and a pixel or
    a month straddling the breakpoint decomposed at a materially different rate.
    Because this function is the shared root of ``run_rothc`` and the ECSI model,
    the defect reached both.

    ``max_smd_mm <= 0`` returns 1.0 (no deficit information available).
    """
    if max_smd_mm <= 0:
        return 1.0

    smd = min(max(smd_mm, 0.0), max_smd_mm)
    breakpoint_mm = _MOISTURE_BREAKPOINT * max_smd_mm

    # Lower segment: maximum modifier at zero deficit, down to the join value.
    at_breakpoint = _MOISTURE_FLOOR + (_MOISTURE_MAX - _MOISTURE_FLOOR) * (
        (max_smd_mm - breakpoint_mm) / max_smd_mm
    )
    if smd <= breakpoint_mm:
        return _MOISTURE_FLOOR + (_MOISTURE_MAX - _MOISTURE_FLOOR) * (
            (max_smd_mm - smd) / max_smd_mm
        )

    # Upper segment: from the join value down to the floor at maximum deficit.
    remaining = max_smd_mm - breakpoint_mm
    if remaining <= 0:
        return at_breakpoint
    t = (smd - breakpoint_mm) / remaining
    return at_breakpoint + t * (_MOISTURE_FLOOR - at_breakpoint)


def initial_pools(initial_soc_t_ha: float) -> tuple[dict[str, float], float]:
    """Split total SOC into IOM + the four active pools (RothC defaults).

    Note: the RothC IOM estimator ``IOM = 0.049 * SOC^1.139`` is itself
    clay-independent, so this function takes no clay argument.
    """
    iom = 0.049 * initial_soc_t_ha**1.139
    active = max(initial_soc_t_ha - iom, 0.0)
    pools = {pool: active * frac for pool, frac in INITIAL_SPLIT.items()}
    return pools, iom


def run_rothc(
    initial_soc_t_ha: float,
    clay_pct: float,
    monthly: list[MonthClimate],
    residue_c_t_ha_per_month: float = 0.0,
    manure_c_t_ha_per_month: float = 0.0,
    plant_retainment: float = PLANT_RETAINMENT,
    years: int = 1,
) -> dict:
    """Run the monthly RothC loop for ``years`` years.

    Args:
        initial_soc_t_ha: total SOC (0-30 cm equivalent) at start, tC/ha.
        clay_pct: soil clay content (used for IOM estimation), %.
        monthly: 12 (or more) MonthClimate slices; repeated each year.
        residue_c_t_ha_per_month: plant residue carbon input, tC/ha/month.
        manure_c_t_ha_per_month: manure carbon input, tC/ha/month
            (routed with the same 59/41 split — documented simplification).
        plant_retainment: RothC P modifier (0.6 default).
        years: number of years to simulate.

    Returns:
        Dict with final pools, SOC before/after, annual delta, respired CO2
        and CO2-equivalent (delta * 3.67).
    """
    if not monthly:
        raise ValueError("monthly climate list must not be empty")
    pools, iom = initial_pools(initial_soc_t_ha)
    co2_fraction, stab_fraction = stabilization_split(clay_pct)
    input_c = max(residue_c_t_ha_per_month + manure_c_t_ha_per_month, 0.0)
    cumulative_co2 = 0.0

    for _ in range(years):
        for mc in monthly:
            t_mod = temp_factor(mc.tmean_c)
            w_mod = water_factor(mc.smd_mm, mc.max_smd_mm)
            rate = {p: RATES[p] / 12.0 * t_mod * w_mod * plant_retainment for p in pools}
            decomposed = {p: pools[p] * (1.0 - np.exp(-rate[p])) for p in pools}

            co2 = sum(decomposed[p] * co2_fraction for p in pools)
            stabilized = sum(decomposed[p] * stab_fraction for p in pools)
            bio_in = stabilized * BIO_FRAC
            hum_in = stabilized * HUM_FRAC

            pools["DPM"] = pools["DPM"] - decomposed["DPM"] + input_c * RESIDUE_SPLIT["DPM"]
            pools["RPM"] = pools["RPM"] - decomposed["RPM"] + input_c * RESIDUE_SPLIT["RPM"]
            pools["BIO"] = pools["BIO"] - decomposed["BIO"] + bio_in
            pools["HUM"] = pools["HUM"] - decomposed["HUM"] + hum_in
            cumulative_co2 += co2

    soc_before = initial_soc_t_ha
    soc_after = sum(pools.values()) + iom
    delta_yr = (soc_after - soc_before) / years
    return {
        "pools_t_ha": {k: float(round(v, 4)) for k, v in pools.items()},
        "iom_t_ha": float(round(iom, 4)),
        "soc_before_t_ha": round(soc_before, 4),
        "soc_after_t_ha": round(soc_after, 4),
        "soc_change_t_ha_yr": round(delta_yr, 4),
        "co2_respired_t_ha": round(cumulative_co2, 4),
        "co2e_t_ha": round(delta_yr * 3.67, 4),
        "co2_fraction": round(co2_fraction, 4),
        "stabilized_fraction": round(stab_fraction, 4),
        "data_source": "simulated",
        "model": "RothC (in-house port, pending reference validation)",
    }
