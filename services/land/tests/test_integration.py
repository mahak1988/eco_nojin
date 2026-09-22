"""Integration tests for Land Intelligence Service with real engine and database."""

import numpy as np
import pytest

from adapters.engine_adapter import EngineAdapter
from adapters.hydroma_adapter import HydromaAdapter
from engine.land.models import (
    CapabilityAssessment,
    DrainageAnalysis,
    LandCapabilityClass,
    TerrainAnalysis,
    TerrainType,
)
from services.land.service import LandService


@pytest.fixture
def land_service():
    """LandService with real engine adapter."""
    return LandService(engine=EngineAdapter())


@pytest.fixture
def sample_dem():
    """Sample DEM with gentle slope."""
    dem = np.zeros((10, 10), dtype=float)
    for i in range(10):
        dem[i, :] = 1000 + i * 10
    return dem


@pytest.fixture
def rolling_dem():
    """Sample DEM with rolling terrain."""
    x = np.linspace(0, 2 * np.pi, 10)
    y = np.linspace(0, 2 * np.pi, 10)
    X, Y = np.meshgrid(x, y)
    return 1000 + 50 * np.sin(X) * np.cos(Y)


class TestLandServiceEngineIntegration:
    """تست‌های یکپارچگی سرویس زمین با موتور واقعی"""

    def test_create_and_analyze_terrain(self, land_service, sample_dem):
        """تست ایجاد پروفایل و تحلیل توپوگرافی با موتور واقعی"""
        profile = land_service.create_profile(
            name="مزرعه یکپارچگی",
            location_lat=32.65,
            location_lon=51.67,
            area_ha=10.0,
        )

        analysis = land_service.analyze_terrain(
            profile_id=profile.id,
            dem_array=sample_dem,
            resolution=30.0,
        )

        assert isinstance(analysis, TerrainAnalysis)
        assert analysis.profile_id == profile.id
        assert analysis.terrain_type is not None
        assert analysis.slope_mean is not None
        assert analysis.elevation_mean == 1000.0 + 4.5 * 10

        updated = land_service.get_profile(profile.id)
        assert updated.terrain_analysis is not None
        assert updated.terrain_analysis.profile_id == profile.id

    def test_analyze_rolling_terrain(self, land_service, rolling_dem):
        """تست تحلیل زمین rolling"""
        profile = land_service.create_profile(
            name="Rolling Test",
            location_lat=0,
            location_lon=0,
        )

        analysis = land_service.analyze_terrain(
            profile_id=profile.id,
            dem_array=rolling_dem,
            resolution=30.0,
        )

        assert isinstance(analysis, TerrainAnalysis)
        assert analysis.terrain_type != TerrainType.FLAT
        assert analysis.slope_mean > 0

    def test_analyze_drainage_with_real_engine(self, land_service, sample_dem):
        """تست تحلیل زهکشی با موتور واقعی"""
        profile = land_service.create_profile(
            name="زهکشی یکپارچگی",
            location_lat=0,
            location_lon=0,
        )

        analysis = land_service.analyze_drainage(
            profile_id=profile.id,
            dem_array=sample_dem,
            resolution=30.0,
            area_km2=1.0,
        )

        assert isinstance(analysis, DrainageAnalysis)
        assert analysis.profile_id == profile.id
        assert analysis.drainage_pattern is not None

        updated = land_service.get_profile(profile.id)
        assert updated.drainage_analysis is not None

    def test_assess_capability_with_real_engine(self, land_service):
        """تست ارزیابی قابلیت با موتور واقعی"""
        profile = land_service.create_profile(
            name="قابلیت یکپارچگی",
            location_lat=0,
            location_lon=0,
        )

        assessment = land_service.assess_capability(
            profile_id=profile.id,
            slope_degrees=10.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate",
        )

        assert isinstance(assessment, CapabilityAssessment)
        assert assessment.profile_id == profile.id
        assert assessment.capability_class is not None
        assert assessment.confidence_score > 0
        assert len(assessment.suitable_uses) > 0
        assert len(assessment.recommendations) > 0

        updated = land_service.get_profile(profile.id)
        assert updated.capability_assessment is not None

    def test_full_land_analysis_workflow(self, land_service, sample_dem):
        """تست گردش کار کامل تحلیل زمین"""
        profile = land_service.create_profile(
            name="گردش کار کامل",
            location_lat=32.65,
            location_lon=51.67,
            area_ha=10.0,
        )

        terrain = land_service.analyze_terrain(profile.id, sample_dem, resolution=30.0)
        drainage = land_service.analyze_drainage(
            profile.id, sample_dem, resolution=30.0, area_km2=1.0
        )
        capability = land_service.assess_capability(
            profile_id=profile.id,
            slope_degrees=8.0,
            soil_depth_m=1.2,
            erosion_risk="moderate",
        )

        assert isinstance(terrain, TerrainAnalysis)
        assert isinstance(drainage, DrainageAnalysis)
        assert isinstance(capability, CapabilityAssessment)

        updated = land_service.get_profile(profile.id)
        assert updated.terrain_analysis is not None
        assert updated.drainage_analysis is not None
        assert updated.capability_assessment is not None

    def test_profile_not_found_errors(self, land_service, sample_dem):
        """تست خطاهای پروفایل یافت نشد"""
        with pytest.raises(ValueError, match="Profile not found"):
            land_service.analyze_terrain("non-existent", sample_dem, resolution=30.0)

        with pytest.raises(ValueError, match="Profile not found"):
            land_service.analyze_drainage("non-existent", sample_dem, resolution=30.0)

        with pytest.raises(ValueError, match="Profile not found"):
            land_service.assess_capability("non-existent", slope_degrees=10.0)

    def test_capability_class_mapping(self, land_service):
        """تست نگاشت صحیح کلاس‌های قابلیت اراضی"""
        test_cases = [
            (2.0, LandCapabilityClass.CLASS_I),
            (8.0, LandCapabilityClass.CLASS_II),
            (15.0, LandCapabilityClass.CLASS_III),
            (25.0, LandCapabilityClass.CLASS_III),
            (35.0, LandCapabilityClass.CLASS_IV),
            (50.0, LandCapabilityClass.CLASS_VII),
        ]

        for slope, expected_class in test_cases:
            profile = land_service.create_profile(
                name=f"test_{slope}", location_lat=0, location_lon=0
            )
            erosion = "very_high" if slope >= 50 else "low"
            assessment = land_service.assess_capability(
                profile_id=profile.id,
                slope_degrees=slope,
                soil_depth_m=1.5,
                erosion_risk=erosion,
            )
            assert assessment.capability_class == expected_class, (
                f"Slope {slope} should map to {expected_class}, got {assessment.capability_class}"
            )

    def test_arid_climate_limitation(self, land_service):
        """تست محدودیت اقلیم خشک"""
        profile = land_service.create_profile(name="خشک", location_lat=0, location_lon=0)
        assessment = land_service.assess_capability(
            profile_id=profile.id,
            slope_degrees=2.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="arid",
        )

        assert "water_scarcity" in assessment.limiting_factors
        assert assessment.subclass == "c"


