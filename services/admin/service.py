"""AdminService"""
import time
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from services.admin.schemas import (
    SystemHealth, ServiceStatus, ServiceHealthCheck,
    ProjectStatus, AdminStats, AuditLog as AuditLogSchema,
)
from services.admin.repository import AdminRepository

_START_TIME = time.time()

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminRepository(db)
    
    async def check_database_health(self) -> ServiceHealthCheck:
        start = time.time()
        try:
            await self.db.execute(select(1))
            return ServiceHealthCheck(
                name="database", status=ServiceStatus.HEALTHY,
                latency_ms=round((time.time() - start) * 1000, 2),
            )
        except Exception as e:
            return ServiceHealthCheck(name="database", status=ServiceStatus.DOWN, message=str(e)[:100])
    
    async def get_system_health(self) -> SystemHealth:
        db_health = await self.check_database_health()
        services = [db_health]
        if any(s.status == ServiceStatus.DOWN for s in services):
            overall = ServiceStatus.DOWN
        elif any(s.status == ServiceStatus.DEGRADED for s in services):
            overall = ServiceStatus.DEGRADED
        else:
            overall = ServiceStatus.HEALTHY
        return SystemHealth(
            overall_status=overall, services=services,
            uptime_seconds=int(time.time() - _START_TIME),
            checked_at=datetime.now(timezone.utc),
        )
    
    async def get_project_status(self) -> ProjectStatus:
        return ProjectStatus(
            phase="Production (Phase 3)", version="3.1.0",
            total_modules=28, active_modules=7,
            description="Eco Nojin - Regenerative Rural Economy Platform",
        )
    
    async def get_stats(self) -> AdminStats:
        stats = AdminStats(uptime_seconds=int(time.time() - _START_TIME))
        try:
            from services.marketplace.models import MarketplaceOrder
            r = await self.db.execute(select(func.count(MarketplaceOrder.id)))
            stats.total_orders = r.scalar() or 0
        except Exception:
            pass
        try:
            from services.tourism.models import TourismBooking
            r = await self.db.execute(select(func.count(TourismBooking.id)))
            stats.total_bookings = r.scalar() or 0
        except Exception:
            pass
        try:
            from services.landscape.models import LandscapeVillage
            r = await self.db.execute(select(func.count(LandscapeVillage.id)))
            stats.total_villages = r.scalar() or 0
        except Exception:
            pass
        return stats
    
    async def log_action(self, action: str, actor_id: Optional[str] = None,
                       resource_type: Optional[str] = None,
                       resource_id: Optional[str] = None,
                       details: Optional[dict] = None) -> AuditLogSchema:
        log = await self.repo.write_audit_log(
            action, actor_id, resource_type, resource_id, details,
        )
        return AuditLogSchema(
            id=log.id, actor_id=log.actor_id, action=log.action,
            resource_type=log.resource_type, resource_id=log.resource_id,
            details=log.details, created_at=log.created_at,
        )
    
    async def get_audit_logs(self, limit: int = 100) -> List[AuditLogSchema]:
        logs = await self.repo.get_recent_logs(limit=limit)
        return [
            AuditLogSchema(
                id=log.id, actor_id=log.actor_id, action=log.action,
                resource_type=log.resource_type, resource_id=log.resource_id,
                details=log.details, created_at=log.created_at,
            )
            for log in logs
        ]
    