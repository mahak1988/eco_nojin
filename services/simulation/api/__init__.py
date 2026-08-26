"""Simulation FastAPI router"""
from typing import Dict, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db
from services.simulation.service import SimulationService
from services.simulation.schemas import (
    SimulationContext, SimulationResult, SimulationType,
    SoilProfile, WeatherData, CropParameters, WindbreakConfig, MultiLayerConfig,
)

router = APIRouter(prefix="/simulation", tags=["Simulation"])

class RunSimulationRequest(BaseModel):
    simulation_type: SimulationType
    context: SimulationContext

@router.get("/simulators", response_model=List[Dict])
async def list_simulators():
    """لیست تمام شبیه‌سازهای موجود"""
    service = SimulationService()
    return service.list_simulators()

@router.post("/run", response_model=SimulationResult)
async def run_simulation(req: RunSimulationRequest):
    """اجرای یک شبیه‌سازی خاص"""
    service = SimulationService()
    return await service.run_simulation(req.simulation_type, req.context)

@router.post("/comprehensive", response_model=Dict[str, SimulationResult])
async def run_comprehensive(ctx: SimulationContext):
    """اجرای تمام شبیه‌سازی‌های مرتبط"""
    service = SimulationService()
    return await service.run_comprehensive(ctx)

# Endpoints تخصصی برای سناریوهای مهم
@router.post("/windbreak-design")
async def design_windbreak(ctx: SimulationContext):
    """طراحی بادشکن"""
    service = SimulationService()
    return await service.run_simulation(SimulationType.WINDBREAK, ctx)

@router.post("/erosion-analysis")
async def analyze_erosion(ctx: SimulationContext):
    """تحلیل فرسایش بادی و آبی"""
    service = SimulationService()
    wind = await service.run_simulation(SimulationType.WIND_EROSION, ctx)
    water = await service.run_simulation(SimulationType.WATER_EROSION, ctx)
    return {"wind_erosion": wind, "water_erosion": water}

@router.post("/multi-layer-plan")
async def plan_multilayer(ctx: SimulationContext):
    """طراحی کشت چندلایه"""
    service = SimulationService()
    return await service.run_simulation(SimulationType.MULTI_LAYER, ctx)

@router.post("/water-budget")
async def water_budget(ctx: SimulationContext):
    """بودجه آب: نفوذ + رواناب + تغذیه آبخوان"""
    service = SimulationService()
    infiltration = await service.run_simulation(SimulationType.INFILTRATION, ctx)
    watershed = await service.run_simulation(SimulationType.WATERSHED, ctx)
    return {"infiltration": infiltration, "watershed": watershed}
    