"""Unit tests for Land Intelligence models"""

import pytest

from engine.land.models import (
    CapabilityAssessment,
    LandCapabilityClass,
    LandProfile,
    TerrainAnalysis,
    TerrainType,
)


class TestLandModels:
    """تست‌های واحد مدل‌های زمین"""

    def test_land_profile_validation(self):
        """تست اعتبارسنجی پروفایل"""
        # Valid
        profile = LandProfile(id="test", name="تست", location_lat=32.65, location_lon=51.67)
        assert profile.name == "تست"

        # Invalid latitude
        with pytest.raises(ValueError):
            LandProfile(id="test", name="تست", location_lat=91, location_lon=0)

        # Invalid longitude
        with pytest.raises(ValueError):
            LandProfile(id="test", name="تست", location_lat=0, location_lon=181)

    def test_terrain_analysis_Integerization(self):
        """تست سریال‌سازی تحلیل توپوگرافی"""
        analysis = TerrainAnalysis(
            profile_id="test",
            terrain_type=TerrainType.ROLLING,
            elevation_min=1000,
            elevation_max=1100,
            elevation_mean=1050,
            slope_mean=10,
            slope_max=20,
            aspect_dominant="S",
            roughness_index=0.1,
            curvature_mean=0,
            data_source="modelled",
            model="terrain_analysis",
        )

        # Serialize
        data = analysis.model_dump()
        assert data["terrain_type"] == TerrainType.ROLLING
        assert data["elevation_mean"] == 1050

        # DeIntegerize
        # `data` already carries data_source and model, since model_dump() now
        # includes them. Passing them again is a duplicate keyword and raises
        # TypeError, so they are restored from the dump alone.
        restored = TerrainAnalysis(**data)
        assert restored.terrain_type == analysis.terrain_type
        assert restored.elevation_mean == analysis.elevation_mean
        assert restored.data_source == analysis.data_source
        assert restored.model == analysis.model

    def test_capability_assessment_recommendations(self):
        """تست توصیه‌های ارزیابی قابلیت"""
        assessment = CapabilityAssessment(
            profile_id="test",
            capability_class=LandCapabilityClass.CLASS_III,
            subclass="e",
            limiting_factors=["slope", "erosion_risk"],
            suitable_uses=["rainfed_agriculture"],
            constraints={},
            recommendations=["Use contour farming"],
            confidence_score=0.85,
        )

        assert len(assessment.recommendations) > 0
        assert "contour" in assessment.recommendations[0].lower()
