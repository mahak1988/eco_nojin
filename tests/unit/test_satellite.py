"""Tests for satellite data processing."""

import numpy as np

from engine.hydroma.satellite import get_analyzer
from engine.hydroma.satellite.processors.indices import (
    calculate_evi,
    calculate_nbr,
    calculate_ndvi,
    calculate_ndwi,
    calculate_savi,
    interpret_ndvi,
)


def test_ndvi_calculation():
    """Verify NDVI calculation for known values."""
    red = np.array([[200, 400], [600, 800]])
    nir = np.array([[2000, 1800], [1500, 1200]])

    ndvi = calculate_ndvi(red, nir)

    assert ndvi[0, 0] > 0.8
    assert 0.4 < ndvi[1, 0] < 0.7


def test_ndvi_range():
    """Verify NDVI is bounded between -1 and 1."""
    np.random.seed(42)
    red = np.random.uniform(100, 1000, (10, 10))
    nir = np.random.uniform(100, 4000, (10, 10))

    ndvi = calculate_ndvi(red, nir)

    assert ndvi.min() >= -1.0
    assert ndvi.max() <= 1.0


def test_evi_calculation():
    """Verify EVI calculation with clipping."""
    red = np.array([[800]])
    np.array([[1200]])
    blue = np.array([[400]])  # Correct: blue, not green
    nir = np.array([[3500]])

    evi = calculate_evi(red, nir, blue)

    # With clipping, EVI should be in [-1, 1]
    assert -1 <= evi[0, 0] <= 1


def test_savi_calculation():
    """Verify SAVI with soil brightness correction."""
    red = np.array([[500]])
    nir = np.array([[2000]])

    savi = calculate_savi(red, nir, L=0.5)
    assert -1 <= savi[0, 0] <= 1


def test_ndwi_water_detection():
    """Verify NDWI identifies water."""
    green = np.array([[1500]])
    nir = np.array([[500]])

    ndwi = calculate_ndwi(green, nir)
    assert ndwi[0, 0] > 0
    assert -1 <= ndwi[0, 0] <= 1


def test_nbr_burn_detection():
    """Verify NBR identifies burned areas."""
    nir_healthy = np.array([[3000]])
    swir_healthy = np.array([[1000]])

    nir_burned = np.array([[1000]])
    swir_burned = np.array([[3000]])

    nbr_healthy = calculate_nbr(nir_healthy, swir_healthy)
    nbr_burned = calculate_nbr(nir_burned, swir_burned)

    assert nbr_healthy[0, 0] > nbr_burned[0, 0]
    assert -1 <= nbr_healthy[0, 0] <= 1
    assert -1 <= nbr_burned[0, 0] <= 1


def test_interpret_ndvi_classes():
    """Verify NDVI interpretation ranges."""
    assert interpret_ndvi(-0.1)["class"] == "non-vegetated"
    assert interpret_ndvi(0.05)["class"] == "bare_soil"
    assert interpret_ndvi(0.15)["class"] == "sparse"
    assert interpret_ndvi(0.35)["class"] == "moderate"
    assert interpret_ndvi(0.55)["class"] == "dense"
    assert interpret_ndvi(0.75)["class"] == "very_dense"


def test_analyzer_singleton():
    """Verify analyzer singleton pattern."""
    a1 = get_analyzer()
    a2 = get_analyzer()
    assert a1 is a2


def test_analyzer_handles_invalid_coords():
    """Verify analyzer returns fallback for problematic locations."""
    analyzer = get_analyzer()
    result = analyzer.analyze_point(lat=0.0, lon=-30.0)

    assert hasattr(result, "ndvi")
    assert hasattr(result, "recommendation")
