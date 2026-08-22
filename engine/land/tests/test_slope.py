"""Tests for Slope and Aspect Calculator"""

import pytest
import numpy as np
from engine.land.slope_aspect import SlopeAspectCalculator


class TestSlopeAspectCalculator:
    """تست‌های محاسبه‌گر شیب و جهت"""
    
    @pytest.fixture
    def calculator(self):
        """ایجاد محاسبه‌گر با وضوح 30 متر"""
        return SlopeAspectCalculator(resolution=30.0)
    
    @pytest.fixture
    def flat_dem(self):
        """DEM مسطح"""
        return np.full((10, 10), 1000.0)
    
    @pytest.fixture
    def sloped_dem(self):
        """DEM با شیب"""
        dem = np.zeros((10, 10))
        for i in range(10):
            dem[i, :] = 1000 + i * 30  # 30m elevation change per row
        return dem
    
    def test_flat_terrain(self, calculator, flat_dem):
        """تست زمین مسطح"""
        slope, aspect = calculator.calculate_slope_aspect(flat_dem)
        
        # Flat terrain should have zero slope
        assert np.allclose(slope, 0, atol=1e-6)
    
    def test_sloped_terrain(self, calculator, sloped_dem):
        """تست زمین شیب‌دار"""
        slope, aspect = calculator.calculate_slope_aspect(sloped_dem)
        
        # Should have non-zero slope
        assert np.mean(slope) > 0
        
        # Slope should be positive
        assert np.all(slope >= 0)
    
    def test_slope_to_percent(self, calculator):
        """تست تبدیل شیب به درصد"""
        slope_degrees = np.array([0, 15, 30, 45, 60])
        slope_percent = calculator.slope_to_percent(slope_degrees)
        
        # 45 degrees should be 100%
        assert np.isclose(slope_percent[3], 100, atol=1e-6)
        
        # 0 degrees should be 0%
        assert np.isclose(slope_percent[0], 0, atol=1e-6)
    
    def test_aspect_to_cardinal(self, calculator):
        """تست تبدیل جهت شیب به جهت‌های اصلی"""
        aspect_degrees = np.array([0, 45, 90, 135, 180, 225, 270, 315])
        cardinals = calculator.aspect_to_cardinal(aspect_degrees)
        
        expected = np.array(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        assert np.array_equal(cardinals, expected)
    
    def test_curvature(self, calculator, sloped_dem):
        """تست محاسبه انحنا"""
        profile_curv, plan_curv, total_curv = calculator.calculate_curvature(sloped_dem)
        
        # Should return arrays of same shape
        assert profile_curv.shape == sloped_dem.shape
        assert plan_curv.shape == sloped_dem.shape
        assert total_curv.shape == sloped_dem.shape
    
    def test_roughness_index(self, calculator, sloped_dem):
        """تست شاخص ناهمواری"""
        roughness = calculator.calculate_roughness_index(sloped_dem)
        
        # Should return array of same shape
        assert roughness.shape == sloped_dem.shape
        
        # Should be non-negative
        assert np.all(roughness >= 0)