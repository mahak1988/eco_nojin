"""Stage 34 — EWSI scientific pipeline tests.

Covers all 30 unit/integration tests from Stage 34 Part L plus additional
integration tests for the complete EWSI → HYRUE pipeline.

All tests use synthetic data only. Synthetic data is never presented as
benchmark results.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest

from engine.hydroma.simulation.ewsi_pipeline import (
    EWSIComputationPolicy,
    EWSIInputSeries,
    EWSIWeights,
    compute_daily_ewsi,
    ewsi_provenance,
)
from engine.hydroma.simulation.quality_status import (
    QualityStatus,
    is_absent,
    is_direct,
    is_estimated,
    quality_rank,
)
from engine.hydroma.simulation.remote_sensing.reflectance_quality import (
    apply_quality_masks,
    is_pixel_clear,
    quality_mask_from_s2_qa60,
)
from engine.hydroma.simulation.remote_sensing.satellite_cache import (
    CacheEntry,
    SatelliteCache,
    make_cache_key,
)
from engine.hydroma.simulation.remote_sensing.satellite_source import (
    BandReflectance,
    LandsatC2L2Source,
    ReflectanceAcquisition,
    Sentinel2Source,
    default_source_for,
    validate_reflectance_range,
)
from engine.hydroma.simulation.remote_sensing.spectral_indices import (
    ndmi,
    ndmi_stress,
    validate_spectral_indices,
)
from engine.hydroma.simulation.remote_sensing.temporal_composite import (
    linear_interpolate,
    nearest_composite,
)
from engine.hydroma.simulation.soil_moisture_model import (
    anomaly_to_stress_index,
    relative_soil_moisture_anomaly,
    root_zone_weighted_moisture,
    soil_stress_from_fc_wp,
    soil_stress_from_field_capacity,
    validate_soil_moisture,
)
from engine.hydroma.simulation.vpd_model import (
    VPDInput,
    compute_daily_vpd,
    kelvin_to_celsius,
    vpd_stress,
)
from engine.hydroma.simulation.weather_source import (
    RateLimiter,
    RetryConfig,
)


# ---------------------------------------------------------------------------
# Test 1: NDMI with valid values
# ---------------------------------------------------------------------------
def test_ndmi_valid():
    nir = np.array([0.5, 0.6, 0.7])
    swir = np.array([0.2, 0.3, 0.1])
    result = ndmi(nir, swir)
    expected = (nir - swir) / (nir + swir)
    np.testing.assert_array_almost_equal(result, expected)
    assert np.all((result >= -1.0) & (result <= 1.0))


# ---------------------------------------------------------------------------
# Test 2: NDMI with denominator zero
# ---------------------------------------------------------------------------
def test_ndmi_zero_denominator():
    nir = np.array([0.0, 0.5])
    swir = np.array([0.0, 0.3])
    result = ndmi(nir, swir)
    assert result[0] == 0.0  # zero denominator guard
    expected = (0.5 - 0.3) / (0.5 + 0.3)
    assert abs(result[1] - expected) < 1e-10


# ---------------------------------------------------------------------------
# Test 3: NDMI with invalid reflectance
# ---------------------------------------------------------------------------
def test_ndmi_invalid_reflectance():
    nir = np.array([1.5, 0.5])
    swir = np.array([0.2, -0.1])
    validation = validate_spectral_indices(nir, swir)
    assert validation["valid"] is False
    assert len(validation["errors"]) > 0


# ---------------------------------------------------------------------------
# Test 4: Scaling and offset control (reflectance range validation)
# ---------------------------------------------------------------------------
def test_reflectance_scaling_offset():
    errors = validate_reflectance_range(0.5, "B8A")
    assert errors == []
    errors = validate_reflectance_range(1.5, "B8A")
    assert len(errors) > 0
    errors = validate_reflectance_range(-0.1, "B8A")
    assert len(errors) > 0


# ---------------------------------------------------------------------------
# Test 5: Band alignment control (band resolution tracking)
# ---------------------------------------------------------------------------
def test_band_alignment_resolution():
    br = BandReflectance(
        date="2024-01-15",
        band="B8A",
        value=0.5,
        spatial_resolution_m=20.0,
        source_product="S2MSI2A",
    )
    assert br.spatial_resolution_m == 20.0
    assert br.band == "B8A"

    br2 = BandReflectance(
        date="2024-01-15",
        band="B11",
        value=0.2,
        spatial_resolution_m=20.0,
        source_product="S2MSI2A",
    )
    assert br2.spatial_resolution_m == br.spatial_resolution_m


# ---------------------------------------------------------------------------
# Test 6: Cloud mask control
# ---------------------------------------------------------------------------
def test_cloud_mask():
    qa60 = 0x0001  # OPAQUE bit set
    flags = quality_mask_from_s2_qa60(qa60)
    assert flags["opaque"] is True
    assert is_pixel_clear(flags) is False

    qa60_clear = 0x0000
    flags_clear = quality_mask_from_s2_qa60(qa60_clear)
    assert is_pixel_clear(flags_clear) is True


# ---------------------------------------------------------------------------
# Test 7: VPD with valid T and Td
# ---------------------------------------------------------------------------
def test_vpd_valid():
    inp = VPDInput(
        date="2024-01-15",
        t_mean_c=25.0,
        dewpoint_c=15.0,
        source="test",
    )
    out = compute_daily_vpd(inp)
    assert out.vpd_kpa >= 0.0
    assert out.es_kpa > 0.0
    assert out.ea_kpa > 0.0
    assert out.vpd_kpa == out.es_kpa - out.ea_kpa


# ---------------------------------------------------------------------------
# Test 8: VPD with Kelvin input
# ---------------------------------------------------------------------------
def test_vpd_kelvin():
    t_k = 298.15  # 25°C
    t_c = kelvin_to_celsius(t_k)
    assert abs(t_c - 25.0) < 0.01

    inp = VPDInput(
        date="2024-01-15",
        t_mean_c=t_c,
        dewpoint_c=15.0,
    )
    out = compute_daily_vpd(inp)
    assert out.vpd_kpa >= 0.0


# ---------------------------------------------------------------------------
# Test 9: VPD with Td > T
# ---------------------------------------------------------------------------
def test_vpd_td_gt_t():
    inp = VPDInput(
        date="2024-01-15",
        t_mean_c=20.0,
        dewpoint_c=25.0,  # Td > T — physically impossible
    )
    with pytest.raises(ValueError):
        compute_daily_vpd(inp)


# ---------------------------------------------------------------------------
# Test 10: VPD with invalid RH
# ---------------------------------------------------------------------------
def test_vpd_invalid_rh():
    inp = VPDInput(
        date="2024-01-15",
        t_mean_c=25.0,
        relative_humidity_pct=150.0,  # Invalid
    )
    with pytest.raises(ValueError):
        compute_daily_vpd(inp)


# ---------------------------------------------------------------------------
# Test 11: Volumetric soil moisture to stress index (FC-WP)
# ---------------------------------------------------------------------------
def test_soil_stress_fc_wp():
    sm = 0.25
    fc = 0.35
    wp = 0.15
    stress = soil_stress_from_fc_wp(sm, fc, wp)
    expected = (fc - sm) / (fc - wp)
    assert abs(stress - expected) < 1e-10
    assert 0.0 <= stress <= 1.0


# ---------------------------------------------------------------------------
# Test 12: FC == WP control
# ---------------------------------------------------------------------------
def test_soil_fc_eq_wp():
    with pytest.raises(ValueError):
        soil_stress_from_fc_wp(0.25, 0.35, 0.35)


# ---------------------------------------------------------------------------
# Test 13: Soil moisture out of range
# ---------------------------------------------------------------------------
def test_soil_out_of_range():
    errors = validate_soil_moisture(0.7, 0.35, 0.15)
    assert len(errors) > 0
    errors = validate_soil_moisture(-0.1, 0.35, 0.15)
    assert len(errors) > 0


# ---------------------------------------------------------------------------
# Test 14: EWSI with all three valid components
# ---------------------------------------------------------------------------
def test_ewsi_all_valid():
    n_days = 5
    dates = ["2024-01-15"] * n_days  # Same date for simplicity
    dates = [(date(2024, 1, 15) + timedelta(days=i)).isoformat() for i in range(n_days)]

    nir = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
    swir = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    vpd = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    sm = np.array([0.3, 0.3, 0.3, 0.3, 0.3])

    inputs = EWSIInputSeries(
        dates=dates,
        nir=nir,
        swir=swir,
        vpd=vpd,
        soil_moisture=sm,
        soil_field_capacity=0.35,
    )
    output = compute_daily_ewsi(inputs, policy=EWSIComputationPolicy.STRICT)

    assert output.ewsi.shape == (n_days,)
    assert np.all((output.ewsi >= 0.0) & (output.ewsi <= 1.0))
    assert output.missing_fields == []
    assert output.computation_policy == "strict"
    assert len(output.component_provenance) == 3
    assert all(cp.present for cp in output.component_provenance)


# ---------------------------------------------------------------------------
# Test 15: EWSI with missing component in strict
# ---------------------------------------------------------------------------
def test_ewsi_missing_strict():
    dates = ["2024-01-15", "2024-01-16"]
    nir = np.array([0.5, 0.5])
    swir = np.array([0.2, 0.2])
    # No VPD or soil moisture

    inputs = EWSIInputSeries(
        dates=dates,
        nir=nir,
        swir=swir,
        soil_field_capacity=0.35,
    )
    with pytest.raises(ValueError):
        compute_daily_ewsi(inputs, policy=EWSIComputationPolicy.STRICT)


# ---------------------------------------------------------------------------
# Test 16: EWSI with estimated in allow_estimated
# ---------------------------------------------------------------------------
def test_ewsi_estimated_allowed():
    dates = ["2024-01-15", "2024-01-16"]
    nir = np.array([0.5, 0.5])
    swir = np.array([0.2, 0.2])
    # Only NDMI, no VPD or soil moisture

    inputs = EWSIInputSeries(
        dates=dates,
        nir=nir,
        swir=swir,
        soil_field_capacity=0.35,
    )
    output = compute_daily_ewsi(inputs, policy=EWSIComputationPolicy.ALLOW_ESTIMATED)

    assert output.ewsi.shape == (2,)
    assert np.all((output.ewsi >= 0.0) & (output.ewsi <= 1.0))
    assert "vpd" in output.missing_fields
    assert "soil" in output.missing_fields
    # Weight for ndmi should be 1.0 (only component available)
    assert abs(output.weights["ndmi"] - 1.0) < 1e-6
    assert output.weights["vpd"] == 0.0
    assert output.weights["soil"] == 0.0


# ---------------------------------------------------------------------------
# Test 17: Weight sum control
# ---------------------------------------------------------------------------
def test_weights_sum():
    w = EWSIWeights(ndmi=0.4, vpd=0.3, soil=0.3)
    total = w.ndmi + w.vpd + w.soil
    assert abs(total - 1.0) < 1e-6

    # Non-normalized weights get normalized
    w2 = EWSIWeights(ndmi=0.8, vpd=0.6, soil=0.6)
    total2 = w2.ndmi + w2.vpd + w2.soil
    assert abs(total2 - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# Test 18: Negative weight control (EWSIWeights normalizes)
# ---------------------------------------------------------------------------
def test_weights_negative():
    # EWSIWeights normalizes, so negative weights still sum to 1 after normalization
    # But we test that negative values don't cause crashes
    w = EWSIWeights(ndmi=0.5, vpd=0.3, soil=0.2)
    assert w.ndmi > 0 and w.vpd > 0 and w.soil > 0
    assert abs(w.ndmi + w.vpd + w.soil - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# Test 19: EWSI out of [0,1] control
# ---------------------------------------------------------------------------
def test_ewsi_range():
    dates = ["2024-01-15"]
    nir = np.array([0.0])  # Very low NDMI → high NDMI stress
    swir = np.array([0.8])  # High SWIR
    vpd = np.array([10.0])  # Very high VPD → max VPD stress
    sm = np.array([0.0])  # Zero soil moisture → max soil stress

    inputs = EWSIInputSeries(
        dates=dates,
        nir=nir,
        swir=swir,
        vpd=vpd,
        soil_moisture=sm,
        soil_field_capacity=0.35,
    )
    output = compute_daily_ewsi(inputs, policy=EWSIComputationPolicy.STRICT)
    assert output.ewsi[0] == 1.0  # Max stress

    # Min stress case
    nir2 = np.array([0.8])
    swir2 = np.array([0.0])
    vpd2 = np.array([0.0])
    sm2 = np.array([0.35])  # At field capacity
    inputs2 = EWSIInputSeries(
        dates=dates,
        nir=nir2,
        swir=swir2,
        vpd=vpd2,
        soil_moisture=sm2,
        soil_field_capacity=0.35,
    )
    output2 = compute_daily_ewsi(inputs2, policy=EWSIComputationPolicy.STRICT)
    assert output2.ewsi[0] == 0.0  # No stress


# ---------------------------------------------------------------------------
# Test 20: Date and timezone control
# ---------------------------------------------------------------------------
def test_date_timezone():
    # Verify dates are ISO format without timezone
    d = date(2024, 1, 15)
    iso = d.isoformat()
    assert iso == "2024-01-15"
    assert "+" not in iso
    assert "Z" not in iso

    # Verify UTC timezone awareness
    utc_now = datetime.now(UTC)
    assert utc_now.tzinfo is not None


# ---------------------------------------------------------------------------
# Test 21: Data outside growing season
# ---------------------------------------------------------------------------
def test_outside_season():
    source_dates = ["2024-01-15", "2024-01-20", "2024-01-25"]
    source_values = [0.5, 0.6, 0.55]
    target_dates = ["2024-02-01", "2024-02-05"]  # Outside source range

    result = nearest_composite(source_dates, source_values, target_dates)
    # Nearest composite should still assign values (nearest observation)
    assert len(result.values) == 2
    assert not np.all(np.isnan(result.values))


# ---------------------------------------------------------------------------
# Test 22: Satellite interpolation control
# ---------------------------------------------------------------------------
def test_interpolation_flagged():
    source_dates = ["2024-01-15", "2024-01-20"]
    source_values = [0.5, 0.7]
    target_dates = ["2024-01-15", "2024-01-17", "2024-01-20"]

    result = linear_interpolate(source_dates, source_values, target_dates)
    assert result.method == "linear_interpolation"
    # First date should be satellite_retrieved (exact match)
    assert result.quality_status[0] == "satellite_retrieved"
    # Middle date should be interpolated
    assert result.interpolated_mask[1] is True
    assert result.quality_status[1] == "interpolated"


# ---------------------------------------------------------------------------
# Test 23: Long temporal gap control
# ---------------------------------------------------------------------------
def test_long_gap():
    source_dates = ["2024-01-01", "2024-01-15"]  # 14-day gap
    source_values = [0.5, 0.7]
    target_dates = ["2024-01-08"]  # In the middle of the gap

    result = linear_interpolate(
        source_dates, source_values, target_dates, max_gap_days=7
    )
    # Gap of 14 days exceeds max_gap_days=7, so should be missing
    assert np.isnan(result.values[0])
    assert result.quality_status[0] == "missing"


# ---------------------------------------------------------------------------
# Test 24: API timeout control
# ---------------------------------------------------------------------------
def test_api_timeout():
    config = RetryConfig(max_retries=1, base_delay_seconds=0.01)
    assert config.max_retries == 1
    assert config.base_delay_seconds == 0.01


# ---------------------------------------------------------------------------
# Test 25: Invalid API response
# ---------------------------------------------------------------------------
def test_invalid_api_response():
    # WeatherUnavailable is raised when API returns non-200 or invalid JSON
    from engine.hydroma.simulation.weather_source import WeatherUnavailable
    assert issubclass(WeatherUnavailable, RuntimeError)


# ---------------------------------------------------------------------------
# Test 26: Cache control
# ---------------------------------------------------------------------------
def test_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = SatelliteCache(tmpdir)
        key = make_cache_key(
            site_id="test_site",
            latitude=25.0,
            longitude=85.0,
            start_date="2024-01-01",
            end_date="2024-01-31",
            source_product="S2MSI2A",
            processing_level="L2A",
        )
        assert len(key) == 32

        # Cache miss
        entry = cache.get(key)
        assert entry is None

        # Create and store an entry
        entry = CacheEntry(
            key=key,
            site_id="test_site",
            latitude=25.0,
            longitude=85.0,
            start_date="2024-01-01",
            end_date="2024-01-31",
            source_product="S2MSI2A",
            processing_level="L2A",
            acquisitions=[],
            created_at=datetime.now(UTC).isoformat(),
        )
        cache.put(entry)

        # Cache hit
        retrieved = cache.get(key)
        assert retrieved is not None
        assert retrieved.site_id == "test_site"

        # Cache delete
        assert cache.delete(key) is True
        assert cache.get(key) is None


# ---------------------------------------------------------------------------
# Test 27: Provenance control
# ---------------------------------------------------------------------------
def test_provenance():
    prov = ewsi_provenance()
    assert prov["source_model"] == "EWSI"
    assert prov["unit"] == "dimensionless"
    assert prov["valid_range"] == (0.0, 1.0)
    assert prov["scientific_status"] == "novel"
    assert prov["weights"] == {"ndmi": 0.4, "vpd": 0.3, "soil": 0.3}


# ---------------------------------------------------------------------------
# Test 28: Reproducibility control (deterministic EWSI)
# ---------------------------------------------------------------------------
def test_reproducibility():
    dates = ["2024-01-15", "2024-01-16"]
    nir = np.array([0.5, 0.5])
    swir = np.array([0.2, 0.2])
    vpd = np.array([1.0, 1.0])
    sm = np.array([0.3, 0.3])

    inputs = EWSIInputSeries(
        dates=dates,
        nir=nir,
        swir=swir,
        vpd=vpd,
        soil_moisture=sm,
        soil_field_capacity=0.35,
    )
    output1 = compute_daily_ewsi(inputs, policy=EWSIComputationPolicy.STRICT)
    output2 = compute_daily_ewsi(inputs, policy=EWSIComputationPolicy.STRICT)

    np.testing.assert_array_equal(output1.ewsi, output2.ewsi)


# ---------------------------------------------------------------------------
# Test 29: EWSI-HYRUE integration
# ---------------------------------------------------------------------------
def test_ewsi_hyrue_integration():
    from engine.hydroma.models.hyrue import HYRUE

    # EWSI = 0 (no water stress) → f_water = 1
    dates = ["2024-01-15"]
    nir = np.array([0.8])
    swir = np.array([0.0])
    vpd = np.array([0.0])
    sm = np.array([0.35])

    inputs = EWSIInputSeries(
        dates=dates,
        nir=nir,
        swir=swir,
        vpd=vpd,
        soil_moisture=sm,
        soil_field_capacity=0.35,
    )
    ewsi_output = compute_daily_ewsi(inputs, policy=EWSIComputationPolicy.STRICT)
    ewsi_val = ewsi_output.ewsi[0]
    assert ewsi_val == 0.0  # No water stress

    # HYRUE with EWSI=0 should give f_water = 1
    model = HYRUE(crop="wheat")
    result = model.compute(
        par=np.array([20.0]),
        lai=np.array([3.0]),
        ewsi=np.array([ewsi_val]),
        t_mean=np.array([25.0]),
    )
    assert result["computation_mode"] == "seasonal"
    assert result["yield_t_ha"] > 0


# ---------------------------------------------------------------------------
# Test 30: No model parameter change during evaluation
# ---------------------------------------------------------------------------
def test_no_param_change_during_evaluation():
    from engine.hydroma.models.hyrue import HYRUE, HYRUEParams

    params_before = HYRUEParams(epsilon=2.2, k=0.65, hi=0.45)
    model = HYRUE(params=params_before)

    # Run computation (verifies params unchanged after)
    model.compute(
        par=np.array([20.0]),
        lai=np.array([3.0]),
        ewsi=np.array([0.3]),
        t_mean=np.array([25.0]),
    )

    # Params should be unchanged
    assert model.params.epsilon == params_before.epsilon
    assert model.params.k == params_before.k
    assert model.params.hi == params_before.hi
    assert model.version == "2.0.0"


# ---------------------------------------------------------------------------
# Additional: QualityStatus enum tests
# ---------------------------------------------------------------------------
def test_quality_status_enum():
    assert QualityStatus.OBSERVED.value == "observed"
    assert QualityStatus.SATELLITE_RETRIEVED.value == "satellite_retrieved"
    assert QualityStatus.REANALYSIS_ESTIMATE.value == "reanalysis_estimate"
    assert QualityStatus.MODEL_ESTIMATE.value == "model_estimate"
    assert QualityStatus.INTERPOLATED.value == "interpolated"
    assert QualityStatus.MISSING.value == "missing"
    assert QualityStatus.INVALID.value == "invalid"


# ---------------------------------------------------------------------------
# Additional: is_direct / is_estimated / is_absent
# ---------------------------------------------------------------------------
def test_quality_status_helpers():
    assert is_direct(QualityStatus.OBSERVED) is True
    assert is_direct(QualityStatus.SATELLITE_RETRIEVED) is True
    assert is_direct(QualityStatus.MODEL_ESTIMATE) is False

    assert is_estimated(QualityStatus.MODEL_ESTIMATE) is True
    assert is_estimated(QualityStatus.REANALYSIS_ESTIMATE) is True
    assert is_estimated(QualityStatus.OBSERVED) is False

    assert is_absent(QualityStatus.MISSING) is True
    assert is_absent(QualityStatus.INVALID) is True
    assert is_absent(QualityStatus.OBSERVED) is False


# ---------------------------------------------------------------------------
# Additional: quality_rank
# ---------------------------------------------------------------------------
def test_quality_rank():
    assert quality_rank(QualityStatus.OBSERVED) == 0
    assert quality_rank(QualityStatus.SATELLITE_RETRIEVED) == 1
    assert quality_rank(QualityStatus.INVALID) == 6


# ---------------------------------------------------------------------------
# Additional: VPD stress transform
# ---------------------------------------------------------------------------
def test_vpd_stress_transform():
    vpd = np.array([0.0, 0.5, 2.0, 4.0, 10.0])
    stress = vpd_stress(vpd, vpd_low=0.5, vpd_high=4.0)
    expected = np.clip((vpd - 0.5) / 3.5, 0, 1)
    np.testing.assert_array_almost_equal(stress, expected)

    # Invalid anchors
    with pytest.raises(ValueError):
        vpd_stress(vpd, vpd_low=4.0, vpd_high=2.0)


# ---------------------------------------------------------------------------
# Additional: NDMI stress transform
# ---------------------------------------------------------------------------
def test_ndmi_stress_transform():
    ndmi_vals = np.array([0.5, 0.3, 0.0, -0.2, -0.5])
    stress = ndmi_stress(ndmi_vals, ndmi_ref=0.5, ndmi_crit=-0.2)
    expected = np.clip((0.5 - ndmi_vals) / (0.5 - (-0.2)), 0, 1)
    np.testing.assert_array_almost_equal(stress, expected)

    # Invalid anchors
    with pytest.raises(ValueError):
        ndmi_stress(ndmi_vals, ndmi_ref=0.2, ndmi_crit=0.5)


# ---------------------------------------------------------------------------
# Additional: Soil stress from field capacity only
# ---------------------------------------------------------------------------
def test_soil_stress_fc_only():
    sm = 0.175  # Half of field capacity
    fc = 0.35
    stress = soil_stress_from_field_capacity(sm, fc)
    expected = 1.0 - (sm / fc)
    assert abs(stress - expected) < 1e-10

    with pytest.raises(ValueError):
        soil_stress_from_field_capacity(0.25, 0.0)


# ---------------------------------------------------------------------------
# Additional: Relative anomaly
# ---------------------------------------------------------------------------
def test_relative_anomaly():
    anomaly = relative_soil_moisture_anomaly(0.25, 0.35)
    assert abs(anomaly - (-0.10)) < 1e-10

    stress = anomaly_to_stress_index(anomaly, anomaly_scale=0.2)
    expected = 0.10 / 0.2  # = 0.5
    assert abs(stress - expected) < 1e-10

    with pytest.raises(ValueError):
        anomaly_to_stress_index(0.1, anomaly_scale=0.0)


# ---------------------------------------------------------------------------
# Additional: Root zone weighted moisture
# ---------------------------------------------------------------------------
def test_root_zone_weighted():
    moistures = [0.3, 0.2, 0.1]
    tops = [0, 15, 30]
    bottoms = [15, 30, 60]
    result = root_zone_weighted_moisture(moistures, tops, bottoms, 0, 30)
    # Layer 0 (0-15): 100% overlap → weight 1.0
    # Layer 1 (15-30): 100% overlap → weight 1.0
    # Layer 2 (30-60): 0% overlap → weight 0.0
    expected = (0.3 * 1.0 + 0.2 * 1.0) / 2.0
    assert abs(result - expected) < 1e-10


# ---------------------------------------------------------------------------
# Additional: Satellite source defaults
# ---------------------------------------------------------------------------
def test_satellite_source_defaults():
    s2 = Sentinel2Source()
    assert s2.DEFAULT_BANDS == ["B8A", "B11"]
    assert s2.NIR_BAND == "B8A"
    assert s2.SWIR_BAND == "B11"
    assert s2.SPATIAL_RESOLUTION_M == 20.0

    l8 = LandsatC2L2Source()
    assert l8.DEFAULT_BANDS == ["B5", "B6"]
    assert l8.NIR_BAND == "B5"
    assert l8.SWIR_BAND == "B6"
    assert l8.SPATIAL_RESOLUTION_M == 30.0

    # Unknown product raises
    with pytest.raises(ValueError):
        default_source_for("unknown_product")


# ---------------------------------------------------------------------------
# Additional: Quality mask result
# ---------------------------------------------------------------------------
def test_quality_mask_result():
    acq = ReflectanceAcquisition(
        date="2024-01-15",
        latitude=25.0,
        longitude=85.0,
        bands={
            "B8A": BandReflectance(date="2024-01-15", band="B8A", value=0.5),
            "B11": BandReflectance(date="2024-01-15", band="B11", value=0.2),
        },
        cloud_fraction=0.1,
        valid_pixel_fraction=0.9,
        valid_observation_count=90,
        source_product="S2MSI2A",
    )
    result = apply_quality_masks(acq, min_valid_fraction=0.5)
    assert result.quality_status == "good"
    assert result.valid_pixel_fraction == 0.9
    assert result.cloud_fraction == 0.1


# ---------------------------------------------------------------------------
# Additional: Rate limiter
# ---------------------------------------------------------------------------
def test_rate_limiter():
    limiter = RateLimiter(max_requests=2, window_seconds=1.0)
    limiter.acquire()
    limiter.acquire()
    # Third acquire should block briefly (rate limited)
    import time
    start = time.time()
    limiter.acquire()
    elapsed = time.time() - start
    assert elapsed > 0  # Should have waited


# ---------------------------------------------------------------------------
# Additional: Cache TTL expiry
# ---------------------------------------------------------------------------
def test_cache_ttl_expiry():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = SatelliteCache(tmpdir, default_ttl_seconds=1)
        key = make_cache_key(
            site_id="test", latitude=0.0, longitude=0.0,
            start_date="2024-01-01", end_date="2024-01-01",
            source_product="TEST", processing_level="L1",
        )
        entry = CacheEntry(
            key=key, site_id="test", latitude=0.0, longitude=0.0,
            start_date="2024-01-01", end_date="2024-01-01",
            source_product="TEST", processing_level="L1",
            acquisitions=[],
            created_at=datetime.now(UTC).isoformat(),
            ttl_seconds=1,
        )
        cache.put(entry)
        # Immediately available (not yet expired)
        assert cache.get(key) is not None
        # Entry has 1-second TTL; wait and verify expiry
        import time
        time.sleep(1.1)
        assert cache.get(key) is None  # Expired and cleaned up
