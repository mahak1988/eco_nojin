"""Tests for Terrain Analysis"""

import numpy as np
import pytest

from engine.land.models import TerrainType
from engine.land.terrain_analysis import TerrainAnalyzer


class TestTerrainAnalyzer:
    """تست‌های تحلیل‌گر توپوگرافی"""

    @pytest.fixture
    def analyzer(self):
        """ایجاد تحلیل‌گر با وضوح 30 متر"""
        return TerrainAnalyzer(resolution=30.0)

    @pytest.fixture
    def flat_dem(self):
        """DEM مسطح"""
        return np.full((10, 10), 1000.0)

    @pytest.fixture
    def rolling_dem(self):
        """DEM با توپوگرافی rolling"""
        x = np.linspace(0, 2*np.pi, 10)
        y = np.linspace(0, 2*np.pi, 10)
        X, Y = np.meshgrid(x, y)
        return 1000 + 50 * np.sin(X) * np.cos(Y)

    def test_analyze_flat(self, analyzer, flat_dem):
        """تست تحلیل زمین مسطح"""
        analysis = analyzer.analyze(flat_dem)

        assert analysis.terrain_type == TerrainType.FLAT
        assert analysis.slope_mean < 3
        assert analysis.elevation_mean == 1000.0

    def test_analyze_rolling(self, analyzer, rolling_dem):
        """تست تحلیل زمین rolling"""
        analysis = analyzer.analyze(rolling_dem)

        # Should not be flat
        assert analysis.terrain_type != TerrainType.FLAT

        # Should have reasonable values
        assert analysis.slope_mean > 0
        assert analysis.elevation_min < analysis.elevation_max

    def test_terrain_classification(self, analyzer):
        """تست طبقه‌بندی توپوگرافی"""
        # Flat (mean slope < 3°)
        flat_slopes = np.array([1, 2, 2.5])
        assert analyzer._classify_terrain(flat_slopes) == TerrainType.FLAT

        # Rolling (3° <= mean slope < 8°)
        rolling_slopes = np.array([5, 6, 7])
        assert analyzer._classify_terrain(rolling_slopes) == TerrainType.ROLLING

        # Hilly (8° <= mean slope < 20°)
        hilly_slopes = np.array([10, 12, 15])
        assert analyzer._classify_terrain(hilly_slopes) == TerrainType.HILLY

        # Mountainous (mean slope >= 20°)
        mountain_slopes = np.array([25, 30, 35])
        assert analyzer._classify_terrain(mountain_slopes) == TerrainType.MOUNTAINOUS

    def test_dominant_aspect(self, analyzer):
        """تست تعیین جهت شیب غالب"""
        # Import module-level function (not bound method)
        from engine.land.terrain_analysis import (
            _aspect_to_cardinal,
            _get_dominant_aspect,
        )

        # All aspects pointing south (180°)
        aspects = np.full(100, 180.0)

        # First verify helper functions work
        cardinal = _aspect_to_cardinal(180.0)
        assert cardinal == "S", f"180° should be 'S', got {cardinal!r}"

        # Now test dominant aspect
        dominant = _get_dominant_aspect(aspects)
        assert dominant == "S", f"Expected 'S', got {dominant!r}"

        # Mixed but mostly east (90°)
        aspects = np.array([90.0, 90.0, 90.0, 180.0, 270.0])
        dominant = _get_dominant_aspect(aspects)
        assert dominant == "E", f"Expected 'E', got {dominant!r}"

        # North-facing (0°)
        aspects = np.full(50, 0.0)
        dominant = _get_dominant_aspect(aspects)
        assert dominant == "N", f"Expected 'N', got {dominant!r}"
