"""Unit tests for the three-level MRV module (EM-01): QA/QC and metrics."""

import pytest

from engine.hydroma.mrv import metrics
from engine.hydroma.mrv.qa import is_usable, validate_reading, validate_satellite_index


# ============================================================================
# QA/QC boundaries
# ============================================================================
class TestQaQcBoundaries:
    """Physical-range screening for IoT readings and satellite indices."""

    def test_soil_moisture_ok_suspect_rejected(self):
        assert validate_reading("soil_moisture", 50.0).qa_status == "ok"
        assert validate_reading("soil_moisture", 97.0).qa_status == "suspect"
        assert validate_reading("soil_moisture", 0.0).qa_status == "suspect"
        assert validate_reading("soil_moisture", 101.0).qa_status == "rejected"
        assert validate_reading("soil_moisture", -5.0).qa_status == "rejected"

    def test_temp_and_ec_bands(self):
        assert validate_reading("temp", 25.0).qa_status == "ok"
        assert validate_reading("temp", -30.0).qa_status == "suspect"
        assert validate_reading("temp", 55.0).qa_status == "suspect"
        assert validate_reading("temp", -50.0).qa_status == "rejected"
        assert validate_reading("ec", 3.0).qa_status == "ok"
        assert validate_reading("ec", 18.0).qa_status == "suspect"
        assert validate_reading("ec", 25.0).qa_status == "rejected"

    def test_ndvi_lai_and_cfactor(self):
        assert validate_satellite_index("NDVI", 0.7).qa_status == "ok"
        assert validate_satellite_index("NDVI", -0.5).qa_status == "suspect"
        assert validate_satellite_index("NDVI", 1.5).qa_status == "rejected"
        assert validate_satellite_index("LAI", 4.0).qa_status == "ok"
        assert validate_satellite_index("LAI", 9.0).qa_status == "suspect"
        assert validate_satellite_index("LAI", 12.0).qa_status == "rejected"
        assert validate_satellite_index("C-factor", 1.5).qa_status == "rejected"

    def test_unknown_sensor_rejected_and_is_usable(self):
        report = validate_reading("uranium_level", 1.0)
        assert report.qa_status == "rejected"
        assert "Unknown" in report.message
        assert not is_usable("rejected")
        assert is_usable("ok") and is_usable("suspect")


# ============================================================================
# Transparent dashboard metrics
# ============================================================================
class TestMetrics:
    """Honest computations with provenance badges."""

    def test_co2e_uses_ipcc_367_factor(self):
        # 10 t C/ha delta over 2 ha -> 20 t C -> 20 * 3.67 = 73.4 t CO2e
        out = metrics.co2e_sequestered(soc_delta_tha=10.0, area_ha=2.0)
        assert out["co2e_sequestered_t"] == pytest.approx(73.4, abs=0.01)
        assert out["data_source"] == "real"
        assert out.get("warning") is None

    def test_erosion_reduction_is_honest(self):
        out = metrics.erosion_reduction(
            soil_loss_before_tha=12.0, soil_loss_after_tha=3.0, area_ha=5.0
        )
        assert out["erosion_before_t_yr"] == pytest.approx(60.0)
        assert out["erosion_after_t_yr"] == pytest.approx(15.0)
        assert out["erosion_reduction_t_yr"] == pytest.approx(45.0)
        assert out["reduction_pct"] == pytest.approx(75.0)
        # negative reduction (erosion increased) must be reported as-is
        worse = metrics.erosion_reduction(3.0, 12.0, 5.0)
        assert worse["erosion_reduction_t_yr"] == pytest.approx(-45.0)

    def test_soc_change_pct(self):
        out = metrics.soc_change_pct(1.5, 1.8)
        assert out["soc_change_pct"] == pytest.approx(20.0)
        # 0.3% SOC x 1.3 g/cm3 x 0.3 m x 10000 = 11.7 t C/ha
        assert out["soc_delta_tha"] == pytest.approx(11.7, abs=0.01)

    def test_simulated_inputs_never_look_real(self):
        out = metrics.compute_dashboard(
            site_id="sim-site",
            rusle_before_tha=10.0,
            rusle_after_tha=4.0,
            area_ha=3.0,
            soc_before_pct=1.5,
            soc_after_pct=1.8,
            households=10,
            income_per_household_usd=500.0,
            observed_sources=["simulated"],
        )
        for metric in out["metrics"].values():
            assert metric["data_source"] == "simulated"
            assert metric["warning"], "simulated metrics must carry a warning"

    def test_dashboard_without_data_never_fabricates(self):
        out = metrics.compute_dashboard(site_id="empty-site")
        for value in out["metrics"].values():
            assert value is None

    def test_dashboard_real_data_no_warning(self):
        out = metrics.compute_dashboard(
            site_id="real-site",
            soc_before_pct=1.0,
            soc_after_pct=1.5,
            area_ha=4.0,
            observed_sources=["real", "real"],
        )
        assert out["metrics"]["soc_change_pct"]["data_source"] == "real"
        assert out["metrics"]["soc_change_pct"].get("warning") is None
        # delta SOC = (1.5-1.0)% * 1.3 * 0.3 * 10000 = 19.5 t/ha * 4 ha * 3.67
        assert out["metrics"]["co2e_sequestered_t"]["co2e_sequestered_t"] == pytest.approx(
            19.5 * 4.0 * 3.67, abs=0.01
        )