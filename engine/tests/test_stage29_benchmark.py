"""Tests for Stage 29: Benchmark specification and status evaluation.

Tests cover:
- BenchmarkSpec creation with defaults
- BenchmarkStatus enum values
- InputPolicy enum values
- DatasetProvenance enum values
- BenchmarkBlocker enum values
- DatasetInventory dataclass
- check_prerequisites() with various data scenarios
- evaluate_status() returns BLOCKED when prerequisites are unmet
- evaluate_status() returns READY when real data is provided
- to_dict() serialization
"""

from __future__ import annotations

from engine.hydroma.eval.benchmark import (
    BenchmarkBlocker,
    BenchmarkSpec,
    BenchmarkStatus,
    DatasetInventory,
    DatasetProvenance,
    InputPolicy,
)
from engine.hydroma.eval.validation_protocol import (
    EvaluationTarget,
    ValidationProtocol,
)


class TestBenchmarkStatus:
    """Tests for BenchmarkStatus enum."""

    def test_values(self):
        assert BenchmarkStatus.NOT_READY.value == "not_ready"
        assert BenchmarkStatus.BLOCKED.value == "blocked"
        assert BenchmarkStatus.READY.value == "ready"
        assert BenchmarkStatus.RUNNING.value == "running"
        assert BenchmarkStatus.COMPLETED.value == "completed"
        assert BenchmarkStatus.FAILED.value == "failed"


class TestInputPolicy:
    """Tests for InputPolicy enum."""

    def test_values(self):
        assert InputPolicy.STRICT.value == "strict"
        assert InputPolicy.ALLOW_ESTIMATED_INPUTS.value == "allow_estimated_inputs"


class TestDatasetProvenance:
    """Tests for DatasetProvenance enum."""

    def test_values(self):
        assert (
            DatasetProvenance.REAL_FIELD_OBSERVATIONS.value
            == "real_field_observations"
        )
        assert DatasetProvenance.SYNTHETIC_TEST_FIXTURES.value == "synthetic_test_fixtures"


class TestBenchmarkBlocker:
    """Tests for BenchmarkBlocker enum."""

    def test_values(self):
        assert (
            BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA.value
            == "no_real_field_yield_data"
        )
        assert BenchmarkBlocker.NO_VALIDATION_DATASET.value == "no_validation_dataset"
        assert (
            BenchmarkBlocker.NO_INDEPENDENT_EVALUATION_DATA.value
            == "no_independent_evaluation_data"
        )


class TestDatasetInventory:
    """Tests for DatasetInventory dataclass."""

    def test_defaults(self):
        """DatasetInventory has sensible defaults."""
        inv = DatasetInventory(
            dataset_id="test_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_campaign_2024",
        )
        assert inv.dataset_id == "test_ds"
        assert inv.crop_count == 0
        assert inv.site_count == 0
        assert inv.yield_observations_available is False


class TestBenchmarkSpecCreation:
    """Tests for BenchmarkSpec construction and defaults."""

    def test_default_spec(self):
        """Default spec is NOT_READY."""
        spec = BenchmarkSpec()
        assert spec.benchmark_id.startswith("BENCH-")
        assert spec.benchmark_version == "1.0"
        assert spec.dataset_id == ""
        assert spec.dataset_provenance == DatasetProvenance.REAL_FIELD_OBSERVATIONS
        assert spec.evaluation_target == EvaluationTarget.NONE
        assert spec.input_policy == InputPolicy.STRICT
        assert spec.benchmark_status == BenchmarkStatus.NOT_READY
        assert spec.blockers == []

    def test_spec_with_protocol(self):
        """Spec with protocol and real data inventory can be READY."""
        protocol = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="spatial test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S1", "S2", "S3"],
            seasons_in_scope=["s1"],
        )
        spec = BenchmarkSpec(
            protocol=protocol,
            evaluation_target=EvaluationTarget.SPATIAL,
            model_parameters_hash="abc123",
        )
        assert spec.protocol == protocol
        assert spec.evaluation_target == EvaluationTarget.SPATIAL


