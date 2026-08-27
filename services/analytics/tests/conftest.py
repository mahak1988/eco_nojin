"""Fixtures for analytics integration tests (Phase 6C fix: missing fixture)."""
import pytest

from services.analytics.service import AnalyticsService


@pytest.fixture
async def analytics_service(db_session) -> AnalyticsService:
    """Real AnalyticsService bound to the shared async DB session."""
    return AnalyticsService(db_session)
