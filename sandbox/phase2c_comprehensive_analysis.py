"""
Phase 2C: Comprehensive Land Analysis
======================================
Combines Soil + Climate + Land Capability into unified assessment.

Outputs:
- Land Suitability Score (0-100)
- Land Use Recommendations (agriculture, pasture, forest, conservation)
- Crop Suitability Scoring for major crops
- Improvement Recommendations

Run: python sandbox/phase2c_comprehensive_analysis.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")


def create_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ {path.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("🌍 Phase 2C: Comprehensive Land Analysis")
    print("=" * 70)

    # ================================================================
    # 1. Main module: comprehensive_analyzer.py
    # ================================================================
    print("\n[1/3] Creating comprehensive_analyzer.py...")

    analyzer_code = '''"""
Comprehensive Land Analyzer
============================
Combines Soil + Climate + Land Capability into unified assessment.

Scientific basis:
- FAO Land Evaluation Framework (1976)
- USDA Land Capability Classification
- Sys et al. (1991) Land Evaluation and Crop Suitability
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
    suitability_class: str  # "excellent", "good", "moderate", "poor", "unsuitable"
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
    Comprehensive land analyzer combining soil, climate, and terrain.

    Algorithm:
    1. Evaluate soil quality (40% weight)
    2. Evaluate climate suitability (35% weight)
    3. Evaluate terrain capability (25% weight)
    4. Generate land use recommendations
    5. Score crop suitability
    """

    # Crop requirements database
    CROP_REQUIREMENTS = {
        CropType.WHEAT: {
            "optimal_ph": (6.0, 7.5),
            "optimal_temp": (15, 25),
            "min_precip_mm": 400,
            "max_slope_pct": 8,
            "min_depth_cm": 60,
            "drought_tolerance": "moderate",
        },
        CropType.CORN: {
            "optimal_ph": (5.8, 7.0),
            "optimal_temp": (20, 30),
            "min_precip_mm": 500,
            "max_slope_pct": 6,
            "min_depth_cm": 80,
            "drought_tolerance": "low",
        },
        CropType.RICE: {
            "optimal_ph": (5.5, 6.5),
            "optimal_temp": (25, 35),
            "min_precip_mm": 1000,
            "max_slope_pct": 3,
            "min_depth_cm": 50,
            "drought_tolerance": "very_low",
        },
        CropType.COTTON: {
            "optimal_ph": (5.8, 8.0),
            "optimal_temp": (20, 30),
            "min_precip_mm": 500,
            "max_slope_pct": 8,
            "min_depth_cm": 70,
            "drought_tolerance": "high",
        },
        CropType.SOYBEAN: {
            "optimal_ph": (6.0, 7.0),
            "optimal_temp": (20, 30),
            "min_precip_mm": 500,
            "max_slope_pct": 8,
            "min_depth_cm": 60,
            "drought_tolerance": "moderate",
        },
        CropType.BARLEY: {
            "optimal_ph": (6.0, 7.5),
            "optimal_temp": (10, 20),
            "min_precip_mm": 300,
            "max_slope_pct": 10,
            "min_depth_cm": 50,
            "drought_tolerance": "high",
        },
    }

    # Capability class scores (USDA)
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
        """
        Perform comprehensive land analysis.

        Args:
            soil: Soil profile summary
            climate: Climate summary
            terrain: Terrain summary

        Returns:
            ComprehensiveLandAnalysis with all results
        """
        try:
            # Step 1: Evaluate components
            soil_score, soil_issues = self._evaluate_soil(soil)
            climate_score, climate_issues = self._evaluate_climate(climate)
            terrain_score, terrain_issues = self._evaluate_terrain(terrain)

            # Step 2: Weighted average
            suitability_score = (
                soil_score * 0.40 +
                climate_score * 0.35 +
                terrain_score * 0.25
            )

            # Step 3: Collect all issues
            all_issues = soil_issues + climate_issues + terrain_issues

            # Step 4: Generate land use recommendations
            land_use_recs = self._recommend_land_use(
                suitability_score, terrain.capability_class, all_issues
            )

            # Step 5: Score crop suitability
            crop_suitabilities = self._score_crops(soil, climate, terrain)

            # Step 6: Generate improvement recommendations
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
                improvement_recommendations=["Re-collect data with better quality"],
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _evaluate_soil(self, soil: SoilSummary) -> tuple[float, List[str]]:
        """Evaluate soil quality (0-100)"""
        score = 100.0
        issues = []

        # pH evaluation
        if soil.ph < 5.5:
            score -= 20
            issues.append("soil_too_acidic")
        elif soil.ph > 8.0:
            score -= 15
            issues.append("soil_too_alkaline")

        # Depth evaluation
        if soil.depth_cm < 30:
            score -= 25
            issues.append("soil_too_shallow")
        elif soil.depth_cm < 60:
            score -= 10
            issues.append("soil_moderately_shallow")

        # Texture evaluation
        if soil.clay_pct > 60:
            score -= 15
            issues.append("soil_too_clayey")
        elif soil.sand_pct > 85:
            score -= 15
            issues.append("soil_too_sandy")

        # Organic matter
        if soil.organic_matter_pct < 1.0:
            score -= 20
            issues.append("low_organic_matter")
        elif soil.organic_matter_pct < 2.0:
            score -= 10
            issues.append("moderate_organic_matter")

        # Drainage
        if soil.drainage_class == "poorly_drained":
            score -= 20
            issues.append("poor_drainage")

        # Salinity
        if soil.ec_dsm > 4.0:
            score -= 30
            issues.append("high_salinity")
        elif soil.ec_dsm > 2.0:
            score -= 15
            issues.append("moderate_salinity")

        return max(0.0, score), issues

    def _evaluate_climate(self, climate: ClimateSummary) -> tuple[float, List[str]]:
        """Evaluate climate suitability (0-100)"""
        score = 100.0
        issues = []

        # Temperature
        if climate.mean_temp_c < 5:
            score -= 25
            issues.append("climate_too_cold")
        elif climate.mean_temp_c > 35:
            score -= 20
            issues.append("climate_too_hot")

        # Precipitation
        if climate.annual_precip_mm < 250:
            score -= 30
            issues.append("climate_too_dry")
        elif climate.annual_precip_mm < 400:
            score -= 15
            issues.append("climate_semi_arid")

        # Growing season
        if climate.frost_free_days < 90:
            score -= 25
            issues.append("growing_season_too_short")
        elif climate.frost_free_days < 150:
            score -= 10
            issues.append("growing_season_short")

        # Aridity
        if climate.aridity_index < 0.2:
            score -= 20
            issues.append("high_aridity")
        elif climate.aridity_index < 0.5:
            score -= 10
            issues.append("moderate_aridity")

        return max(0.0, score), issues

    def _evaluate_terrain(self, terrain: TerrainSummary) -> tuple[float, List[str]]:
        """Evaluate terrain capability (0-100)"""
        score = self.CAPABILITY_SCORES.get(terrain.capability_class, 50)
        issues = []

        if terrain.erosion_risk == "high":
            issues.append("erosion_risk")
        if terrain.slope_pct > 15:
            issues.append("steep_slope")

        return score, issues

    def _recommend_land_use(
        self,
        suitability_score: float,
        capability_class: str,
        issues: List[str],
    ) -> List[LandUseCategory]:
        """Generate land use recommendations"""
        recommendations = []

        if suitability_score >= 80 and capability_class in ["I", "II"]:
            recommendations.append(LandUseCategory.INTENSIVE_AGRICULTURE)
            recommendations.append(LandUseCategory.RAINFED_AGRICULTURE)
        elif suitability_score >= 60 and capability_class in ["I", "II", "III"]:
            recommendations.append(LandUseCategory.RAINFED_AGRICULTURE)
            recommendations.append(LandUseCategory.PASTURE)
        elif suitability_score >= 40 and capability_class in ["III", "IV"]:
            recommendations.append(LandUseCategory.PASTURE)
            recommendations.append(LandUseCategory.FORESTRY)
        elif suitability_score >= 25 and capability_class in ["IV", "V", "VI"]:
            recommendations.append(LandUseCategory.FORESTRY)
            recommendations.append(LandUseCategory.CONSERVATION)
        else:
            recommendations.append(LandUseCategory.CONSERVATION)

        return recommendations

    def _score_crops(
        self,
        soil: SoilSummary,
        climate: ClimateSummary,
        terrain: TerrainSummary,
    ) -> List[CropSuitability]:
        """Score suitability for each major crop"""
        results = []

        for crop, reqs in self.CROP_REQUIREMENTS.items():
            score = 100.0
            issues = []
            recs = []

            # pH check
            if not (reqs["optimal_ph"][0] <= soil.ph <= reqs["optimal_ph"][1]):
                score -= 20
                issues.append("pH outside optimal range")
                if soil.ph < reqs["optimal_ph"][0]:
                    recs.append("Apply lime to raise pH")
                else:
                    recs.append("Apply sulfur to lower pH")

            # Depth check
            if soil.depth_cm < reqs["min_depth_cm"]:
                score -= 25
                issues.append(f"Insufficient soil depth (need {reqs['min_depth_cm']}cm)")
                recs.append("Consider shallow-rooted alternatives")

            # Temperature check
            if not (reqs["optimal_temp"][0] <= climate.mean_temp_c <= reqs["optimal_temp"][1]):
                score -= 15
                issues.append("Temperature outside optimal range")
                recs.append("Consider greenhouse or season extension")

            # Precipitation check
            if climate.annual_precip_mm < reqs["min_precip_mm"]:
                score -= 20
                issues.append(f"Insufficient precipitation (need {reqs['min_precip_mm']}mm)")
                recs.append("Irrigation required")

            # Slope check
            if terrain.slope_pct > reqs["max_slope_pct"]:
                score -= 15
                issues.append(f"Slope too steep (max {reqs['max_slope_pct']}%)")
                recs.append("Use contour farming or terracing")

            # Determine suitability class
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
                recs.append("Crop is well-suited for this land")

            results.append(CropSuitability(
                crop=crop,
                score=max(0.0, score),
                suitability_class=suit_class,
                limiting_factors=issues,
                recommendations=recs,
            ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _generate_improvements(self, issues: List[str]) -> List[str]:
        """Generate improvement recommendations"""
        improvements = []

        issue_set = set(issues)

        if "soil_too_acidic" in issue_set:
            improvements.append("Apply agricultural lime to raise soil pH")

        if "soil_too_alkaline" in issue_set:
            improvements.append("Apply elemental sulfur or organic matter to lower pH")

        if "low_organic_matter" in issue_set or "moderate_organic_matter" in issue_set:
            improvements.append("Add compost or manure to increase organic matter")
            improvements.append("Practice conservation tillage")

        if "poor_drainage" in issue_set:
            improvements.append("Install tile drainage system")
            improvements.append("Create raised beds")

        if "high_salinity" in issue_set or "moderate_salinity" in issue_set:
            improvements.append("Implement leaching with high-quality water")
            improvements.append("Install subsurface drainage")
            improvements.append("Grow salt-tolerant crops")

        if "erosion_risk" in issue_set or "steep_slope" in issue_set:
            improvements.append("Implement contour farming")
            improvements.append("Establish cover crops")
            improvements.append("Create buffer strips")

        if "climate_too_dry" in issue_set or "high_aridity" in issue_set:
            improvements.append("Install efficient irrigation system (drip/trickle)")
            improvements.append("Implement water harvesting")
            improvements.append("Use mulch to reduce evaporation")

        if "growing_season_too_short" in issue_set or "growing_season_short" in issue_set:
            improvements.append("Use season extension techniques (row covers, high tunnels)")
            improvements.append("Select early-maturing varieties")

        if not improvements:
            improvements.append("Land is in good condition - maintain current practices")

        return improvements
'''

    create_file(
        PROJECT_ROOT / "engine" / "land" / "integration" / "comprehensive_analyzer.py",
        analyzer_code
    )

    # ================================================================
    # 2. Test module
    # ================================================================
    print("\n[2/3] Creating test_comprehensive_analyzer.py...")

    test_code = '''"""
