"""SmartMapService - intelligent map generation"""
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession


class MapLayer(str, Enum):
    DEM = "dem"
    LANDCOVER = "landcover"
    RAINFALL = "rainfall"
    TEMPERATURE = "temperature"
    SOIL = "soil"
    VEGETATION = "vegetation"

class OutputFormat(str, Enum):
    GEOTIFF = "geotiff"
    PNG = "png"
    GEOJSON = "geojson"
    MBTILES = "mbtiles"

@dataclass
class MapRequest:
    bbox: dict[str, float]
    layers: list[MapLayer]
    resolution: float = 30.0  # meters per pixel
    output_format: OutputFormat = OutputFormat.GEOTIFF

@dataclass
class MapResult:
    map_id: str
    layers_included: list[MapLayer]
    file_path: str | None
    size_bytes: int
    generated_at: datetime
    processing_time_ms: int

class SmartMapService:
    """
    سرویس تولید نقشه‌های هوشمند
    
    قابلیت‌ها:
    - ترکیب چندین لایه داده
    - تولید نقشه‌های DEM، Landcover، Rainfall
    - خروجی در فرمت‌های مختلف
    - Cache برای درخواست‌های تکراری
    - یکپارچه‌سازی با fetcher ها
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache = {}

    async def generate_map(self, request: MapRequest) -> MapResult:
        """تولید نقشه بر اساس درخواست"""
        import time
        start = time.time()

        # Cache key
        cache_key = self._make_cache_key(request)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # تولید نقشه (شبیه‌سازی)
        map_id = f"map_{datetime.now(UTC).timestamp():.0f}"

        # در production: استفاده از DEMFetcher, LandCoverFetcher, etc
        file_path = await self._generate_file(map_id, request)

        result = MapResult(
            map_id=map_id,
            layers_included=request.layers,
            file_path=file_path,
            size_bytes=1024 * 1024,  # 1MB
            generated_at=datetime.now(UTC),
            processing_time_ms=int((time.time() - start) * 1000),
        )

        self._cache[cache_key] = result
        return result

    async def _generate_file(self, map_id: str, request: MapRequest) -> str | None:
        """تولید فایل نقشه"""
        from pathlib import Path
        maps_dir = Path("data/maps")
        maps_dir.mkdir(parents=True, exist_ok=True)

        ext = {
            OutputFormat.GEOTIFF: ".tif",
            OutputFormat.PNG: ".png",
            OutputFormat.GEOJSON: ".geojson",
            OutputFormat.MBTILES: ".mbtiles",
        }.get(request.output_format, ".tif")

        file_path = maps_dir / f"{map_id}{ext}"

        # شبیه‌سازی - در production باید داده واقعی تولید شود
        file_path.write_bytes(b"MOCK_MAP_DATA")
        return str(file_path)

    def _make_cache_key(self, request: MapRequest) -> str:
        """ساخت کلید cache"""
        import hashlib
        data = f"{request.bbox}:{request.layers}:{request.resolution}"
        return hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()

    async def get_available_layers(self, bbox: dict[str, float]) -> list[MapLayer]:
        """لیست لایه‌های موجود برای یک منطقه"""
        # همه لایه‌ها به‌صورت پیش‌فرض موجود
        return list(MapLayer)

    async def combine_layers(
        self, base_map: MapResult, overlay_layers: list[MapLayer],
    ) -> MapResult:
        """ترکیب لایه‌ها"""
        # شبیه‌سازی ترکیب
        return MapResult(
            map_id=f"combined_{base_map.map_id}",
            layers_included=base_map.layers_included + overlay_layers,
            file_path=base_map.file_path,
            size_bytes=base_map.size_bytes * 2,
            generated_at=datetime.now(UTC),
            processing_time_ms=100,
        )
