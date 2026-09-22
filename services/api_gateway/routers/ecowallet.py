"""EcoCoin Wallet API Routes - FastAPI endpoints for wallet operations"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from sqlalchemy import func, select

from database.models import EcoWallet
from services.api_gateway.auth import get_current_user, require_user
from services.api_gateway.exceptions import EcoNojinException
from services.api_gateway.routers.auth import get_async_db
from services.finance.wallet_service import WalletService, LedgerService, TransactionType

router = APIRouter(prefix="/api/v1/ecowallet", tags=["ecowallet"])


# Dependency injection: a real async DB-backed wallet service (previously a
# stub returning None, which made every endpoint in this router unusable).
# WalletService is async, so it needs the AsyncSession dependency.
async def get_wallet_service(db=Depends(get_async_db)) -> WalletService:
    return WalletService(db)


# ============================================================================
# Models
# ============================================================================


class EarnRequest(BaseModel):
    category: str = Field(
        ...,
        pattern=r"^(tree_planting|soil_restoration|water_conservation|biodiversity|cleanup|regenerative_farming|carbon_verification|education|community|satellite_verification|mrv_submission)$",
    )
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    reference_id: Optional[str] = None


class EarnResponse(BaseModel):
    amount_earned: Decimal
    new_balance: Decimal
    category: str


class RedeemRequest(BaseModel):
    category: str = Field(
        ...,
        pattern=r"^(consultation|satellite_report|marketplace_discount|training|certification)$",
    )
    reference_id: Optional[str] = None


class RedeemResponse(BaseModel):
    amount_redeemed: Decimal
    new_balance: Decimal
    category: str


class TransferRequest(BaseModel):
    to_user: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    description: str = ""


class TransferResponse(BaseModel):
    success: bool
    from_user: str
    to_user: str
    amount: Decimal
    timestamp: datetime


class WalletState(BaseModel):
    user_id: str
    balance: Decimal
    total_earned: Decimal
    total_redeemed: Decimal
    is_active: bool


class EarningsHistory(BaseModel):
    date: str
    earnings_type: str
    amount: str
    source: str
    status: str
    processed_at: Optional[str] = None


class DailyCapStatus(BaseModel):
    earned_today: Decimal
    daily_cap: Decimal
    remaining: Decimal


class UssdRequest(BaseModel):
    """USSD wallet action payload (feature-phone channel)."""

    action: str = Field(default="balance", pattern="^(balance)$")
    language: Optional[str] = Field(default="fa", pattern="^(fa|en|ar|tr)$")
    user_id: Optional[str] = None  # ignored: the token identity is authoritative


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/wallets", response_model=WalletState, status_code=201)
async def create_wallet(
    service: WalletService = Depends(get_wallet_service),
    current=Depends(require_user),
):
    """Create (or return) the wallet of the authenticated user."""
    user_id = str(current.id)
    wallet = await service._get_or_create_wallet(user_id)
    return WalletState(
        user_id=user_id,
        balance=wallet.balance,
        total_earned=wallet.total_earned,
        total_redeemed=wallet.total_redeemed,
        is_active=wallet.is_active,
    )


@router.post("/earn", response_model=EarnResponse)
async def earn_tokens(
    payload: EarnRequest,
    service: WalletService = Depends(get_wallet_service),
    current=Depends(require_user),
):
    """Earn ECO tokens for the authenticated user (body identity ignored)."""
    user_id = str(current.id)
    try:
        amount, new_balance = await service.earn(
            user_id=user_id,
            category=payload.category,
            quantity=payload.quantity,
            reference_id=payload.reference_id,
        )
        return EarnResponse(
            amount_earned=amount,
            new_balance=new_balance,
            category=payload.category,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/redeem", response_model=RedeemResponse)
async def redeem_tokens(
    payload: RedeemRequest,
    service: WalletService = Depends(get_wallet_service),
    current=Depends(require_user),
):
    """Redeem ECO tokens for the authenticated user."""
    user_id = str(current.id)
    try:
        amount, new_balance = await service.redeem(
            user_id=user_id,
            category=payload.category,
            reference_id=payload.reference_id,
        )
        return RedeemResponse(
            amount_redeemed=amount,
            new_balance=new_balance,
            category=payload.category,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transfer", response_model=TransferResponse)
async def transfer_tokens(
    payload: TransferRequest,
    service: WalletService = Depends(get_wallet_service),
    current=Depends(require_user),
):
    """Transfer ECO tokens from the authenticated user (phase-gated)."""
    from_user = str(current.id)
    try:
        success = await service.transfer(
            from_user=from_user,
            to_user=payload.to_user,
            amount=payload.amount,
            description=payload.description,
        )
        return TransferResponse(
            success=success,
            from_user=from_user,
            to_user=payload.to_user,
            amount=payload.amount,
            timestamp=datetime.now(),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallet/{user_id}", response_model=WalletState)
async def get_wallet_state(
    user_id: str,
    service: WalletService = Depends(get_wallet_service),
):
    """Get wallet state for a user"""
    state = await service.get_wallet_state(user_id)
    return WalletState(**state)


@router.get("/earnings", response_model=List[EarningsHistory])
async def list_earnings(
    user_id: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    service: WalletService = Depends(get_wallet_service),
):
    """List user earnings history"""
    earnings = await service.list_earnings(user_id, limit=limit)
    return [
        EarningsHistory(
            date=e["date"],
            earnings_type=e["earnings_type"],
            amount=e["amount"],
            source=e["source"],
            status=e["status"],
            processed_at=e.get("processed_at"),
        )
        for e in earnings
    ]


@router.get("/daily-cap", response_model=DailyCapStatus)
async def get_daily_cap(
    user_id: str = Query(..., min_length=1),
    service: WalletService = Depends(get_wallet_service),
):
    """Get daily earning cap status"""
    from datetime import UTC, date
    from sqlalchemy import select, func
    from database.models import DailyEarnings

    # This would be implemented in the service
    # For now, return mock
    return DailyCapStatus(
        earned_today=Decimal("0"),
        daily_cap=Decimal("200"),
        remaining=Decimal("200"),
    )


@router.get("/earning-options")
async def get_earning_options():
    """Get all available earning categories and rates"""
    from services.finance.wallet_service import WalletService

    options = [
        {"category": cat, "eco_per_unit": str(data), "description": f"Earn ECO for {cat}"}
        for cat, data in WalletService.EARNING_RATES.items()
    ]
    return {"options": options}


@router.get("/redemption-options")
async def get_redemption_options():
    """Get all available redemption options"""
    from services.finance.wallet_service import WalletService

    options = [
        {"category": cat, "eco_cost": str(data), "description": f"Redeem ECO for {cat}"}
        for cat, data in WalletService.REDEMPTION_RATES.items()
    ]
    return {"options": options}


@router.get("/stats")
async def wallet_stats(
    db=Depends(get_async_db),
    current=Depends(require_user),
):
    """Aggregate wallet statistics (honest: zeros when the ledger is empty)."""
    row = (
        await db.execute(
            select(
                func.count(EcoWallet.id),
                func.coalesce(func.sum(EcoWallet.balance), 0),
                func.coalesce(func.sum(EcoWallet.total_earned), 0),
                func.coalesce(func.sum(EcoWallet.total_redeemed), 0),
                func.count(EcoWallet.id).filter(EcoWallet.is_active.is_(True)),
            )
        )
    ).one()
    total_wallets, total_balance, total_earned, total_redeemed, active_wallets = row
    return {
        "total_wallets": int(total_wallets or 0),
        "active_wallets": int(active_wallets or 0),
        "total_balance": float(total_balance or 0),
        "total_earned": float(total_earned or 0),
        "total_redeemed": float(total_redeemed or 0),
        "currency": "ECO",
        "requested_by": str(current.id),
    }


@router.post("/ussd")
async def ussd_wallet_action(
    payload: UssdRequest,
    service: WalletService = Depends(get_wallet_service),
    current=Depends(require_user),
):
    """USSD-style wallet action for feature phones (balance only for now).

    The authenticated identity wins over any body ``user_id`` so a caller
    cannot query somebody else's balance.
    """
    if payload.action != "balance":
        raise HTTPException(status_code=422, detail=f"Unsupported USSD action: {payload.action}")
    user_id = str(current.id)
    state = await service.get_wallet_state(user_id)
    return {
        "action": payload.action,
        "balance": float(state.get("balance", 0)),
        "currency": "ECO",
        "language": payload.language or "fa",
        "user_id": user_id,
    }


@router.get("/health")
async def health_check():
    return {"status": "operational", "module": "ecowallet", "version": "1.0.0"}
