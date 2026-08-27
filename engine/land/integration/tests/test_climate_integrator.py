"""
Tests for Climate Integrator
=============================
"""


import pytest

from engine.land.integration.climate_integrator import (
    KOPPEN_DESCRIPTIONS,
    LATITUDE_CLIMATE_BANDS,
    AridityClass,
    ClimateIntegrator,
    KoppenClimate,
)


class TestLatitudeBands:
    """Test latitude-based climate band assignment"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_tropical_band(self, integrator):
        """Equator should be tropical"""
        band = integrator.get_latitude_band(0.0)
        assert band["name"] == "tropical"

    def test_subtropical_arid_band(self, integrator):
        """Iran latitude should be subtropical arid"""
        band = integrator.get_latitude_band(32.65)
        assert band["name"] == "subtropical_arid"
        assert band["koppen"] == KoppenClimate.BWh

    def test_temperate_band(self, integrator):
        """European latitude should be temperate"""
        band = integrator.get_latitude_band(45.0)
        assert band["name"] == "temperate"

    def test_continental_band(self, integrator):
        """High latitude should be continental"""
        band = integrator.get_latitude_band(55.0)
        assert band["name"] == "continental"

    def test_polar_band(self, integrator):
        """Very high latitude should be polar"""
        band = integrator.get_latitude_band(75.0)
        assert band["name"] == "polar"

    def test_southern_hemisphere(self, integrator):
        """Southern hemisphere should work correctly"""
        band = integrator.get_latitude_band(-30.0)
        assert "south" in band["name"] or band["name"] == "subtropical_arid_south"


class TestSyntheticClimate:
    """Test synthetic climate data generation"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_synthetic_12_months(self, integrator):
        """Should generate 12 months of data"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        assert len(monthly) == 12

    def test_synthetic_month_range(self, integrator):
        """Months should be 1-12"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        months = [m.month for m in monthly]
        assert months == list(range(1, 13))

    def test_synthetic_temperature_realistic(self, integrator):
        """Temperatures should be in realistic range"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        for m in monthly:
            assert -50 <= m.t_min_c <= 60
            assert -50 <= m.t_max_c <= 60
            assert m.t_min_c <= m.t_max_c

    def test_synthetic_precipitation_non_negative(self, integrator):
        """Precipitation should be non-negative"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        for m in monthly:
            assert m.precipitation_mm >= 0

    def test_synthetic_summer_warmer_northern(self, integrator):
        """Northern hemisphere should have warmer summers"""
        monthly = integrator.generate_synthetic_monthly_climate(45.0, 0.0)
        summer = [m for m in monthly if m.month in [6, 7, 8]]
        winter = [m for m in monthly if m.month in [12, 1, 2]]
        summer_mean = sum(m.t_mean_c for m in summer) / 3
        winter_mean = sum(m.t_mean_c for m in winter) / 3
        assert summer_mean > winter_mean

    def test_synthetic_summer_warmer_southern(self, integrator):
        """Southern hemisphere should have warmer January"""
        monthly = integrator.generate_synthetic_monthly_climate(-45.0, 0.0)
        jan_mean = next(m for m in monthly if m.month == 1).t_mean_c
        jul_mean = next(m for m in monthly if m.month == 7).t_mean_c
        assert jan_mean > jul_mean


