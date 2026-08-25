"""Admin repository"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.admin.models import AuditLog

class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def write_audit_log(
        self, action: str, actor_id: Optional[str] = None,
        resource_type: Optional[str] = None, resource_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        log = AuditLog(
            actor_id=actor_id, action=action,
            resource_type=resource_type, resource_id=resource_id, details=details,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_recent_logs(self, limit: int = 100) -> List[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
    