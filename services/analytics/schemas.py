"""Pydantic schemas for Analytics"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class PeriodType(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class AggregationRequest(BaseModel):
    village_id: Optional[str] = None
    period: PeriodType = PeriodType.MONTH
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: Optional[List[str]] = None

class AggregationResult(BaseModel):
    period: PeriodType
    total_records: int
    aggregated_values: Dict[str, Any]
    generated_at: datetime

class SalesSummary(BaseModel):
    total_orders: int = 0
    total_revenue: Decimal = Decimal("0")
    average_order_value: Decimal = Decimal("0")
    top_products: List[Dict[str, Any]] = Field(default_factory=list)
    period: PeriodType

class TourismMetrics(BaseModel):
    total_bookings: int = 0
    total_guests: int = 0
    revenue: Decimal = Decimal("0")
    regenerative_activities: int = 0

class LandscapeMetrics(BaseModel):
    active_villages: int = 0
    governance_members: int = 0
    fund_balance: Decimal = Decimal("0")

class AnalyticsDashboard(BaseModel):
    village_id: Optional[str] = None
    period: PeriodType
    sales: SalesSummary
    tourism: TourismMetrics
    landscape: LandscapeMetrics
    generated_at: datetime
    