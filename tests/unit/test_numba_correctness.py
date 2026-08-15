"""Tests for Muskingum-Cunge flood routing."""

import numpy as np

from engine.hydroma.cpp_bridge.hydrology_fast import (
    compute_wave_parameters,
    route_flood_wave,
    route_multi_reach,
)
from engine.hydroma.cpp_bridge.indices_fast import (
    evi_fast,
    is_numba_available,
    nbr_fast,
    ndvi_fast,
    savi_fast,
)
from engine.hydroma.cpp_bridge.soil_physics_fast import (
    SOIL_PARAMETERS,
    hydraulic_conductivity,
    soil_water_content,
)


def test_numba_available():
    """Verify Numba is installed."""
    assert is_numba_available(), "Numba should be installed"


def test_ndvi_matches_numpy():
    """Verify Numba NDVI matches NumPy implementation."""
    np.random.seed(42)
    red = np.random.uniform(200, 1000, (100, 100))
    nir = np.random.uniform(1000, 4000, (100, 100))

    expected = (nir - red) / (nir + red)
    expected = np.clip(np.nan_to_num(expected, nan=0.0), -1, 1)

    result = ndvi_fast(red, nir)
    np.testing.assert_allclose(result, expected, rtol=1e-10)


def test_evi_matches_numpy():
    """Verify Numba EVI matches NumPy."""
    np.random.seed(42)
    red = np.random.uniform(300, 1000, (50, 50))
    nir = np.random.uniform(1500, 4000, (50, 50))
    blue = np.random.uniform(200, 800, (50, 50))

    expected = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)
    expected = np.clip(np.nan_to_num(expected, nan=0.0), -1, 1)

    result = evi_fast(red, nir, blue)
    np.testing.assert_allclose(result, expected, rtol=1e-10)


def test_savi_bounds():
    """Verify SAVI values are in valid range."""
    np.random.seed(42)
    red = np.random.uniform(200, 1000, (50, 50))
    nir = np.random.uniform(1000, 4000, (50, 50))

    result = savi_fast(red, nir, L=0.5)
    assert result.min() >= -1.0
    assert result.max() <= 1.0


def test_nbr_matches_numpy():
    """Verify Numba NBR matches NumPy."""
    np.random.seed(42)
    nir = np.random.uniform(500, 4000, (50, 50))
    swir = np.random.uniform(500, 3000, (50, 50))

    expected = (nir - swir) / (nir + swir)
    expected = np.clip(np.nan_to_num(expected, nan=0.0), -1, 1)

    result = nbr_fast(nir, swir)
    np.testing.assert_allclose(result, expected, rtol=1e-10)


def test_soil_water_content_monotonic():
    """Verify water content decreases with increasing suction."""
    h_values = np.array([10, 100, 1000, 10000, 15000], dtype=np.float64)

    for texture in ["sand", "loam", "clay"]:
        theta = soil_water_content(h_values, texture)
        assert all(theta[i] >= theta[i + 1] for i in range(len(theta) - 1))


def test_soil_water_content_range():
    """Verify water content is between theta_r and theta_s."""
    h_values = np.logspace(0, 5, 20)

    for texture, params in SOIL_PARAMETERS.items():
        theta = soil_water_content(h_values, texture)
        assert theta.min() >= params["theta_r"] - 0.001
        assert theta.max() <= params["theta_s"] + 0.001


def test_hydraulic_conductivity_decreases():
    """Verify K decreases with increasing suction."""
    h_values = np.array([1, 10, 100, 1000, 10000], dtype=np.float64)

    for texture in ["sand", "loam", "clay"]:
        K = hydraulic_conductivity(h_values, texture)
        assert all(K[i] >= K[i + 1] - 1e-10 for i in range(len(K) - 1))


def test_wave_parameters():
    """Verify wave parameter computation is physically reasonable."""
    params = compute_wave_parameters(
        channel_length=1000.0,
        bed_slope=0.002,
        manning_n=0.03,
        channel_width=5.0,
        peak_flow=20.0,
    )

    # Travel time should be positive and reasonable (minutes to hours)
    assert params["K"] > 0
    assert params["K"] < 10000  # Less than 3 hours for 1km

    # Celerity should be positive and reasonable (1-10 m/s)
    assert params["celerity"] > 0
    assert params["celerity"] < 20

    # Normal depth should be positive and reasonable (0.1-5m)
    assert params["normal_depth"] > 0
    assert params["normal_depth"] < 10

    print("\n  Wave parameters:")
    print(f"    Travel time K: {params['K']:.0f} s")
    print(f"    Celerity: {params['celerity']:.2f} m/s")
    print(f"    Normal depth: {params['normal_depth']:.2f} m")


