"""Rangeland (مرتع) API router (BG-014).

Wires the existing ``services/rangeland/service.py`` business layer into HTTP
endpoints under ``/api/v1/rangeland`` and mounts them in ``api_gateway/main.py``.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from database.hub import hub
from services.api_gateway.auth import require_user
from services.api_gateway.exceptions import NotFoundException as DomainNotFound
from services.rangeland.schemas import (
    RangelandCreate,
    RangelandOut,
    RangelandStats,
    RangelandUpdate,
)
from services.rangeland.service import RangelandService

router = APIRouter(prefix="/api/v1/rangeland", tags=["rangeland"])


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_service(db: Annotated[Any, Depends(get_db)]) -> RangelandService:
    return RangelandService(db)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[RangelandOut])
async def list_rangelands(
    village_id: str | None = None,
    usage_type: str | None = None,
    condition: str | None = None,
    limit: int = 200,
    service: Annotated[RangelandService, Depends(get_service)] = None,
):
    """فهرست مرتع‌ها."""
    return await service.list_rangelands(
        village_id=village_id,
        usage_type=usage_type,
        condition=condition,
        limit=limit,
    )


@router.get("/{rangeland_id}", response_model=RangelandOut)
async def get_rangeland(
    rangeland_id: str,
    service: Annotated[RangelandService, Depends(get_service)],
):
    """دریافت مرتع."""
    r = await service.get_rangeland(rangeland_id)
    if r is None:
        raise DomainNotFound(f"مرتع یافت نشد: {rangeland_id}")
    return r


@router.post(
    "/",
    response_model=RangelandOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_user)],
)
async def create_rangeland(
    payload: RangelandCreate,
    service: Annotated[RangelandService, Depends(get_service)],
):
    """ثبت مرتع جدید."""
    return await service.create_rangeland(**payload.model_dump())


@router.patch("/{rangeland_id}", response_model=RangelandOut, dependencies=[Depends(require_user)])
async def update_rangeland(
    rangeland_id: str,
    payload: RangelandUpdate,
    service: Annotated[RangelandService, Depends(get_service)],
):
    """به‌روزرسانی مرتع."""
    return await service.update_rangeland(rangeland_id, payload.model_dump(exclude_unset=True))


@router.delete("/{rangeland_id}", response_model=RangelandOut, dependencies=[Depends(require_user)])
async def delete_rangeland(
    rangeland_id: str,
    service: Annotated[RangelandService, Depends(get_service)],
):
    """حذف مرتع."""
    ok = await service.delete_rangeland(rangeland_id)
    if not ok:
        raise DomainNotFound(f"مرتع یافت نشد: {rangeland_id}")


@router.get("/stats/territory/{village_id}", response_model=RangelandStats)
async def rangeland_stats(
    village_id: str,
    service: Annotated[RangelandService, Depends(get_service)],
):
    """آمار مرتع‌های یک قلمرو."""
    return await service.stats_for_territory(village_id)