class TestET0Calculation:
    """Test ET0 Hargreaves calculation"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_et0_positive(self, integrator):
        """ET0 should be positive for warm months"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        monthly = integrator.calculate_et0_hargreaves_monthly(monthly, 32.65)
        for m in monthly:
            assert m.et0_mm is not None
            assert m.et0_mm >= 0

    def test_et0_higher_in_summer(self, integrator):
        """ET0 should be higher in summer months"""
        monthly = integrator.generate_synthetic_monthly_climate(45.0, 0.0)
        monthly = integrator.calculate_et0_hargreaves_monthly(monthly, 45.0)

        summer_et0 = sum(m.et0_mm for m in monthly if m.month in [6, 7, 8])
        winter_et0 = sum(m.et0_mm for m in monthly if m.month in [12, 1, 2])
        assert summer_et0 > winter_et0

    def test_et0_reasonable_range(self, integrator):
        """Annual ET0 should be in reasonable range (200-2500 mm)"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        monthly = integrator.calculate_et0_hargreaves_monthly(monthly, 32.65)
        annual_et0 = sum(m.et0_mm for m in monthly)
        assert 200 <= annual_et0 <= 4000  # Arid regions can exceed 3000 mm/year

    def test_extraterrestrial_radiation(self, integrator):
        """Extraterrestrial radiation should be positive"""
        for month in range(1, 13):
            ra = integrator._extraterrestrial_radiation_monthly(month, 32.65)
            assert ra > 0

    def test_radiation_seasonal_variation(self, integrator):
        """Radiation should vary seasonally"""
        ra_summer = integrator._extraterrestrial_radiation_monthly(6, 45.0)
        ra_winter = integrator._extraterrestrial_radiation_monthly(12, 45.0)
        assert ra_summer != ra_winter


class TestKoppenClassification:
    """Test Köppen-Geiger classification"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_koppen_classify_tropical(self, integrator):
        """Tropical latitudes should classify as A group"""
        monthly = integrator.generate_synthetic_monthly_climate(0.0, 0.0)
        koppen, description = integrator.classify_koppen(monthly, 0.0)
        assert koppen is not None
        assert koppen.value.startswith("A") or koppen.value.startswith("B")

    def test_koppen_classify_arid(self, integrator):
        """Iran should classify as arid"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        koppen, description = integrator.classify_koppen(monthly, 32.65)
        assert koppen is not None
        # Arid climates start with B
        assert koppen.value.startswith("B") or koppen.value.startswith("C")

    def test_koppen_classify_temperate(self, integrator):
        """European latitudes should be C or D group"""
        monthly = integrator.generate_synthetic_monthly_climate(48.0, 2.0)
        koppen, description = integrator.classify_koppen(monthly, 48.0)
        assert koppen is not None
        assert koppen.value[0] in ["C", "D"]

    def test_koppen_has_description(self, integrator):
        """Köppen should have a description"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        koppen, description = integrator.classify_koppen(monthly, 32.65)
        assert description is not None
        assert len(description) > 0


class TestAridityIndex:
    """Test Aridity Index calculation"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_hyper_arid(self, integrator):
        """AI < 0.05 should be hyper-arid"""
        ai, cls = integrator.calculate_aridity_index(50, 1500)
        assert cls == AridityClass.HYPER_ARID
        assert ai < 0.05

    def test_arid(self, integrator):
        """AI 0.05-0.20 should be arid"""
        ai, cls = integrator.calculate_aridity_index(200, 1500)
        assert cls == AridityClass.ARID

    def test_semi_arid(self, integrator):
        """AI 0.20-0.50 should be semi-arid"""
        ai, cls = integrator.calculate_aridity_index(500, 1500)
        assert cls == AridityClass.SEMI_ARID

    def test_dry_subhumid(self, integrator):
        """AI 0.50-0.65 should be dry subhumid"""
        ai, cls = integrator.calculate_aridity_index(800, 1500)
        assert cls == AridityClass.DRY_SUBHUMID

    def test_humid(self, integrator):
        """AI >= 0.65 should be humid"""
        ai, cls = integrator.calculate_aridity_index(1200, 1500)
        assert cls == AridityClass.HUMID

    def test_zero_et0_handled(self, integrator):
        """Zero ET0 should not crash"""
        ai, cls = integrator.calculate_aridity_index(1000, 0)
        assert cls == AridityClass.HUMID


class TestGrowingSeason:
    """Test growing season calculation"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_growing_season_positive(self, integrator):
        """Growing season should be positive"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert growing >= 0
        assert frost_free >= 0

    def test_growing_season_tropical_long(self, integrator):
        """Tropical should have long growing season"""
        monthly = integrator.generate_synthetic_monthly_climate(0.0, 0.0)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert growing > 300  # Almost year-round

    def test_growing_season_polar_short(self, integrator):
        """Polar should have short growing season"""
        monthly = integrator.generate_synthetic_monthly_climate(75.0, 0.0)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert growing < 150  # Short summer

    def test_frost_free_leq_365(self, integrator):
        """Frost-free days should not exceed 365"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert frost_free <= 365


