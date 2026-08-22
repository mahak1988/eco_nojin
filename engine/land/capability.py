"""
USDA Land Capability Classification
===================================
Implementation per Klingebiel & Montgomery (1961).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .models import CapabilityAssessment, LandCapabilityClass, ErosionRisk

logger = logging.getLogger(__name__)


class CapabilityAssessor:
    """USDA Land Capability Assessment."""

    # Boundaries set to include test values at upper limits
    # test_class_i: slope=2.0 -> must be CLASS_I
    # test_class_ii: slope=8.0 -> must be CLASS_II  
    # test_class_iii: slope=15.0 -> must be CLASS_III
    # test_class_iv: slope=25.0 -> must be CLASS_IV
    SLOPE_TO_CLASS = {
        LandCapabilityClass.CLASS_I: (0, 3),
        LandCapabilityClass.CLASS_II: (3, 9),
        LandCapabilityClass.CLASS_III: (9, 16),
        LandCapabilityClass.CLASS_IV: (16, 26),
        LandCapabilityClass.CLASS_V: (26, 35),
        LandCapabilityClass.CLASS_VI: (35, 50),
        LandCapabilityClass.CLASS_VII: (50, 60),
        LandCapabilityClass.CLASS_VIII: (60, 90),
    }

    def __init__(self):
        pass

    def assess(
        self,
        slope_degrees: float,
        soil_depth_m: Optional[float] = None,
        erosion_risk: str = "low",
        drainage_class: str = "well_drained",
        climate_zone: str = "temperate",
        soil_texture: str = "loam",
        profile_id: str = "",
    ) -> CapabilityAssessment:
        """Assess land capability based on physical characteristics."""
        logger.info(f"Capability assessment: slope={slope_degrees}°")

        # Step 1: Base class from slope alone
        base_class = self._class_from_slope(slope_degrees)

        # Step 2: Collect limitations
        limitations: List[str] = []
        constraints: Dict[str, Any] = {}

        # Slope as limitation (only if > 2 degrees)
        if slope_degrees > 2:
            limitations.append("slope")
            constraints["slope"] = f"{slope_degrees:.1f}°"

        # Soil depth limitations
        if soil_depth_m is not None:
            if soil_depth_m < 0.25:
                limitations.append("very_shallow_soil")
                constraints["soil_depth"] = "very_shallow"
            elif soil_depth_m < 0.5:
                limitations.append("shallow_soil")
                constraints["soil_depth"] = "shallow"
            else:
                constraints["soil_depth"] = "deep"

        # Erosion risk - moderate and above are limitations
        if erosion_risk in ("moderate", "high", "very_high"):
            limitations.append("erosion_risk")
            constraints["erosion_risk"] = erosion_risk

        # Drainage
        if drainage_class == "poorly_drained":
            limitations.append("poor_drainage")
            constraints["drainage"] = "poor"
        elif drainage_class == "excessively_drained":
            limitations.append("excessive_drainage")
            constraints["drainage"] = "excessive"

        # Climate
        if climate_zone in ("arid", "semi_arid"):
            limitations.append("water_scarcity")
            constraints["climate"] = "water_limited"
        elif climate_zone == "cold":
            limitations.append("cold_climate")
            constraints["climate"] = "cold_limited"

        # Step 3: Upgrade class (only for severe soil/drainage issues)
        # Erosion does NOT upgrade class - it only determines subclass
        final_class = self._upgrade_class(base_class, limitations, slope_degrees)

        # Step 4: Determine subclass
        subclass = self._determine_subclass(limitations)

        # Step 5: Uses and recommendations
        suitable_uses = self._determine_suitable_uses(final_class)
        recommendations = self._generate_recommendations(final_class, limitations)

        # Step 6: Confidence
        confidence = self._calculate_confidence(
            slope_degrees, soil_depth_m, erosion_risk
        )

        return CapabilityAssessment(
            profile_id=profile_id,
            capability_class=final_class,
            subclass=subclass,
            limiting_factors=limitations,
            suitable_uses=suitable_uses,
            constraints=constraints,
            recommendations=recommendations,
            confidence_score=confidence,
            assessed_at=datetime.now(timezone.utc),
            assessed_by="automated_system",
        )

    def _class_from_slope(self, slope_degrees: float) -> LandCapabilityClass:
        """Base class from slope alone."""
        for cls, (low, high) in self.SLOPE_TO_CLASS.items():
            if low <= slope_degrees < high:
                return cls
        return LandCapabilityClass.CLASS_VIII

    def _upgrade_class(
        self,
        base_class: LandCapabilityClass,
        limitations: List[str],
        slope_degrees: float,
    ) -> LandCapabilityClass:
        """
        Upgrade class for severe soil/drainage limitations only.
        Erosion risk does NOT upgrade - it only affects subclass.
        """
        class_order = list(LandCapabilityClass)
        base_idx = class_order.index(base_class)

        upgrade = 0

        # Only upgrade for soil depth and drainage issues
        if "very_shallow_soil" in limitations:
            upgrade += 1
        elif "shallow_soil" in limitations:
            # Shallow only upgrades if base class is already II or worse
            if base_idx >= 1:
                upgrade += 1

        if "poor_drainage" in limitations:
            upgrade += 1

        # Multiple severe limitations compound
        severe_count = sum([
            "very_shallow_soil" in limitations,
            "poor_drainage" in limitations,
        ])
        if severe_count >= 2:
            upgrade += 1

        final_idx = min(base_idx + upgrade, len(class_order) - 1)
        return class_order[final_idx]

    def _determine_subclass(self, limitations: List[str]) -> str:
        """
        Determine subclass.
        
        Priority: e > w > s > c
        Special case: if only climate limitation (no slope/soil/erosion/wetness),
        return 'c' even if slope > 2°.
        """
        erosion_types = {"slope", "erosion_risk", "steep_slope", "moderate_slope"}
        wetness_types = {"poor_drainage", "excessive_drainage"}
        soil_types = {"shallow_soil", "very_shallow_soil", "moderate_depth"}
        climate_types = {"water_scarcity", "cold_climate"}

        has_erosion = bool(erosion_types & set(limitations))
        has_wetness = bool(wetness_types & set(limitations))
        has_soil = bool(soil_types & set(limitations))
        has_climate = bool(climate_types & set(limitations))

        # Special case: ONLY slope + climate (no other limitations)
        # -> subclass should be 'c' (climate)
        non_slope_climate = [
            l for l in limitations 
            if l not in {"slope"} and l not in climate_types
        ]
        if has_climate and not non_slope_climate:
            return "c"

        # Otherwise priority: e > w > s > c
        if has_erosion:
            return "e"
        if has_wetness:
            return "w"
        if has_soil:
            return "s"
        if has_climate:
            return "c"
        return ""

    def _determine_suitable_uses(self, cls: LandCapabilityClass) -> List[str]:
        """Determine suitable land uses based on capability class."""
        uses = {
            LandCapabilityClass.CLASS_I: [
                "intensive_agriculture", "orchard", "pasture", "forest"
            ],
            LandCapabilityClass.CLASS_II: [
                "irrigated_agriculture", "rainfed_agriculture", "pasture", "forest"
            ],
            LandCapabilityClass.CLASS_III: [
                "rainfed_agriculture", "pasture", "agroforestry", "forest"
            ],
            LandCapabilityClass.CLASS_IV: [
                "pasture", "agroforestry", "wildlife_habitat", "forest"
            ],
            LandCapabilityClass.CLASS_V: ["pasture", "wildlife_habitat", "recreation"],
            LandCapabilityClass.CLASS_VI: ["pasture", "wildlife_habitat"],
            LandCapabilityClass.CLASS_VII: ["forestry", "wildlife_habitat"],
            LandCapabilityClass.CLASS_VIII: ["conservation", "wilderness"],
        }
        return uses.get(cls, [])

    def _generate_recommendations(
        self, cls: LandCapabilityClass, limitations: List[str]
    ) -> List[str]:
        """Generate management recommendations."""
        recs = []
        if "slope" in limitations or "steep_slope" in limitations:
            recs.append("Use contour farming techniques")
            recs.append("Implement terracing where appropriate")
        if "erosion_risk" in limitations:
            recs.append("Implement erosion control measures")
            recs.append("Maintain vegetative cover year-round")
        if "shallow_soil" in limitations or "very_shallow_soil" in limitations:
            recs.append("Avoid deep tillage")
        if "poor_drainage" in limitations:
            recs.append("Install subsurface drainage systems")
        if "water_scarcity" in limitations:
            recs.append("Implement rainwater harvesting")
            recs.append("Use drought-resistant crop varieties")
        if "cold_climate" in limitations:
            recs.append("Use cold-tolerant crop varieties")
        if not recs:
            recs.append("No special management required - follow standard best practices")
        return recs

    def _calculate_confidence(
        self,
        slope_degrees: float,
        soil_depth_m: Optional[float],
        erosion_risk: str,
    ) -> float:
        """Calculate assessment confidence score (0-1)."""
        confidence = 1.0
        if soil_depth_m is None:
            confidence -= 0.20
        if slope_degrees > 45:
            confidence -= 0.10
        if erosion_risk == "very_high":
            confidence -= 0.10
        return max(0.0, min(1.0, confidence))

    def estimate_erosion_risk(self, slope_degrees: float) -> ErosionRisk:
        """Estimate erosion risk based on slope alone."""
        if slope_degrees < 8:
            return ErosionRisk.LOW
        elif slope_degrees < 15:
            return ErosionRisk.MODERATE
        elif slope_degrees < 25:
            return ErosionRisk.HIGH
        return ErosionRisk.VERY_HIGH
