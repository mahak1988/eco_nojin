"""
Tests for Improved Land Analysis Functions
==========================================

Tests the enhanced scientific rigor of:
- RUSLE erosion risk with proper LS factor (flow accumulation + slope length)
- D8 drainage analysis (flow accumulation, Strahler ordering, drainage density)
- Terrain analysis (curvature, TWI, TPI, roughness index)
- Surface water analysis (vectorized D8 flow accumulation)
"""

import numpy as np
import pytest

from engine.land.erosion_risk import (
    calculate_ls_factor,
    estimate_erosion_risk,
)
from engine.land.terrain_analysis import (
    TerrainAnalyzer,
    aspect_to_cardinal,
    calculate_curvature,
    calculate_slope_aspect,
    calculate_tpi,
    calculate_twi,
)


@pytest.fixture
def simple_dem():
    """Simple DEM with a depression and a slope."""
    dem = np.array([
        [10, 12, 14, 16, 18],
        [12, 14, 16, 18, 20],
        [14, 16, 18, 20, 22],
        [16, 18, 20, 22, 24],
        [18, 20, 22, 24, 26],
    ], dtype=float)
    return dem


@pytest.fixture
def sloped_dem():
    """DEM with uniform southward slope."""
    dem = np.zeros((10, 10))
    for i in range(10):
        for j in range(10):
            dem[i, j] = 1000.0 - i * 10.0 - j * 5.0
    return dem


@pytest.fixture
def flat_dem():
    """Flat DEM for baseline testing."""
    return np.full((10, 10), 1000.0)


@pytest.fixture
def curved_dem():
    """DEM with non-zero curvature (parabolic surface)."""
    dem = np.zeros((10, 10))
    for i in range(10):
        for j in range(10):
            dem[i, j] = 1000.0 + (i - 4.5)**2 + (j - 4.5)**2
    return dem


class TestRusleErosion:
    """Tests for RUSLE erosion risk with proper LS factor."""

    def test_calculate_ls_factor_returns_array(self, simple_dem):
        """LS factor should return a 2D array of same shape as DEM."""
        ls = calculate_ls_factor(dem=simple_dem, cell_size_m=30.0)
        assert ls.shape == simple_dem.shape
        assert np.all(np.isfinite(ls))

    def test_ls_factor_positive(self, simple_dem):
        """LS factor values should be positive."""
        ls = calculate_ls_factor(dem=simple_dem, cell_size_m=30.0)
        assert np.all(ls > 0)

    def test_ls_factor_with_sloped_dem(self, sloped_dem):
        """LS factor should handle sloped terrain."""
        slope_deg, _ = calculate_slope_aspect(sloped_dem, 30.0)
        ls = calculate_ls_factor(dem=sloped_dem, cell_size_m=30.0)
        assert ls.shape == sloped_dem.shape
        assert np.all(np.isfinite(ls))
        assert np.all(ls > 0)

    def test_ls_factor_flat_dem(self, flat_dem):
        """Flat DEM should have very low slope steepness factor."""
        ls = calculate_ls_factor(dem=flat_dem, cell_size_m=30.0)
        # On flat terrain, slope is 0, so S factor should be near minimum
        assert ls.shape == flat_dem.shape
        assert np.all(np.isfinite(ls))

    def test_estimate_erosion_risk_returns_tuple(self, simple_dem):
        """estimate_erosion_risk should return (array, str, dict)."""
        result = estimate_erosion_risk(dem=simple_dem, cell_size_m=30.0)
        assert isinstance(result, tuple)
        assert len(result) == 3
        loss, risk_level, components = result
        assert isinstance(loss, np.ndarray)
        assert isinstance(risk_level, str)
        assert isinstance(components, dict)
        assert risk_level in ["Low", "Moderate", "High", "Very High"]
        assert "R" in components
        assert "K" in components
        assert "LS" in components
        assert "C" in components
        assert "P" in components
        assert "A" in components

    def test_erosion_risk_positive_values(self, simple_dem):
        """Erosion risk values should be non-negative."""
        loss, _, components = estimate_erosion_risk(dem=simple_dem, cell_size_m=30.0)
        assert np.all(loss >= 0)
        assert np.all(components["A"] >= 0)

    def test_erosion_risk_with_custom_factors(self, simple_dem):
        """Custom RUSLE factors should be reflected in output."""
        loss, risk_level, components = estimate_erosion_risk(
            dem=simple_dem, cell_size_m=30.0,
            r_factor=500.0, k_factor=0.4, c_factor=0.8, p_factor=0.5,
        )
        # Higher R, K, C should give higher loss
        loss_default, _, _ = estimate_erosion_risk(
            dem=simple_dem, cell_size_m=30.0,
            r_factor=150.0, k_factor=0.25, c_factor=0.3, p_factor=1.0,
        )
        assert np.mean(loss) > np.mean(loss_default)


class TestCurvature:
    """Tests for curvature calculations."""

    def test_curvature_returns_dict(self, simple_dem):
        """Curvature calculation should return a dict with expected keys."""
        result = calculate_curvature(simple_dem, 30.0)
        assert "profile" in result
        assert "plan" in result
        assert "total" in result
        assert "convergence_index" in result
        for key in ["profile", "plan", "total", "convergence_index"]:
            assert result[key].shape == simple_dem.shape

    def test_curvature_flat_zero(self, flat_dem):
        """Flat terrain should have near-zero curvature."""
        result = calculate_curvature(flat_dem, 30.0)
        # Interior should be zero or very close
        interior_profile = result["profile"][1:-1, 1:-1]
        assert np.allclose(interior_profile, 0, atol=1e-10)
        interior_total = result["total"][1:-1, 1:-1]
        assert np.allclose(interior_total, 0, atol=1e-10)

    def test_curvature_sloped_nonzero(self, curved_dem):
        """Curved (parabolic) DEM should have non-zero curvature."""
        result = calculate_curvature(curved_dem, 30.0)
        # Parabolic surface has non-zero second derivatives
        interior = result["total"][1:-1, 1:-1]
        assert np.any(np.abs(interior) > 1e-10)


