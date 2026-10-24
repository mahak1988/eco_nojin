"""Simulation FastAPI router"""

from fastapi import APIRouter
from pydantic import BaseModel

from database.hub import hub
from services.simulation.schemas import (
    CropParameters,
    MultiLayerConfig,
    SimulationContext,
    SimulationResult,
    SimulationType,
    SoilProfile,
    WeatherData,
    WindbreakConfig,
)
from services.simulation.service import SimulationService

__all__ = [
    'APIRouter',
    'BaseModel',
    'CropParameters',
    'MultiLayerConfig',
    'RunSimulationRequest',
    'SimulationContext',
    'SimulationResult',
    'SimulationService',
    'SimulationType',
    'SoilProfile',
    'WeatherData',
    'WindbreakConfig',
    'analyze_erosion',
    'design_windbreak',
    'get_db',
    'hub',
    'list_simulators',
    'plan_multilayer',
    'router',
    'run_comprehensive',
    'run_simulation',
    'water_budget',
]


# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session


router = APIRouter(prefix="/simulation", tags=["Simulation"])


class RunSimulationRequest(BaseModel):
    simulation_type: SimulationType
    context: SimulationContext


@router.get("/simulators", response_model=list[dict])
async def list_simulators():
    """لیست تمام شبیه‌سازهای موجود"""
    service = SimulationService()
    return service.list_simulators()


@router.post("/run", response_model=SimulationResult)
async def run_simulation(req: RunSimulationRequest):
    """اجرای یک شبیه‌سازی خاص"""
    service = SimulationService()
    return await service.run_simulation(req.simulation_type, req.context)


@router.post("/comprehensive", response_model=dict[str, SimulationResult])
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
