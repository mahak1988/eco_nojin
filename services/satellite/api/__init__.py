"""Satellite FastAPI router"""
from typing import Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub

# Compatibility: get_db via hub
async def get_db():
    async with hub.get_async_session() as session:
        yield session
from services.satellite.monitoring_service import SatelliteMonitoringService

router = APIRouter(prefix="/satellite", tags=["Satellite"])

class MonitorFieldRequest(BaseModel):
    village_id: str
    bbox: dict[str, float]
    days_back: int = 30

@router.post("/monitor-field")
async def monitor_field(req: MonitorFieldRequest, db: AsyncSession = Depends(get_db)):
    service = SatelliteMonitoringService(db)
    return await service.monitor_field(req.village_id, req.bbox, req.days_back)

@router.post("/detect-changes")
async def detect_changes(req: MonitorFieldRequest, db: AsyncSession = Depends(get_db)):
    service = SatelliteMonitoringService(db)
    return await service.detect_changes(req.bbox, req.days_back)
