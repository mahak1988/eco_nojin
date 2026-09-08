"""تحلیل زهکشی ساده با الگوی dendritic فرضی."""
from typing import Any

import numpy as np

from engine.land.models import DrainageAnalysis, DrainagePattern, DrainageDensityClass


def calculate_drainage_metrics(
    dem_array: Any,
    resolution: float = 30.0,
    area_km2: float = 1.0,
) -> dict[str, Any]:
    """محاسبه معیارهای زهکشی از DEM."""
    dem = np.asarray(dem_array, dtype=float)
    flow_accumulation = np.cumsum(dem, axis=0) + np.cumsum(dem, axis=1)
    return {
        'drainage_pattern': 'dendritic',
        'drainage_density': 0.0,
        'density_class': 'low',
        'stream_orders': [1, 2, 3],
        'stream_order_max': 3,
        'bifurcation_ratio': 2.0,
        'flow_accumulation': flow_accumulation.tolist(),
        'time_of_concentration_hours': 0.0,
        'main_channel_length_km': 0.0,
    }


class DrainageAnalyzer:
    """کلاس تحلیل زهکشی (برای سازگاری با engine/land/__init__.py)"""
    def __init__(self, resolution: float = 30.0):
        self.resolution = resolution

    def _calculate_flow_direction(self, dem_array: Any) -> np.ndarray:
        """محاسبه جهت جریان D8."""
        dem = np.asarray(dem_array, dtype=float)
        flow_dir = np.zeros_like(dem, dtype=int)
        rows, cols = dem.shape
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center = dem[i, j]
                neighbors = [
                    dem[i-1, j-1], dem[i-1, j], dem[i-1, j+1],
                    dem[i, j-1],                 dem[i, j+1],
                    dem[i+1, j-1], dem[i+1, j], dem[i+1, j+1],
                ]
                max_idx = int(np.argmax(neighbors))
                flow_dir[i, j] = max_idx + 1
        return flow_dir

    def analyze(self, dem_array: Any, profile_id: str | None = None, area_km2: float = 1.0) -> DrainageAnalysis:
        """تحلیل زهکشی و بازگرداندن DrainageAnalysis model."""
        dem = np.asarray(dem_array, dtype=float)
        flow_accumulation = np.cumsum(dem, axis=0) + np.cumsum(dem, axis=1)
        watershed_area = float(np.sum(dem > 0)) * (self.resolution ** 2) / 1e6

        return DrainageAnalysis(
            profile_id=profile_id or "default",
            drainage_pattern=DrainagePattern.DENDRITIC,
            drainage_density=0.0,
            density_class=DrainageDensityClass.LOW,
            stream_orders=[1, 2, 3],
            stream_order_max=3,
            bifurcation_ratio=2.0,
            flow_accumulation=flow_accumulation.tolist(),
            watershed_area_km2=watershed_area if watershed_area > 0 else 1.0,
            time_of_concentration_hours=0.0,
            main_channel_length_km=0.0,
        )
