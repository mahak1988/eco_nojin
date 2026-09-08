"""ارزیابی قابلیت اراضی."""
from typing import Any

from engine.land.models import CapabilityAssessment, LandCapabilityClass


def assess_land_capability(
    profile_id: str | None = None,
    slope_degrees: float = 0.0,
    soil_depth_m: float | None = None,
    erosion_risk: str = "low",
    drainage_class: str = "well_drained",
    climate_zone: str = "temperate",
    soil_texture: str = "loam",
) -> CapabilityAssessment:
    """ارزیابی قابلیت اراضی و بازگرداندن CapabilityAssessment model."""

    confidence_score = 0.9
    limiting_factors: list[str] = []

    if soil_depth_m is None:
        confidence_score -= 0.1
        limiting_factors.append("unknown_soil_depth")

    if erosion_risk == "moderate":
        cap_class = LandCapabilityClass.CLASS_III
        subclass = "e"
        limiting_factors.append("erosion_risk")
    elif erosion_risk == "high":
        cap_class = LandCapabilityClass.CLASS_IV
        subclass = "e"
        limiting_factors.append("erosion_risk")
    elif erosion_risk == "very_high":
        cap_class = LandCapabilityClass.CLASS_VII
        subclass = "e"
        limiting_factors.append("erosion_risk")
    elif slope_degrees < 5:
        cap_class = LandCapabilityClass.CLASS_I
        subclass = None
    elif slope_degrees < 15:
        cap_class = LandCapabilityClass.CLASS_II
        subclass = None
    elif slope_degrees < 30:
        cap_class = LandCapabilityClass.CLASS_III
        subclass = None
    else:
        cap_class = LandCapabilityClass.CLASS_IV
        subclass = None

    if climate_zone == "arid":
        limiting_factors.append("water_scarcity")
        if cap_class in [LandCapabilityClass.CLASS_I, LandCapabilityClass.CLASS_II]:
            cap_class = LandCapabilityClass.CLASS_IV
            subclass = "c"
        elif cap_class == LandCapabilityClass.CLASS_III:
            subclass = "c"

    if cap_class == LandCapabilityClass.CLASS_I:
        suitable_uses = ["agriculture", "horticulture", "pasture"]
        recommendations = ["Maintain current land use", "Apply precision agriculture"]
    elif cap_class == LandCapabilityClass.CLASS_II:
        suitable_uses = ["agriculture", "pasture", "forestry"]
        recommendations = ["Good for most crops", "Apply conservation tillage"]
    elif cap_class == LandCapabilityClass.CLASS_III:
        suitable_uses = ["agriculture", "pasture", "agroforestry"]
        recommendations = ["Use erosion control measures", "Implement crop rotation"]
    elif cap_class == LandCapabilityClass.CLASS_IV:
        suitable_uses = ["pasture", "forestry", "agroforestry"]
        recommendations = ["Limit intensive agriculture", "Apply soil conservation"]
    elif cap_class == LandCapabilityClass.CLASS_V:
        suitable_uses = ["pasture", "forestry"]
        recommendations = ["Use for grazing only", "Avoid cultivation"]
    elif cap_class == LandCapabilityClass.CLASS_VI:
        suitable_uses = ["forestry", "recreation"]
        recommendations = ["Protect from erosion", "Reforestation recommended"]
    elif cap_class == LandCapabilityClass.CLASS_VII:
        suitable_uses = ["recreation", "wildlife habitat"]
        recommendations = ["Leave in natural state", "Prevent degradation"]
    else:
        suitable_uses = ["wildlife habitat", "conservation"]
        recommendations = ["Strict conservation", "No development"]

    return CapabilityAssessment(
        profile_id=profile_id or "default",
        capability_class=cap_class,
        subclass=subclass,
        limiting_factors=limiting_factors,
        suitable_uses=suitable_uses,
        recommendations=recommendations,
        confidence_score=confidence_score,
    )


class CapabilityAssessor:
    """کلاس ارزیابی قابلیت اراضی (برای سازگاری با engine/land/__init__.py)"""
    def __init__(self):
        pass

    def assess(self, **kwargs) -> CapabilityAssessment:
        return assess_land_capability(**kwargs)
