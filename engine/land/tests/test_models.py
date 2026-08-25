"""Tests for Land Intelligence models"""

import pytest
from engine.land.models import (
    LandProfile,
    TerrainAnalysis,
    TerrainType,
    DrainageAnalysis,
    DrainagePattern,
    CapabilityAssessment,
    LandCapabilityClass,
    SlopeAspectResult,
)
from datetime import datetime


class TestSlopeAspectResult:
    """تست‌های SlopeAspectResult"""
    
    def test_valid_slope_aspect(self):
        """تست شیب و جهت معتبر"""
        result = SlopeAspectResult(
            slope_degrees=15.5,
            slope_percent=27.7,
            aspect_degrees=180.0,
            aspect_cardinal="S"
        )
        
        assert result.slope_degrees == 15.5
        assert result.slope_percent == 27.7
        assert result.aspect_degrees == 180.0
        assert result.aspect_cardinal == "S"
    
    def test_slope_bounds(self):
        """تست محدوده شیب"""
        # Valid
        SlopeAspectResult(slope_degrees=0, slope_percent=0, aspect_degrees=0, aspect_cardinal="N")
        SlopeAspectResult(slope_degrees=90, slope_percent=10000, aspect_degrees=360, aspect_cardinal="N")
        
        # Invalid
        with pytest.raises(ValueError):
            SlopeAspectResult(slope_degrees=-1, slope_percent=0, aspect_degrees=0, aspect_cardinal="N")
        
        with pytest.raises(ValueError):
            SlopeAspectResult(slope_degrees=91, slope_percent=0, aspect_degrees=0, aspect_cardinal="N")
        
        with pytest.raises(ValueError):
            SlopeAspectResult(slope_degrees=0, slope_percent=0, aspect_degrees=361, aspect_cardinal="N")


class TestTerrainAnalysis:
    """تست‌های TerrainAnalysis"""
    
    def test_valid_terrain_analysis(self):
        """تست تحلیل توپوگرافی معتبر"""
        analysis = TerrainAnalysis(
            profile_id="test-profile",
            terrain_type=TerrainType.ROLLING,
            elevation_min=1200.0,
            elevation_max=1350.0,
            elevation_mean=1275.0,
            slope_mean=12.5,
            slope_max=25.0,
            aspect_dominant="S",
            roughness_index=0.15,
            curvature_mean=-0.02
        )
        
        assert analysis.terrain_type == TerrainType.ROLLING
        assert analysis.elevation_mean == 1275.0
        assert analysis.slope_mean == 12.5
    
    def test_terrain_types(self):
        """تست انواع توپوگرافی"""
        for terrain_type in TerrainType:
            analysis = TerrainAnalysis(
                profile_id="test",
                terrain_type=terrain_type,
                elevation_min=0,
                elevation_max=100,
                elevation_mean=50,
                slope_mean=10,
                slope_max=20,
                aspect_dominant="N",
                roughness_index=0.1,
                curvature_mean=0
            )
            assert analysis.terrain_type == terrain_type


class TestDrainageAnalysis:
    """تست‌های DrainageAnalysis"""
    
    def test_valid_drainage_analysis(self):
        """تست تحلیل زهکشی معتبر"""
        analysis = DrainageAnalysis(
            profile_id="test-profile",
            drainage_pattern=DrainagePattern.DENDRITIC,
            drainage_density=2.5,
            stream_order=3,
            watershed_area_km2=15.5,
            time_of_concentration_hours=4.2
        )
        
        assert analysis.drainage_pattern == DrainagePattern.DENDRITIC
        assert analysis.drainage_density == 2.5
        assert analysis.watershed_area_km2 == 15.5


class TestCapabilityAssessment:
    """تست‌های CapabilityAssessment"""
    
    def test_valid_capability_assessment(self):
        """تست ارزیابی قابلیت معتبر"""
        assessment = CapabilityAssessment(
            profile_id="test-profile",
            capability_class=LandCapabilityClass.CLASS_III,
            subclass="e",
            limiting_factors=["slope", "erosion_risk"],
            suitable_uses=["rainfed_agriculture", "pasture"],
            constraints={"slope_limitation": "moderate"},
            recommendations=["Use contour farming"],
            confidence_score=0.85,
            assessed_by="automated_system"
        )
        
        assert assessment.capability_class == LandCapabilityClass.CLASS_III
        assert assessment.subclass == "e"
        assert "slope" in assessment.limiting_factors
        assert assessment.confidence_score == 0.85
    
    def test_all_capability_classes(self):
        """تست تمام کلاس‌های قابلیت"""
        for capability_class in LandCapabilityClass:
            assessment = CapabilityAssessment(
                profile_id="test",
                capability_class=capability_class,
                limiting_factors=[],
                suitable_uses=[],
                constraints={},
                recommendations=[],
                confidence_score=0.8
            )
            assert assessment.capability_class == capability_class


class TestLandProfile:
    """تست‌های LandProfile"""
    
    def test_valid_land_profile(self):
        """تست پروفایل زمین معتبر"""
        profile = LandProfile(
            id="test-profile",
            name="مزرعه نمونه",
            description="زمین کشاورزی ۱۰ هکتاری",
            location_lat=32.65,
            location_lon=51.67,
            area_hectares=10.0,
            dem_source="SRTM_30m",
            dem_resolution_m=30.0
        )
        
        assert profile.id == "test-profile"
        assert profile.name == "مزرعه نمونه"
        assert profile.location_lat == 32.65
        assert profile.location_lon == 51.67
    
    def test_location_bounds(self):
        """تست محدوده مختصات"""
        # Valid
        LandProfile(id="test", name="test", location_lat=0, location_lon=0)
        LandProfile(id="test", name="test", location_lat=90, location_lon=180)
        LandProfile(id="test", name="test", location_lat=-90, location_lon=-180)
        
        # Invalid
        with pytest.raises(ValueError):
            LandProfile(id="test", name="test", location_lat=91, location_lon=0)
        
        with pytest.raises(ValueError):
            LandProfile(id="test", name="test", location_lat=0, location_lon=181)
