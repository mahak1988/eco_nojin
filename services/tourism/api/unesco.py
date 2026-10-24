"""UNESCO Intangible Cultural Heritage router — indicators, assessments, dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_user
from services.tourism.unesco_service import UnescoService

router = APIRouter(prefix="/unesco", tags=["tourism-unesco"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _uid(user) -> str:
    return str(user.id) if hasattr(user, "id") else str(user.get("id"))


def _http_error(exc: Exception, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail=str(exc))


# ═══════════════════════════════════════════════════════════════
# schemas
# ═══════════════════════════════════════════════════════════════


class HeritageElementCreate(BaseModel):
    element_name: str = Field(min_length=1, max_length=200)
    element_name_en: str | None = Field(default=None, max_length=200)
    domain: str = Field(min_length=1, max_length=50)
    description: str | None = None
    threatened_level: str = Field(default="viable", max_length=30)
    inscription_year: int | None = Field(default=None, ge=1900, le=2100)
    safeguarding_plan: dict | None = None


class HeritageElementResponse(BaseModel):
    id: str
    village_id: str
    element_name: str
    element_name_en: str | None
    domain: str
    description: str | None
    threatened_level: str
    inscription_year: int | None
    safeguarding_plan: dict | None
    updated_at: datetime


class IndicatorCreate(BaseModel):
    indicator_code: str = Field(min_length=1, max_length=20)
    indicator_name: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1, max_length=50)
    status: str = Field(min_length=1, max_length=30)
    justification: str | None = None
    safeguarding_plan: dict | None = None


class IndicatorResponse(BaseModel):
    id: str
    village_id: str
    indicator_code: str
    indicator_name: str
    domain: str
    status: str
    last_assessment_at: datetime | None
    justification: str | None
    safeguarding_plan: dict | None
    updated_at: datetime


class AssessmentCreate(BaseModel):
    indicator_code: str = Field(min_length=1, max_length=20)
    calificatif: str = Field(min_length=1, max_length=30)
    justification: str | None = None


class AssessmentResponse(BaseModel):
    id: str
    village_id: str
    indicator_code: str
    calificatif: str
    justification: str | None
    assessed_by: str
    assessed_at: datetime


class DashboardResponse(BaseModel):
    village_id: str | None
    total_indicators: int
    indicators_by_status: dict
    indicators_by_domain: dict
    total_heritage_elements: int
    heritage_elements_by_threatened_level: dict


# ═══════════════════════════════════════════════════════════════
# heritage elements
# ═══════════════════════════════════════════════════════════════


@router.post("/heritage-elements", response_model=HeritageElementResponse)
async def create_heritage_element(
    payload: HeritageElementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = UnescoService(db)
    try:
        element = await service.create_heritage_element(
            village_id=_uid(user),
            element_name=payload.element_name,
            element_name_en=payload.element_name_en,
            domain=payload.domain,
            description=payload.description,
            threatened_level=payload.threatened_level,
            inscription_year=payload.inscription_year,
            safeguarding_plan=payload.safeguarding_plan,
            created_by=_uid(user),
        )
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _element_response(element)


@router.get("/heritage-elements", response_model=list[HeritageElementResponse])
async def list_heritage_elements(
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    domain: Annotated[str | None, Query(max_length=50)] = None,
    threatened_level: Annotated[str | None, Query(max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    service = UnescoService(db)
    elements = await service.list_heritage_elements(
        village_id=village_id,
        domain=domain,
        threatened_level=threatened_level,
        limit=limit,
        offset=offset,
    )
    return [_element_response(e) for e in elements]


# ═══════════════════════════════════════════════════════════════
# indicators
# ═══════════════════════════════════════════════════════════════


@router.post("/indicators", response_model=IndicatorResponse)
async def set_indicator(
    payload: IndicatorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = UnescoService(db)
    try:
        indicator = await service.set_indicator(
            village_id=_uid(user),
            indicator_code=payload.indicator_code,
            indicator_name=payload.indicator_name,
            domain=payload.domain,
            status=payload.status,
            assessed_by=_uid(user),
            justification=payload.justification,
            safeguarding_plan=payload.safeguarding_plan,
        )
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _indicator_response(indicator)


@router.get("/indicators", response_model=list[IndicatorResponse])
async def list_indicators(
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    domain: Annotated[str | None, Query(max_length=50)] = None,
    status: Annotated[str | None, Query(max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    service = UnescoService(db)
    indicators = await service.list_indicators(
        village_id=village_id,
        domain=domain,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_indicator_response(i) for i in indicators]


# ═══════════════════════════════════════════════════════════════
# assessments
# ═══════════════════════════════════════════════════════════════


@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    payload: AssessmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = UnescoService(db)
    try:
        assessment = await service.create_assessment(
            village_id=_uid(user),
            indicator_code=payload.indicator_code,
            calificatif=payload.calificatif,
            assessed_by=_uid(user),
            justification=payload.justification,
        )
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _assessment_response(assessment)


@router.get("/assessments", response_model=list[AssessmentResponse])
async def list_assessments(
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    indicator_code: Annotated[str | None, Query(max_length=20)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    service = UnescoService(db)
    assessments = await service.list_assessments(
        village_id=village_id,
        indicator_code=indicator_code,
        limit=limit,
        offset=offset,
    )
    return [_assessment_response(a) for a in assessments]


# ═══════════════════════════════════════════════════════════════
# dashboard
# ═══════════════════════════════════════════════════════════════


@router.get("/dashboard", response_model=DashboardResponse)
async def unesco_dashboard(
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    service = UnescoService(db)
    return await service.unesco_dashboard(village_id=village_id)


# ═══════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════


def _element_response(e) -> HeritageElementResponse:
    return HeritageElementResponse(
        id=e.id,
        village_id=e.village_id,
        element_name=e.element_name,
        element_name_en=e.element_name_en,
        domain=e.domain,
        description=e.description,
        threatened_level=e.threatened_level,
        inscription_year=e.inscription_year,
        safeguarding_plan=e.safeguarding_plan,
        updated_at=e.updated_at,
    )


def _indicator_response(i) -> IndicatorResponse:
    return IndicatorResponse(
        id=i.id,
        village_id=i.village_id,
        indicator_code=i.indicator_code,
        indicator_name=i.indicator_name,
        domain=i.domain,
        status=i.status,
        last_assessment_at=i.last_assessment_at,
        justification=i.justification,
        safeguarding_plan=i.safeguarding_plan,
        updated_at=i.updated_at,
    )


def _assessment_response(a) -> AssessmentResponse:
    return AssessmentResponse(
        id=a.id,
        village_id=a.village_id,
        indicator_code=a.indicator_code,
        calificatif=a.calificatif,
        justification=a.justification,
        assessed_by=a.assessed_by,
        assessed_at=a.assessed_at,
    )
