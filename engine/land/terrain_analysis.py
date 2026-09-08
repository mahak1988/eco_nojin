"""تحلیل توپوگرافی ساده (محاسبه شیب و جهت) با NumPy."""
from typing import Any

import numpy as np

from engine.land.models import (
    CapabilityAssessment,
    LandCapabilityClass,
    SlopeClass,
    TerrainAnalysis,
    TerrainType,
)


def aspect_to_cardinal(degrees: float) -> str:
    """تبدیل درجه جهت به جهت Cardinal."""
    if np.isnan(degrees):
        return "unknown"
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW",
    ]
    idx = int((degrees + 11.25) / 22.5) % 16
    return directions[idx]


_aspect_to_cardinal = aspect_to_cardinal


def classify_slope_usda(slope_percent: float) -> SlopeClass:
    """طبقه‌بندی شیب بر اساس استاندارد USDA."""
    if slope_percent < 2:
        return SlopeClass.CLASS_0
    elif slope_percent < 5:
        return SlopeClass.CLASS_1
    elif slope_percent < 10:
        return SlopeClass.CLASS_2
    elif slope_percent < 20:
        return SlopeClass.CLASS_3
    elif slope_percent < 40:
        return SlopeClass.CLASS_4
    else:
        return SlopeClass.CLASS_5


def _get_dominant_aspect(aspects: np.ndarray) -> str:
    """تعیین جهت غالب از آرایه جهات."""
    aspects = np.asarray(aspects, dtype=float)
    valid = aspects[~np.isnan(aspects)]
    if valid.size == 0:
        return "unknown"
    median = float(np.median(valid))
    return aspect_to_cardinal(median)


def calculate_terrain_metrics(dem_array: Any, resolution: float = 30.0) -> dict[str, Any]:
    """محاسبه معیارهای توپوگرافی از DEM."""
    dem = np.asarray(dem_array, dtype=float)
    if dem.size == 0:
        return {}
    grad_y, grad_x = np.gradient(dem, edge_order=1)
    slope = np.sqrt(grad_x**2 + grad_y**2)
    slope_deg = np.degrees(np.arctan(slope))
    aspect_rad = np.arctan2(-grad_y, grad_x)
    aspect_deg = (np.degrees(aspect_rad) + 360) % 360

    return {
        'terrain_type': 'unknown',
        'elevation_min': float(np.min(dem)),
        'elevation_max': float(np.max(dem)),
        'elevation_mean': float(np.mean(dem)),
        'slope_mean': float(np.mean(slope_deg)),
        'slope_max': float(np.max(slope_deg)),
        'aspect_dominant': float(np.median(aspect_deg)),
    }


class TerrainAnalyzer:
    """کلاس تحلیل توپوگرافی (برای سازگاری با engine/land/__init__.py)"""
    def __init__(self, resolution: float = 30.0):
        self.resolution = resolution

    def _classify_terrain(self, slopes: np.ndarray) -> TerrainType:
        """طبقه‌بندی توپوگرافی بر اساس میانگین شیب."""
        mean_slope = float(np.mean(slopes))
        if mean_slope < 3:
            return TerrainType.FLAT
        elif mean_slope < 8:
            return TerrainType.ROLLING
        elif mean_slope < 20:
            return TerrainType.HILLY
        else:
            return TerrainType.MOUNTAINOUS

    def analyze(self, dem_array: Any, profile_id: str | None = None) -> TerrainAnalysis:
        """تحلیل توپوگرافی و بازگرداندن TerrainAnalysis model."""
        dem = np.asarray(dem_array, dtype=float)
        if dem.size == 0:
            raise ValueError("DEM array is empty")

        valid_mask = np.isfinite(dem)
        if not np.any(valid_mask):
            raise ValueError("DEM array contains no valid data")

        valid_dem = dem[valid_mask]
        grad_y, grad_x = np.gradient(dem, edge_order=1)
        slope = np.sqrt(grad_x**2 + grad_y**2)
        slope_deg = np.degrees(np.arctan(slope))
        aspect_rad = np.arctan2(-grad_y, grad_x)
        aspect_deg = (np.degrees(aspect_rad) + 360) % 360

        valid_slope = slope_deg[valid_mask]
        valid_aspect = aspect_deg[valid_mask]

        slope_mean = float(np.nanmean(slope_deg))
        slope_max = float(np.nanmax(slope_deg))
        elevation_min = float(np.min(valid_dem))
        elevation_max = float(np.max(valid_dem))
        elevation_mean = float(np.mean(valid_dem))
        elevation_range = elevation_max - elevation_min

        aspect_median = float(np.nanmedian(valid_aspect))
        aspect_dominant = _get_dominant_aspect(valid_aspect)

        terrain_type = self._classify_terrain(valid_slope)

        return TerrainAnalysis(
            profile_id=profile_id or "default",
            terrain_type=terrain_type,
            elevation_min=elevation_min,
            elevation_max=elevation_max,
            elevation_mean=elevation_mean,
            elevation_range=elevation_range,
            slope_mean=slope_mean,
            slope_max=slope_max,
            slope_class_dominant=classify_slope_usda(np.tan(np.radians(slope_mean)) * 100.0),
            aspect_dominant=aspect_dominant,
            roughness_index=0.0,
        )
