"""Reporting FastAPI router"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db
from services.reporting.schemas import ReportCreate, ReportRead
from services.reporting.service import ReportingService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/", response_model=ReportRead, status_code=201)
async def create_report(data: ReportCreate, db: AsyncSession = Depends(get_db)):
    return await ReportingService(db).create_report(data)

@router.post("/<report_id>/generate", response_model=ReportRead)
async def generate_report(report_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await ReportingService(db).generate_report(report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/<report_id>", response_model=ReportRead)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await ReportingService(db).get_report(report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=list[ReportRead])
async def list_reports(
    report_type: str | None = None, limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await ReportingService(db).list_reports(report_type=report_type, limit=limit)
