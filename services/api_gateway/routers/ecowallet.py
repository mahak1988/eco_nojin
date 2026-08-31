"""EcoWallet router - ECO token economy system.

Pentest fix C2: every balance-mutating endpoint requires authentication and
the wallet identity is always taken from the authenticated user, never from
the request body. Unknown earning/redemption categories are rejected and a
daily earning cap is enforced.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from database.models import User
from services.api_gateway.auth import require_user

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

# Daily earning cap per user (ECO tokens) - prevents unbounded minting.
DAILY_EARN_CAP = 200.0


# ============================================================================
# Models
# ============================================================================
class WalletCreateRequest(BaseModel):
    # Deprecated: ignored. The wallet is always created for the authenticated user.
    user_id: str | None = Field(None, description="Deprecated and ignored; identity comes from the auth token")


class WalletResponse(BaseModel):
    user_id: str
    balance: float


class EarnRequest(BaseModel):
    user_id: str | None = Field(None, description="Deprecated and ignored; identity comes from the auth token")
    category: str
    quantity: float = Field(default=1.0, gt=0)
    language: str = "en"


class EarnResponse(BaseModel):
    amount_earned: float
    new_balance: float
    category: str


class RedeemRequest(BaseModel):
    user_id: str | None = Field(None, description="Deprecated and ignored; identity comes from the auth token")
    category: str
    language: str = "en"


class RedeemResponse(BaseModel):
    amount_redeemed: float
    new_balance: float
    category: str


class UssdRequest(BaseModel):
    user_id: str | None = Field(None, description="Deprecated and ignored; identity comes from the auth token")
    action: str
    language: str = "en"


class UssdResponse(BaseModel):
    action: str
    balance: float
    message: str


# ============================================================================
# In-memory wallet storage (phase-1 scope; DB persistence tracked separately)
# ============================================================================
_wallets: dict[str, dict] = {}
# user_id -> (ISO date, earned today)
_daily_earned: dict[str, tuple[str, float]] = {}


def _get_or_create_wallet(user_id: str) -> dict:
    """Return the user's wallet, creating a zero-balance one if missing."""
    if user_id not in _wallets:
        _wallets[user_id] = {
            "balance": 0.0,
            "created_at": datetime.now(UTC).replace(tzinfo=None),
        }
    return _wallets[user_id]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/wallets", status_code=200, response_model=WalletResponse)
def create_wallet(payload: WalletCreateRequest, user: User = Depends(require_user)):
    """Create (or return) the wallet of the authenticated user."""
    wallet = _get_or_create_wallet(user.id)
    return WalletResponse(user_id=user.id, balance=wallet["balance"])


@router.post("/earn", response_model=EarnResponse)
def earn_tokens(payload: EarnRequest, user: User = Depends(require_user)):
    """Earn ECO tokens for the authenticated user (daily cap enforced)."""
    rate = EARNING_RATES.get(payload.category, {}).get("eco", 0.0)
    if rate <= 0:
        raise HTTPException(status_code=422, detail=f"Unknown earning category: {payload.category}")

    amount = rate * payload.quantity
    today = datetime.now(UTC).date().isoformat()
    earned_date, earned_amount = _daily_earned.get(user.id, ("", 0.0))
    earned_today = earned_amount if earned_date == today else 0.0
    if earned_today + amount > DAILY_EARN_CAP:
        raise HTTPException(
            status_code=400,
            detail=f"Daily earning cap of {DAILY_EARN_CAP} ECO exceeded",
        )

    wallet = _get_or_create_wallet(user.id)
    wallet["balance"] += amount
    _daily_earned[user.id] = (today, earned_today + amount)

    return EarnResponse(
        amount_earned=amount,
        new_balance=wallet["balance"],
        category=payload.category,
    )


@router.post("/redeem", response_model=RedeemResponse)
def redeem_tokens(payload: RedeemRequest, user: User = Depends(require_user)):
    """Redeem ECO tokens from the authenticated user's wallet."""
    rate = REDEMPTION_RATES.get(payload.category, {}).get("eco", 0.0)
    if rate <= 0:
        raise HTTPException(status_code=422, detail=f"Unknown redemption category: {payload.category}")

    wallet = _wallets.get(user.id)
    if wallet is None or wallet["balance"] < rate:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    wallet["balance"] -= rate
    return RedeemResponse(
        amount_redeemed=rate,
        new_balance=wallet["balance"],
        category=payload.category,
    )


@router.post("/ussd", response_model=UssdResponse)
def ussd_action(payload: UssdRequest, user: User = Depends(require_user)):
    """USSD-style balance action for the authenticated user."""
    wallet = _get_or_create_wallet(user.id)
    balance = wallet["balance"]
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
def ecowallet_stats(user: User = Depends(require_user)):
    """EcoWallet statistics (authenticated)."""
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