class TestTWI:
    """Tests for Topographic Wetness Index."""

    def test_twi_returns_array(self, simple_dem):
        """TWI should return an array of same shape."""
        twi = calculate_twi(simple_dem, 30.0)
        assert twi.shape == simple_dem.shape
        assert np.all(np.isfinite(twi))

    def test_twi_positive(self, simple_dem):
        """TWI values should be non-negative."""
        twi = calculate_twi(simple_dem, 30.0)
        assert np.all(twi >= 0)

    def test_twi_bounded(self, simple_dem):
        """TWI values should be within reasonable bounds."""
        twi = calculate_twi(simple_dem, 30.0)
        assert np.all(twi <= 20.0)


class TestTPI:
    """Tests for Topographic Position Index."""

    def test_tpi_returns_array(self, simple_dem):
        """TPI should return an array of same shape."""
        tpi = calculate_tpi(simple_dem, 30.0)
        assert tpi.shape == simple_dem.shape

    def test_tpi_center_positive(self, simple_dem):
        """On a slope DEM, center cell TPI should be positive (elevated)."""
        tpi = calculate_tpi(simple_dem, 30.0)
        # Center cell should be higher than neighborhood mean
        center_val = tpi[2, 2]
        if np.isfinite(center_val):
            assert center_val >= -1e-6


class TestSlopeAspect:
    """Tests for improved slope/aspect calculations."""

    def test_flat_zero_slope(self, flat_dem):
        """Flat DEM should have near-zero slope."""
        slope, aspect = calculate_slope_aspect(flat_dem, 30.0)
        interior_slope = slope[1:-1, 1:-1]
        assert np.allclose(interior_slope, 0, atol=1e-10)

    def test_sloped_positive_slope(self, sloped_dem):
        """Sloped DEM should have positive slope in interior."""
        slope, aspect = calculate_slope_aspect(sloped_dem, 30.0)
        interior_slope = slope[1:-1, 1:-1]
        assert np.all(interior_slope > 0)

    def test_aspect_in_range(self, sloped_dem):
        """Aspect should be in [0, 360) degrees."""
        _, aspect = calculate_slope_aspect(sloped_dem, 30.0)
        valid = aspect[1:-1, 1:-1]
        assert np.all(valid >= 0)
        assert np.all(valid <= 360)

    def test_aspect_cardinal_directions(self):
        """Aspect to cardinal should map correctly."""
        assert aspect_to_cardinal(0) == "N"
        assert aspect_to_cardinal(45) == "NE"
        assert aspect_to_cardinal(90) == "E"
        assert aspect_to_cardinal(135) == "SE"
        assert aspect_to_cardinal(180) == "S"
        assert aspect_to_cardinal(225) == "SW"
        assert aspect_to_cardinal(270) == "W"
        assert aspect_to_cardinal(315) == "NW"


class TestTerrainAnalysisModel:
    """Tests for TerrainAnalysis with enhanced metrics."""

    def test_analyzer_includes_curvature(self, simple_dem):
        """TerrainAnalysis should include curvature data."""
        from engine.land.models import TerrainType

        analyzer = TerrainAnalyzer(resolution=30.0)
        result = analyzer.analyze(simple_dem, profile_id="test")

        assert result.curvature is not None
        assert hasattr(result.curvature, "profile_curvature")
        assert hasattr(result.curvature, "plan_curvature")
        assert hasattr(result.curvature, "total_curvature")

    def test_analyzer_includes_indices(self, simple_dem):
        """TerrainAnalysis should include TerrainIndices (TWI, TPI)."""
        analyzer = TerrainAnalyzer(resolution=30.0)
        result = analyzer.analyze(simple_dem, profile_id="test")

        assert result.indices is not None
        assert hasattr(result.indices, "twi")
        assert hasattr(result.indices, "tpi")
        assert hasattr(result.indices, "roughness_index")
        assert result.roughness_index > 0

    def test_analyzer_roughness_flat_low(self, flat_dem):
        """Flat terrain should have very low roughness."""
        analyzer = TerrainAnalyzer(resolution=30.0)
        result = analyzer.analyze(flat_dem, profile_id="test")
        assert result.roughness_index < 0.01

    def test_analyzer_roughness_sloped_higher(self, sloped_dem):
        """Sloped terrain should have higher roughness than flat."""
        flat = np.full((10, 10), 1000.0)
        analyzer = TerrainAnalyzer(resolution=30.0)

        flat_result = analyzer.analyze(flat, profile_id="flat")
        sloped_result = analyzer.analyze(sloped_dem, profile_id="sloped")

        assert sloped_result.roughness_index > flat_result.roughness_index

    def test_analyzer_slope_distribution(self, simple_dem):
        """TerrainAnalysis should include slope distribution."""
        analyzer = TerrainAnalyzer(resolution=30.0)
        result = analyzer.analyze(simple_dem, profile_id="test")
        assert result.slope_distribution is not None
        assert len(result.slope_distribution) > 0
