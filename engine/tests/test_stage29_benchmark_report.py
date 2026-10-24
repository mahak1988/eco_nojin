"""Tests for Stage 29: Benchmark report generation.

Tests cover:
- BenchmarkReport fields and defaults
- DatasetInfo fields
- produce_benchmark_report structure for blocked and ready states
- Report correctly reflects no real data
- Report to_dict() output structure
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
    BenchmarkReport,
    DatasetInfo,
    produce_benchmark_report,
)
from engine.hydroma.eval.validation_protocol import EvaluationTarget


def _make_real_inventory() -> DatasetInventory:
    return DatasetInventory(
        dataset_id="real_ds",
        dataset_version="1.0",
        dataset_source="/data/real",
        provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
        observation_source="field_campaign",
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


class TestBenchmarkReportStructure:
    """Tests for BenchmarkReport dataclass structure."""

    def test_default_construction(self):
        """BenchmarkReport can be constructed with required fields."""
        report = BenchmarkReport(
            benchmark_id="BENCH-TEST",
            dataset=DatasetInfo(
                dataset_id="test",
                dataset_version="1.0",
                dataset_source="/data",
                provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            ),
            model_name="HY-RUE",
            model_version="2.0.0",
            model_parameters_hash="sha256:abc",
            evaluation_target=EvaluationTarget.SPATIAL,
            unit_of_independence="site",
            input_policy="strict",
            benchmark_status=BenchmarkStatus.BLOCKED,
            blockers=[BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA],
        )
        assert report.benchmark_id == "BENCH-TEST"
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.external_validation_status == "not_assessed"
        assert report.metrics is None
        assert report.validation_output is None

    def test_to_dict_has_all_sections(self):
        """to_dict() includes all expected sections."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        d = report.to_dict()

        assert "report_id" in d
        assert "benchmark_id" in d
        assert "dataset" in d
        assert "model" in d
        assert "evaluation" in d
        assert "benchmark_status" in d
        assert "blockers" in d
        assert "metrics" in d
        assert "validation_output" in d
        assert "external_validation_status" in d
        assert "scientific_limitations" in d
        assert "notes" in d
        assert "generated_at" in d

    def test_to_dict_dataset_section(self):
        """to_dict() dataset section has expected keys."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        d = report.to_dict()

        ds = d["dataset"]
        assert "dataset_id" in ds
        assert "dataset_version" in ds
        assert "dataset_source" in ds
        assert "provenance" in ds
        assert "coverage" in ds
        assert "inputs_available" in ds
        assert "calibration_overlap" in ds

    def test_to_dict_model_section(self):
        """to_dict() model section has expected keys."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        d = report.to_dict()

        model = d["model"]
        assert "name" in model
        assert "version" in model
        assert "parameters_hash" in model

    def test_to_dict_evaluation_section(self):
        """to_dict() evaluation section has expected keys."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        d = report.to_dict()

        ev = d["evaluation"]
        assert "evaluation_target" in ev
        assert "unit_of_independence" in ev
        assert "input_policy" in ev

    def test_to_dict_blockers_are_string_values(self):
        """to_dict() blockers are string representations."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        d = report.to_dict()

        assert len(d["blockers"]) > 0
        for blocker in d["blockers"]:
            assert isinstance(blocker, str)
            assert blocker == "no_real_field_yield_data" or \
                   blocker == "no_validation_dataset" or \
                   blocker == "incomplete_protocol"


class TestDatasetInfo:
    """Tests for DatasetInfo dataclass."""

    def test_defaults(self):
        """DatasetInfo has sensible defaults."""
        info = DatasetInfo(
            dataset_id="ds1",
            dataset_version="1.0",
            dataset_source="/data",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
        )
        assert info.dataset_id == "ds1"
        assert info.crop_count == 0
        assert info.yield_observations_available is False


class TestReportNoRealData:
    """Tests that report explicitly reflects absence of real data."""

    def test_blocked_report_no_hyrau_calls(self):
        """No HYRUE computation occurs in blocked report."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        assert report.metrics is None
        assert report.validation_output is None

    def test_blocked_report_no_metrics_fields(self):
        """Blocked report does not populate any metric fields."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        # No metric values should be present
        assert report.metrics is None

    def test_synthetic_data_report_marked(self):
        """Report from synthetic data is explicitly marked as such."""
        spec = BenchmarkSpec()
        inv = DatasetInventory(
            dataset_id="synth",
            dataset_version="1.0",
            provenance=DatasetProvenance.SYNTHETIC_TEST_FIXTURES,
            observation_source="synth",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        report = produce_benchmark_report(spec, dataset_inventory=inv)
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.dataset.provenance == DatasetProvenance.SYNTHETIC_TEST_FIXTURES

    def test_blocked_report_notes_mention_no_real_data(self):
        """Blocked report notes mention absence of real data."""
        spec = BenchmarkSpec()
        report = produce_benchmark_report(spec, None)
        notes_text = " ".join(report.notes).lower()
        limitations_text = " ".join(report.scientific_limitations).lower()
        combined = notes_text + limitations_text
        assert "no real" in combined or "synthetic" in combined or "blocked" in combined