Tests for Comprehensive Land Analyzer
"""

import pytest
from engine.land.integration.comprehensive_analyzer import (
    ComprehensiveLandAnalyzer,
    SoilSummary,
    ClimateSummary,
    TerrainSummary,
    LandUseCategory,
    CropType,
)


class TestComprehensiveLandAnalyzer:
    """Test suite for ComprehensiveLandAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        return ComprehensiveLandAnalyzer()

    @pytest.fixture
    def good_soil(self):
        return SoilSummary(
            ph=6.5,
            clay_pct=25,
            silt_pct=40,
            sand_pct=35,
            organic_matter_pct=3.0,
            depth_cm=100,
            ec_dsm=0.5,
            drainage_class="well_drained",
            texture="loam",
        )

    @pytest.fixture
    def good_climate(self):
        return ClimateSummary(
            mean_temp_c=20,
            annual_precip_mm=800,
            frost_free_days=200,
            aridity_index=0.8,
            et0_mm=1200,
        )

    @pytest.fixture
    def good_terrain(self):
        return TerrainSummary(
            slope_pct=2.0,
            elevation_m=1500,
            capability_class="I",
            erosion_risk="low",
        )

    def test_good_land_high_score(
        self, analyzer, good_soil, good_climate, good_terrain
    ):
        """Good land should have high suitability score"""
        result = analyzer.analyze(good_soil, good_climate, good_terrain)
        assert result.suitability_score >= 80
        assert result.land_use_recommendations[0] == LandUseCategory.INTENSIVE_AGRICULTURE

    def test_poor_soil_reduces_score(
        self, analyzer, good_climate, good_terrain
    ):
        """Poor soil should reduce suitability score"""
        poor_soil = SoilSummary(
            ph=4.5,
            clay_pct=80,
            silt_pct=10,
            sand_pct=10,
            organic_matter_pct=0.5,
            depth_cm=20,
            ec_dsm=8.0,
            drainage_class="poorly_drained",
            texture="clay",
        )
        result = analyzer.analyze(poor_soil, good_climate, good_terrain)
        assert result.suitability_score < 50
        assert "soil_too_acidic" in result.limiting_factors
        assert "soil_too_shallow" in result.limiting_factors

    def test_poor_climate_reduces_score(
        self, analyzer, good_soil, good_terrain
    ):
        """Poor climate should reduce suitability score"""
        poor_climate = ClimateSummary(
            mean_temp_c=5,
            annual_precip_mm=150,
            frost_free_days=60,
            aridity_index=0.1,
            et0_mm=2000,
        )
        result = analyzer.analyze(good_soil, poor_climate, good_terrain)
        assert result.suitability_score < 60
        assert "climate_too_dry" in result.limiting_factors

    def test_steep_terrain_reduces_score(
        self, analyzer, good_soil, good_climate
    ):
        """Steep terrain should reduce suitability score"""
        steep_terrain = TerrainSummary(
            slope_pct=25.0,
            elevation_m=2000,
            capability_class="VI",
            erosion_risk="high",
        )
        result = analyzer.analyze(good_soil, good_climate, steep_terrain)
        assert result.suitability_score < 50
        assert result.land_use_recommendations[0] in [
            LandUseCategory.FORESTRY,
            LandUseCategory.CONSERVATION,
        ]

    def test_crop_suitability_scoring(
        self, analyzer, good_soil, good_climate, good_terrain
    ):
        """Should score all major crops"""
        result = analyzer.analyze(good_soil, good_climate, good_terrain)
        assert len(result.crop_suitabilities) == 6  # All 6 crops

        # Should be sorted by score descending
        scores = [cs.score for cs in result.crop_suitabilities]
        assert scores == sorted(scores, reverse=True)

    def test_wheat_suitability_specific(
        self, analyzer, good_soil, good_climate, good_terrain
    ):
        """Wheat should score well on good land"""
        result = analyzer.analyze(good_soil, good_climate, good_terrain)
        wheat = next(cs for cs in result.crop_suitabilities if cs.crop == CropType.WHEAT)
        assert wheat.score >= 70

    def test_rice_requires_water(
        self, analyzer, good_soil, good_terrain
    ):
        """Rice should score poorly in dry climate"""
        dry_climate = ClimateSummary(
            mean_temp_c=25,
            annual_precip_mm=300,  # Too dry for rice
            frost_free_days=200,
            aridity_index=0.3,
            et0_mm=1800,
        )
        result = analyzer.analyze(good_soil, dry_climate, good_terrain)
        rice = next(cs for cs in result.crop_suitabilities if cs.crop == CropType.RICE)
        assert rice.score < 50
        assert any("precipitation" in issue.lower() for issue in rice.limiting_factors)

    def test_improvement_recommendations(
        self, analyzer, good_climate, good_terrain
    ):
        """Should generate specific improvement recommendations"""
        acidic_soil = SoilSummary(
            ph=4.5,
            clay_pct=30,
            silt_pct=35,
            sand_pct=35,
            organic_matter_pct=1.5,
            depth_cm=80,
            ec_dsm=0.5,
            drainage_class="well_drained",
            texture="loam",
        )
        result = analyzer.analyze(acidic_soil, good_climate, good_terrain)
        assert any("lime" in rec.lower() for rec in result.improvement_recommendations)

    def test_error_handling(self, analyzer):
        """Should handle errors gracefully"""
        result = analyzer.analyze(None, None, None)
        assert result.suitability_score == 0.0
        assert result.land_use_recommendations == [LandUseCategory.CONSERVATION]
        assert len(result.limiting_factors) > 0

    def test_confidence_calculation(
        self, analyzer, good_soil, good_climate, good_terrain
    ):
        """Should calculate confidence"""
        result = analyzer.analyze(good_soil, good_climate, good_terrain)
        assert 0.0 <= result.confidence <= 1.0
        assert result.confidence >= 0.7

    def test_land_use_conservation_for_class_viii(
        self, analyzer, good_soil, good_climate
    ):
        """Class VIII should recommend conservation"""
        class_viii = TerrainSummary(
            slope_pct=40.0,
            elevation_m=3000,
            capability_class="VIII",
            erosion_risk="high",
        )
        result = analyzer.analyze(good_soil, good_climate, class_viii)
        assert result.land_use_recommendations[0] == LandUseCategory.CONSERVATION

    def test_weighted_scoring(self, analyzer, good_climate, good_terrain):
        """Should use correct weights (40% soil, 35% climate, 25% terrain)"""
        perfect_soil = SoilSummary(
            ph=6.5,
            clay_pct=25,
            silt_pct=40,
            sand_pct=35,
            organic_matter_pct=3.0,
            depth_cm=100,
            ec_dsm=0.5,
            drainage_class="well_drained",
            texture="loam",
        )
        poor_terrain = TerrainSummary(
            slope_pct=50.0,
            elevation_m=3000,
            capability_class="VIII",
            erosion_risk="high",
        )
        result = analyzer.analyze(perfect_soil, good_climate, poor_terrain)
        # Expected: 100*0.4 + 100*0.35 + 10*0.25 = 77.5
        assert 70 <= result.suitability_score <= 80

    def test_salinity_impact(self, analyzer, good_climate, good_terrain):
        """High salinity should severely reduce score"""
        saline_soil = SoilSummary(
            ph=7.0,
            clay_pct=30,
            silt_pct=35,
            sand_pct=35,
            organic_matter_pct=2.0,
            depth_cm=80,
            ec_dsm=8.0,  # High salinity
            drainage_class="well_drained",
            texture="loam",
        )
        result = analyzer.analyze(saline_soil, good_climate, good_terrain)
        assert "high_salinity" in result.limiting_factors
        assert any("leaching" in rec.lower() for rec in result.improvement_recommendations)

    def test_drought_tolerant_crops(
        self, analyzer, good_soil, good_terrain
    ):
        """Drought-tolerant crops should score better in dry climate"""
        dry_climate = ClimateSummary(
            mean_temp_c=20,
            annual_precip_mm=350,  # Semi-arid
            frost_free_days=180,
            aridity_index=0.4,
            et0_mm=1500,
        )
        result = analyzer.analyze(good_soil, dry_climate, good_terrain)

        barley = next(cs for cs in result.crop_suitabilities if cs.crop == CropType.BARLEY)
        rice = next(cs for cs in result.crop_suitabilities if cs.crop == CropType.RICE)
        assert barley.score > rice.score

    def test_metadata_included(
        self, analyzer, good_soil, good_climate, good_terrain
    ):
        """Should include component scores in metadata"""
        result = analyzer.analyze(good_soil, good_climate, good_terrain)
        assert "soil_score" in result.metadata
        assert "climate_score" in result.metadata
        assert "terrain_score" in result.metadata
'''

    create_file(
        PROJECT_ROOT / "engine" / "land" / "integration" / "tests" / "test_comprehensive_analyzer.py",
        test_code
    )

    # ================================================================
    # 3. Run tests
    # ================================================================
    print("\n[3/3] Running tests...")

    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "engine/land/integration/tests/test_comprehensive_analyzer.py",
         "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    output = result.stdout
    if len(output) > 3000:
        output = output[-3000:]
    print(output)

    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ Phase 2C COMPLETE - All tests passed")
        print("=" * 70)
    else:
        print("\n⚠️  Some tests failed - check output above")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())