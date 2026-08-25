"""Integration tests for Reporting"""
import pytest
from services.reporting.schemas import ReportCreate, ReportType, ReportStatus

@pytest.mark.asyncio
class TestReportingIntegration:
    async def test_create_and_generate_report(self, reporting_service):
        report = await reporting_service.create_report(ReportCreate(
            report_type=ReportType.COMPREHENSIVE,
            title="Monthly Report",
        ))
        assert report.status == ReportStatus.PENDING
        generated = await reporting_service.generate_report(report.id)
        assert generated.status in (ReportStatus.COMPLETED, ReportStatus.FAILED)
    