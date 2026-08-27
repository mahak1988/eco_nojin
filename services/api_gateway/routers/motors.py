"""Scientific Motors API - Real Execution Endpoints."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from shapely.geometry import Polygon

from services.map_engine.orchestrator import MapOrchestrator
from services.scientific_motors.aquacrop import AquaCropMotor
from services.scientific_motors.base import MotorParameters
from services.scientific_motors.hecras import HECRASMOTOR
from services.scientific_motors.rothc import RothCMotor
from services.scientific_motors.swat_plus import SWATPlusMotor
from services.scientific_motors.whatif_engine import WhatIfMotor

router = APIRouter(prefix="/api/motors", tags=["scientific-motors"])

# In-memory storage for results (in production, use Redis/DB)
_motor_results: dict[str, dict[str, Any]] = {}


# ============ Pydantic Models ============

class MotorRunRequest(BaseModel):
    motor_type: str = Field(..., description="Motor type: swat_plus, aquacrop, rothc, hecras, what_if")
    scenario_name: str = Field(default="baseline")
    start_date: str = Field(default="2026-01-01")
    end_date: str = Field(default="2026-12-31")
    time_step: str = Field(default="daily")
    region_bounds: list[float] = Field(
        default=[51.00, 35.00, 51.05, 35.05],
        description="[minx, miny, maxx, maxy]",
    )
    parameters: dict[str, Any] = Field(default_factory=dict)


class MotorStatusResponse(BaseModel):
    run_id: str
    status: str
    summary: dict[str, Any] | None = None
    error_message: str | None = None


class ScientificChainRequest(BaseModel):
    """Phase-2 scientific chain: RUSLE + RothC-26.3 + AquaCrop with REAL data."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    crop: str = Field(default="wheat", description="FAO crop name (aquacrop)")
    planting_date: str = Field(default="2025-03-01", description="YYYY-MM-DD")
    years: int = Field(default=20, ge=1, le=100, description="RothC simulation years")
    slope_pct: float = Field(default=10.0, ge=0, le=90)
    practice: str = Field(default="none", description="RUSLE P factor: none/contour/terrace")
    irrigation_threshold_mm: float | None = Field(default=None, ge=0, le=200)
    observed: dict[str, Any] | None = Field(default=None, description="Observed values for KGE (e.g. yield_ton_ha)")
    use_cache: bool = Field(default=True)
    optimize: bool = Field(default=False, description="Run pymoo NSGA-II (surrogate)")
    catchment_km2: float = Field(default=10.0, ge=0.1, le=10000, description="Catchment area for Pywr/HEC-RAS")


class ScientificChainResponse(BaseModel):
    chain_id: str
    cache_hit: bool
    status: str
    location: dict[str, float]
    inputs: dict[str, Any]
    erosion: dict[str, Any]
    swat: dict[str, Any]
    water: dict[str, Any]
    flood: dict[str, Any]
    optimization: dict[str, Any]
    rothc: dict[str, Any]
    aquacrop: dict[str, Any]
    calibration: dict[str, Any]
    data_sources: dict[str, str]
    error: str | None = None


# ============ Helper Functions ============

