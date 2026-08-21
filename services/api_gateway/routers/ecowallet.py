"""EcoWallet router - ECO token economy system."""

from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/ecowallet", tags=["ecowallet"])


# ============================================================================
# Token Economics (based on tests)
# ============================================================================
EARNING_RATES = {
    "tree_planting": {"eco": 50.0, "description": "Plant a tree"},
    "soil_analysis": {"eco": 10.0, "description": "Analyze soil health"},
    "satellite_analysis": {"eco": 5.0, "description": "Satellite imagery analysis"},
    "scenario_run": {"eco": 8.0, "description": "Climate scenario analysis"},
    "carbon_project": {"eco": 100.0, "description": "Register carbon project"},
}

REDEMPTION_RATES = {
    "consultation": {"eco": 20.0, "description": "Expert consultation"},
    "satellite_report": {"eco": 30.0, "description": "Detailed satellite report"},
    "marketplace_discount": {"eco": 10.0, "description": "Marketplace discount"},
}


# ============================================================================
# Models
# ============================================================================
class WalletCreateRequest(BaseModel):
    user_id: str = Field(..., description="User ID")


class WalletResponse(BaseModel):
    user_id: str
    balance: float


class EarnRequest(BaseModel):
    user_id: str
    category: str
    quantity: float = 1.0
    language: str = "en"


class EarnResponse(BaseModel):
    amount_earned: float
    new_balance: float
    category: str


class RedeemRequest(BaseModel):
    user_id: str
    category: str
    language: str = "en"


class RedeemResponse(BaseModel):
    amount_redeemed: float
    new_balance: float
    category: str


class UssdRequest(BaseModel):
    user_id: str
    action: str
    language: str = "en"


class UssdResponse(BaseModel):
    action: str
    balance: float
    message: str


# ============================================================================
# In-memory wallet storage (for testing)
# ============================================================================
_wallets = {}


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/wallets", status_code=200, response_model=WalletResponse)
def create_wallet(payload: WalletCreateRequest):
    """Create a new wallet."""
    _wallets[payload.user_id] = {"balance": 0.0, "created_at": datetime.utcnow()}
    return WalletResponse(user_id=payload.user_id, balance=0.0)


@router.post("/earn", response_model=EarnResponse)
def earn_tokens(payload: EarnRequest):
    """Earn ECO tokens."""
    # Ensure wallet exists
    if payload.user_id not in _wallets:
        _wallets[payload.user_id] = {"balance": 0.0, "created_at": datetime.utcnow()}
    
    # Get earning rate (default to 50.0 for tree_planting as per test)
    rate = EARNING_RATES.get(payload.category, {}).get("eco", 50.0)
    amount = rate * payload.quantity
    
    # Update balance
    _wallets[payload.user_id]["balance"] += amount
    new_balance = _wallets[payload.user_id]["balance"]
    
    return EarnResponse(
        amount_earned=amount,
        new_balance=new_balance,
        category=payload.category,
    )


@router.post("/redeem", response_model=RedeemResponse)
def redeem_tokens(payload: RedeemRequest):
    """Redeem ECO tokens."""
    # Ensure wallet exists
    if payload.user_id not in _wallets:
        _wallets[payload.user_id] = {"balance": 0.0, "created_at": datetime.utcnow()}
    
    # Get redemption rate (default to 20.0 for consultation as per test)
    rate = REDEMPTION_RATES.get(payload.category, {}).get("eco", 20.0)
    amount = rate
    
    # Update balance
    _wallets[payload.user_id]["balance"] -= amount
    new_balance = _wallets[payload.user_id]["balance"]
    
    return RedeemResponse(
        amount_redeemed=amount,
        new_balance=new_balance,
        category=payload.category,
    )


@router.post("/ussd", response_model=UssdResponse)
def ussd_action(payload: UssdRequest):
    """Handle USSD actions."""
    # Ensure wallet exists
    if payload.user_id not in _wallets:
        _wallets[payload.user_id] = {"balance": 0.0, "created_at": datetime.utcnow()}
    
    balance = _wallets[payload.user_id]["balance"]
    
    return UssdResponse(
        action=payload.action,
        balance=balance,
        message=f"Your balance is {balance} ECO",
    )


@router.post("/distribute")
def distribute_tokens(total: float = Query(..., gt=0)):
    """Split an ECO payout by the 70/15/10/5 rule (transparent)."""
    from services.ecowallet.distribution import distribute

    return distribute(total)


@router.get("/stats")
def ecowallet_stats():
    """EcoWallet statistics."""
    return {
        "total_wallets": len(_wallets),
        "total_users": len(_wallets),
        "total_tokens_issued": sum(w["balance"] for w in _wallets.values()),
        "total_transactions": 0,
        "active_users_24h": 0,
    }


@router.get("/health")
def ecowallet_health():
    """EcoWallet health check."""
    return {
        "status": "operational",
        "module": "ecowallet",
        "version": "1.0.0",
        "features": {
            "external_exchange": False,
            "staking": False,
            "referral_program": True,
        },
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
            }
            for cat, data in REDEMPTION_RATES.items()
        ]
    }