class TestHydromaAdapterIntegration:
    """تست‌های یکپارچگی آداپتور Hydroma"""

    @pytest.fixture
    def hydroma_adapter(self):
        return HydromaAdapter()

    def test_analyze_soil_returns_model(self, hydroma_adapter):
        """تست تحلیل خاک بازگرداندن مدل Pydantic"""
        result = hydroma_adapter.analyze_soil({"ec": 6.5})
        assert isinstance(result, type(hydroma_adapter).analyze_soil.__annotations__["return"])

    def test_analyze_climate_returns_model(self, hydroma_adapter):
        """تست تحلیل اقلیم بازگرداندن مدل Pydantic"""
        result = hydroma_adapter.analyze_climate(
            {"temp_mean_c": 25.0, "t_min_c": 20.0, "t_max_c": 30.0}
        )
        assert result.estimated_et0 >= 0

    def test_analyze_watershed_returns_model(self, hydroma_adapter):
        """تست تحلیل حوضه بازگرداندن مدل Pydantic"""
        result = hydroma_adapter.analyze_watershed(15.0, 5000.0, 50.0)
        assert result.design_proposal is not None

    def test_analyze_groundwater_returns_model(self, hydroma_adapter):
        """تست تحلیل آبخوان بازگرداندن مدل Pydantic"""
        result = hydroma_adapter.analyze_groundwater({"estimated_water_table_depth_m": 12.0})
        assert result.estimated_depth_m == 12.0
        assert result.quality_class == "Fresh"
