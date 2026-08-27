"""Phase 5 router — economy / livelihood cost-benefit analysis."""

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.scientific_motors.economy_motor import EconomyMotor

router = APIRouter(prefix="/api/motors/economy", tags=["economy"])


class EconomyRequest(BaseModel):
    lat: float
    lon: float
    area_ha: float = Field(default=100, gt=0)
    intervention: str = "conservation_ag"  # conservation_ag|agroforestry|terrace|rotational_grazing|none
    slope_pct: float = Field(default=10.0, gt=0)
    discount_rate: float = Field(default=0.10, ge=0, le=0.5)
    horizon_years: int = Field(default=20, ge=1, le=50)
    prices: Optional[Dict[str, float]] = None


@router.post("/")
async def run_economy(req: EconomyRequest) -> Dict[str, Any]:
    """Cost-benefit + livelihood index from the REAL chain (2 runs: baseline vs intervention)."""
    result = await EconomyMotor().arun(
        lat=req.lat,
        lon=req.lon,
        area_ha=req.area_ha,
        intervention=req.intervention,
        slope_pct=req.slope_pct,
        discount_rate=req.discount_rate,
        horizon_years=req.horizon_years,
        prices=req.prices or {},
    )
    return {
        "run_id": result.run_id,
        "status": result.status.value,
        "outputs": result.outputs,
        "error": result.error_message,
    }
