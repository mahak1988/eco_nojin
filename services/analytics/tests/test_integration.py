"""Integration tests for Analytics"""
import pytest

from services.analytics.schemas import PeriodType


@pytest.mark.asyncio
class TestAnalyticsIntegration:
    async def test_dashboard_generation(self, analytics_service):
        dashboard = await analytics_service.get_dashboard(period=PeriodType.MONTH)
        assert dashboard is not None
        assert dashboard.period == PeriodType.MONTH
        assert dashboard.sales is not None

    async def test_sales_aggregation(self, analytics_service):
        summary = await analytics_service.aggregate_sales(period=PeriodType.MONTH)
        assert summary is not None
        assert summary.total_orders >= 0
