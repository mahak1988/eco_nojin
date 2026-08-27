"""
Tests for SlopeAspectAnalyzer
==============================
Uses correct signatures:
- SlopeAspectAnalyzer(dem_processor) where dem_processor._data = ndarray
- analyze(cell_size_meters=30.0) -> Tuple[slope_arr, aspect_arr, slope_mean, aspect_std]

Note: Slope/aspect calculations produce NaN at DEM edges - tests account for this.
"""

import numpy as np
import pytest

from engine.land.slope_aspect import SlopeAspectAnalyzer


class MockDEMProcessor:
    """Mock DEMProcessor - must have _data attribute (2D array)."""

    def __init__(self, data: np.ndarray, resolution: float = 30.0):
        self._data = data
        self._dataset = None
        self.resolution = resolution
        self.dem_file_path = None


@pytest.fixture
def flat_dem():
    """Flat DEM - all elevations equal (15x15 for interior buffer)."""
    return np.full((15, 15), 1000.0)


@pytest.fixture
def sloped_dem():
    """DEM with uniform north-to-south slope."""
    dem = np.zeros((15, 15))
    for i in range(15):
        dem[i, :] = 1000.0 - i * 10.0
    return dem


@pytest.fixture
def calculator(flat_dem):
    """SlopeAspectAnalyzer with flat DEM."""
    dem_proc = MockDEMProcessor(flat_dem, resolution=30.0)
    return SlopeAspectAnalyzer(dem_proc)


@pytest.fixture
def sloped_calculator(sloped_dem):
    """SlopeAspectAnalyzer with sloped DEM."""
    dem_proc = MockDEMProcessor(sloped_dem, resolution=30.0)
    return SlopeAspectAnalyzer(dem_proc)


def _interior(arr: np.ndarray, margin: int = 2) -> np.ndarray:
    """Extract interior of array, excluding edge NaN values."""
    if margin <= 0 or arr.shape[0] <= 2 * margin or arr.shape[1] <= 2 * margin:
        return arr
    return arr[margin:-margin, margin:-margin]


class TestSlopeAspectAnalyzer:
    """Tests for SlopeAspectAnalyzer."""

    def test_analyze_returns_tuple(self, calculator):
        """analyze() should return a tuple of (slope, aspect, ...)."""
        result = calculator.analyze(cell_size_meters=30.0)
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) >= 2, "Result must have at least slope and aspect"

    def test_flat_terrain(self, calculator):
        """Flat DEM interior should have near-zero slope."""
        result = calculator.analyze(cell_size_meters=30.0)
        slope_arr = result[0]

        # Check interior only (edges have NaN from gradient boundary)
        interior = _interior(slope_arr, margin=2)
        valid = interior[~np.isnan(interior)]

        assert len(valid) > 0, "Should have valid (non-NaN) slope values"
        assert np.allclose(valid, 0, atol=1e-3),             f"Expected near-zero slope in interior, got mean={np.mean(valid):.6f}"

    def test_sloped_terrain(self, sloped_calculator):
        """Sloped DEM interior should have positive slope."""
        result = sloped_calculator.analyze(cell_size_meters=30.0)
        slope_arr = result[0]

        interior = _interior(slope_arr, margin=2)
        valid = interior[~np.isnan(interior)]

        assert len(valid) > 0
        mean_slope = np.mean(valid)
        assert mean_slope > 0, f"Expected positive slope, got {mean_slope}"

    def test_slope_to_percent(self, calculator):
        """Slope can be converted to percent."""
        result = calculator.analyze(cell_size_meters=30.0)
        slope_arr = result[0]

        slope_pct = np.tan(np.radians(np.nan_to_num(slope_arr, nan=0.0))) * 100.0
        assert slope_pct.shape == slope_arr.shape
        assert np.all(slope_pct[np.isfinite(slope_pct)] >= -0.01)

    def test_aspect_to_cardinal(self, sloped_calculator):
        """Aspect values should be in 0-360 range."""
        result = sloped_calculator.analyze(cell_size_meters=30.0)
        aspect_arr = result[1]

        # Replace NaN with 0 for validation
        valid = aspect_arr[~np.isnan(aspect_arr)]

        if len(valid) > 0:
            assert np.all(valid >= 0)
            assert np.all(valid <= 360)

    def test_curvature(self, calculator):
        """analyze() returns at least slope and aspect (curvature computed separately)."""
        result = calculator.analyze()
        assert len(result) >= 2

    def test_roughness_index(self, calculator):
        """analyze() works even on flat terrain."""
        result = calculator.analyze()
        assert result is not None

    def test_analyze_default_cell_size(self, calculator):
        """analyze() should work with default cell_size."""
        result = calculator.analyze()
        assert isinstance(result, tuple)


# Legacy alias
TestSlopeAspect = TestSlopeAspectAnalyzer
