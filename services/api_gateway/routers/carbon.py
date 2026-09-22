"""Carbon tokenization API router.

Endpoints for on-chain carbon credit management and Verra integration.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/carbon", tags=["Carbon Credits"])


def get_db():
    with hub.get_session() as session:
        yield session


class _LazyCarbonService:
    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            from services.business_modules.carbon.tokenization import get_tokenization_service

            self._instance = get_tokenization_service()
        return getattr(self._instance, name)


class _LazyVerraService:
    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            from services.business_modules.carbon.verra_integration import get_verra_integration

            self._instance = get_verra_integration()
        return getattr(self._instance, name)


_carbon_service = _LazyCarbonService()
_verra_service = _LazyVerraService()


class TokenizeRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    amount_tonnes: float = Field(..., gt=0)
    credit_type: str = Field("VCS")
    recipient_address: str | None = None


class TransferRequest(BaseModel):
    from_address: str = Field(..., min_length=1)
    to_address: str = Field(..., min_length=1)
    token_id: str = Field(..., min_length=1)


class RetireRequest(BaseModel):
    token_id: str = Field(..., min_length=1)
    retirement_justification: str = Field(default="")


class VerraSearchRequest(BaseModel):
    country: str | None = None
    methodology: str | None = None
    page: int = Field(default=1, ge=1)


@router.post("/tokenize")
def tokenize_credits(
    payload: TokenizeRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Mint carbon credits on-chain."""
    try:
        result = _carbon_service.issue_credits(
            project_id=payload.project_id,
            amount=payload.amount_tonnes,
            credit_type=payload.credit_type,
            recipient_address=payload.recipient_address,
        )
    except Exception as exc:
        logger.error("Tokenization failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        **result,
        "requested_by": user.id,
        "project_id": payload.project_id,
    }


@router.post("/credits/transfer")
def transfer_credits(
    payload: TransferRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Transfer carbon credits."""
    try:
        result = _carbon_service.transfer_credits(
            from_address=payload.from_address,
            to_address=payload.to_address,
            token_id=payload.token_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Transfer failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    return {**result, "requested_by": user.id}


@router.post("/credits/retire")
def retire_credits(
    payload: RetireRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Retire carbon credits."""
    try:
        result = _carbon_service.retire_credits(
            token_id=payload.token_id,
            retirement_justification=payload.retirement_justification,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {**result, "retired_by": user.id}


@router.get("/credits/balance")
def get_balance(
    address: str = Query(..., min_length=1),
    user: User = Depends(require_user),
):
    """Get token balance for address."""
    balance = _carbon_service.get_balance(address)
    return {"address": address, "balance": balance, "unit": "base_units"}


@router.get("/credits/{token_id}/history")
def get_credit_history(
    token_id: str,
    user: User = Depends(require_user),
):
    """Get credit lifecycle history."""
    try:
        history = _carbon_service.get_credit_history(token_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"token_id": token_id, "history": history}


@router.get("/credits/{token_id}/verify")
def verify_credit(
    token_id: str,
    user: User = Depends(require_user),
):
    """Verify credit on-chain."""
    try:
        result = _carbon_service.verify_on_chain(token_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return result


@router.get("/verra/standards")
async def list_standards(user: User = Depends(require_user)):
    """List available carbon credit standards."""
    standards = await _verra_service.list_standards()
    return {"standards": standards}


@router.post("/verra/search")
async def search_verra(
    payload: VerraSearchRequest | None = None,
    user: User = Depends(require_user),
):
    """Search Verra registry."""
    payload = payload or VerraSearchRequest()
    results = await _verra_service.search_projects(
        payload.country, payload.methodology, payload.page
    )
    return {"results": results, "page": payload.page}


@router.post("/verra/sync")
async def sync_verra_project(
    registry_id: str = Query(..., min_length=1),
    user: User = Depends(require_user),
):
    """Sync a Verra project into Eco Nojin."""
    try:
        result = await _verra_service.sync_project_from_verra(registry_id)
    except Exception as exc:
        logger.error("Verra sync failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/verra/{registry_id}")
async def get_verra_project(
    registry_id: str,
    user: User = Depends(require_user),
):
    """Get Verra project details."""
    try:
        result = await _verra_service.get_project(registry_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result
