"""
Tests for Comprehensive Land Analyzer (Fixed)
"""

import pytest

from engine.land.integration.comprehensive_analyzer import (
    ClimateSummary,
    ComprehensiveLandAnalyzer,
    CropType,
    LandUseCategory,
    SoilSummary,
    TerrainSummary,
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
        # With severe penalties: soil_score = 100 - 50 (salinity) - 40 (shallow) = 10
        # suitability = 10*0.4 + 100*0.35 + 100*0.25 = 64
        assert result.suitability_score < 70
        assert "severe_salinity" in result.limiting_factors
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
        # climate_score = 100 - 50 (severe drought) - 25 (cold) - 25 (short season) = 0
        # suitability = 100*0.4 + 0*0.35 + 100*0.25 = 65
        assert result.suitability_score < 70
        assert "severe_drought" in result.limiting_factors

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
        # terrain_score = 30 - 20 (erosion) - 15 (steep) = 0 (capped)
        # suitability = 100*0.4 + 100*0.35 + 0*0.25 = 75
        assert result.suitability_score < 80
        assert result.land_use_recommendations[0] in [
            LandUseCategory.FORESTRY,
            LandUseCategory.CONSERVATION,
            LandUseCategory.RAINFED_AGRICULTURE,
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
        assert rice.score <= 50  # Allow boundary case
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
        # Expected: 100*0.4 + 100*0.35 + 0*0.25 = 75
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
            ec_dsm=8.0,  # High salinity (>6.0 = severe)
            drainage_class="well_drained",
            texture="loam",
        )
        result = analyzer.analyze(saline_soil, good_climate, good_terrain)
        assert "severe_salinity" in result.limiting_factors  # EC > 6.0
        assert any("leaching" in rec.lower() or "salt-tolerant" in rec.lower()
                  for rec in result.improvement_recommendations)

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
