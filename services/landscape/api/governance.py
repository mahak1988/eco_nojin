"""روتر حکمرانی قلمرو (BG-007 + BG-015).

حیات عضو شورای حکمرانی (credential · delegation · expiration · audit):
- افزودن عضو (Credential)
- غیرفعال کردن (is_active -> False)
- فعال‌سازی مجدد
- مدیریت دوره عضویت (Delegation / Expiration)
- خروج از شورا

مسیرها زیر ``/api/v1/landscape/villages/{village_id}/governance`` مونت می‌شوند
(زیرروتر `services/landscape/api/__init__.py`).
خواندن بدون احراز هویت (عمومی)؛ نوشتن نیازمند کاربر احراز هویت‌شده با نقش
نویسندهٔ حکمرانی است.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from database.hub import hub
from database.models import User
from services.api_gateway.auth import ROLE_ADMIN, require_roles
from services.api_gateway.errors import safe_detail_for_status

from ..service import LandscapeService, get_hub_service

router = APIRouter(prefix="/api/v1/landscape", tags=["landscape-governance"])

#: نقش‌های نویسندهٔ حکمرانی — همان مجموعه‌ای که
#: ``services.marketplace.hub_service._GOVERNANCE_WRITE_ROLES`` برای مجوز
#: نوشتن محتوای روستا تعریف می‌کند، به‌علاوهٔ ادمین پلتفرم. عضویت شورا
#: تصمیم حکمرانی است، نه نوشتن خود روستا، پس هر سه مسیر افزودن/حذف/غیرفعال‌سازی
#: همین نقش‌ها را می‌خواهند.
_GOVERNANCE_WRITE_ROLES = (
    ROLE_ADMIN,
    "landscape_manager",
    "council_member",
    "marketplace_rep",
    "tourism_rep",
    "agriculture_rep",
)

_require_governance_writer = require_roles(*_GOVERNANCE_WRITE_ROLES)


async def _get_db():
    """دریافت Session برای این درخواست."""
    async with hub.get_async_session() as session:
        yield session


async def _run(db, func, *args, **kwargs):
    """کامینون برای await کردن روی ``LandscapeService``."""
    service = await get_hub_service(db)
    return await func(service, *args, **kwargs)


async def _run_with_400(db, func, *args, **kwargs):
    """مثل ``_run`` ولی ``ValueError`` را به HTTP 400 تبدیل می‌کند."""
    try:
        return await _run(db, func, *args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


# ===========================================================================
# List / add (Credential)
# ===========================================================================

@router.get("/villages/{village_id}/governance", tags=["landscape-governance-list"])
async def list_governance_members(
    village_id: str,
    active_only: Annotated[bool, Query(description="فقط اعضای فعال را برگردان")] = False,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    members = await _run(db, LandscapeService.get_governance_members, village_id)
    if active_only:
        members = [m for m in members if m.is_active is not False]
    return {"items": members}


@router.post("/villages/{village_id}/governance", tags=["landscape-governance-create"])
async def add_governance_member(
    village_id: str,
    payload: dict,
    actor: Annotated[User, Depends(_require_governance_writer)],
    db: Annotated[Any, Depends(_get_db)],
):
    return await _run(
        db,
        LandscapeService.add_governance_member,
        village_id=village_id,
        **payload,
    )


# ===========================================================================
# Lifecycle (Delegation / Expiration / Audit)
# ===========================================================================

@router.patch("/villages/{village_id}/governance/{user_id}/deactivate",
              tags=["landscape-governance-deactivate"])
async def deactivate_member(
    village_id: str,
    user_id: str,
    actor: Annotated[User, Depends(_require_governance_writer)],
    db: Annotated[Any, Depends(_get_db)],
):
    return await _run_with_400(
        db,
        LandscapeService.deactivate_governance_member,
        village_id=village_id,
        user_id=user_id,
    )


@router.patch("/villages/{village_id}/governance/{user_id}/reactivate",
              tags=["landscape-governance-reactivate"])
async def reactivate_member(
    village_id: str,
    user_id: str,
    actor: Annotated[User, Depends(_require_governance_writer)],
    db: Annotated[Any, Depends(_get_db)],
):
    return await _run_with_400(
        db,
        LandscapeService.reactivate_governance_member,
        village_id=village_id,
        user_id=user_id,
    )


@router.patch("/villages/{village_id}/governance/{user_id}/term",
              tags=["landscape-governance-term"])
async def set_member_term(
    village_id: str,
    user_id: str,
    actor: Annotated[User, Depends(_require_governance_writer)],
    term_start: Annotated[str | None, Query(description="تاریخ شروع دوره YYYY-MM-DD")] = None,
    term_end: Annotated[str | None, Query(description="تاریخ پایان دوره YYYY-MM-DD")] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    return await _run_with_400(
        db,
        LandscapeService.set_member_term,
        village_id=village_id,
        user_id=user_id,
        term_start=term_start,
        term_end=term_end,
    )


@router.delete("/villages/{village_id}/governance/{user_id}",
               tags=["landscape-governance-remove"])
async def remove_member(
    village_id: str,
    user_id: str,
    actor: Annotated[User, Depends(_require_governance_writer)],
    db: Annotated[Any, Depends(_get_db)],
):
    await _run_with_400(
        db,
        LandscapeService.remove_governance_member,
        village_id=village_id,
        user_id=user_id,
    )
    return {"status": "removed", "village_id": village_id, "user_id": user_id}
