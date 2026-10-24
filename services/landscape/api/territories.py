"""روتر API قلمروها (BG-001).

هر قلمرو معادل یک رکورد ``landscape_villages`` است (سازگاری با D3 — هیچ جدول
جدیدی ساخته نمی‌شود). مسیرها زیر ``/api/v1/territories`` و زیر روتر اصلی
``/api/v1/`` مونت می‌شوند.

- ``GET /api/v1/territories`` — فهرست با صفحه‌بندی، جستجو و فیلتر منطقه.
- ``GET /api/v1/territories/{village_id}`` — جزئیات یک قلمرو.

خواندن بدون احراز هویت (عمومی) است. مسیرهای نوشتاری (submit → review →
resubmit → archive → verify) کاربر احراز هویت‌شده می‌خواهند و
``verify``/``review`` نقش نویسندهٔ حکمرانی (مدیر منظر یا ادمین) را؛ همان
واژگان نقشی که ``services.marketplace.hub_service`` برای مجوز نوشتن روی
محتوای روستا به کار می‌برد.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from database.hub import hub
from database.models import User
from services.api_gateway.auth import ROLE_ADMIN, require_roles, require_user
from services.api_gateway.errors import safe_detail_for_status

from ..service import LandscapeService, get_hub_service

router = APIRouter(prefix="/api/v1/territories", tags=["territories"])

#: نقش‌های نویسندهٔ حکمرانی منظر — همان مجموعه‌ای که
#: ``services.marketplace.hub_service._GOVERNANCE_WRITE_ROLES`` برای مجوز
#: نوشتن محتوای روستا تعریف می‌کند، به‌علاوهٔ ادمین پلتفرم. تأیید/رد
#: قلمرو (``review`` و ``verify``) تصمیم حکمرانی است، نه نوشتن خود سرزمین.
_TERRITORY_WRITERS = (ROLE_ADMIN, "landscape_manager", "council_member")

_require_territory_writer = require_roles(*_TERRITORY_WRITERS)


async def _get_db():
    """دریافت Session برای این درخواست."""
    async with hub.get_async_session() as session:
        yield session


async def _run(db, func, *args, **kwargs):
    """کامینون برای await کردن روی ``LandscapeService``."""
    service = await get_hub_service(db)
    return await func(service, *args, **kwargs)


def _territory_summary(village) -> dict[str, Any]:
    """Return the public registry projection, not the full persistence model."""
    return {
        "village_id": village.village_id,
        "name": village.name,
        "region": village.region,
        "country": village.country,
        "brand_name": village.brand_name,
        "active_modules": village.active_modules or [],
        "total_members": village.total_members or 0,
        "active_sellers": village.active_sellers or 0,
        "active_tour_guides": village.active_tour_guides or 0,
        "verification_status": village.verification_status,
        "representative_status": village.representative_status,
        "workflow_status": village.workflow_status,
        "created_at": village.created_at,
        "updated_at": village.updated_at,
    }


@router.get("", tags=["territories-list"])
async def list_territories(
    page: Annotated[int, Query(ge=1, description="شماره صفحه")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="تعداد سطر در هر صفحه")] = 20,
    q: Annotated[str | None, Query(description="جستجو در کد، نام و منطقه")] = None,
    region: Annotated[str | None, Query(description="فیلتر بر پایه منطقه")] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    results, total, page, page_size = await _run(
        db, LandscapeService.list_territories, page=page, page_size=page_size, q=q, region=region
    )
    return {
        "items": [_territory_summary(village) for village in results],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("/{village_id}", tags=["territories-detail"])
async def get_territory(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    t = await _run(db, LandscapeService.get_territory, village_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"territory {village_id} not found")
    return _territory_summary(t)


@router.patch("/{village_id}/verify", tags=["territory-registry"])
async def verify_territory(
    village_id: str,
    verification_status: Annotated[str, Query(pattern="^(verified|rejected)$")],
    actor: Annotated[User, Depends(_require_territory_writer)],
    representative_status: Annotated[str | None, Query(pattern="^(active|suspended)$")] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """Update territory registry verification and representative status (BG-016)."""
    t = await _run(db, LandscapeService.get_territory, village_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"territory {village_id} not found")

    updates = {}
    if verification_status:
        updates["verification_status"] = verification_status
    if representative_status:
        updates["representative_status"] = representative_status

    updated = await _run(db, LandscapeService.update_territory, village_id, updates)
    return _territory_summary(updated)


# --------------------------------------------------------------- workflow (BG-001-WF)

@router.post("/{village_id}/submit", tags=["territory-workflow"])
async def submit_territory(
    village_id: str,
    actor: Annotated[User, Depends(require_user)],
    reviewer_id: Annotated[str | None, Query(description="Reviewer user ID")] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """Submit territory for review (draft -> submitted)."""
    try:
        updated = await _run(db, LandscapeService.submit_territory, village_id, reviewer_id)
        return _territory_summary(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Submit failed") from e


@router.post("/{village_id}/review", tags=["territory-workflow"])
async def review_territory(
    village_id: str,
    reviewer_id: Annotated[str, Query(description="Reviewer user ID")],
    actor: Annotated[User, Depends(_require_territory_writer)],
    approve: Annotated[bool, Query(description="Approve (true) or reject (false)")] = True,
    review_notes: Annotated[str | None, Query(description="Reviewer notes")] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """Review submitted territory (submitted -> published/rejected)."""
    try:
        updated = await _run(
            db,
            LandscapeService.review_territory,
            village_id,
            reviewer_id,
            review_notes,
            approve,
        )
        return _territory_summary(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Review failed") from e


@router.post("/{village_id}/resubmit", tags=["territory-workflow"])
async def resubmit_territory(
    village_id: str,
    actor: Annotated[User, Depends(require_user)],
    reviewer_id: Annotated[str | None, Query(description="Reviewer user ID")] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """Resubmit a rejected territory (rejected -> submitted)."""
    try:
        updated = await _run(db, LandscapeService.resubmit_territory, village_id, reviewer_id)
        return _territory_summary(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Resubmit failed") from e


@router.post("/{village_id}/archive", tags=["territory-workflow"])
async def archive_territory(
    village_id: str,
    actor: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """Archive a published territory (published -> archived)."""
    try:
        updated = await _run(db, LandscapeService.archive_territory, village_id)
        return _territory_summary(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Archive failed") from e