class TestCheckPrerequisites:
    """Tests for BenchmarkSpec.check_prerequisites()."""

    def test_no_inventory_returns_blockers(self):
        """No inventory → blockers returned."""
        spec = BenchmarkSpec()
        blockers = spec.check_prerequisites(None)
        assert BenchmarkBlocker.NO_VALIDATION_DATASET in blockers
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in blockers
        assert BenchmarkBlocker.INCOMPLETE_PROTOCOL in blockers

    def test_synthetic_data_blocked(self):
        """Synthetic data → NO_REAL_FIELD_YIELD_DATA blocker."""
        inv = DatasetInventory(
            dataset_id="synth_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.SYNTHETIC_TEST_FIXTURES,
            observation_source="synthetic",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec()
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in blockers

    def test_no_yield_data_blocked(self):
        """Real provenance but no yield observations → blocker."""
        inv = DatasetInventory(
            dataset_id="real_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_station_2024",
            yield_observations_available=False,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec()
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in blockers

    def test_no_weather_data_blocked(self):
        """Real provenance, yield data, but no weather → blocker."""
        inv = DatasetInventory(
            dataset_id="real_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_station_2024",
            yield_observations_available=True,
            weather_observations_available=False,
        )
        spec = BenchmarkSpec()
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.NO_WEATHER_INPUTS in blockers

    def test_no_protocol_blocked(self):
        """No protocol → INCOMPLETE_PROTOCOL blocker."""
        inv = DatasetInventory(
            dataset_id="real_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_station_2024",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec()
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.INCOMPLETE_PROTOCOL in blockers

    def test_incomplete_protocol_blocked(self):
        """Incomplete protocol → INCOMPLETE_PROTOCOL blocker."""
        inv = DatasetInventory(
            dataset_id="real_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_station_2024",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        protocol = ValidationProtocol()  # default is incomplete
        spec = BenchmarkSpec(protocol=protocol)
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.INCOMPLETE_PROTOCOL in blockers

    def test_same_cal_val_dataset_blocked(self):
        """Same calibration/validation dataset → NOT_INDEPENDENT blocker."""
        inv = DatasetInventory(
            dataset_id="real_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_station_2024",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        protocol = ValidationProtocol(
            calibration_dataset_id="same_ds",
            validation_dataset_id="same_ds",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="spatial test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S1", "S2", "S3"],
            seasons_in_scope=["s1"],
        )
        spec = BenchmarkSpec(protocol=protocol)
        blockers = spec.check_prerequisites(inv)
        assert BenchmarkBlocker.NO_INDEPENDENT_EVALUATION_DATA in blockers

    def test_all_prerequisites_met(self):
        """Real data + complete protocol + distinct datasets → no blockers."""
        inv = DatasetInventory(
            dataset_id="real_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_station_2024",
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
        )
        protocol = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="spatial test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S1", "S2", "S3"],
            seasons_in_scope=["s1"],
        )
        spec = BenchmarkSpec(protocol=protocol)
        blockers = spec.check_prerequisites(inv)
        assert blockers == []


class TestEvaluateStatus:
    """Tests for BenchmarkSpec.evaluate_status()."""

    def test_blocked_without_data(self):
        """No inventory → BLOCKED."""
        spec = BenchmarkSpec()
        status = spec.evaluate_status(None)
        assert status == BenchmarkStatus.BLOCKED
        assert len(spec.blockers) > 0

    def test_blocked_with_synthetic(self):
        """Synthetic data → BLOCKED."""
        inv = DatasetInventory(
            dataset_id="synth_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.SYNTHETIC_TEST_FIXTURES,
            observation_source="synthetic",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec()
        status = spec.evaluate_status(inv)
        assert status == BenchmarkStatus.BLOCKED

    def test_ready_with_real_data(self):
        """Real data + complete protocol → READY."""
        inv = DatasetInventory(
            dataset_id="real_ds",
            dataset_version="1.0",
            provenance=DatasetProvenance.REAL_FIELD_OBSERVATIONS,
            observation_source="field_station_2024",
            yield_observations_available=True,
            weather_observations_available=True,
        )
        protocol = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="spatial test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S1", "S2", "S3"],
            seasons_in_scope=["s1"],
        )
        spec = BenchmarkSpec(protocol=protocol)
        status = spec.evaluate_status(inv)
        assert status == BenchmarkStatus.READY
        assert spec.blockers == []


class TestBenchmarkSpecSerialization:
    """Tests for BenchmarkSpec.to_dict()."""

    def test_to_dict(self):
        """to_dict returns expected structure."""
        spec = BenchmarkSpec(
            dataset_id="test_ds",
            dataset_version="1.0",
            dataset_source="/path/to/data",
            evaluation_target=EvaluationTarget.SPATIAL,
            input_policy=InputPolicy.ALLOW_ESTIMATED_INPUTS,
        )
        d = spec.to_dict()
        assert d["benchmark_id"].startswith("BENCH-")
        assert d["dataset_id"] == "test_ds"
        assert d["evaluation_target"] == "spatial"
        assert d["input_policy"] == "allow_estimated_inputs"
        assert d["protocol"] is None

    def test_to_dict_with_protocol(self):
        """to_dict includes protocol when provided."""
        protocol = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S1", "S2", "S3"],
            seasons_in_scope=["s1"],
        )
        spec = BenchmarkSpec(protocol=protocol)
        d = spec.to_dict()
        assert d["protocol"] is not None
        assert d["protocol"]["evaluation_target"] == "spatial"