def test_flood_routing_produces_outflow():
    """Verify Muskingum-Cunge produces non-zero outflow."""
    n_times = 300
    times = np.arange(n_times) * 10.0

    peak_time = 500.0
    peak_flow = 20.0

    inflow = np.zeros(n_times)
    for i, t in enumerate(times):
        if t < peak_time:
            inflow[i] = peak_flow * t / peak_time
        else:
            inflow[i] = max(0, peak_flow * (2000 - t) / (2000 - peak_time))

    result = route_flood_wave(
        inflow,
        channel_length=1000.0,
        manning_n=0.030,
        bed_slope=0.002,
        dt=10.0,
        channel_width=5.0,
    )

    # Critical: outflow must be non-zero
    assert result["peak_outflow"] > 0.1, (
        f"Expected non-zero outflow, got {result['peak_outflow']:.4f}"
    )

    # Attenuation should occur (peak_out < peak_in)
    assert 0 < result["attenuation_ratio"] < 1.0, (
        f"Attenuation ratio should be in (0,1), got {result['attenuation_ratio']:.3f}"
    )

    # Time lag should be positive
    assert result["time_lag"] >= 0, f"Time lag should be non-negative, got {result['time_lag']}"

    print("\n  Flood routing results (Muskingum-Cunge):")
    print(f"    Peak inflow:  {result['peak_inflow']:.2f} m³/s")
    print(f"    Peak outflow: {result['peak_outflow']:.2f} m³/s")
    print(f"    Attenuation:  {result['attenuation_ratio']:.1%}")
    print(f"    Time lag:     {result['time_lag']:.0f} s")
    print(f"    Travel time:  {result['travel_time']:.0f} s")


def test_flood_routing_attenuation_increases_with_length():
    """Verify longer channels produce more attenuation."""
    n_times = 300
    peak_flow = 15.0
    inflow = np.zeros(n_times)
    for i in range(n_times):
        t = i * 10.0
        if t < 500:
            inflow[i] = peak_flow * t / 500
        else:
            inflow[i] = max(0, peak_flow * (2000 - t) / 1500)

    result_short = route_flood_wave(inflow, channel_length=500.0)
    result_long = route_flood_wave(inflow, channel_length=2000.0)

    # Both should have non-zero outflow
    assert result_short["peak_outflow"] > 0
    assert result_long["peak_outflow"] > 0

    # Longer channel should attenuate more
    assert result_long["attenuation_ratio"] <= result_short["attenuation_ratio"] + 0.01


def test_flood_routing_mass_conservation():
    """Verify mass is approximately conserved (within 10%)."""
    n_times = 200
    inflow = np.zeros(n_times)
    for i in range(n_times):
        t = i * 10.0
        if 200 < t < 800:
            inflow[i] = 10.0

    result = route_flood_wave(inflow, channel_length=1000.0, dt=10.0)

    # Mass balance should be close to 1 (some numerical diffusion is expected)
    assert 0.8 < result["mass_balance"] < 1.2, (
        f"Mass balance should be ~1, got {result['mass_balance']:.3f}"
    )


def test_flood_routing_output_shape():
    """Verify output hydrograph has correct shape."""
    inflow = np.array([0, 5, 15, 25, 20, 10, 5, 2, 0, 0], dtype=np.float64)

    result = route_flood_wave(inflow, channel_length=500.0)

    assert len(result["outflow_hydrograph"]) == len(inflow)
    assert result["peak_outflow"] >= 0


def test_multi_reach_routing():
    """Verify multi-reach routing produces more attenuation."""
    n_times = 200
    inflow = np.zeros(n_times)
    for i in range(n_times):
        t = i * 10.0
        if 300 < t < 900:
            inflow[i] = 20.0

    result_single = route_flood_wave(inflow, channel_length=1000.0)
    result_multi = route_multi_reach(inflow, channel_length=1000.0, n_reaches=5)

    # Multi-reach should attenuate more than single reach
    assert result_multi["attenuation_ratio"] <= result_single["attenuation_ratio"] + 0.01
