"""Analytics FastAPI router"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub

# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session
from services.analytics.schemas import (
    AnalyticsDashboard,
    LandscapeMetrics,
    PeriodType,
    SalesSummary,
    TourismMetrics,
)
from services.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_dashboard(
    village_id: str | None = None,
    period: PeriodType = PeriodType.MONTH,
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_dashboard(village_id=village_id, period=period)

@router.get("/sales-summary", response_model=SalesSummary)
async def get_sales(
    village_id: str | None = None,
    period: PeriodType = PeriodType.MONTH,
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService(db).aggregate_sales(village_id, period)

@router.get("/tourism-metrics", response_model=TourismMetrics)
async def get_tourism(
    village_id: str | None = None,
    period: PeriodType = PeriodType.MONTH,
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService(db).aggregate_tourism(village_id, period)

@router.get("/landscape-metrics", response_model=LandscapeMetrics)
async def get_landscape(db: AsyncSession = Depends(get_db)):
    return await AnalyticsService(db).aggregate_landscape()
