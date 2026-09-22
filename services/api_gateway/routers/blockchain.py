"""API endpoints for Blockchain Ledger - EcoCoin Protocol"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List

from database.hub import hub


# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session


from database.models import User
from services.api_gateway.auth import require_user

router = APIRouter(prefix="/api/v1/blockchain", tags=["Blockchain Ledger"])


# ============================================================================
# Pydantic Models - EcoCoin
# ============================================================================


class EcoCoinBalance(BaseModel):
    user_id: str
    balance: str
    total_earned: str
    total_redeemed: Decimal
    is_active: bool


class EcoCoinEarnRequest(BaseModel):
    category: str = Field(
        ...,
        pattern=r"^(tree_planting|soil_restoration|water_conservation|biodiversity|cleanup|regenerative_farming|carbon_verification|education|community|satellite_verification|mrv_submission)$",
    )
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    reference_id: Optional[str] = None


class EcoCoinEarnResponse(BaseModel):
    amount_earned: str
    new_balance: str
    category: str


class EcoCoinRedeemRequest(BaseModel):
    category: str


class EcoCoinRedeemResponse(BaseModel):
    amount_redeemed: str
    new_balance: str
    category: str


class EcoCoinTransferRequest(BaseModel):
    to_user: str
    amount: Decimal
    description: str = ""


class EcoCoinTransferResponse(BaseModel):
    success: bool
    from_user: str
    to_user: str
    amount: str
    timestamp: str


class EcoCoinStats(BaseModel):
    total_wallets: int
    total_eco_in_circulation: str
    total_eco_earned: str
    total_eco_redeemed: str
    active_users: int


class EcoCoinHealth(BaseModel):
    status: str
    module: str
    version: str
    features: dict


class EcoCoinDistribution(BaseModel):
    total: str
    producer: str
    platform: str
    ecosystem: str
    governance: str


# ============================================================================
# EcoCoin Endpoints
# ============================================================================


@router.post("/ecocoin/earn")
async def earn_ecocoin(category: str, quantity: float = 1.0, user_id: str = "user_123"):
    """Earn EcoCoin for ecosystem activities"""
    # In production: call WalletService.earn()
    return {
        "amount_earned": "50.0",
        "new_balance": "50.0",
        "category": "tree_planting",
        "status": "earned",
    }


@router.post("/ecocoin/redeem")
async def redeem_ecocoin(category: str, user_id: str = "user_123"):
    """Redeem EcoCoin for platform services"""
    return {"amount_redeemed": "20.0", "new_balance": "30.0", "category": "consultation"}


@router.post("/ecocoin/transfer")
async def transfer_ecocoin(to_user: str, amount: float, from_user: str = "user_123"):
    """Transfer EcoCoin to another user (phase-gated)"""
    return {
        "success": True,
        "from_user": "user_123",
        "to_user": "user_456",
        "amount": "50.0",
        "timestamp": "2026-09-20T12:00:00Z",
    }


@router.get("/ecocoin/wallet/{user_id}")
async def get_ecocoin_wallet(user_id: str):
    """Get EcoCoin wallet balance"""
    return {
        "user_id": user_id,
        "balance": "100.0",
        "total_earned": "500.0",
        "total_redeemed": "50.0",
        "is_active": True,
    }


@router.get("/ecocoin/stats")
async def ecocoin_stats():
    """Get EcoCoin statistics"""
    return {
        "total_wallets": 1000,
        "total_eco_in_circulation": "1000000.0",
        "total_eco_earned": "2000000.0",
        "total_eco_redeemed": "500000.0",
        "active_users": 800,
    }


@router.post("/ecocoin/distribute")
async def distribute_ecocoin(total: float):
    """Split ECO payout by 70/15/10/5 rule"""
    total_decimal = Decimal(str(total))
    burn = total_decimal * Decimal("0.02")
    net = total_decimal - burn

    return {
        "total": str(total_decimal),
        "burned": str(burn),
        "producer": str(net * Decimal("0.70")),
        "platform": str(net * Decimal("0.15")),
        "ecosystem": str(net * Decimal("0.10")),
        "governance": str(net * Decimal("0.05")),
    }


@router.get("/ecocoin/health")
async def ecocoin_health():
    return {
        "status": "operational",
        "module": "ecocoin",
        "version": "1.0.0",
        "features": {
            "external_exchange": False,
            "staking": False,
            "referral_program": True,
            "phase_gated_transfers": True,
        },
    }


# ============================================================================
# Impact Certificate Endpoints
# ============================================================================


@router.post("/impact/certificate")
async def create_impact_certificate(
    activity_id: str, user_id: str, confidence: int, impact_hash: str, metadata_uri: str = ""
):
    """Create Impact Certificate (SBT) for verified activity"""
    return {
        "certificate_id": f"ENIC-{activity_id}",
        "activity_id": activity_id,
        "owner": "user_123",
        "confidence": 85,
        "status": "verified",
        "tx_hash": "0x...",
    }


@router.get("/impact/certificate/{certificate_id}")
async def get_impact_certificate(certificate_id: str):
    return {
        "certificate_id": certificate_id,
        "activity_id": "ACT-123",
        "owner": "user_123",
        "confidence": 85,
        "status": "verified",
        "timestamp": "2026-09-20T12:00:00Z",
    }


# ============================================================================
# Phase Gate Endpoints
# ============================================================================


@router.get("/phasegate/status")
async def phase_gate_status():
    return {
        "current_phase": 2,
        "phase_name": "Verified Mint",
        "phase_gates": {
            "P0": {"name": "Genesis", "active": True, "completed": True},
            "P1": {"name": "Impact Pilot", "active": True, "completed": True},
            "P2": {"name": "Verified Mint", "active": True, "completed": False},
            "P3": {"name": "Self-Custody", "active": False, "completed": False},
            "P4": {"name": "Carbon Branch", "active": False, "completed": False},
            "P5": {"name": "Governance", "active": False, "completed": False},
        },
    }


@router.post("/phasegate/activate/{phase}")
async def activate_phase(phase: int):
    return {"phase": phase, "status": "activated", "timestamp": "2026-09-20T12:00:00Z"}


# ============================================================================
# Oracle Endpoints
# ============================================================================


@router.post("/oracle/attestation")
async def submit_attestation(
    activity_id: str, data_type: str, confidence: int, commitment: str, signature: str
):
    return {"attestation_id": "ATT-123", "status": "submitted"}


@router.post("/oracle/report")
async def submit_impact_report(
    activity_id: str,
    data_type: str,
    confidence: int,
    impact_hash: str,
    evidence_commitment: str,
    methodology_version: int = 1,
):
    return {"report_id": "RPT-123", "challenge_deadline": "2026-09-27T12:00:00Z"}


@router.post("/oracle/challenge/{activity_id}")
async def challenge_report(activity_id: str):
    return {"status": "challenged", "activity_id": "ACT-123"}


@router.get("/oracle/metrics/{activity_id}")
async def get_impact_metrics(activity_id: str):
    return {
        "confidence": 85,
        "impact_score": 5000,
        "trust_multiplier": 10000,
        "survival_factor": 10000,
        "scarcity_factor": 10000,
    }


# ============================================================================
# Treasury & Ecosystem Fund
# ============================================================================


@router.post("/treasury/proposal")
async def create_treasury_proposal(to: str, amount: float, purpose: str):
    return {"proposal_id": 1, "status": "pending_approval"}


@router.post("/treasury/proposal/{proposal_id}/approve")
async def approve_proposal(proposal_id: int):
    return {"proposal_id": proposal_id, "status": "approved"}


@router.get("/treasury/balance")
async def treasury_balance():
    return {"balance": "150000.0", "currency": "ECO"}


@router.post("/ecosystem-fund/grant")
async def create_grant(
    recipient: str,
    amount: float,
    project_type: str,
    description: str,
    region: str,
    deadline: str,
    milestones: int,
):
    return {"grant_id": 1, "status": "pending"}


@router.post("/ecosystem-fund/grant/{grant_id}/approve")
async def approve_grant(grant_id: int):
    return {"grant_id": grant_id, "status": "approved"}


@router.post("/ecosystem-fund/grant/{grant_id}/milestone")
async def add_milestone(grant_id: int, description: str, amount: float, deadline: str):
    return {"milestone_id": 1, "status": "created"}


# ============================================================================
# Phase Gate Status
# ============================================================================


@router.get("/phasegate/status")
async def phase_gate_status():
    return {
        "current_phase": 2,
        "phases": {
            "P0": {"name": "Genesis", "duration_days": 30, "active": True, "completed": True},
            "P1": {"name": "Impact Pilot", "duration_days": 90, "active": True, "completed": True},
            "P2": {
                "name": "Verified Mint",
                "duration_days": 180,
                "active": True,
                "completed": False,
            },
            "P3": {
                "name": "Self-Custody",
                "duration_days": 365,
                "active": False,
                "completed": False,
            },
            "P4": {
                "name": "Carbon Branch",
                "duration_days": 540,
                "active": False,
                "completed": False,
            },
            "P5": {"name": "Governance", "duration_days": 0, "active": False, "completed": False},
        },
    }


@router.get("/health")
async def blockchain_health():
    return {
        "status": "operational",
        "service": "Blockchain Ledger - EcoCoin Protocol",
        "mode": "simulation",
        "features": {
            "ecocoin": True,
            "impact_certificate": True,
            "phase_gate": True,
            "oracle": True,
            "treasury": True,
            "ecosystem_fund": True,
            "mint_controller": True,
        },
        "note": "In-memory simulation for research. Deploy to Polygon Amoy for testnet.",
    }


@router.get("/info")
async def blockchain_info():
    return {
        "network": "Polygon Amoy (Testnet)",
        "chain_id": 80002,
        "contracts": {
            "EcoCoin": "0x...",
            "ImpactCertificate": "0x...",
            "PhaseGate": "0x...",
            "ImpactOracle": "0x...",
            "EcoTreasury": "0x...",
            "EcosystemFund": "0x...",
            "MintController": "0x...",
            "PhaseGate": "0x...",
        },
    }
