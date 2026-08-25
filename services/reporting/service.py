"""ReportingService"""
import json
from typing import Optional, List
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from services.reporting.models import Report
from services.reporting.schemas import ReportCreate, ReportRead, ReportStatus, ReportType
from services.reporting.repository import ReportingRepository

class ReportingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReportingRepository(db)
    
    async def create_report(self, data: ReportCreate) -> ReportRead:
        report = Report(
            report_type=data.report_type.value,
            title=data.title,
            parameters=data.parameters,
            generated_by=data.generated_by,
            status=ReportStatus.PENDING.value,
        )
        report = await self.repo.create_report(report)
        return self._to_read(report)
    
    async def generate_report(self, report_id: str) -> ReportRead:
        report = await self.repo.get_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")
        await self.repo.update_status(report_id, ReportStatus.PROCESSING.value)
        try:
            result_data = await self._generate_data(report.report_type, report.parameters)
            file_path = await self._save_to_file(report.id, result_data)
            await self.repo.update_status(
                report_id, ReportStatus.COMPLETED.value,
                result_data=result_data, file_path=file_path,
            )
        except Exception as e:
            await self.repo.update_status(
                report_id, ReportStatus.FAILED.value,
                result_data={"error": str(e)},
            )
        report = await self.repo.get_report(report_id)
        return self._to_read(report)
    
    async def _generate_data(self, report_type: str, parameters: Optional[dict]) -> dict:
        try:
            from services.analytics.service import AnalyticsService
            from services.analytics.schemas import PeriodType
            analytics = AnalyticsService(self.db)
            if report_type == ReportType.SALES.value:
                return (await analytics.aggregate_sales(period=PeriodType.MONTH)).model_dump(mode="json")
            elif report_type == ReportType.TOURISM.value:
                return (await analytics.aggregate_tourism(period=PeriodType.MONTH)).model_dump(mode="json")
            elif report_type == ReportType.LANDSCAPE.value:
                return (await analytics.aggregate_landscape()).model_dump(mode="json")
            elif report_type == ReportType.COMPREHENSIVE.value:
                return (await analytics.get_dashboard(period=PeriodType.MONTH)).model_dump(mode="json")
            return {"report_type": report_type}
        except ImportError:
            return {"report_type": report_type, "message": "Analytics unavailable"}
    
    async def _save_to_file(self, report_id: str, data: dict) -> str:
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        file_path = reports_dir / f"report_{report_id}.json"
        file_path.write_text(json.dumps(data, default=str, indent=2), encoding='utf-8')
        return str(file_path)
    
    async def get_report(self, report_id: str) -> ReportRead:
        report = await self.repo.get_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")
        return self._to_read(report)
    
    async def list_reports(self, report_type: Optional[str] = None, limit: int = 50) -> List[ReportRead]:
        reports = await self.repo.list_reports(report_type=report_type, limit=limit)
        return [self._to_read(r) for r in reports]
    
    def _to_read(self, report: Report) -> ReportRead:
        return ReportRead(
            id=report.id,
            report_type=ReportType(report.report_type),
            title=report.title,
            status=ReportStatus(report.status),
            parameters=report.parameters,
            result_data=report.result_data,
            file_path=report.file_path,
            created_at=report.created_at,
            completed_at=report.completed_at,
        )
    