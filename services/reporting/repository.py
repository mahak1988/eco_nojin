"""Reporting repository"""
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.reporting.models import Report


class ReportingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(self, report: Report) -> Report:
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_report(self, report_id: str) -> Report | None:
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        return result.scalar_one_or_none()

    async def list_reports(self, report_type: str | None = None, limit: int = 50) -> list[Report]:
        stmt = select(Report)
        if report_type:
            stmt = stmt.where(Report.report_type == report_type)
        stmt = stmt.order_by(Report.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, report_id: str, status: str,
                           result_data: dict | None = None,
                           file_path: str | None = None):
        values = {"status": status}
        if result_data is not None:
            values["result_data"] = result_data
        if file_path is not None:
            values["file_path"] = file_path
        if status == "completed":
            values["completed_at"] = datetime.now(UTC)
        stmt = update(Report).where(Report.id == report_id).values(**values)
        await self.db.execute(stmt)
        await self.db.commit()
