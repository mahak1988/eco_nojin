"""The compliance registry over HTTP (P9).

The service (``services/compliance/service.py``) holds the rules; this router
exposes them and adds nothing of its own. Two invariants are enforced here and
pinned by tests:

* a caller never sees another subject's credentials or assessments — the status
  and listing endpoints are scoped to the caller unless they carry an approver
  role;
* every response is evidence-linked: the status view exposes the assessment's
  ``evidence_ref``, so no response can be quoted as a bare verdict.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_roles, require_user
from services.api_gateway.errors import domain_detail
from services.compliance.models import AssessmentOutcome
from services.compliance.service import ComplianceError, ComplianceService

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _is_approver(user: User) -> bool:
    return str(getattr(user, "role", "")) == "admin"


def _validate_future(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value


class ClassifyRequest(BaseModel):
    activity_code: str = Field(..., min_length=1, max_length=100)
    jurisdiction_id: str = Field(..., min_length=1, max_length=36)
    note: str | None = None


class CredentialRequest(BaseModel):
    kind: str = Field(..., min_length=1, max_length=32)
    reference: str | None = None
    issuer: str | None = None
    expires_at: datetime | None = None


class VerifyRequest(BaseModel):
    method: str = Field(..., min_length=1, max_length=200)
    evidence_ref: str | None = None
    approve: bool


class AssessRequest(BaseModel):
    activity_code: str
    jurisdiction_id: str
    outcome: str
    evidence_ref: str = Field(..., min_length=1, max_length=300)
    note: str | None = None


class SourceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    jurisdiction: str = Field(..., min_length=1, max_length=100)
    url: str | None = None


class JurisdictionRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=1, max_length=100)


class RequirementRequest(BaseModel):
    source_id: str
    jurisdiction_id: str
    activity_code: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=400)
    mandatory: bool = True


class ExceptionRequest(BaseModel):
    requirement_id: str
    subject_type: str
    subject_id: str
    reason: str = Field(..., min_length=1, max_length=500)
    expires_at: datetime | None = None


@router.post("/classify/{subject_type}/{subject_id}", status_code=201)
async def classify(
    subject_type: str,
    subject_id: str,
    payload: ClassifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    if not _is_approver(user) and subject_id != str(user.id):
        raise HTTPException(
            status_code=403, detail="Cannot classify another subject"
        )
    service = ComplianceService(db)
    try:
        classification = await service.classify_activity(
            subject_type=subject_type,
            subject_id=subject_id,
            activity_code=payload.activity_code,
            jurisdiction_id=payload.jurisdiction_id,
            classified_by=str(user.id),
            note=payload.note,
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {
        "id": str(classification.id),
        "activity_code": classification.activity_code,
        "jurisdiction_id": classification.jurisdiction_id,
    }


@router.post("/credentials/{subject_type}/{subject_id}", status_code=201)
async def register_credential(
    subject_type: str,
    subject_id: str,
    payload: CredentialRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    if not _is_approver(user) and subject_id != str(user.id):
        raise HTTPException(
            status_code=403, detail="Cannot register a credential for another subject"
        )
    service = ComplianceService(db)
    try:
        credential = await service.register_credential(
            subject_type=subject_type,
            subject_id=subject_id,
            kind=payload.kind,
            reference=payload.reference,
            issuer=payload.issuer,
            expires_at=_validate_future(payload.expires_at),
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(credential.id), "kind": credential.kind, "status": credential.status}


@router.post("/credentials/{credential_id}/verify")
async def verify_credential(
    credential_id: str,
    payload: VerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    service = ComplianceService(db)
    try:
        credential = await service.verify_credential(
            credential_id,
            verifier_id=str(user.id),
            method=payload.method,
            evidence_ref=payload.evidence_ref,
            approve=payload.approve,
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(credential.id), "status": credential.status}


@router.post("/assess/{subject_type}/{subject_id}", status_code=201)
async def assess(
    subject_type: str,
    subject_id: str,
    payload: AssessRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    if not _is_approver(user) and subject_id != str(user.id):
        raise HTTPException(status_code=403, detail="Cannot assess another subject")
    if payload.outcome not in {o.value for o in AssessmentOutcome}:
        raise HTTPException(status_code=422, detail=f"Unknown outcome: {payload.outcome}")
    service = ComplianceService(db)
    try:
        assessment = await service.assess(
            subject_type=subject_type,
            subject_id=subject_id,
            activity_code=payload.activity_code,
            jurisdiction_id=payload.jurisdiction_id,
            outcome=payload.outcome,
            evidence_ref=payload.evidence_ref,
            assessed_by=str(user.id),
            note=payload.note,
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(assessment.id), "outcome": assessment.outcome}


@router.get("/status/{subject_type}/{subject_id}")
async def status(
    subject_type: str,
    subject_id: str,
    jurisdiction_id: Annotated[str, Query(max_length=36)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """The evidence-linked status — scoped to the caller unless an approver."""
    if not _is_approver(user) and subject_id != str(user.id):
        raise HTTPException(status_code=403, detail="Cannot read another subject's status")
    service = ComplianceService(db)
    return await service.subject_status(subject_type, subject_id, jurisdiction_id)


# ======================================================================
# Reference data CRUD (admin only)
# ======================================================================

@router.post("/sources", status_code=201)
async def create_source(
    payload: SourceRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    service = ComplianceService(db)
    try:
        source = await service.add_source(
            name=payload.name,
            jurisdiction=payload.jurisdiction,
            url=payload.url,
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(source.id), "name": source.name, "jurisdiction": source.jurisdiction}


@router.get("/sources")
async def list_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    from sqlalchemy import select

    from services.compliance.models import RegulatorySource
    result = await db.execute(select(RegulatorySource).order_by(RegulatorySource.created_at.desc()))
    sources = result.scalars().all()
    return {
        "items": [
            {
                "id": str(s.id),
                "name": s.name,
                "jurisdiction": s.jurisdiction,
                "url": s.url,
                "published_at": s.published_at.isoformat() if s.published_at else None,
                "effective_from": s.effective_from.isoformat() if s.effective_from else None,
                "effective_to": s.effective_to.isoformat() if s.effective_to else None,
            }
            for s in sources
        ]
    }


@router.post("/jurisdictions", status_code=201)
async def create_jurisdiction(
    payload: JurisdictionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    service = ComplianceService(db)
    try:
        jurisdiction = await service.add_jurisdiction(
            code=payload.code,
            name=payload.name,
            country=payload.country,
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(jurisdiction.id), "code": jurisdiction.code, "name": jurisdiction.name}


@router.get("/jurisdictions")
async def list_jurisdictions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    from sqlalchemy import select

    from services.compliance.models import Jurisdiction
    result = await db.execute(select(Jurisdiction).order_by(Jurisdiction.created_at.desc()))
    jurisdictions = result.scalars().all()
    return {
        "items": [
            {
                "id": str(j.id),
                "code": j.code,
                "name": j.name,
                "country": j.country,
            }
            for j in jurisdictions
        ]
    }


@router.post("/requirements", status_code=201)
async def create_requirement(
    payload: RequirementRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    service = ComplianceService(db)
    try:
        requirement = await service.add_requirement(
            source_id=payload.source_id,
            jurisdiction_id=payload.jurisdiction_id,
            activity_code=payload.activity_code,
            title=payload.title,
            mandatory=payload.mandatory,
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(requirement.id), "title": requirement.title, "mandatory": requirement.mandatory}


@router.get("/requirements")
async def list_requirements(
    jurisdiction_id: Annotated[str, Query(max_length=36)],
    activity_code: Annotated[str, Query(max_length=100)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    service = ComplianceService(db)
    requirements = await service.requirements_for(jurisdiction_id, activity_code)
    return {
        "items": [
            {
                "id": str(r.id),
                "title": r.title,
                "mandatory": r.mandatory,
                "activity_code": r.activity_code,
            }
            for r in requirements
        ]
    }


# ======================================================================
# Exception management
# ======================================================================

@router.post("/exceptions", status_code=201)
async def grant_exception(
    payload: ExceptionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    service = ComplianceService(db)
    try:
        exception = await service.grant_exception(
            requirement_id=payload.requirement_id,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            reason=payload.reason,
            granted_by=str(user.id),
            expires_at=_validate_future(payload.expires_at),
        )
    except ComplianceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(exception.id), "requirement_id": str(exception.requirement_id)}


@router.get("/exceptions")
async def list_exceptions(
    subject_type: str,
    subject_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    from sqlalchemy import select

    from services.compliance.models import ComplianceException
    result = await db.execute(
        select(ComplianceException).where(
            ComplianceException.subject_type == subject_type,
            ComplianceException.subject_id == subject_id,
        ).order_by(ComplianceException.created_at.desc())
    )
    exceptions = result.scalars().all()
    return {
        "items": [
            {
                "id": str(e.id),
                "requirement_id": str(e.requirement_id),
                "reason": e.reason,
                "granted_by": e.granted_by,
                "expires_at": e.expires_at.isoformat() if e.expires_at else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in exceptions
        ]
    }


# ======================================================================
# Expiry sweeps (admin only)
# ======================================================================

@router.post("/sweep-expired", status_code=200)
async def sweep_expired(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    """Manually trigger expiry sweep for credentials and assessments."""
    service = ComplianceService(db)
    expired = await service.sweep_expired()
    return {"expired_ids": expired, "count": len(expired)}


@router.get("/audit-log")
async def audit_log(
    subject_type: Annotated[str, Query(max_length=32)],
    subject_id: Annotated[str, Query(max_length=36)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    from sqlalchemy import select

    from services.compliance.models import ComplianceAuditLog
    result = await db.execute(
        select(ComplianceAuditLog).where(
            ComplianceAuditLog.subject_type == subject_type,
            ComplianceAuditLog.subject_id == subject_id,
        ).order_by(ComplianceAuditLog.created_at.desc()).limit(200)
    )
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": str(l.id),
                "action": l.action,
                "actor": l.actor,
                "detail": l.detail,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]
    }