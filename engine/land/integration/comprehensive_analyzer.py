"""
Comprehensive Land Analyzer (Fixed Scoring)
=============================================
Stricter scoring with proper weight distribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class LandUseCategory(str, Enum):
    """Land use recommendation categories"""
    INTENSIVE_AGRICULTURE = "intensive_agriculture"
    RAINFED_AGRICULTURE = "rainfed_agriculture"
    PASTURE = "pasture"
    FORESTRY = "forestry"
    CONSERVATION = "conservation"


class CropType(str, Enum):
    """Major crop types for suitability scoring"""
    WHEAT = "wheat"
    CORN = "corn"
    RICE = "rice"
    COTTON = "cotton"
    SOYBEAN = "soybean"
    BARLEY = "barley"


@dataclass
class SoilSummary:
    """Simplified soil profile summary"""
    ph: float = 6.5
    clay_pct: float = 25.0
    silt_pct: float = 40.0
    sand_pct: float = 35.0
    organic_matter_pct: float = 2.0
    depth_cm: float = 100.0
    ec_dsm: float = 0.5
    drainage_class: str = "well_drained"
    texture: str = "loam"


@dataclass
class ClimateSummary:
    """Simplified climate summary"""
    mean_temp_c: float = 20.0
    annual_precip_mm: float = 600.0
    frost_free_days: int = 200
    aridity_index: float = 0.6
    et0_mm: float = 1200.0


@dataclass
class TerrainSummary:
    """Simplified terrain summary"""
    slope_pct: float = 3.0
    elevation_m: float = 1500.0
    capability_class: str = "II"
    erosion_risk: str = "low"


@dataclass
class CropSuitability:
    """Crop suitability result"""
    crop: CropType
    score: float  # 0-100
    suitability_class: str
    limiting_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ComprehensiveLandAnalysis:
    """Complete comprehensive land analysis result"""
    suitability_score: float  # 0-100
    land_use_recommendations: List[LandUseCategory] = field(default_factory=list)
    crop_suitabilities: List[CropSuitability] = field(default_factory=list)
    limiting_factors: List[str] = field(default_factory=list)
    improvement_recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComprehensiveLandAnalyzer:
    """
    Comprehensive land analyzer with STRICT scoring.
    
    Weights (stricter):
    - Soil: 40% (but penalties are severe)
    - Climate: 35%
    - Terrain: 25%
    """

    CROP_REQUIREMENTS = {
        CropType.WHEAT: {
            "optimal_ph": (6.0, 7.5),
            "optimal_temp": (15, 25),
            "min_precip_mm": 400,
            "max_slope_pct": 8,
            "min_depth_cm": 60,
        },
        CropType.CORN: {
            "optimal_ph": (5.8, 7.0),
            "optimal_temp": (20, 30),
            "min_precip_mm": 500,
            "max_slope_pct": 6,
            "min_depth_cm": 80,
        },
        CropType.RICE: {
            "optimal_ph": (5.5, 6.5),
            "optimal_temp": (25, 35),
            "min_precip_mm": 1000,
            "max_slope_pct": 3,
            "min_depth_cm": 50,
        },
        CropType.COTTON: {
            "optimal_ph": (5.8, 8.0),
            "optimal_temp": (20, 30),
            "min_precip_mm": 500,
            "max_slope_pct": 8,
            "min_depth_cm": 70,
        },
        CropType.SOYBEAN: {
            "optimal_ph": (6.0, 7.0),
            "optimal_temp": (20, 30),
            "min_precip_mm": 500,
            "max_slope_pct": 8,
            "min_depth_cm": 60,
        },
        CropType.BARLEY: {
            "optimal_ph": (6.0, 7.5),
            "optimal_temp": (10, 20),
            "min_precip_mm": 300,
            "max_slope_pct": 10,
            "min_depth_cm": 50,
        },
    }

    CAPABILITY_SCORES = {
        "I": 100, "II": 85, "III": 70, "IV": 55,
        "V": 40, "VI": 30, "VII": 20, "VIII": 10,
    }

    def analyze(
        self,
        soil: SoilSummary,
        climate: ClimateSummary,
        terrain: TerrainSummary,
    ) -> ComprehensiveLandAnalysis:
        """Perform comprehensive land analysis with strict scoring."""
        try:
            soil_score, soil_issues = self._evaluate_soil(soil)
            climate_score, climate_issues = self._evaluate_climate(climate)
            terrain_score, terrain_issues = self._evaluate_terrain(terrain)

            # Weighted average
            suitability_score = (
                soil_score * 0.40 +
                climate_score * 0.35 +
                terrain_score * 0.25
            )

            all_issues = soil_issues + climate_issues + terrain_issues
            land_use_recs = self._recommend_land_use(
                suitability_score, terrain.capability_class, all_issues
            )
            crop_suitabilities = self._score_crops(soil, climate, terrain)
            improvements = self._generate_improvements(all_issues)

            return ComprehensiveLandAnalysis(
                suitability_score=suitability_score,
                land_use_recommendations=land_use_recs,
                crop_suitabilities=crop_suitabilities,
                limiting_factors=all_issues,
                improvement_recommendations=improvements,
                confidence=0.8,
                metadata={
                    "soil_score": soil_score,
                    "climate_score": climate_score,
                    "terrain_score": terrain_score,
                },
            )

        except Exception as e:
            return ComprehensiveLandAnalysis(
                suitability_score=0.0,
                land_use_recommendations=[LandUseCategory.CONSERVATION],
                crop_suitabilities=[],
                limiting_factors=[f"Analysis error: {str(e)}"],
                improvement_recommendations=["Re-collect data"],
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _evaluate_soil(self, soil: SoilSummary) -> tuple[float, List[str]]:
        """Evaluate soil with STRICT penalties."""
        score = 100.0
        issues = []

        # pH: severe penalties
        if soil.ph < 5.0:
            score -= 40
            issues.append("severely_acidic")
        elif soil.ph < 5.5:
            score -= 25
            issues.append("soil_too_acidic")
        elif soil.ph > 8.5:
            score -= 35
            issues.append("severely_alkaline")
        elif soil.ph > 8.0:
            score -= 20
            issues.append("soil_too_alkaline")

        # Depth: severe penalty for shallow
        if soil.depth_cm < 30:
            score -= 40
            issues.append("soil_too_shallow")
        elif soil.depth_cm < 60:
            score -= 20
            issues.append("soil_moderately_shallow")

        # Texture
        if soil.clay_pct > 60:
            score -= 20
            issues.append("soil_too_clayey")
        elif soil.sand_pct > 85:
            score -= 20
            issues.append("soil_too_sandy")

        # Organic matter
        if soil.organic_matter_pct < 1.0:
            score -= 25
            issues.append("low_organic_matter")
        elif soil.organic_matter_pct < 2.0:
            score -= 15
            issues.append("moderate_organic_matter")

        # Drainage
        if soil.drainage_class == "poorly_drained":
            score -= 25
            issues.append("poor_drainage")

        # Salinity: SEVERE penalty
        if soil.ec_dsm > 6.0:
            score -= 50
            issues.append("severe_salinity")
        elif soil.ec_dsm > 4.0:
            score -= 35
            issues.append("high_salinity")
        elif soil.ec_dsm > 2.0:
            score -= 20
            issues.append("moderate_salinity")

        return max(0.0, score), issues

    def _evaluate_climate(self, climate: ClimateSummary) -> tuple[float, List[str]]:
        """Evaluate climate with STRICT penalties."""
        score = 100.0
        issues = []

        # Temperature
        if climate.mean_temp_c < 5:
            score -= 40
            issues.append("climate_too_cold")
        elif climate.mean_temp_c > 35:
            score -= 35
            issues.append("climate_too_hot")

        # Precipitation: SEVERE penalty for arid
        if climate.annual_precip_mm < 250:
            score -= 50
            issues.append("severe_drought")
        elif climate.annual_precip_mm < 400:
            score -= 30
            issues.append("climate_semi_arid")

        # Growing season
        if climate.frost_free_days < 90:
            score -= 40
            issues.append("growing_season_too_short")
        elif climate.frost_free_days < 150:
            score -= 20
            issues.append("growing_season_short")

        # Aridity
        if climate.aridity_index < 0.2:
            score -= 35
            issues.append("high_aridity")
        elif climate.aridity_index < 0.5:
            score -= 15
            issues.append("moderate_aridity")

        return max(0.0, score), issues

    def _evaluate_terrain(self, terrain: TerrainSummary) -> tuple[float, List[str]]:
        """Evaluate terrain with STRICT penalties."""
        score = self.CAPABILITY_SCORES.get(terrain.capability_class, 50)
        issues = []

        if terrain.erosion_risk == "high":
            score -= 20
            issues.append("erosion_risk")
        if terrain.slope_pct > 15:
            score -= 15
            issues.append("steep_slope")

        return max(0.0, score), issues

    def _recommend_land_use(
        self,
        suitability_score: float,
        capability_class: str,
        issues: List[str],
    ) -> List[LandUseCategory]:
        """Generate land use recommendations."""
        recommendations = []

        if suitability_score >= 80 and capability_class in ["I", "II"]:
            recommendations.append(LandUseCategory.INTENSIVE_AGRICULTURE)
        elif suitability_score >= 60 and capability_class in ["I", "II", "III"]:
            recommendations.append(LandUseCategory.RAINFED_AGRICULTURE)
        elif suitability_score >= 40 and capability_class in ["III", "IV"]:
            recommendations.append(LandUseCategory.PASTURE)
        elif suitability_score >= 25 and capability_class in ["IV", "V", "VI"]:
            recommendations.append(LandUseCategory.FORESTRY)
        else:
            recommendations.append(LandUseCategory.CONSERVATION)

        return recommendations

    def _score_crops(
        self,
        soil: SoilSummary,
        climate: ClimateSummary,
        terrain: TerrainSummary,
    ) -> List[CropSuitability]:
        """Score crops with STRICT penalties."""
        results = []

        for crop, reqs in self.CROP_REQUIREMENTS.items():
            score = 100.0
            issues = []
            recs = []

            # pH
            if not (reqs["optimal_ph"][0] <= soil.ph <= reqs["optimal_ph"][1]):
                score -= 25
                issues.append("pH outside optimal range")
                recs.append("Apply lime or sulfur")

            # Depth
            if soil.depth_cm < reqs["min_depth_cm"]:
                score -= 30
                issues.append(f"Insufficient depth (need {reqs['min_depth_cm']}cm)")
                recs.append("Consider shallow-rooted crops")

            # Temperature
            if not (reqs["optimal_temp"][0] <= climate.mean_temp_c <= reqs["optimal_temp"][1]):
                score -= 20
                issues.append("Temperature outside optimal range")
                recs.append("Use greenhouse or season extension")

            # Precipitation: SEVERE penalty
            if climate.annual_precip_mm < reqs["min_precip_mm"]:
                deficit = reqs["min_precip_mm"] - climate.annual_precip_mm
                penalty = min(50, 20 + deficit / 20)
                score -= penalty
                issues.append(f"Insufficient precipitation (need {reqs['min_precip_mm']}mm)")
                recs.append("Irrigation required")

            # Slope
            if terrain.slope_pct > reqs["max_slope_pct"]:
                score -= 20
                issues.append(f"Slope too steep (max {reqs['max_slope_pct']}%)")
                recs.append("Use contour farming or terracing")

            # Suitability class
            if score >= 85:
                suit_class = "excellent"
            elif score >= 70:
                suit_class = "good"
            elif score >= 55:
                suit_class = "moderate"
            elif score >= 40:
                suit_class = "poor"
            else:
                suit_class = "unsuitable"

            if not recs:
                recs.append("Crop is well-suited")

            results.append(CropSuitability(
                crop=crop,
                score=max(0.0, score),
                suitability_class=suit_class,
                limiting_factors=issues,
                recommendations=recs,
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _generate_improvements(self, issues: List[str]) -> List[str]:
        """Generate improvement recommendations."""
        improvements = []
        issue_set = set(issues)

        if "severely_acidic" in issue_set or "soil_too_acidic" in issue_set:
            improvements.append("Apply agricultural lime to raise pH")

        if "severely_alkaline" in issue_set or "soil_too_alkaline" in issue_set:
            improvements.append("Apply sulfur or organic matter to lower pH")

        if "low_organic_matter" in issue_set:
            improvements.append("Add compost or manure")
            improvements.append("Practice conservation tillage")

        if "poor_drainage" in issue_set:
            improvements.append("Install tile drainage")
            improvements.append("Create raised beds")

        if "severe_salinity" in issue_set or "high_salinity" in issue_set:
            improvements.append("Implement leaching with high-quality water")
            improvements.append("Install subsurface drainage")
            improvements.append("Grow salt-tolerant crops")

        if "erosion_risk" in issue_set or "steep_slope" in issue_set:
            improvements.append("Implement contour farming")
            improvements.append("Establish cover crops")
            improvements.append("Create buffer strips")

        if "severe_drought" in issue_set or "climate_semi_arid" in issue_set:
            improvements.append("Install efficient irrigation (drip/trickle)")
            improvements.append("Implement water harvesting")
            improvements.append("Use mulch to reduce evaporation")

        if "growing_season_too_short" in issue_set:
            improvements.append("Use season extension techniques")
            improvements.append("Select early-maturing varieties")

        if not improvements:
            improvements.append("Land is in good condition - maintain current practices")

        return improvements
