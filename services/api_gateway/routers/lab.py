"""Phase 4-D router — lab data upload + measured-vs-modelled comparison."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.mrv import lab_data

router = APIRouter(prefix="/api/mrv/lab", tags=["mrv-lab"])


class LabSampleRow(BaseModel):
    lat: float
    lon: float
    soc_t_ha: float
    lab_id: Optional[str] = None
    depth_cm: Optional[float] = 30
    lab: Optional[str] = None
    sampled_at: Optional[str] = None


class LabSamplesRequest(BaseModel):
    samples: List[LabSampleRow]


@router.post("/samples")
async def add_samples(req: LabSamplesRequest) -> Dict[str, Any]:
    """Register real lab SOC measurements (stored locally under data/lab/)."""
    return lab_data.add_lab_samples([r.model_dump() for r in req.samples])


@router.get("/samples")
async def get_samples() -> Dict[str, Any]:
    return lab_data.list_lab_samples()


@router.post("/compare")
async def compare() -> Dict[str, Any]:
    """Measured vs modelled (SoilGrids) SOC — honest stats (bias/RMSE/MAPE/R2)."""
    return await lab_data.compare_model()
