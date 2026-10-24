"""The governance router: the village/rangeland onboarding workflow over HTTP (P7).

``services/village/service.py`` already carries the rules (a step needs a
submitted application; activation needs an adopted charter and a live
coordinator; sensitive fields are private until published one by one). This
router exposes it without re-implementing any of them — same conventions as
``services/tourism/api/router.py``. Cross-village isolation is server-side: a
non-admin caller can only read a space they administer, and the list is scoped.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_roles, require_user
from services.api_gateway.errors import domain_detail
from services.village.models import CommunitySpaceKind
from services.village.service import GovernanceError, VillageGovernanceService

# ═══════════════════════════════════════════════════════════════
# KYC / Digital Identity schemas (P7.1)
# ═══════════════════════════════════════════════════════════════


class KycSubmit(BaseModel):
    evidence_ref: str | None = Field(None, max_length=300)
    national_id: str | None = Field(None, max_length=50)
    eidas_level: str | None = Field(None, max_length=20)  # low|substantial|high


class KycApprove(BaseModel):
    pass


class KycReject(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class KycRead(BaseModel):
    village_id: str
    kyc_status: str
    kyc_submitted_at: str | None
    kyc_approved_at: str | None
    verification_status: str
    representative_identity_verified: bool

router = APIRouter(prefix="/api/v1/village-governance", tags=["village-governance"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


async def _load_space(db: AsyncSession, space_id: str):
    from sqlalchemy import select

    from services.village.models import CommunitySpace

    space = (
        await db.execute(select(CommunitySpace).where(CommunitySpace.id == space_id))
    ).scalar_one_or_none()
    if space is None:
        raise HTTPException(status_code=404, detail="Community space not found")
    return space


async def _require_admin_of(db: AsyncSession, space, user: User) -> None:
    """Server-side tenancy: the caller must administer the space or be an admin."""
    from sqlalchemy import select

    from services.village.models import WorkingGroup, WorkingGroupMembership

    if str(getattr(user, "role", "")) == "admin":
        return
    membership = (
        await db.execute(
            select(WorkingGroupMembership)
            .join(WorkingGroup, WorkingGroup.id == WorkingGroupMembership.group_id)
            .where(
                WorkingGroup.space_id == space.id,
                WorkingGroupMembership.user_id == str(user.id),
                WorkingGroupMembership.ended_reason.is_(None),
            )
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=403, detail="Not an administrator of this space")


@router.post("/spaces", status_code=201)
async def register_space(
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = VillageGovernanceService(db)
    try:
        space = await service.register_space(
            village_id=payload["village_id"],
            name=payload["name"],
            kind=payload.get("kind", "village"),
            region=payload.get("region"),
            country=payload.get("country"),
            actor_id=str(user.id),
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"Missing field: {exc.args[0]}") from exc
    except GovernanceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(space.id), "village_id": space.village_id, "status": space.status}


@router.get("/spaces")
async def list_spaces(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List the community spaces this caller administers.

    A non-admin never sees another village's spaces (the same server-side
    tenancy as the read endpoint); an admin sees all. P5's dashboard called
    this collection and got 405 — the route is the fix, not a client workaround.
    """
    from sqlalchemy import select

    from services.village.models import CommunitySpace, WorkingGroup, WorkingGroupMembership

    query = select(CommunitySpace)
    if str(getattr(user, "role", "")) != "admin":
        administered = (
            select(WorkingGroup.space_id)
            .join(WorkingGroupMembership, WorkingGroupMembership.group_id == WorkingGroup.id)
            .where(
                WorkingGroupMembership.user_id == str(user.id),
                WorkingGroupMembership.ended_reason.is_(None),
            )
        )
        query = query.where(CommunitySpace.id.in_(administered))
    rows = (
        await db.execute(query.order_by(CommunitySpace.created_at.desc()).limit(limit).offset(offset))
    ).scalars().all()
    return {
        "items": [
            {
                "id": str(space.id),
                "village_id": space.village_id,
                "name": space.name,
                "kind": space.kind,
                "status": space.status,
            }
            for space in rows
        ],
        "count": len(rows),
    }


