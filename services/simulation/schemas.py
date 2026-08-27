"""Pydantic schemas for unified simulation"""
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationType(str, Enum):
    CROP_GROWTH = "crop_growth"
    SOIL_CARBON = "soil_carbon"
    WATERSHED = "watershed"
    WIND_EROSION = "wind_erosion"
    WATER_EROSION = "water_erosion"
    INFILTRATION = "infiltration"
    RUNOFF = "runoff"
    AQUIFER_RECHARGE = "aquifer_recharge"
    WINDBREAK = "windbreak"
    MULTI_LAYER = "multi_layer_cropping"
    LIVESTOCK = "livestock"
    COMPREHENSIVE = "comprehensive"

class BBox(BaseModel):
    north: float
    south: float
    east: float
    west: float

class SoilProfile(BaseModel):
    texture: str  # sand, loam, clay, silt_loam, etc.
    organic_carbon_pct: float = 1.0
    bulk_density: float = 1.3
    ph: float = 7.0
    depth_cm: int = 100
    sand_pct: float = 40.0
    silt_pct: float = 40.0
    clay_pct: float = 20.0
    infiltration_rate_mm_hr: float = 15.0

class WeatherData(BaseModel):
    temp_min_c: float = 5.0
    temp_max_c: float = 30.0
    precipitation_mm: float = 0.0
    wind_speed_ms: float = 2.5
    wind_direction_deg: float = 180.0
    humidity_pct: float = 50.0
    solar_radiation_mj_m2: float = 18.0

class CropParameters(BaseModel):
    crop_type: str
    planting_date: date
    harvest_date: date | None = None
    variety: str | None = None
    row_spacing_m: float = 0.75
    plant_density_per_m2: float = 8.0

class WindbreakConfig(BaseModel):
    """بادشکن - Windbreak configuration"""
    tree_species: str = "cypress"
    height_m: float = 8.0
    row_spacing_m: float = 15.0
    porosity_pct: float = 40.0  # درصد نفوذپذیری باد
    orientation_deg: float = 90.0  # عمود بر باد غالب
    length_m: float = 100.0

class MultiLayerConfig(BaseModel):
    """کشت چندلایه - Multi-layer/Agroforestry"""
    canopy_layer: CropParameters  # لایه بالایی (درختان)
    sub_canopy_layer: CropParameters | None = None  # لایه میانی
    ground_layer: CropParameters | None = None  # لایه زمینی
    shade_tolerance: float = 0.6

class SimulationContext(BaseModel):
    """Context جامع برای تمام شبیه‌سازی‌ها"""
    simulation_id: str
    simulation_type: SimulationType
    bbox: BBox | None = None
    village_id: str | None = None
    field_id: str | None = None
    soil: SoilProfile = Field(default_factory=SoilProfile)
    weather: WeatherData = Field(default_factory=WeatherData)
    crop: CropParameters | None = None
    windbreak: WindbreakConfig | None = None
    multi_layer: MultiLayerConfig | None = None
    start_date: date = Field(default_factory=lambda: date.today())
    end_date: date | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)

class SimulationResult(BaseModel):
    """نتیجه استاندارد تمام شبیه‌سازی‌ها"""
    simulation_id: str
    simulation_type: SimulationType
    status: SimulationStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    summary: dict[str, Any] = Field(default_factory=dict)
    time_series: list[dict[str, Any]] = Field(default_factory=list)
    spatial_data: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
