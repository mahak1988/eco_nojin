"""EcoWallet router - ECO token economy system."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import EcoTransaction, EcoWallet, User
from services.api_gateway.auth import require_user

router = APIRouter(prefix="/api/v1/ecowallet", tags=["ecowallet"])


# ============================================================================
# Token Economics
# ============================================================================
EARNING_RATES = {
    "tree_planting": {"eco": 50.0, "description": "Plant a tree", "icon": "🌳"},
    "soil_analysis": {"eco": 10.0, "description": "Analyze soil health", "icon": "🧪"},
    "satellite_analysis": {"eco": 5.0, "description": "Satellite imagery analysis", "icon": "🛰️"},
    "scenario_run": {"eco": 8.0, "description": "Climate scenario analysis", "icon": "📊"},
    "carbon_project": {"eco": 100.0, "description": "Register carbon project", "icon": "🌱"},
    "erosion_analysis": {"eco": 12.0, "description": "Erosion risk assessment", "icon": "⛰️"},
    "marketplace_sale": {"eco": 20.0, "description": "Complete marketplace sale", "icon": "🛒"},
    "referral": {"eco": 25.0, "description": "Refer a new farmer", "icon": "👥"},
    "daily_checkin": {"eco": 2.0, "description": "Daily app check-in", "icon": "✅"},
    "complete_tutorial": {"eco": 15.0, "description": "Complete learning module", "icon": "📚"},
}

REDEMPTION_RATES = {
    "expert_consultation": {
        "eco": 50.0,
        "description": "1-hour expert consultation",
        "icon": "👨‍🌾",
        "value_usd": 25,
    },
    "satellite_report": {
        "eco": 30.0,
        "description": "Detailed satellite report",
        "icon": "📄",
        "value_usd": 15,
    },
    "marketplace_discount": {
        "eco": 10.0,
        "description": "$5 marketplace discount",
        "icon": "💸",
        "value_usd": 5,
    },
    "carbon_credit_purchase": {
        "eco": 100.0,
        "description": "1 carbon credit",
        "icon": "🌍",
        "value_usd": 50,
    },
    "premium_features": {
        "eco": 200.0,
        "description": "3 months premium access",
        "icon": "⭐",
        "value_usd": 100,
    },
    "soil_lab_test": {
        "eco": 75.0,
        "description": "Professional lab soil test",
        "icon": "🔬",
        "value_usd": 40,
    },
    "drone_survey": {
        "eco": 150.0,
        "description": "Drone aerial survey (1 ha)",
        "icon": "🚁",
        "value_usd": 75,
    },
}


# ============================================================================
# Models
# ============================================================================
class WalletResponse(BaseModel):
    balance: float
    total_earned: float
    total_redeemed: float
    is_active: bool
    created_at: str


class TransactionResponse(BaseModel):
    transaction_id: str
    amount: float
    transaction_type: str
    category: str
    description: str
    balance_after: float
    timestamp: str


class EarnRequest(BaseModel):
    category: str
    quantity: float = Field(1.0, gt=0)
    description: str | None = None


class RedeemRequest(BaseModel):
    category: str
    description: str | None = None


# ============================================================================
# Endpoints
# ============================================================================
@router.get("/wallet", response_model=WalletResponse)
def get_wallet(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get user's wallet info."""
    wallet = db.query(EcoWallet).filter(EcoWallet.user_id == user.id).first()
    if not wallet:
        wallet = EcoWallet(
            user_id=user.id, balance=0.0, total_earned=0.0, total_redeemed=0.0, is_active=True
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return WalletResponse(
        balance=wallet.balance,
        total_earned=wallet.total_earned,
        total_redeemed=wallet.total_redeemed,
        is_active=wallet.is_active,
        created_at=wallet.created_at.isoformat() if wallet.created_at else "",
    )


@router.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
    limit: int = 50, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    """Get transaction history."""
    wallet = db.query(EcoWallet).filter(EcoWallet.user_id == user.id).first()
    if not wallet:
        return []
    transactions = (
        db.query(EcoTransaction)
        .filter(EcoTransaction.wallet_id == wallet.id)
        .order_by(EcoTransaction.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        TransactionResponse(
            transaction_id=t.transaction_id,
            amount=t.amount,
            transaction_type=t.transaction_type,
            category=t.category,
            description=t.description or "",
            balance_after=t.balance_after,
            timestamp=t.timestamp.isoformat() if t.timestamp else "",
        )
        for t in transactions
    ]


@router.post("/earn")
def earn_eco(req: EarnRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Earn ECO tokens from activities."""
    wallet = db.query(EcoWallet).filter(EcoWallet.user_id == user.id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    if req.category not in EARNING_RATES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {req.category}")

    rate = EARNING_RATES[req.category]
    amount = rate["eco"] * req.quantity

    transaction = EcoTransaction(
        transaction_id=str(uuid.uuid4()),
        wallet_id=wallet.id,
        amount=amount,
        transaction_type="earn",
        category=req.category,
        description=req.description or f"Earned from {rate['description']}",
        balance_after=wallet.balance + amount,
    )
    db.add(transaction)
    wallet.balance += amount
    wallet.total_earned += amount
    wallet.last_activity = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "amount_earned": amount,
        "new_balance": wallet.balance,
        "transaction_id": transaction.transaction_id,
    }


@router.post("/redeem")
def redeem_eco(
    req: RedeemRequest, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    """Redeem ECO tokens for services."""
    wallet = db.query(EcoWallet).filter(EcoWallet.user_id == user.id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    if req.category not in REDEMPTION_RATES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {req.category}")

    rate = REDEMPTION_RATES[req.category]
    amount = rate["eco"]

    if wallet.balance < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Need {amount} ECO, have {wallet.balance:.2f} ECO",
        )

    transaction = EcoTransaction(
        transaction_id=str(uuid.uuid4()),
        wallet_id=wallet.id,
        amount=amount,
        transaction_type="redeem",
        category=req.category,
        description=req.description or f"Redeemed for {rate['description']}",
        balance_after=wallet.balance - amount,
    )
    db.add(transaction)
    wallet.balance -= amount
    wallet.total_redeemed += amount
    wallet.last_activity = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "amount_redeemed": amount,
        "new_balance": wallet.balance,
        "transaction_id": transaction.transaction_id,
        "service_received": rate["description"],
    }


@router.get("/earning-options")
def get_earning_options():
    """Get all earning opportunities."""
    return {
        "options": [
            {
                "category": cat,
                "eco_amount": data["eco"],
                "description": data["description"],
                "icon": data["icon"],
            }
            for cat, data in EARNING_RATES.items()
        ]
    }


@router.get("/redemption-options")
def get_redemption_options():
    """Get all redemption options."""
    return {
        "options": [
            {
                "category": cat,
                "eco_cost": data["eco"],
                "description": data["description"],
                "icon": data["icon"],
                "value_usd": data["value_usd"],
            }
            for cat, data in REDEMPTION_RATES.items()
        ]
    }


@router.get("/stats")
def get_wallet_stats(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get detailed wallet statistics."""
    wallet = db.query(EcoWallet).filter(EcoWallet.user_id == user.id).first()
    if not wallet:
        return {"error": "Wallet not found"}

    transactions = db.query(EcoTransaction).filter(EcoTransaction.wallet_id == wallet.id).all()

    earn_by_cat = {}
    redeem_by_cat = {}
    monthly_flow = {}

    for t in transactions:
        if t.transaction_type == "earn":
            earn_by_cat[t.category] = earn_by_cat.get(t.category, 0) + t.amount
        else:
            redeem_by_cat[t.category] = redeem_by_cat.get(t.category, 0) + t.amount

        month_key = t.timestamp.strftime("%Y-%m") if t.timestamp else "unknown"
        if month_key not in monthly_flow:
            monthly_flow[month_key] = {"earned": 0, "redeemed": 0}
        if t.transaction_type == "earn":
            monthly_flow[month_key]["earned"] += t.amount
        else:
            monthly_flow[month_key]["redeemed"] += t.amount

    # Convert to chart-friendly format
    monthly_chart = [
        {"month": k, "earned": v["earned"], "redeemed": v["redeemed"]}
        for k, v in sorted(monthly_flow.items())
    ]

    return {
        "balance": wallet.balance,
        "total_earned": wallet.total_earned,
        "total_redeemed": wallet.total_redeemed,
        "transaction_count": len(transactions),
        "earn_by_category": earn_by_cat,
        "redeem_by_category": redeem_by_cat,
        "monthly_flow": monthly_chart,
        "earning_options_count": len(EARNING_RATES),
        "redemption_options_count": len(REDEMPTION_RATES),
    }