@router.get("/spaces/{space_id}")
async def get_space(
    space_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    space = await _load_space(db, space_id)
    # A stranger may not read another village's space at all.
    if str(getattr(user, "role", "")) != "admin":
        await _require_admin_of(db, space, user)
    return {
        "id": str(space.id),
        "village_id": space.village_id,
        "name": space.name,
        "kind": space.kind,
        "status": space.status,
        # P5: the map renders the PUBLIC centroid; the exact boundary is private
        # and never crosses the wire from this endpoint.
        "public_centroid": space.public_centroid,
        "sensitive_fields_published": space.sensitive_fields_published,
        "published_fields": space.published_fields,
    }


@router.post("/spaces/{space_id}/applications", status_code=201)
async def submit_application(
    space_id: str,
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    space = await _load_space(db, space_id)
    await _require_admin_of(db, space, user)
    service = VillageGovernanceService(db)
    try:
        application = await service.submit_application(
            space_id, step=payload["step"], actor_id=str(user.id),
            evidence_ref=payload.get("evidence_ref"),
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"Missing field: {exc.args[0]}") from exc
    except GovernanceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return {"id": str(application.id), "step": application.step, "status": application.status}


@router.post("/spaces/{space_id}/advance")
async def advance(
    space_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    await _load_space(db, space_id)
    service = VillageGovernanceService(db)
    try:
        advanced = await service.advance(space_id, actor_id=str(user.id))
    except GovernanceError as exc:
        raise HTTPException(status_code=409, detail=domain_detail(exc, 409)) from exc
    return {"id": str(advanced.id), "status": advanced.status}


@router.post("/spaces/{space_id}/activate")
async def activate(
    space_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    # Load first so an unknown space is a 404 (like every sibling route); only
    # a genuine state conflict maps to 409 below.
    await _load_space(db, space_id)
    service = VillageGovernanceService(db)
    try:
        space = await service.activate(space_id, actor_id=str(user.id))
    except GovernanceError as exc:
        raise HTTPException(status_code=409, detail=domain_detail(exc, 409)) from exc
    return {"id": str(space.id), "status": space.status}


@router.post("/spaces/{space_id}/link-marketplace")
async def link_marketplace(
    space_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """Ensure a LandscapeVillage record exists for this community space.

    Creates (or refreshes) the marketplace-hub village row so
    hub_service endpoints can resolve and write to this village. Admin or
    space administrator required.
    """
    space = await _load_space(db, space_id)
    if str(getattr(user, "role", "")) != "admin":
        await _require_admin_of(db, space, user)

    VillageGovernanceService(db)
    from services.landscape.models import LandscapeVillage

    result = await db.execute(
        select(LandscapeVillage).where(LandscapeVillage.village_id == space.village_id)
    )
    lv = result.scalar_one_or_none()
    if lv is None:
        lv = LandscapeVillage(
            village_id=space.village_id,
            name=space.name,
            region=space.region,
            country=space.country,
            coordinates=None,
            geo_boundary=None,
            brand_name=None,
            brand_logo_url=None,
            gi_registration=None,
            is_active=True,
            established_at=None,
            active_modules=["marketplace"],
            total_members=0,
            active_sellers=0,
            active_tour_guides=0,
            monthly_gmv=Decimal("0.00"),
            ecological_metrics_data={},
            smart_contract_address=None,
            blockchain_network=None,
            verification_status="pending",
            representative_status="none",
            workflow_status="published",
        )
        db.add(lv)
        await db.commit()
        await db.refresh(lv)

    return {
        "village_id": lv.village_id,
        "name": lv.name,
        "is_active": lv.is_active,
        "active_modules": lv.active_modules,
        "verification_status": lv.verification_status,
    }


@router.get("/villages/{village_id}/dashboard", response_model=dict)
async def unified_dashboard(
    village_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """داشبورد یک‌نشته روستا — همهٔ ماژول‌ها در یک پاسخ.

    جمع‌آوری داده‌های حکمرانی، بازارگاه، مرتع، اکوتورزم و یونسکو
    برای یک روستا مشخص.
    """
    service = VillageGovernanceService(db)
    try:
        return await service.unified_village_dashboard(village_id)
    except GovernanceError as e:
        raise HTTPException(status_code=400, detail=domain_detail(e, 400)) from e


@router.get("/spaces/{space_id}/decisions")
async def decisions(
    space_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    limit: int = Query(default=50, ge=1, le=200),
):
    """The append-only local decision log — readable by the space's administrators."""
    from sqlalchemy import select

    from services.village.models import GovernanceDecision

    space = await _load_space(db, space_id)
    if str(getattr(user, "role", "")) != "admin":
        await _require_admin_of(db, space, user)
    rows = (
        await db.execute(
            select(GovernanceDecision)
            .where(GovernanceDecision.space_id == space_id)
            .order_by(GovernanceDecision.recorded_at.desc())
            .limit(limit)
        )
    ).scalars()
    return {
        "decisions": [
            {
                "id": str(d.id),
                "kind": d.kind,
                "summary": d.summary,
                "decided_by": d.decided_by,
                "recorded_at": d.recorded_at.isoformat(),
            }
            for d in rows
        ]
    }


@router.post("/spaces/{space_id}/link-rangeland/{rangeland_id}")
async def link_rangeland(
    space_id: str,
    rangeland_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """Link a rangeland to a pastoral_rangeland governance space.

    Requires the space to be ACTIVE with kind=pastoral_rangeland. Admin or
    space administrator required.
    """
    space = await _load_space(db, space_id)
    if str(getattr(user, "role", "")) != "admin":
        await _require_admin_of(db, space, user)

    if space.kind != CommunitySpaceKind.PASTORAL_RANGELAND.value:
        raise HTTPException(
            status_code=400,
            detail=f"space {space_id} is not a pastoral_rangeland (kind={space.kind})",
        )

    from services.rangeland.models import Rangeland

    result = await db.execute(
        select(Rangeland).where(Rangeland.rangeland_id == rangeland_id)
    )
    rangeland = result.scalar_one_or_none()
    if rangeland is None:
        raise HTTPException(status_code=404, detail="Rangeland not found")
    if rangeland.village_id != space.village_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"rangeland {rangeland_id} belongs to village {rangeland.village_id}, "
                f"not {space.village_id}"
            ),
        )

    rangeland.governance_space_id = str(space.id)
    await db.commit()
    await db.refresh(rangeland)

    return {
        "rangeland_id": rangeland.rangeland_id,
        "governance_space_id": rangeland.governance_space_id,
        "village_id": rangeland.village_id,
    }


# ═══════════════════════════════════════════════════════════════
# KYC / Digital Identity endpoints (P7.1)
# ═══════════════════════════════════════════════════════════════


@router.post("/spaces/{space_id}/kyc/submit", response_model=KycRead)
async def submit_kyc(
    space_id: str,
    payload: KycSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """ثبت اسناد KYC / هویتدیجیتال edustنده روستا."""
    space = await _load_space(db, space_id)
    if str(getattr(user, "role", "")) != "admin":
        await _require_admin_of(db, space, user)
    service = VillageGovernanceService(db)
    try:
        await service.submit_kyc(
            space_id,
            actor_id=str(user.id),
            evidence_ref=payload.evidence_ref,
            national_id=payload.national_id,
            eidas_level=payload.eidas_level,
        )
    except GovernanceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return await _kyc_read(db, space_id)


@router.post("/spaces/{space_id}/kyc/approve", response_model=KycRead)
async def approve_kyc(
    space_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    """تایید KYC توسط ادمین پلتفرم — روستا در مارکت‌پلیس قابل مشاهده می‌شود."""
    await _load_space(db, space_id)
    service = VillageGovernanceService(db)
    try:
        await service.approve_kyc(space_id, actor_id=str(user.id))
    except GovernanceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return await _kyc_read(db, space_id)


@router.post("/spaces/{space_id}/kyc/reject", response_model=KycRead)
async def reject_kyc(
    space_id: str,
    payload: KycReject,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles("admin"))],
):
    """رد KYC با دلیل توسط ادمین پلتفرم."""
    await _load_space(db, space_id)
    service = VillageGovernanceService(db)
    try:
        await service.reject_kyc(space_id, actor_id=str(user.id), reason=payload.reason)
    except GovernanceError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return await _kyc_read(db, space_id)


@router.get("/spaces/{space_id}/kyc", response_model=KycRead)
async def get_kyc(
    space_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """مشاهده وضعیت KYC روستا."""
    space = await _load_space(db, space_id)
    if str(getattr(user, "role", "")) != "admin":
        await _require_admin_of(db, space, user)
    return await _kyc_read(db, space_id)


async def _kyc_read(db: AsyncSession, space_id: str) -> KycRead:
    from sqlalchemy import select

    from services.landscape.models import LandscapeVillage
    from services.village.models import CommunitySpace

    space = (
        await db.execute(select(CommunitySpace).where(CommunitySpace.id == space_id))
    ).scalar_one_or_none()
    if space is None:
        raise HTTPException(status_code=404, detail="Community space not found")

    lv = (
        await db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == space.village_id)
        )
    ).scalar_one_or_none()
    if lv is None:
        raise HTTPException(status_code=404, detail="Landscape village not found")

    return KycRead(
        village_id=lv.village_id,
        kyc_status=lv.kyc_status,
        kyc_submitted_at=lv.kyc_submitted_at.isoformat() if lv.kyc_submitted_at else None,
        kyc_approved_at=lv.kyc_approved_at.isoformat() if lv.kyc_approved_at else None,
        verification_status=lv.verification_status,
        representative_identity_verified=lv.representative_identity_verified,
    )
