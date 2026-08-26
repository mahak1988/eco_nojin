"""Map Engine FastAPI router"""
from typing import List, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db
from services.map_engine.smart_service import (
    SmartMapService, MapRequest, MapLayer, OutputFormat,
)

router = APIRouter(prefix="/maps", tags=["Maps"])

class GenerateMapRequest(BaseModel):
    bbox: Dict[str, float]
    layers: List[str]
    resolution: float = 30.0
    output_format: str = "geotiff"

@router.post("/generate")
async def generate_map(req: GenerateMapRequest, db: AsyncSession = Depends(get_db)):
    service = SmartMapService(db)
    request = MapRequest(
        bbox=req.bbox,
        layers=[MapLayer(l) for l in req.layers],
        resolution=req.resolution,
        output_format=OutputFormat(req.output_format),
    )
    result = await service.generate_map(request)
    return {
        "map_id": result.map_id,
        "file_path": result.file_path,
        "processing_time_ms": result.processing_time_ms,
    }

@router.get("/available-layers")
async def get_available_layers(
    north: float, south: float, east: float, west: float,
    db: AsyncSession = Depends(get_db),
):
    service = SmartMapService(db)
    bbox = {"north": north, "south": south, "east": east, "west": west}
    layers = await service.get_available_layers(bbox)
    return {"layers": [l.value for l in layers]}
    