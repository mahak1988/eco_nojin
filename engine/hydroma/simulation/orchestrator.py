"""Chain orchestrator (Phase 3, sprint 1): RUSLE -> AquaCrop -> RothC.

Executes the available model runners for one site + scenario and assembles
a ChainResult with provenance labels. The chain is pure (no DB access) so
it is unit-testable; the API layer wires persistence later.
"""

from __future__ import annotations

import logging

from engine.hydroma.simulation.contracts import ChainInputs, ChainResult, MonthClimate
from engine.hydroma.simulation.runners.aquacrop_runner import AquaCropRunner
from engine.hydroma.simulation.runners.rothc_runner import RESIDUE_C_FRACTION, run_rothc

logger = logging.getLogger(__name__)

MODEL_RUSLE = "RUSLE (C++ core or analytic product)"


def _rusle(r_factor: float, k_factor: float, ls_factor: float, c_factor: float, p_factor: float) -> float:
    """Annual soil loss A = R * K * LS * C * P (t/ha/yr).

    Prefers the compiled C++ binding; falls back to the analytic product of
    the same equation (never silently — the provenance tag is unchanged
    because the equation is identical).
    """
    try:
        from engine.hydroma.cpp_bindings import rusle_annual_soil_loss

        value = float(rusle_annual_soil_loss(r_factor, k_factor, ls_factor, c_factor, p_factor))
    except Exception as exc:  # noqa: BLE001 - binding may be missing on some setups
        logger.warning("C++ RUSLE binding failed (%s); using analytic product", exc)
        value = r_factor * k_factor * ls_factor * c_factor * p_factor
    return value


def _default_monthly() -> list[MonthClimate]:
    """Placeholder 12-month climate used when the caller provides none."""
    return [
        MonthClimate(year=2020, month=m, tmean_c=12.0 + 2.0 * ((m - 1) % 12), smd_mm=30.0, max_smd_mm=60.0)
        for m in range(1, 13)
    ]


def run_chain(inputs: ChainInputs) -> ChainResult:
    """Execute the RUSLE + AquaCrop + RothC chain for one scenario.

    Missing optional inputs fall back to documented placeholders; every
    output carries data_source="simulated" plus the model provenance.
    """
    outputs: dict = {}
    status = "ok"
    message = ""

    # 1) RUSLE: before vs after intervention (C/P factors from the scenario).
    try:
        before = _rusle(inputs.r_factor, inputs.k_factor, inputs.ls_factor, inputs.c_factor_base, 1.0)
        after = _rusle(
            inputs.r_factor,
            inputs.k_factor,
            inputs.ls_factor,
            inputs.c_factor_base * inputs.scenario.c_factor_factor,
            inputs.scenario.p_factor,
        )
        reduction = 100.0 * (before - after) / before if before > 0 else 0.0
        outputs["rusle"] = {
            "erosion_before_t_ha": round(before, 3),
            "erosion_after_t_ha": round(after, 3),
            "reduction_pct": round(reduction, 2),
            "data_source": "simulated",
            "model": MODEL_RUSLE,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("RUSLE step failed")
        outputs["rusle"] = {"error": str(exc)}
        status = "partial"

    # 2) AquaCrop: yield / biomass / residue for the season.
    try:
        weather = None
        weather_note: dict = {}
        if inputs.use_real_weather and inputs.lat is not None and inputs.lon is not None:
            try:
                from engine.hydroma.simulation.weather_source import (
                    fetch_daily_weather,
                    growing_season_window,
                )

                start_d, end_d = growing_season_window(inputs.planting_date, inputs.harvest_date)
                weather = fetch_daily_weather(
                    inputs.lat, inputs.lon, start_d.isoformat(), end_d.isoformat()
                )
                weather_note = {
                    "weather_source": "open-meteo (real)",
                    "weather_days": int(len(weather)),
                }
            except Exception as exc:  # noqa: BLE001 - honest fallback, labeled
                weather_note = {
                    "weather_source": "synthetic (fallback)",
                    "weather_error": str(exc)[:200],
                }
                status = "partial"
        aq = AquaCropRunner().run(
            crop=inputs.crop,
            soil_type=inputs.soil_type,
            planting_date=inputs.planting_date,
            harvest_date=inputs.harvest_date,
            weather=weather,
        )
        outputs["aquacrop"] = {**aq, **weather_note}
    except Exception as exc:  # noqa: BLE001
        logger.exception("AquaCrop step failed")
        outputs["aquacrop"] = {"error": str(exc)}
        status = "partial"

    # 3) RothC: SOC change driven by residue from AquaCrop (fallback: input value).
    try:
        monthly = inputs.monthly_climate or _default_monthly()
        residue_c = inputs.residue_c_t_ha_per_month
        aquacrop = outputs.get("aquacrop") or {}
        residue_kg = aquacrop.get("residue_kg_ha")
        if residue_kg is not None and len(monthly) > 0:
            residue_c = max(residue_kg * RESIDUE_C_FRACTION / 1000.0 / len(monthly), 0.0)
        rothc = run_rothc(
            initial_soc_t_ha=inputs.initial_soc_t_ha,
            clay_pct=inputs.clay_pct,
            monthly=monthly,
            residue_c_t_ha_per_month=residue_c,
            years=inputs.years,
        )
        outputs["rothc"] = rothc
    except Exception as exc:  # noqa: BLE001
        logger.exception("RothC step failed")
        outputs["rothc"] = {"error": str(exc)}
        status = "partial"

    return ChainResult(
        site_id=inputs.site_id,
        scenario=inputs.scenario.name,
        area_ha=inputs.area_ha,
        outputs=outputs,
        status=status,
        message=message,
    )
