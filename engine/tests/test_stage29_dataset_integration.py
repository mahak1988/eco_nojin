"""Tests for Stage 29: Dataset integration and inventory checks.

Tests cover:
- DatasetInventory correctly reflects data availability
- create_blocked_report when no real data
- produce_benchmark_report with synthetic data produces BLOCKED
- produce_benchmark_report with real data and complete protocol produces READY
- Report includes correct scientific limitations
"""

from __future__ import annotations

from engine.hydroma.eval.benchmark import (
    BenchmarkBlocker,
    BenchmarkSpec,
    BenchmarkStatus,
    DatasetInventory,
    DatasetProvenance,
)
from engine.hydroma.eval.benchmark_report import (
    produce_benchmark_report,
)
from engine.hydroma.eval.validation_protocol import (
    EvaluationTarget,
    ValidationProtocol,
)


def _make_complete_protocol() -> ValidationProtocol:
    return ValidationProtocol(
        calibration_dataset_id="cal_v1",
        validation_dataset_id="val_v1",
        evaluation_target=EvaluationTarget.SPATIAL,
        evaluation_scope="spatial test",
        crops_in_scope=["wheat"],
        sites_in_scope=["S1", "S2", "S3"],
        seasons_in_scope=["s1"],
    )


def _make_real_inventory() -> DatasetInventory:
    return DatasetInventory(
        dataset_id="real_field_yield_v1",
        dataset_version="1.0",
        dataset_source="/data/field_observations",
        provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
        observation_source="national_field_campaign_2024",
        crop_count=3,
        site_count=12,
        field_count=48,
        season_count=5,
        observation_count=200,
        yield_observations_available=True,
        weather_observations_available=True,
        par_available=True,
        lai_available=False,
        ews_inputs_available=True,
        calibration_overlap="none",
    )


def _make_synthetic_inventory() -> DatasetInventory:
    return DatasetInventory(
        dataset_id="synth_test_fixtures",
        dataset_version="1.0",
        dataset_source="engine/tests/fixtures/synthetic",
        provenance=DatasetProvenance.SYNTHETIC_TEST_FIXTURES,
        observation_source="synthetic_test_generator",
        crop_count=1,
        site_count=5,
        field_count=5,
        season_count=5,
        observation_count=25,
        yield_observations_available=True,
        weather_observations_available=True,
        par_available=True,
        lai_available=True,
        ews_inputs_available=True,
        calibration_overlap="full",
    )


class TestDatasetInventoryProvenance:
    """Tests that DatasetInventory correctly tracks data provenance."""

    def test_synthetic_provenance_blocked(self):
        """Synthetic data provenance → blocked at prerequisite check."""
        spec = BenchmarkSpec()
        inv = _make_synthetic_inventory()
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in blockers

    def test_real_provenance_passes(self):
        """Real data provenance with complete protocol → no blockers."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        blockers = spec.check_prerequisites(inv)
        assert blockers == []

    def test_synthetic_data_label_detected(self):
        """Synthetic test fixtures must be explicitly marked as such."""
        inv = _make_synthetic_inventory()
        assert inv.provenance == DatasetProvenance.SYNTHETIC_TEST_FIXTURES
        assert inv.observation_source == "synthetic_test_generator"
        assert inv.calibration_overlap == "full"

    def test_no_yield_data_blocked(self):
        """Real provenance but no yield observations → blocked."""
        spec = BenchmarkSpec()
        inv = DatasetInventory(
            dataset_id="real_weather_only",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="met_station_2024",
            yield_observations_available=False,
            weather_observations_available=True,
        )
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in blockers


class TestBlockedReportNoData:
    """Tests for BLOCKED report when no real data is available."""

    def test_blocked_report_no_inventory(self):
        """No inventory → BLOCKED report with correct status."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, dataset_inventory=None)
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.metrics is None
        assert report.validation_output is None
        assert report.external_validation_status == "blocked"
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in report.blockers

    def test_blocked_report_synthetic_data(self):
        """Synthetic data → BLOCKED report."""
        spec = BenchmarkSpec()
        inv = _make_synthetic_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.metrics is None
        assert report.external_validation_status == "blocked"

    def test_blocked_report_synthetic_in_provenance(self):
        """BLOCKED report marks dataset as synthetic."""
        spec = BenchmarkSpec()
        inv = _make_synthetic_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.dataset.provenance == DatasetProvenance.SYNTHETIC_TEST_FIXTURES

    def test_blocked_report_no_metrics(self):
        """BLOCKED report has no metrics computed."""
        spec = BenchmarkSpec()
        inv = _make_synthetic_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.metrics is None

    def test_blocked_report_no_validation_output(self):
        """BLOCKED report has no ValidationOutput."""
        spec = BenchmarkSpec()
        inv = _make_synthetic_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.validation_output is None

    def test_blocked_report_has_sci_limitations(self):
        """BLOCKED report includes scientific limitations."""
        spec = BenchmarkSpec()
        inv = _make_synthetic_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert len(report.scientific_limitations) > 0
        assert any("real" in lim.lower() for lim in report.scientific_limitations)


class TestReadyReportWithRealData:
    """Tests for READY report when real data is available."""

    def test_ready_status_no_metrics(self):
        """READY report has no metrics (execution is separate)."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.benchmark_status == BenchmarkStatus.READY
        assert report.metrics is None
        assert report.validation_output is None
        assert report.external_validation_status == "not_assessed"

    def test_ready_report_has_dataset_info(self):
        """READY report includes full dataset inventory."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.dataset.dataset_id == "real_field_yield_v1"
        assert report.dataset.site_count == 12
        assert report.dataset.observation_count == 200
        assert report.dataset.yield_observations_available is True

    def test_ready_not_validated_external(self):
        """READY report explicitly does not claim validated_external."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.external_validation_status == "not_assessed"
        assert "not yet been executed" in report.scientific_limitations[0]
