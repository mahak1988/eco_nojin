"""Tests for Stage 29: Benchmark execution and report generation.

Tests cover:
- BenchmarkSpec with various blockers
- produce_benchmark_report returns correct structure
- create_blocked_report produces valid report
- Blocked report does not compute HYRUE predictions
- Blocked report does not produce evaluation metrics
- Report to_dict() serialization
- Integration with ValidationProtocol and produce_validation_report
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
    BenchmarkMetrics,
    create_blocked_report,
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
        observation_count=200,
        yield_observations_available=True,
        weather_observations_available=True,
        par_available=True,
        ews_inputs_available=True,
        calibration_overlap="none",
    )


class TestBenchmarkExecutionStatus:
    """Tests for benchmark execution status transitions."""

    def test_initial_status_not_ready(self):
        """New spec starts as NOT_READY."""
        spec = BenchmarkSpec()
        assert spec.benchmark_status == BenchmarkStatus.NOT_READY

    def test_evaluate_without_data(self):
        """evaluate_status with no data → BLOCKED."""
        spec = BenchmarkSpec()
        status = spec.evaluate_status(None)
        assert status == BenchmarkStatus.BLOCKED
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in spec.blockers

    def test_evaluate_with_synthetic(self):
        """evaluate_status with synthetic data → BLOCKED."""
        spec = BenchmarkSpec()
        inv = DatasetInventory(
            dataset_id="synth",
            dataset_version="1.0",
            provenance=DatasetProvenance.SYNTHETIC_TEST_FIXTURES,
            observation_source="synth",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        status = spec.evaluate_status(inv)
        assert status == BenchmarkStatus.BLOCKED

    def test_evaluate_with_real_data_ready(self):
        """evaluate_status with real data + protocol → READY."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        status = spec.evaluate_status(inv)
        assert status == BenchmarkStatus.READY
        assert spec.blockers == []

    def test_ready_does_not_claim_validated(self):
        """READY status must not be confused with VALIDATED_EXTERNAL."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        status = spec.evaluate_status(inv)
        assert status == BenchmarkStatus.READY
        assert status != BenchmarkStatus.COMPLETED
        assert status != BenchmarkStatus.FAILED


class TestNoHyRUEExecutionOnBlock:
    """Tests that no model execution happens when benchmark is blocked."""

    def test_blocked_report_no_hyrau_call(self):
        """Produce blocked report — no HYRUE computation."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        # The report is generated without calling compute_seasonal_prediction
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.metrics is None

    def test_blocked_report_to_dict_has_no_metrics(self):
        """to_dict() of BLOCKED report has metrics = None."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        d = report.to_dict()
        assert d["metrics"] is None
        assert d["validation_output"] is None


class TestCreateBlockedReport:
    """Tests for create_blocked_report factory."""

    def test_blocked_report_with_inventory(self):
        """create_blocked_report with synthetic inventory."""
        spec = BenchmarkSpec()
        inv = DatasetInventory(
            dataset_id="synth",
            dataset_version="1.0",
            provenance=DatasetProvenance.SYNTHETIC_TEST_FIXTURES,
            observation_source="synth",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        report = create_blocked_report(spec, dataset_inventory=inv, reason="test")
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.dataset.provenance == DatasetProvenance.SYNTHETIC_TEST_FIXTURES
        assert report.external_validation_status == "blocked"

    def test_blocked_report_without_inventory(self):
        """create_blocked_report without inventory."""
        spec = BenchmarkSpec()
        report = create_blocked_report(spec, dataset_inventory=None, reason="test")
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.dataset.dataset_id == ""


class TestReportSerialization:
    """Tests for BenchmarkReport.to_dict()."""

    def test_blocked_report_to_dict(self):
        """to_dict() works for BLOCKED report."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        d = report.to_dict()

        assert d["benchmark_status"] == "blocked"
        assert d["report_id"].startswith("BENCHRPT-")
        assert d["model"]["name"] == "HY-RUE"
        assert d["dataset"]["provenance"] == "synthetic_test_fixtures"
        assert d["metrics"] is None
        assert d["validation_output"] is None
        assert d["external_validation_status"] == "blocked"
        assert len(d["scientific_limitations"]) > 0
        assert len(d["blockers"]) > 0

    def test_ready_report_to_dict(self):
        """to_dict() works for READY report."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        d = report.to_dict()

        assert d["benchmark_status"] == "ready"
        assert d["dataset"]["provenance"] == "real_field_observations"
        assert d["dataset"]["coverage"]["site_count"] == 12
        assert d["metrics"] is None
        assert d["external_validation_status"] == "not_assessed"


class TestBenchmarkMetrics:
    """Tests for BenchmarkMetrics dataclass."""

    def test_defaults_none(self):
        """All metrics default to None."""
        m = BenchmarkMetrics()
        assert m.mae is None
        assert m.rmse is None
        assert m.bias is None
        assert m.r_squared is None
        assert m.mape is None
        assert m.n_valid_pairs == 0

    def test_with_values(self):
        """Metrics can be set."""
        m = BenchmarkMetrics(
            mae=0.5,
            rmse=0.7,
            bias=0.1,
            r_squared=0.85,
            mape=8.3,
            n_valid_pairs=42,
        )
        assert m.mae == 0.5
        assert m.n_valid_pairs == 42


class TestStage28Integration:
    """Tests that BenchmarkReport correctly integrates with Stage 28."""

    def test_blocked_status_propagates(self):
        """Benchmark BLOCKED → external_validation_status = blocked."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        assert report.external_validation_status == "blocked"

    def test_ready_does_not_propagate_validated(self):
        """Benchmark READY → external_validation_status is not_assessed."""
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inv = _make_real_inventory()
        report = produce_benchmark_report(spec, inv)
        assert report.external_validation_status == "not_assessed"

    def test_no_validation_output_on_block(self):
        """No ValidationOutput is produced when benchmark is blocked."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        assert report.validation_output is None
