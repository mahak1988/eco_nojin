"""Phase 8-B routers — drought (SPI/SPEI), CMIP6 climate scenarios,
auto-calibration. All free, no registration (Open-Meteo / scipy)."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.scientific_motors.drought_motor import run_drought
from services.scientific_motors.climate_motor import run_climate
from services.scientific_motors.calibration import run_calibration

router = APIRouter(prefix="/api/v1/motors", tags=["phase8b"])


class DroughtRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    timescale_months: int = Field(default=3, ge=1, le=24)


class ClimateRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    scenario: str = "SSP245"


class CalibrateRequest(BaseModel):
    observed: Optional[List[float]] = None
    modelled: Optional[List[float]] = None
    calibrate: Optional[List[str]] = None
    iterations: int = Field(default=40, ge=5, le=200)


@router.post("/drought")
async def drought(req: DroughtRequest) -> Dict[str, Any]:
    """SPI/SPEI from real ERA5 data (Open-Meteo)."""
    try:
        return run_drought(req.lat, req.lon, req.timescale_months)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/climate")
async def climate(req: ClimateRequest) -> Dict[str, Any]:
    """CMIP6 (SSP) 30-year scenario vs ERA5 baseline (Open-Meteo Climate API)."""
    try:
        return run_climate(req.lat, req.lon, req.scenario)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/calibrate")
async def calibrate(req: CalibrateRequest) -> Dict[str, Any]:
    """Auto-calibration of CN/Ks/AWC/C-P factors from observed feedback."""
    try:
        return run_calibration(req.observed, req.modelled, req.calibrate, req.iterations)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
