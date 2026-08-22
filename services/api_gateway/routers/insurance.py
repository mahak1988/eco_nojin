"""Index-based insurance API (Phase 10)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.business_modules.insurance.index_insurance import (
    IndexInputError,
    evaluate_index_insurance,
)

router = APIRouter(prefix="/api/v1/insurance", tags=["insurance"])


class IndexRequest(BaseModel):
    """NDVI index insurance evaluation request."""

    farm_id: str = Field(..., min_length=1, max_length=100)
    ndvi_values: list[float] = Field(..., min_length=3, max_length=366)
    reference_ndvi: float = Field(..., gt=0.0, le=1.0)
    trigger_deficit: float = Field(0.15, gt=0.0, lt=1.0)
    full_payout_deficit: float = Field(0.45, gt=0.0, lt=1.0)


@router.post("/index")
def evaluate_index(payload: IndexRequest):
    """Evaluate NDVI seasonal index and payout trigger (no premium pricing)."""
    try:
        result = evaluate_index_insurance(
            farm_id=payload.farm_id,
            ndvi_values=payload.ndvi_values,
            reference_ndvi=payload.reference_ndvi,
            trigger_deficit=payload.trigger_deficit,
            full_payout_deficit=payload.full_payout_deficit,
        )
    except IndexInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.__dict__


@router.get("/capabilities")
def insurance_capabilities():
    """Honest capability statement (no actuarial claims)."""
    return {
        "index": "seasonal mean NDVI vs reference",
        "pricing": False,
        "note": "پرداخت نیازمند بازبینی اکچوئری و مقررات بیمه است",
        "phase": "phase10-step1",
    }
