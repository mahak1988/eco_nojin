"""Compliance API router — KYC/AML, greenwashing, and credit bridge.

Endpoints for:
- KYC/AML verification and screening
- Greenwashing assessment and disclosure
- Credit bridge reconciliation (off-chain / on-chain)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_user
from services.carbon.compliance.greenwashing_guard import (
    DisclosureStatus,
    GreenwashingGuard,
)
from services.carbon.compliance.kyc_aml import (
    KYCService,
    KYCStatus,
)
from services.carbon.integration.credit_bridge import (
    CreditBridge,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance"])


def get_db():
    with hub.get_session() as session:
        yield session


def get_kyc_service():
    from services.carbon.compliance.kyc_aml import get_kyc_service as _get

    return _get()


def get_greenwashing_guard():
    from services.carbon.compliance.greenwashing_guard import GreenwashingGuard

    return GreenwashingGuard()


def get_credit_bridge():
    from services.carbon.integration.credit_bridge import get_credit_bridge as _get

    return _get()


# --------------------------------------------------------------------------- #
# Request schemas
# --------------------------------------------------------------------------- #


class KYCRegisterRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    date_of_birth: str | None = None
    kyc_level: str = "basic"


class KYCVerifyRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


class KYCRejectRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class AMLCheckRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


class GreenwashingAssessRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    claimed_tonnes: float | None = None
    actual_tonnes: float | None = None
    registered_methodology: str | None = None
    verified_methodology: str | None = None
    motor_methodology: str | None = None
    claimed_permanence: float | None = None
    motor_permanence_factor: float | None = None
    area_ha: float | None = None
    issued_tonnes: float | None = None


class DisclosureCreateRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    credit_id: str | None = None
    disclosure_type: str = Field(..., min_length=1, max_length=120)
    content: dict[str, Any]
    status: str = DisclosureStatus.RESTRICTED.value
    methodology: str | None = None


class BridgeRegisterRequest(BaseModel):
    credit_id: str = Field(..., min_length=1)
    token_id: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)


class BridgeSyncIssuanceRequest(BaseModel):
    credit_id: str = Field(..., min_length=1)
    token_id: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    holder_id: str = Field(..., min_length=1)
    data_mode: str = "modelled_estimate"
    correlation_id: str | None = None


# --------------------------------------------------------------------------- #
# KYC/AML endpoints
# --------------------------------------------------------------------------- #


@router.post("/kyc/register")
def kyc_register(
    payload: KYCRegisterRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    kyc_svc: KYCService = Depends(get_kyc_service),
):
    """Register a KYC record for a user."""
    try:
        record = kyc_svc.register_user(payload.user_id, **payload.model_dump(exclude_unset=True))
        return {
            "user_id": record.user_id,
            "kyc_level": record.kyc_level,
            "status": record.status.value,
            "risk_level": record.risk_level.value,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kyc/{user_id}")
def kyc_get(
    user_id: str,
    user: User = Depends(require_user),
    kyc_svc: KYCService = Depends(get_kyc_service),
):
    """Get KYC record for a user."""
    record = kyc_svc.get_record(user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="KYC record not found")
    return {
        "user_id": record.user_id,
        "kyc_level": record.kyc_level,
        "status": record.status.value,
        "risk_level": record.risk_level.value,
        "aml_checks": [
            {
                "check_type": c.check_type,
                "status": c.status,
                "risk_level": c.risk_level.value,
                "details": c.details,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in record.aml_checks
        ],
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
    }


@router.post("/kyc/verify")
def kyc_verify(
    payload: KYCVerifyRequest,
    user: User = Depends(require_user),
    kyc_svc: KYCService = Depends(get_kyc_service),
):
    """Mark KYC record as verified."""
    success = kyc_svc.verify_kyc(payload.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="KYC record not found")
    return {"user_id": payload.user_id, "status": KYCStatus.VERIFIED.value}


@router.post("/kyc/reject")
def kyc_reject(
    payload: KYCRejectRequest,
    user: User = Depends(require_user),
    kyc_svc: KYCService = Depends(get_kyc_service),
):
    """Reject KYC record."""
    success = kyc_svc.reject_kyc(payload.user_id, payload.reason)
    if not success:
        raise HTTPException(status_code=404, detail="KYC record not found")
    return {
        "user_id": payload.user_id,
        "status": KYCStatus.REJECTED.value,
        "reason": payload.reason,
    }


@router.post("/aml/check")
def aml_check(
    payload: AMLCheckRequest,
    user: User = Depends(require_user),
    kyc_svc: KYCService = Depends(get_kyc_service),
):
    """Run AML checks for a user."""
    try:
        checks = kyc_svc.run_aml_checks(payload.user_id)
        risk = kyc_svc.assess_risk(payload.user_id)
        return {
            "user_id": payload.user_id,
            "risk_level": risk.value,
            "compliant": kyc_svc.is_compliant(payload.user_id),
            "checks": [
                {
                    "check_type": c.check_type,
                    "status": c.status,
                    "risk_level": c.risk_level.value,
                    "details": c.details,
                }
                for c in checks
            ],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --------------------------------------------------------------------------- #
# Greenwashing endpoints
# --------------------------------------------------------------------------- #


@router.post("/greenwashing/assess")
def greenwashing_assess(
    payload: GreenwashingAssessRequest,
    user: User = Depends(require_user),
    guard: GreenwashingGuard = Depends(get_greenwashing_guard),
):
    """Run greenwashing assessment for a project."""
    result = guard.run_full_assessment(
        project_id=payload.project_id,
        claimed_tonnes=payload.claimed_tonnes,
        actual_tonnes=payload.actual_tonnes,
        registered_methodology=payload.registered_methodology,
        verified_methodology=payload.verified_methodology,
        motor_methodology=payload.motor_methodology,
        claimed_permanence=payload.claimed_permanence,
        motor_permanence_factor=payload.motor_permanence_factor,
        area_ha=payload.area_ha,
        issued_tonnes=payload.issued_tonnes,
    )
    return result


@router.get("/greenwashing/flags/{project_id}")
def greenwashing_flags(
    project_id: str,
    user: User = Depends(require_user),
    guard: GreenwashingGuard = Depends(get_greenwashing_guard),
):
    """Get greenwashing flags for a project."""
    return guard.get_flags(project_id)


@router.post("/greenwashing/disclosure")
def create_disclosure(
    payload: DisclosureCreateRequest,
    user: User = Depends(require_user),
    guard: GreenwashingGuard = Depends(get_greenwashing_guard),
):
    """Create a disclosure record."""
    record = guard.create_disclosure(
        project_id=payload.project_id,
        credit_id=payload.credit_id,
        disclosure_type=payload.disclosure_type,
        content=payload.content,
        status=DisclosureStatus(payload.status),
        methodology=payload.methodology,
    )
    return {
        "project_id": record.project_id,
        "credit_id": record.credit_id,
        "disclosure_type": record.disclosure_type,
        "status": record.status.value,
        "disclosed_at": record.disclosed_at.isoformat(),
    }


@router.get("/greenwashing/disclosure/{project_id}")
def get_disclosures(
    project_id: str,
    user: User = Depends(require_user),
    status: str | None = Query(None),
    guard: GreenwashingGuard = Depends(get_greenwashing_guard),
):
    """Get disclosure records for a project."""
    records = guard.get_disclosures(
        project_id=project_id,
        status=DisclosureStatus(status) if status else None,
    )
    return [
        {
            "project_id": r.project_id,
            "credit_id": r.credit_id,
            "disclosure_type": r.disclosure_type,
            "status": r.status.value,
            "content": r.content,
            "disclosed_at": r.disclosed_at.isoformat(),
            "reviewer": r.reviewer,
            "methodology": r.methodology,
        }
        for r in records
    ]


@router.get("/greenwashing/public/{project_id}")
def public_disclosure(
    project_id: str,
    user: User = Depends(require_user),
    guard: GreenwashingGuard = Depends(get_greenwashing_guard),
):
    """Generate public-facing disclosure for a project."""
    return guard.public_disclosure(project_id)


@router.post("/greenwashing/verify-owner")
def verify_project_owner(
    project_id: str = Query(..., min_length=1),
    owner_id: str = Query(..., min_length=1),
    user: User = Depends(require_user),
    guard: GreenwashingGuard = Depends(get_greenwashing_guard),
):
    """Verify project owner KYC compliance."""
    return guard.verify_project_owner(project_id, owner_id)


# --------------------------------------------------------------------------- #
# Credit bridge endpoints
# --------------------------------------------------------------------------- #


@router.post("/bridge/correlate")
def bridge_correlate(
    payload: BridgeRegisterRequest,
    user: User = Depends(require_user),
    bridge: CreditBridge = Depends(get_credit_bridge),
):
    """Register correlation between off-chain credit and on-chain token."""
    bridge.register_correlation(
        credit_id=payload.credit_id,
        token_id=payload.token_id,
        project_id=payload.project_id,
    )
    return {
        "credit_id": payload.credit_id,
        "token_id": payload.token_id,
        "project_id": payload.project_id,
    }


@router.get("/bridge/correlation/{credit_id}")
def bridge_correlation(
    credit_id: str,
    user: User = Depends(require_user),
    bridge: CreditBridge = Depends(get_credit_bridge),
):
    """Get correlation data for a credit."""
    corr = bridge.get_correlation(credit_id)
    if corr is None:
        raise HTTPException(status_code=404, detail="Correlation not found")
    return corr


@router.post("/bridge/sync/issuance")
def bridge_sync_issuance(
    payload: BridgeSyncIssuanceRequest,
    user: User = Depends(require_user),
    bridge: CreditBridge = Depends(get_credit_bridge),
):
    """Synchronize issuance across off-chain and on-chain."""
    event = bridge.sync_issuance(
        credit_id=payload.credit_id,
        token_id=payload.token_id,
        project_id=payload.project_id,
        amount=payload.amount,
        holder_id=payload.holder_id,
        data_mode=payload.data_mode,
        correlation_id=payload.correlation_id,
    )
    return {
        "event_id": event.event_id,
        "status": event.status.value,
        "synced_at": event.synced_at.isoformat() if event.synced_at else None,
        "error": event.error,
    }


@router.get("/bridge/reconcile/{credit_id}")
def bridge_reconcile(
    credit_id: str,
    user: User = Depends(require_user),
    bridge: CreditBridge = Depends(get_credit_bridge),
):
    """Check double-counting risk for a credit."""
    result = bridge.check_double_counting_risk(credit_id)
    return {
        "credit_id": result.credit_id,
        "risk": result.risk.value,
        "off_chain_total": result.off_chain_total,
        "on_chain_total": result.on_chain_total,
        "off_chain_state": result.off_chain_state,
        "on_chain_state": result.on_chain_state,
        "discrepancies": result.discrepancies,
    }


@router.get("/bridge/reconcile/project/{project_id}")
def bridge_reconcile_project(
    project_id: str,
    user: User = Depends(require_user),
    bridge: CreditBridge = Depends(get_credit_bridge),
):
    """Reconcile all credits for a project."""
    return bridge.reconcile_project(project_id)


@router.get("/bridge/events/{credit_id}")
def bridge_events(
    credit_id: str,
    user: User = Depends(require_user),
    bridge: CreditBridge = Depends(get_credit_bridge),
):
    """Get bridge events for a credit."""
    return bridge.get_bridge_events(credit_id)
