"""Livestock FastAPI router"""
from typing import List
from fastapi import APIRouter, HTTPException
from services.livestock.service import LivestockService
from services.livestock.schemas import (
    LivestockSimulationRequest, LivestockSimulationResult,
)
from services.livestock.nutrition.forage_quality import ndvi_to_forage_quality

router = APIRouter(prefix="/livestock", tags=["Livestock"])

@router.get("/animal-types")
async def list_animal_types():
    service = LivestockService()
    return service.list_animal_types()

@router.post("/simulate", response_model=LivestockSimulationResult)
async def simulate(request: LivestockSimulationRequest):
    try:
        service = LivestockService()
        return service.simulate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forage-from-ndvi")
async def forage_from_ndvi(ndvi: float, season: str = "spring"):
    return ndvi_to_forage_quality(ndvi, season)

@router.post("/compare")
async def compare_scenarios(requests: List[LivestockSimulationRequest]):
    service = LivestockService()
    return service.compare_scenarios(requests)
    