"""Reporting FastAPI router"""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.api_gateway.errors import safe_detail_for_status, safe_error_detail
from services.reporting.schemas import ReportCreate, ReportRead
from services.reporting.service import ReportingService

__all__ = [
    'APIRouter',
    'Annotated',
    'AsyncGenerator',
    'AsyncSession',
    'Depends',
    'HTTPException',
    'ReportCreate',
    'ReportRead',
    'ReportingService',
    'create_report',
    'generate_report',
    'get_db',
    'get_report',
    'hub',
    'list_reports',
    'router',
    'safe_detail_for_status',
    'safe_error_detail',
]


# Compatibility: get_db via hub
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with hub.get_async_session() as session:
        yield session


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportRead, status_code=201)
async def create_report(data: ReportCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await ReportingService(db).create_report(data)


@router.post("/{report_id}/generate", response_model=ReportRead)
async def generate_report(report_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await ReportingService(db).generate_report(report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(report_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await ReportingService(db).get_report(report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/", response_model=list[ReportRead])
async def list_reports(
    report_type: str | None = None,
    limit: int = 50,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    return await ReportingService(db).list_reports(report_type=report_type, limit=limit)
