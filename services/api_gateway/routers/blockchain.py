"""API endpoints for Blockchain Ledger - EcoCoin Protocol"""

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.hub import hub


# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session


router = APIRouter(prefix="/api/v1/blockchain", tags=["Blockchain Ledger"])


#: Honest capability report, defined once so /health and /ecocoin/health cannot
#: drift apart. 2026-09-26: every entry below was previously reported as
#: available while none of it was implemented.
#:
#: /health is the endpoint the admin panel and the public health page read
#: (apps/web/src/lib/api/health.ts, lib/workspaces/registry.ts,
#: components/admin/admin-sections.ts), which is precisely why it must not
#: overstate. Each reason is long enough to be checked against the source.
_ECOCOIN_NOT_IMPLEMENTED: dict[str, str] = {
    "ecocoin": (
        "not_implemented — contracts/src/EcoCoin.sol has never compiled; mint() "
        "reverts unconditionally because _burn runs before _mint on a zero "
        "balance, and HARD_CAP is dead code because totalSupply() is always 0."
    ),
    "impact_certificate": (
        "not_implemented — ImpactOracle._mintRewards is unreachable and "
        "ImpactOracle has no duplicate-activity guard."
    ),
    "phase_gate": (
        "not_implemented — PhaseGate is never instantiated; its VVB gate returns "
        "a hardcoded true and every phase cap initialises to 0."
    ),
    "oracle": (
        "not_implemented — attestation signatures are stored and never verified; "
        "stake is not escrowed; slashing is a no-op."
    ),
    "treasury": (
        "not_implemented — never funded. 30% of every mint goes to a contract "
        "with no withdrawal function."
    ),
    "ecosystem_fund": (
        "not_implemented — never funded; totalAllocated is fabricated."
    ),
    "mint_controller": (
        "not_implemented — never invoked by any contract in the repository."
    ),
}


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
    reference_id: str | None = None


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
    """Honest capability report for the EcoCoin module.

    Shares its source of truth with /health so the two cannot diverge.
    """
    return {
        "status": "degraded",
        "module": "ecocoin",
        "version": "1.0.0",
        "production_ready": False,
        "features": {
            "external_exchange": False,
            "staking": False,
            "referral_program": False,
            "phase_gated_transfers": False,
        },
        "implementation_status": dict(_ECOCOIN_NOT_IMPLEMENTED),
        "referral_program_note": (
            "Removed. No referral code, referrer_id field, DB column, or feature "
            "flag existed anywhere in the codebase; the flag was a literal in a "
            "return statement."
        ),
        "note": (
            "In-memory simulation only. No contract is deployed on any network. "
            "See reports/ECOCOIN_STRATEGY_FA_2026-09-26.md for the remediation "
            "plan and the legal framework for the replacement design."
        ),
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
    """Phase-gate status, in the shape the frontend actually reads.

    2026-09-26 correction. Three separate defects were resolved here:

    1. This route was registered twice with two same-named handlers. The second
       shadowed the first in the module namespace while FastAPI served the
       first, so the duplicate was unreachable in every sense.
    2. Neither version matched `PhaseGateStatus` in the frontend
       (`{ phase, gates, all_passed }`), which is what
       public/goals/manifesto and public/goals/roadmap destructure. Both
       public pages were reading keys the API never returned.
    3. The previous payload asserted that phases 0 and 1 were *completed* for
       a protocol that has never compiled. That claim is removed.
    """
    gates = [
        {
            "id": pid,
            "name": name,
            "active": False,
            "completed": False,
            "duration_days": days,
        }
        for pid, name, days in (
            ("P0", "Genesis", 30),
            ("P1", "Impact Pilot", 90),
            ("P2", "Verified Mint", 180),
            ("P3", "Self-Custody", 365),
            ("P4", "Carbon Branch", 540),
            ("P5", "Governance", 0),
        )
    ]
    return {
        "phase": "P0",
        "gates": gates,
        # Nothing is passed, because nothing is implemented.
        "all_passed": False,
        "implemented": False,
        "note": (
            "No phase gate is satisfied. PhaseGate.sol has never compiled and "
            "is not instantiated anywhere; its VVB gate returns a hardcoded "
            "true and every phase cap initialises to 0. See "
            "reports/ECOCOIN_STRATEGY_FA_2026-09-26.md."
        ),
    }


@router.post("/phasegate/activate/{phase}")
async def activate_phase(phase: int):
    """Phase activation is not available: there is no deployed PhaseGate.

    Previously this returned a hardcoded `status: activated`, which implied
    the transition had occurred.
    """
    raise HTTPException(
        status_code=503,
        detail=(
            "Phase activation is unavailable: PhaseGate is not deployed and has "
            "never compiled. See reports/ECOCOIN_STRATEGY_FA_2026-09-26.md"
        ),
    )


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
# Health and deployment status
#
# These two endpoints are read by the admin panel and the public health page
# (apps/web/src/lib/api/health.ts, lib/workspaces/registry.ts,
# components/admin/admin-sections.ts), so they must not overstate readiness.
# 2026-09-26: all seven capability flags below were True while zero of the
# seven were implemented. They are derived from _ECOCOIN_NOT_IMPLEMENTED so
# the two endpoints cannot drift apart.
# ============================================================================


@router.get("/health")
async def blockchain_health():
    return {
        "status": "degraded",
        "service": "Blockchain Ledger - EcoCoin Protocol",
        "mode": "simulation",
        "deployed": False,
        "production_ready": False,
        "features": dict.fromkeys(_ECOCOIN_NOT_IMPLEMENTED, False),
        "implementation_status": dict(_ECOCOIN_NOT_IMPLEMENTED),
        "note": (
            "In-memory simulation for research. No contract is deployed on any "
            "network and none has ever compiled. This endpoint previously "
            "reported all seven capabilities as available, which was false. "
            "See reports/ECOCOIN_STRATEGY_FA_2026-09-26.md."
        ),
    }


@router.get("/info")
async def blockchain_info():
    return {
        "network": None,
        "chain_id": None,
        "deployed": False,
        "configured_network": "Polygon Amoy (Testnet)",
        "contracts": dict.fromkeys(
            (
                "EcoCoin",
                "ImpactCertificate",
                "PhaseGate",
                "ImpactOracle",
                "EcoTreasury",
                "EcosystemFund",
                "MintController",
            ),
            None,
        ),
        "note": (
            "No contract has been deployed. The '0x...' placeholders returned "
            "before this correction implied otherwise."
        ),
    }


