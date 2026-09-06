"""Admin FastAPI router"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub

# Compatibility: get_db via hub
async def get_db():
    async with hub.get_async_session() as session:
        yield session
from services.admin.schemas import AdminStats, AuditLog, ProjectStatus, SystemHealth
from services.admin.service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/health", response_model=SystemHealth)
async def get_health(db: AsyncSession = Depends(get_db)):
    return await AdminService(db).get_system_health()

@router.get("/status", response_model=ProjectStatus)
async def get_status(db: AsyncSession = Depends(get_db)):
    return await AdminService(db).get_project_status()

@router.get("/stats", response_model=AdminStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await AdminService(db).get_stats()

@router.get("/audit-logs", response_model=list[AuditLog])
async def get_audit_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await AdminService(db).get_audit_logs(limit=limit)
