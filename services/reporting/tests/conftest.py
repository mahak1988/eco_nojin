"""Fixtures for reporting integration tests (Phase 6C fix: missing fixture)."""
import pytest

from services.reporting.service import ReportingService


@pytest.fixture
async def reporting_service(db_session) -> ReportingService:
    """Real ReportingService bound to the shared async DB session."""
    return ReportingService(db_session)
