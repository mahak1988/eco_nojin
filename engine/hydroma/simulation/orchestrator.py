"""Chain orchestrator (Phase 3, sprint 1): RUSLE -> AquaCrop -> RothC.

Executes the available model runners for one site + scenario and assembles
a ChainResult with provenance labels. The chain is pure (no DB access) so
it is unit-testable; the API layer wires persistence later.
"""

from __future__ import annotations
import structlog

logger = structlog.get_logger()

import logging
from datetime import date, timedelta
from typing import Any, Callable

from engine.hydroma.simulation.contracts import (
    AquaCropInput,
    ChainInputs,
    ChainResult,
    HECRASInput,
    HECRASOutput,
    MonthClimate,
    RothCInput,
    RUSLEInput,
    SWATInput,
    SWATOutput,
    WEAPInput,
    WEAPOutput,
)
from engine.hydroma.simulation.hecras import simulate_hecras
from engine.hydroma.simulation.runners.aquacrop_runner import AquaCropRunner
from engine.hydroma.simulation.weap import simulate_weap
from engine.hydroma.simulation.weather_source import fetch_daily_weather, growing_season_window

logger = logging.getLogger(__name__)


def _rusle(r_factor: float, k_factor: float, ls_factor: float, c_factor: float, p_factor: float) -> float:
    """Annual soil loss A = R * K * LS * C * P (t/ha/yr).

    Prefers the compiled C++ binding; falls back to the analytic product of
    the same equation (never silently — the provenance tag is unchanged
    because the equation is identical).
    """
    try:
        from engine.hydroma.cpp_bindings import rusle_annual_soil_loss

        value = float(rusle_annual_soil_loss(r_factor, k_factor, ls_factor, c_factor, p_factor))
    except Exception as exc:
        logger.warning("C++ RUSLE binding failed (%s); using analytic product", exc)
        value = r_factor * k_factor * ls_factor * c_factor * p_factor
    return value


def _default_monthly() -> list[MonthClimate]:
    """Placeholder 12-month climate used when the caller provides none."""
    return [
        MonthClimate(year=2020, month=m, tmean_c=12.0 + 2.0 * ((m - 1) % 12), smd_mm=30.0, max_smd_mm=60.0)
        for m in range(1, 13)
    ]


def _run_swat_plus(input_data: SWATInput) -> SWATOutput:
    """Placeholder for SWAT+ execution."""
    logger.info(f"Running SWAT+ for land profile {input_data.land_profile_id}")
    num_days = (input_data.end_date - input_data.start_date).days
    return SWATOutput(
        runoff_m3=[1000.0] * num_days,
        soil_water_content=[0.25] * num_days,
        recharge_mm=[5.0] * num_days,
        groundwater_recharge_mm=[2.0] * num_days,
        sediment_yield_t=[0.1] * num_days,
        et_mm=[3.0] * num_days,
        water_yield_m3=[800.0] * num_days
    )


def _run_weap(input_data: SWATOutput) -> WEAPOutput:
    """Placeholder for WEAP execution."""
    demand_data = [200.0] * len(input_data.water_yield_m3)
    return simulate_weap(WEAPInput(
        land_profile_id="default",
        water_demand_data=demand_data,
        water_supply_data=input_data.water_yield_m3,
        allocation_rules=[{"priority": 1, "sector": "municipal"}],
        start_date=input_data.start_date,
        end_date=input_data.end_date
    ))


def _run_hecras(input_data: SWATOutput) -> HECRASOutput:
    """Placeholder for HEC-RAS execution."""
    return simulate_hecras(HECRASInput(
        land_profile_id="default",
        channel_geometry={"length_km": 10.0, "width_avg_m": 20.0, "slope": 0.001},
        boundary_conditions={
            "upstream_flow_m3s": [r / (24 * 3600) for r in input_data.runoff_m3[:10]],
            "downstream_stage_m": 95.0
        },
        initial_conditions={"water_surface_m": 96.0},
        start_date=input_data.start_date,
        end_date=input_data.start_date + timedelta(days=9)
    ))


def run_chain(inputs: ChainInputs, progress_cb: Callable[[str, int], None] | None = None) -> ChainResult:
    """Execute the full simulation chain: SWAT+ -> RUSLE -> RothC -> AquaCrop -> WEAP -> HEC-RAS."""
    outputs: dict[str, Any] = {}
    status = "ok"
    message = ""

    try:
        if progress_cb:
            progress_cb("swat_plus", 5)
        # 1) SWAT+
        swat_in = SWATInput(
            land_profile_id=inputs.site_id,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            climate_data=[],
            soil_data=[],
        )
        swat_out = _run_swat_plus(swat_in)
        outputs["swat_plus"] = swat_out.model_dump()

        if progress_cb:
            progress_cb("rusle", 30)
        # 2) RUSLE
        rusle_in = RUSLEInput(
            land_profile_id=inputs.site_id,
            rainfall_erosivity=inputs.r_factor,
            soil_erodibility=inputs.k_factor,
            slope_length_factor=inputs.ls_factor,
            slope_steepness_factor=1.0,
            cover_factor=inputs.c_factor_base,
            management_factor=1.0,
        )
        rusle_out = _run_rusle(rusle_in)
        outputs["rusle"] = rusle_out

        if progress_cb:
            progress_cb("rothc", 55)
        # 3) RothC
        monthly = inputs.monthly_climate or _default_monthly()
        rothc_in = RothCInput(
            land_profile_id=inputs.site_id,
            soil_organic_carbon_t_ha=inputs.initial_soc_t_ha,
            crop_residues_t_ha=2.0,
            temperature_data=[m.tmean_c for m in monthly],
            rainfall_data=[m.smd_mm for m in monthly],
            clay_content_percent=inputs.clay_pct,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )
        rothc_out = _run_rothc(rothc_in)
        outputs["rothc"] = rothc_out

        if progress_cb:
            progress_cb("aquacrop", 75)
        # 4) AquaCrop
        weather = None
        if inputs.use_real_weather and inputs.lat is not None and inputs.lon is not None:
            try:
                start_d, end_d = growing_season_window(inputs.planting_date, inputs.harvest_date)
                weather = fetch_daily_weather(inputs.lat, inputs.lon, start_d.isoformat(), end_d.isoformat())
            except Exception as exc:
                logger.warning("Weather fetch failed: %s", exc)
        aquacrop_in = AquaCropInput(
            land_profile_id=inputs.site_id,
            crop_type=inputs.crop,
            climate_data=[],
            soil_data=[],
            irrigation_data=[],
            planting_date=inputs.planting_date,
            harvest_date=inputs.harvest_date,
        )
        aquacrop_out = AquaCropRunner().run(
            crop=inputs.crop,
            soil_type=inputs.soil_type,
            planting_date=inputs.planting_date,
            harvest_date=inputs.harvest_date,
            weather=weather,
        )
        outputs["aquacrop"] = aquacrop_out

        # 5) WEAP
        weap_out = _run_weap(swat_out)
        outputs["weap"] = weap_out

        # 6) HEC-RAS
        hecras_out = _run_hecras(swat_out)
        outputs["hecras"] = hecras_out

    except Exception as exc:
        logger.exception("Chain execution failed")
        status = "failed"
        message = str(exc)

    return ChainResult(
        site_id=inputs.site_id,
        scenario=inputs.scenario.name,
        area_ha=inputs.area_ha,
        outputs=outputs,
        status=status,
        message=message,
    )
