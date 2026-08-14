"""API endpoints for Scenario Engine."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from engine.hydroma.scenarios.climate_scenarios import (
    get_climate_projection, compare_scenarios, apply_climate_change
)
from engine.hydroma.scenarios.crop_scenarios import (
    simulate_crop_yield, compare_crops, CROP_DATABASE
)
from engine.hydroma.scenarios.whatif_engine import (
    Scenario, run_whatif_analysis, generate_climate_transition_scenarios
)
from engine.hydroma.scenarios.monte_carlo import (
    monte_carlo_yield, monte_carlo_climate
)

router = APIRouter(prefix="/api/v1/scenarios", tags=["Scenario Engine"])


# --- Request/Response Models ---

class ClimateRequest(BaseModel):
    scenario: str = Field(..., description="SSP scenario (SSP1-2.6, SSP2-4.5, SSP5-8.5)")
    time_horizon: int = Field(..., ge=2025, le=2100)
    baseline_temp: float = Field(18.0, ge=-20, le=50)
    baseline_precip: float = Field(300.0, ge=0)


class CropRequest(BaseModel):
    crop_type: str = Field(..., description="Crop type from database")
    available_water: float = Field(..., ge=0, description="Available water in mm")
    mean_temp: float = Field(..., ge=-10, le=50)
    co2_concentration: float = Field(420.0, ge=280, le=1000)
    irrigation_efficiency: float = Field(0.6, ge=0.1, le=1.0)


class WhatIfScenario(BaseModel):
    name: str
    crop_type: str
    available_water: float
    mean_temp: float
    co2_concentration: float = 420.0
    irrigation_efficiency: float = 0.6
    description: str = ""


class WhatIfRequest(BaseModel):
    scenarios: List[WhatIfScenario]


class MonteCarloRequest(BaseModel):
    crop_type: str
    mean_water: float = Field(..., ge=0)
    water_std: float = Field(..., ge=0)
    mean_temp: float = Field(..., ge=-10, le=50)
    temp_std: float = Field(..., ge=0)
    n_simulations: int = Field(500, ge=10, le=5000)


# --- Endpoints ---

@router.get("/crops")
def list_available_crops():
    """List all available crops for simulation."""
    return {
        "crops": list(CROP_DATABASE.keys()),
        "count": len(CROP_DATABASE),
    }


@router.post("/climate")
def climate_projection(payload: ClimateRequest):
    """Get climate projection for a scenario."""
    try:
        projection = get_climate_projection(
            payload.scenario,
            payload.time_horizon,
            payload.baseline_temp,
            payload.baseline_precip,
        )
        
        projected = apply_climate_change(
            payload.baseline_temp,
            payload.baseline_precip,
            1500.0,
            projection,
        )
        
        return {
            "projection": projection.__dict__,
            "projected_values": projected,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/climate/compare")
def compare_climate_scenarios(payload: ClimateRequest):
    """Compare all SSP scenarios for a time horizon."""
    results = compare_scenarios(
        payload.time_horizon,
        payload.baseline_temp,
        payload.baseline_precip,
    )
    
    return {
        "time_horizon": payload.time_horizon,
        "scenarios": {k: v.__dict__ for k, v in results.items()},
    }


@router.post("/crop")
def crop_simulation(payload: CropRequest):
    """Simulate crop yield under given conditions."""
    if payload.crop_type not in CROP_DATABASE:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown crop: {payload.crop_type}. Available: {list(CROP_DATABASE.keys())}"
        )
    
    return simulate_crop_yield(
        crop_type=payload.crop_type,
        available_water=payload.available_water,
        mean_temp=payload.mean_temp,
        co2_concentration=payload.co2_concentration,
        irrigation_efficiency=payload.irrigation_efficiency,
    )


@router.post("/crop/compare")
def compare_all_crops(payload: CropRequest):
    """Compare all crops for given water and temperature."""
    return compare_crops(
        available_water=payload.available_water,
        mean_temp=payload.mean_temp,
        co2_concentration=payload.co2_concentration,
    )


@router.post("/whatif")
def whatif_analysis(payload: WhatIfRequest):
    """Run what-if analysis comparing scenarios."""
    scenarios = [Scenario(**s.model_dump()) for s in payload.scenarios]
    return run_whatif_analysis(scenarios)


@router.post("/whatif/climate-transition")
def climate_transition(payload: ClimateRequest):
    """Generate climate transition scenarios over time."""
    return generate_climate_transition_scenarios(
        baseline_water=payload.baseline_precip,
        baseline_temp=payload.baseline_temp,
        crop_type="wheat",
        ssp_scenario=payload.scenario,
    )


@router.post("/monte-carlo/yield")
def monte_carlo_yield_endpoint(payload: MonteCarloRequest):
    """Run Monte Carlo simulation for yield uncertainty."""
    return monte_carlo_yield(
        crop_type=payload.crop_type,
        mean_water=payload.mean_water,
        water_std=payload.water_std,
        mean_temp=payload.mean_temp,
        temp_std=payload.temp_std,
        n_simulations=payload.n_simulations,
    )
