"""RothC (Rothamsted Carbon Model) — in-house Python port (Phase 3, sprint 1).

Implements the monthly RothC-26.3 scheme: four active pools (DPM, RPM, BIO,
HUM) + inert IOM, temperature and moisture rate modifiers, and the standard
stabilization split (46% of decomposed C stabilized; of that, 46% to BIO and
54% to HUM).

HONESTY / VALIDATION STATUS:
    Parameter values follow Coleman & Jenkinson (1996). This port must be
    validated against the official RothC-26.3 reference outputs in sprint 2
    before it is used for reporting; results are labeled
    data_source="simulated" with model="RothC (in-house port, ...)".
"""

from __future__ import annotations

import numpy as np

from engine.hydroma.simulation.contracts import MonthClimate

# Annual rate constants (yr^-1) for the reference state: ~10 C (temperature
# modifier = 1), optimal moisture, bare soil (RothC-26.3 standard values).
RATES: dict[str, float] = {"DPM": 10.0, "RPM": 0.3, "BIO": 0.66, "HUM": 0.02}
# Fraction of decomposed C that is stabilized into BIO+HUM (rest is CO2).
X_STAB: float = 0.46
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


def temp_factor(tmean_c: float) -> float:
    """RothC temperature rate modifier (dimensionless, >=0)."""
    return 47.9 / (1.0 + np.exp(106.06 / (tmean_c + 18.27)))


def water_factor(smd_mm: float, max_smd_mm: float) -> float:
    """RothC moisture rate modifier (piecewise, dimensionless, 0..1).

    Uses the documented piecewise form; ``max_smd_mm`` <= 0 returns 1.0.
    """
    if max_smd_mm <= 0:
        return 1.0
    if smd_mm <= 0.444 * max_smd_mm:
        return 0.2 + 0.8 * (max_smd_mm - smd_mm) / max_smd_mm
    return 0.2 * (1.444 * max_smd_mm - smd_mm) / (0.556 * max_smd_mm)


def initial_pools(initial_soc_t_ha: float, clay_pct: float) -> tuple[dict[str, float], float]:
    """Split total SOC into IOM + the four active pools (RothC defaults)."""
    iom = 0.049 * initial_soc_t_ha ** 1.139
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
    pools, iom = initial_pools(initial_soc_t_ha, clay_pct)
    input_c = max(residue_c_t_ha_per_month + manure_c_t_ha_per_month, 0.0)
    cumulative_co2 = 0.0

    for _ in range(years):
        for mc in monthly:
            t_mod = temp_factor(mc.tmean_c)
            w_mod = water_factor(mc.smd_mm, mc.max_smd_mm)
            rate = {p: RATES[p] / 12.0 * t_mod * w_mod * plant_retainment for p in pools}
            decomposed = {p: pools[p] * (1.0 - np.exp(-rate[p])) for p in pools}

            co2 = sum(decomposed[p] * (1.0 - X_STAB) for p in pools)
            stabilized = sum(decomposed[p] * X_STAB for p in pools)
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
        "data_source": "simulated",
        "model": "RothC (in-house port, pending reference validation)",
    }
