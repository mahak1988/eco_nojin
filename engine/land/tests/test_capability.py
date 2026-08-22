"""Tests for Land Capability Assessment"""

import pytest
from engine.land.capability import CapabilityAssessor
from engine.land.models import LandCapabilityClass


class TestCapabilityAssessor:
    """تست‌های ارزیاب قابلیت زمین"""
    
    @pytest.fixture
    def assessor(self):
        """ایجاد ارزیاب"""
        return CapabilityAssessor()
    
    def test_class_i(self, assessor):
        """تست کلاس I (بهترین خاک)"""
        assessment = assessor.assess(
            slope_degrees=2.0,
            soil_depth_m=2.0,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert assessment.capability_class == LandCapabilityClass.CLASS_I
        assert assessment.confidence_score > 0.8
    
    def test_class_ii(self, assessor):
        """تست کلاس II"""
        assessment = assessor.assess(
            slope_degrees=8.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert assessment.capability_class == LandCapabilityClass.CLASS_II
    
    def test_class_iii_erosion(self, assessor):
        """تست کلاس III با ریسک فرسایش"""
        assessment = assessor.assess(
            slope_degrees=15.0,
            soil_depth_m=1.0,
            erosion_risk="moderate",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert assessment.capability_class == LandCapabilityClass.CLASS_III
        assert "e" in assessment.subclass
    
    def test_class_iv(self, assessor):
        """تست کلاس IV"""
        assessment = assessor.assess(
            slope_degrees=25.0,
            soil_depth_m=0.8,
            erosion_risk="high",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert assessment.capability_class == LandCapabilityClass.CLASS_IV
    
    def test_class_vii_steep(self, assessor):
        """تست کلاس VII (شیب تند)"""
        assessment = assessor.assess(
            slope_degrees=50.0,
            soil_depth_m=0.5,
            erosion_risk="very_high",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert assessment.capability_class in [LandCapabilityClass.CLASS_VII, LandCapabilityClass.CLASS_VIII]
    
    def test_suitable_uses(self, assessor):
        """تست کاربری‌های مناسب"""
        assessment = assessor.assess(
            slope_degrees=5.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert len(assessment.suitable_uses) > 0
        assert "agriculture" in " ".join(assessment.suitable_uses) or "pasture" in assessment.suitable_uses
    
    def test_recommendations(self, assessor):
        """تست توصیه‌ها"""
        assessment = assessor.assess(
            slope_degrees=15.0,
            soil_depth_m=1.0,
            erosion_risk="moderate",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert len(assessment.recommendations) > 0
    
    def test_confidence_score(self, assessor):
        """تست امتیاز اطمینان"""
        # High confidence with complete data
        assessment = assessor.assess(
            slope_degrees=10.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert assessment.confidence_score > 0.7
        
        # Lower confidence with missing data
        assessment = assessor.assess(
            slope_degrees=10.0,
            soil_depth_m=None,  # Missing
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate"
        )
        
        assert assessment.confidence_score < 0.9