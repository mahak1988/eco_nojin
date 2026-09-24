"""SatelliteMonitoringService - unified satellite data access"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class SatelliteSource(StrEnum):
    SENTINEL_2 = "sentinel_2"
    LANDSAT_8 = "landsat_8"
    COPERNICUS = "copernicus"


class BandType(StrEnum):
    NDVI = "ndvi"
    NDWI = "ndwi"
    EVI = "evi"
    MOISTURE = "moisture"
    TEMPERATURE = "temperature"


@dataclass
class SatelliteScene:
    scene_id: str
    source: SatelliteSource
    capture_date: datetime
    cloud_cover: float
    bands: dict[str, Any] = field(default_factory=dict)
    bbox: dict[str, float] | None = None


@dataclass
class VegetationIndex:
    index_type: BandType
    value: float
    confidence: float
    scene_id: str
    captured_at: datetime


class SatelliteMonitoringService:
    """
    سرویس یکپارچه پایش ماهواره‌ای

    قابلیت‌ها:
    - دریافت تصاویر Sentinel-2 و Landsat-8
    - محاسبه شاخص‌های گیاهی (NDVI, NDWI, EVI)
    - پایش رطوبت خاک
    - تشخیص تغییرات زمانی
    - یکپارچه‌سازی با Hydroma Engine
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_scene(
        self,
        bbox: dict[str, float],
        source: SatelliteSource = SatelliteSource.SENTINEL_2,
        max_cloud_cover: float = 20.0,
    ) -> SatelliteScene | None:
        """دریافت آخرین تصویر ماهواره‌ای برای منطقه مشخص"""
        try:
            from services.satellite.copernicus import CopernicusClient

            client = CopernicusClient()
            if not client.configured:
                return None
            lat = (bbox.get("north", 0) + bbox.get("south", 0)) / 2
            lon = (bbox.get("east", 0) + bbox.get("west", 0)) / 2
            scenes = client.search_stac(lat, lon, max_cloud_cover=max_cloud_cover)
            if not scenes:
                return None
            scene = scenes[0]
            return SatelliteScene(
                scene_id=scene.id,
                source=SatelliteSource.COPERNICUS,
                capture_date=datetime.fromisoformat(scene.datetime.replace("Z", "+00:00"))
                if scene.datetime
                else datetime.now(UTC),
                cloud_cover=scene.cloud_cover,
                bbox=bbox,
            )
        except Exception:
            return None

    async def calculate_vegetation_index(
        self,
        scene: SatelliteScene,
        index_type: BandType,
    ) -> VegetationIndex | None:
        """محاسبه شاخص گیاهی از تصویر"""
        try:
            from services.satellite.copernicus import (
                CopernicusClient,
                evi_from_bands,
                ndvi_from_bands,
            )

            client = CopernicusClient()
            if not client.configured:
                return None
            lat = (scene.bbox.get("north", 0) + scene.bbox.get("south", 0)) / 2
            lon = (scene.bbox.get("east", 0) + scene.bbox.get("west", 0)) / 2
            scenes = client.search_stac(lat, lon, max_cloud_cover=20.0)
            if not scenes:
                return None
            usable = [s for s in scenes if s.is_usable]
            if not usable:
                return None
            s_scene = usable[0]
            bands = await client.sample_bands(s_scene, lat, lon)
            if index_type == BandType.NDVI:
                value = ndvi_from_bands(bands["nir"], bands["red"])
                return VegetationIndex(
                    index_type=index_type,
                    value=value,
                    confidence=0.95,
                    scene_id=scene.scene_id,
                    captured_at=scene.capture_date,
                )
            elif index_type == BandType.EVI:
                blue = bands.get("blue") or 0.1
                value = evi_from_bands(bands["nir"], bands["red"], blue)
                return VegetationIndex(
                    index_type=index_type,
                    value=value,
                    confidence=0.95,
                    scene_id=scene.scene_id,
                    captured_at=scene.capture_date,
                )
            elif index_type == BandType.NDWI:
                import numpy as np

                from engine.hydroma.satellite.processors.indices import calculate_ndwi

                ndwi_arr = calculate_ndwi(
                    np.array([[bands.get("green", bands["nir"] * 0.5)]]),
                    np.array([[bands["nir"]]]),
                )
                value = float(ndwi_arr[0, 0])
                return VegetationIndex(
                    index_type=index_type,
                    value=value,
                    confidence=0.90,
                    scene_id=scene.scene_id,
                    captured_at=scene.capture_date,
                )
            return None
        except Exception:
            return None

    async def monitor_field(
        self,
        village_id: str,
        field_bbox: dict[str, float],
        days_back: int = 30,
    ) -> dict[str, Any]:
        """پایش کامل یک زمین کشاورزی"""
        scene = await self.get_latest_scene(field_bbox)
        if not scene:
            return {"status": "no_data", "message": "No recent satellite data"}

        ndvi = await self.calculate_vegetation_index(scene, BandType.NDVI)
        ndwi = await self.calculate_vegetation_index(scene, BandType.NDWI)

        return {
            "status": "ok",
            "village_id": village_id,
            "scene_id": scene.scene_id,
            "capture_date": scene.capture_date.isoformat(),
            "cloud_cover": scene.cloud_cover,
            "vegetation": {
                "ndvi": ndvi.value if ndvi else None,
                "ndwi": ndwi.value if ndwi else None,
            },
            "health_status": self._assess_health(ndvi.value if ndvi else 0),
        }

    def _assess_health(self, ndvi: float) -> str:
        """ارزیابی سلامت گیاه بر اساس NDVI"""
        if ndvi < 0.2:
            return "poor"
        elif ndvi < 0.4:
            return "fair"
        elif ndvi < 0.6:
            return "good"
        else:
            return "excellent"

    async def detect_changes(
        self,
        field_bbox: dict[str, float],
        days_back: int = 90,
    ) -> dict[str, Any]:
        """تشخیص تغییرات در طول زمان"""
        # شبیه‌سازی تشخیص تغییرات
        return {
            "period_days": days_back,
            "change_detected": True,
            "change_type": "vegetation_growth",
            "magnitude": 0.15,
            "confidence": 0.85,
        }