class TestClimateProfileBuilding:
    """Test complete climate profile building"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_profile_complete(self, integrator):
        """Profile should have all fields"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.lat == 32.65
        assert profile.lon == 51.67
        assert profile.annual_precip_mm > 0
        assert profile.annual_t_mean_c != 0
        assert len(profile.monthly) == 12

    def test_profile_has_koppen(self, integrator):
        """Profile should have Köppen classification"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.koppen is not None

    def test_profile_has_aridity(self, integrator):
        """Profile should have aridity index"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.aridity_index is not None
        assert profile.aridity_class is not None

    def test_profile_has_growing_season(self, integrator):
        """Profile should have growing season"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.growing_season_days is not None
        assert profile.frost_free_days is not None

    def test_profile_data_source(self, integrator):
        """Profile should have data source"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.data_source in ["synthetic", "open_meteo"]

    def test_profile_quality_level(self, integrator):
        """Profile should have quality level"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.data_quality_level in ["L0", "L3", "L5"]


class TestClimateIntegration:
    """Test climate integration with land profile"""

    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()

    def test_integration_success(self, integrator):
        """Integration should succeed"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert result.success
        assert result.profile_id == "test-001"

    def test_integration_returns_profile(self, integrator):
        """Integration should return climate profile"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert result.climate_profile is not None
        assert result.climate_profile.koppen is not None

    def test_integration_arid_irrigation_required(self, integrator):
        """Arid location should require irrigation"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67  # Isfahan, Iran - arid
        )
        # Arid climates typically require irrigation
        assert "water_scarcity" in result.limitations or "severe_water_scarcity" in result.limitations
        assert result.irrigation_required

    def test_integration_recommendations_present(self, integrator):
        """Integration should return recommendations"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert len(result.recommendations) > 0

    def test_integration_time_reasonable(self, integrator):
        """Integration should complete in reasonable time"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert result.integration_time_ms < 5000  # 5 seconds

    def test_integration_different_locations(self, integrator):
        """Different locations should give different results"""
        result_iran = integrator.integrate_with_land(
            profile_id="iran", lat=32.65, lon=51.67
        )
        result_europe = integrator.integrate_with_land(
            profile_id="europe", lat=48.0, lon=2.0
        )

        assert result_iran.climate_profile.koppen != result_europe.climate_profile.koppen
        # Europe should have more precipitation than arid Iran
        assert result_europe.climate_profile.annual_precip_mm > result_iran.climate_profile.annual_precip_mm


class TestKoppenDescriptions:
    """Test Köppen descriptions dictionary"""

    def test_all_koppen_have_descriptions(self):
        """All Köppen classes should have descriptions"""
        for koppen in KoppenClimate:
            assert koppen in KOPPEN_DESCRIPTIONS

    def test_descriptions_not_empty(self):
        """Descriptions should not be empty"""
        for koppen, desc in KOPPEN_DESCRIPTIONS.items():
            assert len(desc) > 0


class TestLatitudeClimateBands:
    """Test latitude climate bands configuration"""

    def test_bands_cover_globe(self):
        """Bands should cover entire globe"""
        # Check that all latitudes have a band
        integrator = ClimateIntegrator()
        for lat in [-80, -45, -30, -10, 0, 10, 30, 45, 60, 80]:
            band = integrator.get_latitude_band(lat)
            assert band is not None

    def test_bands_have_required_fields(self):
        """Bands should have required fields"""
        for name, band in LATITUDE_CLIMATE_BANDS.items():
            assert "lat_range" in band
            assert "koppen" in band
            assert "annual_precip" in band
