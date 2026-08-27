"""
Tests for Soil Integrator
==========================
"""

import pytest

from engine.land.integration.models import (
    SalinityClass,
    SoilTexture,
)
from engine.land.integration.soil_integrator import SoilIntegrator


class TestSoilTextureClassification:
    """Test soil texture classification"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_classify_loam(self, integrator):
        """Loam: balanced texture"""
        texture = integrator.classify_texture(sand_pct=40, silt_pct=30, clay_pct=30)
        assert texture == SoilTexture.LOAM

    def test_classify_sand(self, integrator):
        """Sand: high sand content"""
        texture = integrator.classify_texture(sand_pct=90, silt_pct=5, clay_pct=5)
        assert texture == SoilTexture.SAND

    def test_classify_clay(self, integrator):
        """Clay: high clay content"""
        texture = integrator.classify_texture(sand_pct=20, silt_pct=30, clay_pct=50)
        assert texture == SoilTexture.CLAY

    def test_classify_silt_loam(self, integrator):
        """Silt loam: high silt content"""
        texture = integrator.classify_texture(sand_pct=20, silt_pct=60, clay_pct=20)
        assert texture == SoilTexture.SILT_LOAM


class TestVanGenuchtenEstimation:
    """Test van Genuchten parameter estimation"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_sand_parameters(self, integrator):
        """Sand should have high alpha and n"""
        params = integrator.estimate_van_genuchten(SoilTexture.SAND)
        assert params["alpha"] > 0.1
        assert params["n"] > 2.0

    def test_clay_parameters(self, integrator):
        """Clay should have low alpha and n"""
        params = integrator.estimate_van_genuchten(SoilTexture.CLAY)
        assert params["alpha"] < 0.05
        assert params["n"] < 1.5

    def test_theta_bounds(self, integrator):
        """Water content should be between 0 and 1"""
        for texture in SoilTexture:
            params = integrator.estimate_van_genuchten(texture)
            assert 0 <= params["theta_r"] < params["theta_s"] <= 1


class TestSoilProfileBuilding:
    """Test soil profile building"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_default_profile_has_6_layers(self, integrator):
        """Default profile should have 6 layers"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        assert len(profile.layers) == 6

    def test_default_profile_depths(self, integrator):
        """Layer depths should match SoilGrids standard"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        expected_depths = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200)]
        for i, layer in enumerate(profile.layers):
            assert layer.depth_min_cm == expected_depths[i][0]
            assert layer.depth_max_cm == expected_depths[i][1]

    def test_texture_sums_to_100(self, integrator):
        """Sand + silt + clay should sum to ~100"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        for layer in profile.layers:
            total = layer.sand_pct + layer.silt_pct + layer.clay_pct
            assert 99.5 <= total <= 100.5

    def test_total_depth_is_200(self, integrator):
        """Total depth should be 200cm"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        assert profile.total_depth_cm == 200


class TestAWCCalculation:
    """Test Available Water Capacity calculation"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_awc_positive(self, integrator):
        """AWC should be positive"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        awc = integrator.calculate_awc(profile)
        assert awc > 0

    def test_awc_reasonable_range(self, integrator):
        """AWC should be in reasonable range (50-300mm for 200cm profile)"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        awc = integrator.calculate_awc(profile)
        assert 50 <= awc <= 400


class TestSalinityClassification:
    """Test salinity classification"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_non_saline(self, integrator):
        """EC < 2 should be non-saline"""
        assert integrator.classify_salinity(1.0) == SalinityClass.NON_SALINE

    def test_slightly_saline(self, integrator):
        """EC 2-4 should be slightly saline"""
        assert integrator.classify_salinity(3.0) == SalinityClass.SLIGHTLY_SALINE

    def test_moderately_saline(self, integrator):
        """EC 4-8 should be moderately saline"""
        assert integrator.classify_salinity(6.0) == SalinityClass.MODERATELY_SALINE

    def test_strongly_saline(self, integrator):
        """EC 8-16 should be strongly saline"""
        assert integrator.classify_salinity(12.0) == SalinityClass.STRONGLY_SALINE

    def test_very_strongly_saline(self, integrator):
        """EC > 16 should be very strongly saline"""
        assert integrator.classify_salinity(20.0) == SalinityClass.VERY_STRONGLY_SALINE


class TestSoilHealth:
    """Test soil health calculation"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_health_score_range(self, integrator):
        """Health score should be 0-100"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        score = integrator.calculate_soil_health(profile)
        assert 0 <= score <= 100

    def test_good_soil_high_score(self, integrator):
        """Good soil should have high health score"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        # Set optimal conditions
        profile.layers[0].ph = 7.0
        profile.layers[0].organic_carbon_g_kg = 20.0
        profile.layers[0].ec_dsm = 0.5
        score = integrator.calculate_soil_health(profile)
        assert score >= 80


class TestSoilIntegration:
    """Test soil integration with land profile"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_integration_success(self, integrator):
        """Integration should succeed"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67,
            terrain_slope_deg=5.0,
            climate_zone="BWh"
        )
        assert result.success
        assert result.profile_id == "test-001"
        assert result.soil_profile is not None

    def test_integration_returns_soil_profile(self, integrator):
        """Integration should return complete soil profile"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67,
            terrain_slope_deg=5.0,
            climate_zone="BWh"
        )
        assert result.soil_profile is not None
        assert len(result.soil_profile.layers) == 6

    def test_integration_returns_suitable_crops(self, integrator):
        """Integration should return suitable crops"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67,
            terrain_slope_deg=5.0,
            climate_zone="BWh"
        )
        assert len(result.suitable_crops) > 0

    def test_integration_returns_recommendations(self, integrator):
        """Integration should return recommendations"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67,
            terrain_slope_deg=5.0,
            climate_zone="BWh"
        )
        assert len(result.recommendations) > 0

    def test_integration_time_reasonable(self, integrator):
        """Integration should complete in reasonable time (<1s)"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67,
            terrain_slope_deg=5.0,
            climate_zone="BWh"
        )
        assert result.integration_time_ms < 1000


class TestLimitationsIdentification:
    """Test limitations identification"""

    @pytest.fixture
    def integrator(self):
        return SoilIntegrator()

    def test_acidic_soil_limitation(self, integrator):
        """Acidic soil should be identified"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        profile.layers[0].ph = 5.0
        limitations = integrator._identify_limitations(profile, terrain_slope_deg=None)
        assert "acidic_soil" in limitations

    def test_salinity_limitation(self, integrator):
        """Saline soil should be identified"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        profile.layers[0].ec_dsm = 10.0
        profile.salinity_class = integrator.classify_salinity(10.0)
        limitations = integrator._identify_limitations(profile, terrain_slope_deg=None)
        assert "high_salinity" in limitations

    def test_erosion_risk_limitation(self, integrator):
        """Steep slope should identify erosion risk"""
        profile = integrator.build_default_profile(lat=32.65, lon=51.67)
        limitations = integrator._identify_limitations(profile, terrain_slope_deg=20.0)
        assert "erosion_risk" in limitations
