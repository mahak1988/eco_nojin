"""API endpoints for organic materials and compost formulation."""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel, Field
from engine.hydroma.materials.compost_formulator import CompostMaterial, calculate_mix_cn_ratio

router = APIRouter(prefix="/api/v1/materials", tags=["Materials & Bio-fertilizers"])

class CompostRequest(BaseModel):
    """Request model for compost mix calculation."""
    materials: List[CompostMaterial] = Field(..., min_length=1, description="List of input materials")

class CompostResponse(BaseModel):
    """Response model for compost mix calculation."""
    cn_ratio: float = Field(..., description="Calculated Carbon to Nitrogen ratio")
    status: str = Field(..., description="Suitability of the C/N ratio for composting")

@router.post("/calculate-compost", response_model=CompostResponse)
def calculate_compost_mix(payload: CompostRequest):
    """Calculate the C/N ratio for a proposed bio-fertilizer mixture."""
    try:
        ratio = calculate_mix_cn_ratio(payload.materials)
        
        # Scientific interpretation based on FAO guidelines
        if 25 <= ratio <= 35:
            status = "Optimal"
        elif ratio < 25:
            status = "Nitrogen rich (Risk of odor/anaerobic conditions)"
        else:
            status = "Carbon rich (Slow decomposition)"
            
        return CompostResponse(cn_ratio=round(ratio, 2), status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