async def _run_motor_background(
    run_id: str,
    motor_type: str,
    region: Polygon,
    params: MotorParameters,
    custom_params: dict[str, Any],
):
    """Background task to run motor and store results."""
    map_orch = MapOrchestrator()

    try:
        # 1. Fetch required layers
        if motor_type == "swat_plus":
            layers = await map_orch._fetch_layers(["dem", "soil", "landcover", "rainfall"], region)
            motor = SWATPlusMotor()
            result = await motor.execute(layers, params)

        elif motor_type == "aquacrop":
            swat_layers = await map_orch._fetch_layers(["dem", "soil", "landcover", "rainfall"], region)
            swat = SWATPlusMotor()
            swat_result = await swat.execute(swat_layers, params)

            inputs = {
                "soil_water_mm": swat_result.outputs.get("soil_water_mm"),
                "et_mm": swat_result.outputs.get("et_mm"),
            }
            crop = custom_params.get("crop", "wheat")
            motor = AquaCropMotor(crop_type=crop)
            result = await motor.execute(inputs, params)

        elif motor_type == "rothc":
            swat_layers = await map_orch._fetch_layers(["dem", "soil", "landcover", "rainfall"], region)
            swat = SWATPlusMotor()
            swat_result = await swat.execute(swat_layers, params)

            aquacrop = AquaCropMotor(crop_type="wheat")
            aquacrop_params = MotorParameters(
                start_date=params.start_date, end_date=params.end_date,
                time_step="daily", scenario_name="baseline",
                custom_params={"irrigation_mm": 50.0},
            )
            aquacrop_result = await aquacrop.execute(
                {"soil_water_mm": swat_result.outputs.get("soil_water_mm"),
                 "et_mm": swat_result.outputs.get("et_mm")},
                aquacrop_params,
            )

            inputs = {
                "soil_water_mm": swat_result.outputs.get("soil_water_mm"),
                "biomass_ton_ha": aquacrop_result.outputs.get("biomass_ton_ha"),
            }
            motor = RothCMotor(years=custom_params.get("years", 20))
            result = await motor.execute(inputs, params)

        elif motor_type == "hecras":
            layers = await map_orch._fetch_layers(["dem", "landcover"], region)
            swat_layers = await map_orch._fetch_layers(["dem", "soil", "landcover", "rainfall"], region)
            swat = SWATPlusMotor()
            swat_params = MotorParameters(
                start_date=params.start_date, end_date=params.end_date,
                time_step="daily", scenario_name="baseline",
            )
            swat_result = await swat.execute(swat_layers, swat_params)

            inputs = {
                "dem": layers.get("dem"),
                "runoff_mm": swat_result.outputs.get("runoff_mm"),
                "slope": None,
                "landcover": layers.get("landcover"),
            }
            motor = HECRASMOTOR()
            result = await motor.execute(inputs, params)

        elif motor_type == "what_if":
            swat_layers = await map_orch._fetch_layers(["dem", "soil", "landcover", "rainfall"], region)
            swat = SWATPlusMotor()
            swat_result = await swat.execute(swat_layers, params)

            aquacrop = AquaCropMotor(crop_type="wheat")
            aquacrop_result = await aquacrop.execute(
                {"soil_water_mm": swat_result.outputs.get("soil_water_mm"),
                 "et_mm": swat_result.outputs.get("et_mm")},
                params,
            )

            rothc = RothCMotor(years=20)
            rothc_result = await rothc.execute(
                {"soil_water_mm": swat_result.outputs.get("soil_water_mm"),
                 "biomass_ton_ha": aquacrop_result.outputs.get("biomass_ton_ha")},
                params,
            )

            inputs = {
                "baseline_yield": aquacrop_result.outputs.get("yield_ton_ha"),
                "baseline_water": swat_result.outputs.get("et_mm"),
                "baseline_carbon": rothc_result.outputs.get("final_soc_t_ha"),
            }
            motor = WhatIfMotor(n_iterations=custom_params.get("n_iterations", 50))
            result = await motor.execute(inputs, params)
        else:
            _motor_results[run_id] = {
                "status": "failed",
                "error_message": f"Unknown motor type: {motor_type}",
            }
            return

        _motor_results[run_id] = {
            "status": result.status.value,
            "summary": result.summary,
            "error_message": result.error_message,
            "execution_time": result.execution_time_seconds,
            "outputs_keys": list(result.outputs.keys()) if result.outputs else [],
        }

    except Exception as e:
        _motor_results[run_id] = {
            "status": "failed",
            "error_message": str(e),
        }


# ============ Endpoints ============

