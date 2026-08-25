"""AnalyticsService"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from services.analytics.schemas import (
    SalesSummary, TourismMetrics, LandscapeMetrics,
    AnalyticsDashboard, PeriodType,
)
from services.analytics.repository import AnalyticsRepository

class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AnalyticsRepository(db)
    
    def _period_delta(self, period: PeriodType) -> timedelta:
        return {
            PeriodType.DAY: timedelta(days=1),
            PeriodType.WEEK: timedelta(weeks=1),
            PeriodType.MONTH: timedelta(days=30),
            PeriodType.QUARTER: timedelta(days=90),
            PeriodType.YEAR: timedelta(days=365),
        }[period]
    
    async def aggregate_sales(
        self, village_id: Optional[str] = None, period: PeriodType = PeriodType.MONTH,
    ) -> SalesSummary:
        try:
            from services.marketplace.models import MarketplaceOrder
            since = datetime.now(timezone.utc) - self._period_delta(period)
            stmt = select(
                func.count(MarketplaceOrder.id).label("total_orders"),
                func.coalesce(func.sum(MarketplaceOrder.total), 0).label("total_revenue"),
                func.coalesce(func.avg(MarketplaceOrder.total), 0).label("avg_value"),
            ).where(MarketplaceOrder.created_at >= since)
            if village_id:
                stmt = stmt.where(MarketplaceOrder.village_id == village_id)
            result = await self.db.execute(stmt)
            row = result.one()
            return SalesSummary(
                total_orders=row.total_orders or 0,
                total_revenue=Decimal(str(row.total_revenue or 0)),
                average_order_value=Decimal(str(row.avg_value or 0)),
                period=period,
            )
        except ImportError:
            return SalesSummary(period=period)
    
    async def aggregate_tourism(
        self, village_id: Optional[str] = None, period: PeriodType = PeriodType.MONTH,
    ) -> TourismMetrics:
        try:
            from services.tourism.models import TourismBooking
            since = datetime.now(timezone.utc) - self._period_delta(period)
            stmt = select(
                func.count(TourismBooking.id).label("total_bookings"),
                func.coalesce(func.sum(TourismBooking.participants_count), 0).label("total_guests"),
                func.coalesce(func.sum(TourismBooking.total), 0).label("revenue"),
            ).where(TourismBooking.created_at >= since)
            if village_id:
                stmt = stmt.where(TourismBooking.village_id == village_id)
            result = await self.db.execute(stmt)
            row = result.one()
            return TourismMetrics(
                total_bookings=row.total_bookings or 0,
                total_guests=int(row.total_guests or 0),
                revenue=Decimal(str(row.revenue or 0)),
            )
        except ImportError:
            return TourismMetrics()
    
    async def aggregate_landscape(self) -> LandscapeMetrics:
        try:
            from services.landscape.models import (
                LandscapeVillage, LandscapeGovernanceMember, LandscapeFund
            )
            v = await self.db.execute(select(func.count(LandscapeVillage.id)).where(LandscapeVillage.is_active == True))
            m = await self.db.execute(select(func.count(LandscapeGovernanceMember.id)))
            f = await self.db.execute(select(func.coalesce(func.sum(LandscapeFund.pending_balance), 0)))
            return LandscapeMetrics(
                active_villages=v.scalar() or 0,
                governance_members=m.scalar() or 0,
                fund_balance=Decimal(str(f.scalar() or 0)),
            )
        except ImportError:
            return LandscapeMetrics()
    
    async def get_dashboard(
        self, village_id: Optional[str] = None, period: PeriodType = PeriodType.MONTH,
    ) -> AnalyticsDashboard:
        sales = await self.aggregate_sales(village_id, period)
        tourism = await self.aggregate_tourism(village_id, period)
        landscape = await self.aggregate_landscape()
        dashboard = AnalyticsDashboard(
            village_id=village_id, period=period,
            sales=sales, tourism=tourism, landscape=landscape,
            generated_at=datetime.now(timezone.utc),
        )
        await self.repo.save_snapshot(
            snapshot_type="dashboard",
            period_start=datetime.now(timezone.utc) - self._period_delta(period),
            period_end=datetime.now(timezone.utc),
            data=dashboard.model_dump(mode="json"),
            village_id=village_id,
        )
        return dashboard
    