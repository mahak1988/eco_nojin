"""Chain orchestrator (Phase 3, sprint 1): RUSLE -> AquaCrop -> RothC.

Executes the available model runners for one site + scenario and assembles
a ChainResult with provenance labels. The chain is pure (no DB access) so
it is unit-testable; the API layer wires persistence later.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import structlog

from engine.hydroma.simulation import weather_source
from engine.hydroma.simulation.contracts import (
    ChainInputs,
    ChainResult,
    HECRASInput,
    HECRASOutput,
    MonthClimate,
    RothCInput,
    RUSLEInput,
    ScenarioParams,
    SWATInput,
    SWATOutput,
    WEAPInput,
    WEAPOutput,
)
from engine.hydroma.simulation.hecras import HecRasUnavailable, simulate_hecras
from engine.hydroma.simulation.runners.aquacrop_runner import AquaCropRunner
from engine.hydroma.simulation.weap import simulate_weap
from engine.hydroma.simulation.weather_source import growing_season_window

logger = structlog.get_logger()

#: Carbon fraction of plant-residue dry matter, for the RothC carbon input.
#: RothC operates on carbon mass; the chain contract carries residue dry matter.
_RESIDUE_C_FRACTION = 0.45


def _rusle(
    r_factor: float, k_factor: float, ls_factor: float, c_factor: float, p_factor: float
) -> float:
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
        MonthClimate(
            year=2020, month=m, tmean_c=12.0 + 2.0 * ((m - 1) % 12), smd_mm=30.0, max_smd_mm=60.0
        )
        for m in range(1, 13)
    ]


def _run_rusle(input_data: RUSLEInput, scenario: ScenarioParams) -> dict:
    """Placeholder for RUSLE execution."""
    before = _rusle(
        input_data.rainfall_erosivity,
        input_data.soil_erodibility,
        input_data.slope_length_factor,
        input_data.cover_factor,
        input_data.management_factor,
    )
    after = _rusle(
        input_data.rainfall_erosivity,
        input_data.soil_erodibility,
        input_data.slope_length_factor,
        input_data.cover_factor * scenario.c_factor_factor,
        input_data.management_factor * scenario.p_factor,
    )
    return {
        "erosion_before_t_ha": before,
        "erosion_after_t_ha": after,
        "reduction_pct": (before - after) / before * 100.0 if before > 0 else 0.0,
        "data_source": "simulated",
        "model": "RUSLE (C++ core or analytic product)",
    }


def _run_rothc(input_data: RothCInput, monthly: list[MonthClimate], years: int = 1) -> dict:
    """Run the real RothC-26.3 port in ``runners/rothc_runner.py``.

    The previous implementation returned ``soc_after = soc_before * 0.95`` --
    carbon always decayed by exactly 5% per year regardless of climate, clay
    content or residue input -- while advertising itself as
    ``"RothC (in-house port, pending reference validation)"``. That label
    pointed at a real, validated implementation that was never called.

    The real port takes soil-moisture deficit directly from ``MonthClimate.smd_mm``
    and never takes rainfall, which also removes the previous call's unit
    conflation (SMD in mm was being passed as ``rainfall_data`` in mm).
    """
    from engine.hydroma.simulation.runners.rothc_runner import run_rothc

    result = run_rothc(
        initial_soc_t_ha=input_data.soil_organic_carbon_t_ha,
        clay_pct=input_data.clay_content_percent,
        monthly=monthly,
        # RothC inputs are carbon; the contract field is residue dry matter.
        residue_c_t_ha_per_month=float(input_data.crop_residues_t_ha) * _RESIDUE_C_FRACTION,
        years=years,
    )
    return {
        "soc_before_t_ha": result["soc_before_t_ha"],
        "soc_after_t_ha": result["soc_after_t_ha"],
        "soc_change_t_ha_yr": result["soc_change_t_ha_yr"],
        "co2_respired_t_ha": result["co2_respired_t_ha"],
        "co2e_t_ha": result["co2e_t_ha"],
        "final_pools_t_ha": result.get("pools_t_ha"),
        "iom_t_ha": result.get("iom_t_ha"),
        "co2_fraction": result.get("co2_fraction"),
        "stabilized_fraction": result.get("stabilized_fraction"),
        "data_source": "simulated",
        "model": "RothC-26.3 (in-house port, monthly loop)",
    }


def _run_swat_plus(input_data: SWATInput) -> dict | None:
    """Run the real SWAT+ binary; return ``None`` when it is unavailable.

    The previous implementation returned seven constant arrays
    (``runoff_m3=[1000.0]*n`` and so on) and, unlike every other chain step,
    carried **no** provenance label, so the fabricated hydrology was
    indistinguishable from a real run downstream.

    ``SwatRunner`` refuses to fabricate when the binary or project directory is
    missing, which is the behaviour the chain should inherit. Returning ``None``
    lets the caller record an explicit "not computed" reason and skip the two
    steps that consume SWAT+ output, instead of reporting invented numbers.
    """
    from engine.hydroma.simulation.runners.swat_runner import (
        SwatConfig,
        SwatRunner,
        SwatUnavailable,
    )

    project_dir = os.environ.get("SWAT_PROJECT_DIR", "")
    try:
        config = SwatConfig(
            executable=os.environ.get("SWAT_EXECUTABLE", ""),
            project_dir=project_dir or ".",
        )
        result = SwatRunner(config).run()
    except SwatUnavailable as exc:
        logger.info("SWAT+ unavailable, hydrology steps skipped: %s", exc)
        return None
    except Exception as exc:
        logger.warning("SWAT+ run failed, hydrology steps skipped: %s", exc)
        return None

    return {
        "land_profile_id": input_data.land_profile_id,
        "start_date": input_data.start_date,
        "end_date": input_data.end_date,
        "data_source": "simulated",
        "model": "SWAT+ (binary, subprocess)",
        **result,
    }


def _run_weap(input_data: SWATOutput) -> WEAPOutput:
    """Placeholder for WEAP execution."""
    demand_data = [200.0] * len(input_data.water_yield_m3)
    return simulate_weap(
        WEAPInput(
            land_profile_id="default",
            water_demand_data=demand_data,
            water_supply_data=input_data.water_yield_m3,
            allocation_rules=[{"priority": 1, "sector": "municipal"}],
            start_date=input_data.start_date,
            end_date=input_data.end_date,
        )
    )


def _run_hecras(input_data: SWATOutput) -> HECRASOutput:
    """Placeholder for HEC-RAS execution."""
    return simulate_hecras(
        HECRASInput(
            land_profile_id="default",
            channel_geometry={"length_km": 10.0, "width_avg_m": 20.0, "slope": 0.001},
            boundary_conditions={
                "upstream_flow_m3s": [r / (24 * 3600) for r in input_data.runoff_m3[:10]],
                "downstream_stage_m": 95.0,
            },
            initial_conditions={"water_surface_m": 96.0},
            start_date=input_data.start_date,
            end_date=input_data.start_date + timedelta(days=9),
        )
    )


def run_chain(
    inputs: ChainInputs, progress_cb: Callable[[str, int], None] | None = None
) -> ChainResult:
    """Execute the full simulation chain: SWAT+ -> RUSLE -> RothC -> AquaCrop -> WEAP -> HEC-RAS."""
    outputs: dict[str, Any] = {}
    status = "ok"
    message = ""
    weather_failed = False

    try:
        if progress_cb:
            progress_cb("swat_plus", 5)
        # 1) SWAT+ -- real binary or an explicit "not computed".
        swat_in = SWATInput(
            land_profile_id=inputs.site_id,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            climate_data=[],
            soil_data=[],
        )
        swat_out = _run_swat_plus(swat_in)
        if swat_out is None:
            # Do not fabricate hydrology. Record why, and let the two dependent
            # steps report themselves as not computed.
            outputs["swat_plus"] = {
                "status": "not_computed",
                "data_source": "unavailable",
                "model": "SWAT+ (binary, subprocess)",
                "reason": "SWAT+ executable or project directory unavailable",
            }
        else:
            outputs["swat_plus"] = swat_out

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
        rusle_out = _run_rusle(rusle_in, inputs.scenario)
        outputs["rusle"] = rusle_out

        if progress_cb:
            progress_cb("rothc", 55)
        # 3) RothC -- real monthly loop.
        #
        # The chain reports an unavailable step explicitly rather than emitting a
        # number. That matters here specifically because the implemented RothC
        # temperature response is not a bounded rate modifier and now refuses
        # rather than returning a value up to 4.79x too large; see temp_factor().
        monthly = inputs.monthly_climate or _default_monthly()
        rothc_in = RothCInput(
            land_profile_id=inputs.site_id,
            soil_organic_carbon_t_ha=inputs.initial_soc_t_ha,
            crop_residues_t_ha=inputs.residue_c_t_ha_per_month,
            temperature_data=[m.tmean_c for m in monthly],
            rainfall_data=[m.smd_mm for m in monthly],
            clay_content_percent=inputs.clay_pct,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )
        try:
            rothc_out = _run_rothc(rothc_in, monthly, years=inputs.years)
        except ValueError as exc:
            logger.warning("RothC step not computed: %s", exc)
            outputs["rothc"] = {
                "status": "not_computed",
                "data_source": "unavailable",
                "model": "RothC-26.3 (in-house port, monthly loop)",
                "reason": str(exc),
            }
            status = "partial"
        else:
            outputs["rothc"] = rothc_out

        if progress_cb:
            progress_cb("aquacrop", 75)
        # 4) AquaCrop
        weather = None
        weather_error = ""
        if inputs.use_real_weather and inputs.lat is not None and inputs.lon is not None:
            try:
                start_d, end_d = growing_season_window(inputs.planting_date, inputs.harvest_date)
                weather = weather_source.fetch_daily_weather(
                    inputs.lat, inputs.lon, start_d.isoformat(), end_d.isoformat()
                )
            except Exception as exc:
                logger.warning("Weather fetch failed: %s", exc)
                weather_failed = True
                # Capture the real cause. The previous code read `message`, which
                # is still "" at this point, so the generic string always won and
                # the actionable exception was always discarded.
                weather_error = str(exc) or exc.__class__.__name__
        aquacrop_out = AquaCropRunner().run(
            crop=inputs.crop,
            soil_type=inputs.soil_type,
            planting_date=inputs.planting_date,
            harvest_date=inputs.harvest_date,
            weather=weather,
        )
        aquacrop_out["weather_source"] = (
            "open-meteo (real)" if weather is not None else "synthetic (fallback)"
        )
        if weather_failed:
            aquacrop_out["weather_error"] = weather_error or "Weather fetch failed"
        outputs["aquacrop"] = aquacrop_out

        # 5) WEAP -- consumes SWAT+ supply, so only meaningful when SWAT+ ran.
        if swat_out is not None:
            outputs["weap"] = _run_weap(swat_out)
        else:
            outputs["weap"] = {
                "status": "not_computed",
                "data_source": "unavailable",
                "reason": "requires SWAT+ water supply",
            }

        # 6) HEC-RAS -- consumes SWAT+ runoff, so only meaningful when SWAT+ ran.
        #
        # Both conditions are reported, not just the first. HEC-RAS is an
        # external executable, so a working SWAT+ binary is not sufficient to
        # make this step computable, and the reason a caller sees should say
        # which of the two was missing.
        if swat_out is not None:
            try:
                outputs["hecras"] = _run_hecras(swat_out)
            except HecRasUnavailable as exc:
                outputs["hecras"] = {
                    "status": "not_computed",
                    "data_source": "unavailable",
                    "model": "HEC-RAS (external executable)",
                    "reason": str(exc),
                }
        else:
            outputs["hecras"] = {
                "status": "not_computed",
                "data_source": "unavailable",
                "model": "HEC-RAS (external executable)",
                "reason": "requires SWAT+ runoff",
            }

    except Exception as exc:
        logger.exception("Chain execution failed")
        status = "failed"
        message = str(exc)

    if weather_failed and status == "ok":
        status = "partial"

    return ChainResult(
        site_id=inputs.site_id,
        scenario=inputs.scenario.name,
        area_ha=inputs.area_ha,
        outputs=outputs,
        status=status,
        message=message,
    )