@router.get("/list")
async def list_motors():
    """List all available scientific motors."""
    return {
        "motors": [
            {
                "type": "swat_plus",
                "name": "SWAT+ Water Balance",
                "icon": "💧",
                "description": "Hydrological simulation (runoff, ET, recharge)",
                "inputs": ["dem", "soil", "landcover", "rainfall"],
            },
            {
                "type": "aquacrop",
                "name": "AquaCrop (FAO)",
                "icon": "🌾",
                "description": "Crop yield prediction (wheat, maize, barley, cotton, tomato)",
                "inputs": ["soil_water_mm", "et_mm"],
            },
            {
                "type": "rothc",
                "name": "RothC Soil Carbon",
                "icon": "🌍",
                "description": "Soil organic carbon dynamics (5-pool model)",
                "inputs": ["soil_water_mm", "biomass_ton_ha"],
            },
            {
                "type": "hecras",
                "name": "HEC-RAS Flood",
                "icon": "🌊",
                "description": "Simplified flood routing and risk mapping",
                "inputs": ["dem", "runoff_mm"],
            },
            {
                "type": "what_if",
                "name": "What-If Scenarios",
                "icon": "🎲",
                "description": "Monte Carlo scenario analysis",
                "inputs": ["baseline_yield", "baseline_water", "baseline_carbon"],
            },
        ]
    }


@router.post("/run")
async def run_motor(request: MotorRunRequest, background_tasks: BackgroundTasks):
    """Start motor execution in background."""
    # Validate motor type
    valid_motors = ["swat_plus", "aquacrop", "rothc", "hecras", "what_if"]
    if request.motor_type not in valid_motors:
        raise HTTPException(400, f"Invalid motor type. Choose from: {valid_motors}")

    # Build region
    b = request.region_bounds
    if len(b) != 4:
        raise HTTPException(400, "region_bounds must be [minx, miny, maxx, maxy]")
    region = Polygon([
        (b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3]), (b[0], b[1]),
    ])

    # Build parameters
    params = MotorParameters(
        start_date=request.start_date,
        end_date=request.end_date,
        time_step=request.time_step,
        scenario_name=request.scenario_name,
        custom_params=request.parameters,
    )

    # Generate run ID
    run_id = f"{request.motor_type}_{request.scenario_name}_{int(time.time())}"

    # Mark as pending
    _motor_results[run_id] = {"status": "running", "summary": None}

    # Launch in background
    background_tasks.add_task(
        _run_motor_background,
        run_id, request.motor_type, region, params, request.parameters,
    )

    return {"run_id": run_id, "status": "running", "message": "Motor started in background"}


@router.post("/chain", response_model=ScientificChainResponse)
async def run_scientific_chain_endpoint(request: ScientificChainRequest):
    """Run the REAL scientific chain for a land parcel:

    RUSLE (rainfall erosivity x SoilGrids K x slope x crop) ->
    RothC-26.3 (pyRothC, real monthly climate + clay/SOC) ->
    AquaCrop (AquaCrop-OSPy, real daily weather + soil texture).

    All inputs come from free sources (Open-Meteo ERA5, ISRIC SoilGrids);
    results are cached by request hash. KGE is computed when observed
    values are provided, otherwise reported as no_observed_data.
    """
    from services.scientific_motors.chain_runner import run_scientific_chain

    return await run_scientific_chain(
        lat=request.lat,
        lon=request.lon,
        crop=request.crop,
        planting_date=request.planting_date,
        years=request.years,
        slope_pct=request.slope_pct,
        practice=request.practice,
        irrigation_threshold_mm=request.irrigation_threshold_mm,
        observed=request.observed,
        use_cache=request.use_cache,
        optimize=request.optimize,
        catchment_km2=request.catchment_km2,
    )


@router.get("/status/{run_id}")
async def get_motor_status(run_id: str):
    """Get status of a motor execution."""
    if run_id not in _motor_results:
        raise HTTPException(404, f"Run ID not found: {run_id}")

    data = _motor_results[run_id]
    return {
        "run_id": run_id,
        "status": data["status"],
        "summary": data.get("summary"),
        "error_message": data.get("error_message"),
        "execution_time": data.get("execution_time"),
        "outputs_keys": data.get("outputs_keys", []),
    }


@router.get("/health")
async def motor_health():
    """Health check."""
    return {
        "status": "healthy",
        "motors_available": 5,
        "active_runs": sum(1 for r in _motor_results.values() if r["status"] == "running"),
    }
