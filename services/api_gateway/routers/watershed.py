"""API endpoints for Watershed Structures."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.hydroma.watershed.calculator import StructureType, design_watershed_structure

router = APIRouter(prefix="/api/v1/watershed", tags=["Watershed Structures"])


class StructureRequest(BaseModel):
    structure_type: str = Field(..., description="Type of structure")
    slope_pct: float = Field(..., ge=0, le=100)
    area_m2: float = Field(..., gt=0)
    rainfall_mm: float = Field(100, ge=0, le=500)


@router.get("/structure-types")
def list_structure_types():
    """List all available structure types."""
    return {
        "structure_types": [{"type": st.value, "name": st.name} for st in StructureType],
        "count": len(StructureType),
    }


@router.post("/design")
def design_structure(payload: StructureRequest):
    """Design a watershed structure."""
    try:
        return design_watershed_structure(
            structure_type=payload.structure_type,
            slope_pct=payload.slope_pct,
            area_m2=payload.area_m2,
            rainfall_mm=payload.rainfall_mm,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
