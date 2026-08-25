"""تحلیل توپوگرافی ساده (محاسبه شیب و جهت) با NumPy."""
import numpy as np
from typing import Any, Dict

def calculate_terrain_metrics(dem_array: Any) -> Dict[str, Any]:
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
    def __init__(self):
        pass

    def analyze(self, dem_array: Any) -> Dict[str, Any]:
        return calculate_terrain_metrics(dem_array)
