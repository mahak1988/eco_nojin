"""Analytics repository"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from services.analytics.models import AnalyticsSnapshot

class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def save_snapshot(
        self, snapshot_type: str, period_start: datetime,
        period_end: datetime, data: dict, village_id: Optional[str] = None,
    ) -> AnalyticsSnapshot:
        snapshot = AnalyticsSnapshot(
            snapshot_type=snapshot_type,
            village_id=village_id,
            period_start=period_start,
            period_end=period_end,
            data=data,
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot
    
    async def get_latest_snapshot(
        self, snapshot_type: str, village_id: Optional[str] = None,
    ) -> Optional[AnalyticsSnapshot]:
        stmt = select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.snapshot_type == snapshot_type
        )
        if village_id:
            stmt = stmt.where(AnalyticsSnapshot.village_id == village_id)
        stmt = stmt.order_by(AnalyticsSnapshot.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def cleanup_old_snapshots(self, older_than_days: int = 90) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        stmt = delete(AnalyticsSnapshot).where(
            AnalyticsSnapshot.created_at < cutoff
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
    