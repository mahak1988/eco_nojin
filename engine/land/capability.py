"""ارزیابی قابلیت اراضی ساده."""
from typing import Any, Dict, Optional

def assess_land_capability(
    slope_degrees: float,
    soil_depth_m: Optional[float] = None,
    erosion_risk: str = "low",
    drainage_class: str = "well_drained",
    climate_zone: str = "temperate",
    soil_texture: str = "loam"
) -> Dict[str, Any]:
    """کلاس بندی ساده قابلیت اراضی بر اساس شیب."""
    if slope_degrees < 5:
        cap_class = "I"
    elif slope_degrees < 15:
        cap_class = "II"
    elif slope_degrees < 30:
        cap_class = "III"
    else:
        cap_class = "IV"
    return {
        'class': cap_class,
        'slope_degrees': slope_degrees,
        'soil_depth_m': soil_depth_m,
        'erosion_risk': erosion_risk,
        'drainage_class': drainage_class,
        'climate_zone': climate_zone,
        'soil_texture': soil_texture,
    }


class CapabilityAssessor:
    """کلاس ارزیابی قابلیت اراضی (برای سازگاری با engine/land/__init__.py)"""
    def __init__(self):
        pass

    def assess(self, **kwargs) -> Dict[str, Any]:
        return assess_land_capability(**kwargs)
