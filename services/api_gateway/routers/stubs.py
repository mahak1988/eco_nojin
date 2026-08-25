"""
Stub endpoints for features not yet implemented.

These return meaningful "not yet available" responses instead of 404,
preventing frontend errors and giving users clear feedback.

This is a temporary file - will be replaced with real implementations
as features are built (e.g., when we build the full wallet system).
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Any

router = APIRouter(tags=["stubs"])


class StubResponse(BaseModel):
    """Standard stub response."""
    available: bool = False
    message: str
    coming_soon: bool = True
    data: Optional[Any] = None


# ==========================================================================
# Wallet endpoint (ecowallet is partially implemented)
# ==========================================================================
@router.get("/api/v1/wallet")
def get_wallet_stub() -> StubResponse:
    """
    Wallet endpoint - stub for not-yet-implemented features.
    
    Real implementation will come in Phase 2 (Carbon credit payments).
    """
    return StubResponse(
        message="Wallet integration coming soon. Will support MATIC and carbon credits.",
        data={
            "balance_matic": 0.0,
            "carbon_credits": 0,
            "transactions": [],
        }
    )


# ==========================================================================
# Scenario endpoints (partially implemented)
# ==========================================================================
@router.post("/api/v1/scenarios/crop")
def crop_scenario_stub() -> StubResponse:
    """
    Crop scenario comparison - stub.
    
    Will integrate with CropAdvisor motor + RAG knowledge base.
    """
    return StubResponse(
        message="Crop comparison feature coming soon. Will use CropAdvisor + knowledge base.",
        data={
            "crops": [],
            "recommendations": [],
        }
    )


@router.post("/api/v1/scenarios/whatif/{scenario_type}")
def whatif_scenario_stub(scenario_type: str) -> StubResponse:
    """
    What-if scenarios - stub.
    
    Will integrate with Hydroma simulation engine.
    """
    return StubResponse(
        message=f"What-if scenario '{scenario_type}' coming soon. Will use Hydroma simulations.",
        data={
            "scenario": scenario_type,
            "results": {},
        }
    )
