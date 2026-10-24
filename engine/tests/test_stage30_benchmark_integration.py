"""Tests for Stage 30: Benchmark integration with dataset manifest.

Tests cover:
- BenchmarkSpec integration with DatasetManifest
- check_prerequisites uses manifest for real data verification
- Synthetic manifest blocks benchmark
- Real manifest with complete protocol → READY
- produce_benchmark_report with manifest integration
- DatasetProvenance propagation through the pipeline
"""

from __future__ import annotations

from engine.hydroma.eval.benchmark import (
    BenchmarkBlocker,
    BenchmarkSpec,
    BenchmarkStatus,
    DatasetProvenance,
)
from engine.hydroma.eval.benchmark_report import produce_benchmark_report
from engine.hydroma.eval.dataset_manifest import (
    DataProvenance,
    DatasetManifest,
    FileHash,
    check_data_independence,
    create_real_dataset_manifest,
    create_synthetic_manifest,
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


class TestBenchmarkWithManifest:
    """Tests for BenchmarkSpec.check_prerequisites with DatasetManifest."""

    def test_manifest_synthetic_blocks(self):
        """Synthetic manifest → BLOCKED."""
        manifest = create_synthetic_manifest()
        spec = BenchmarkSpec(protocol=_make_complete_protocol())

        inventory = _manifest_to_inventory(manifest)
        blockers = spec.check_prerequisites(inventory)
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in blockers

    def test_manifest_real_allows_with_protocol(self):
        """Real manifest + complete protocol → no blockers."""
        manifest = create_real_dataset_manifest(
            dataset_id="real_ds",
            dataset_version="1.0",
            title="Real Data",
            publisher="USDA",
            license_url="https://data.gov",
            source_url="https://data.gov/ds",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("data.csv", "abc123", 1000)],
            yield_observations_available=True,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec(protocol=_make_complete_protocol())

        inventory = _manifest_to_inventory(manifest)
        blockers = spec.check_prerequisites(inventory)
        assert blockers == []

    def test_manifest_no_yield_blocks(self):
        """Manifest without yield observations → BLOCKED."""
        manifest = create_real_dataset_manifest(
            dataset_id="weather_only",
            dataset_version="1.0",
            title="Weather Data",
            publisher="NOAA",
            license_url="https://noaa.gov",
            source_url="https://noaa.gov",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("weather.csv", "abc", 500)],
            yield_observations_available=False,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec(protocol=_make_complete_protocol())

        inventory = _manifest_to_inventory(manifest)
        blockers = spec.check_prerequisites(inventory)
        assert BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA in blockers

    def test_manifest_no_weather_blocks(self):
        """Manifest without weather → BLOCKED."""
        manifest = create_real_dataset_manifest(
            dataset_id="yield_only",
            dataset_version="1.0",
            title="Yield Data",
            publisher="USDA",
            license_url="https://data.gov",
            source_url="https://data.gov",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("yield.csv", "abc", 500)],
            yield_observations_available=True,
            weather_observations_available=False,
        )
        spec = BenchmarkSpec(protocol=_make_complete_protocol())

        inventory = _manifest_to_inventory(manifest)
        blockers = spec.check_prerequisites(inventory)
        assert BenchmarkBlocker.NO_WEATHER_INPUTS in blockers

    def test_independence_check_integration(self):
        """Independent manifest passes independence check."""
        manifest = create_real_dataset_manifest(
            dataset_id="independent_ds",
            dataset_version="1.0",
            title="Independent Data",
            publisher="University",
            license_url="https://univ.edu",
            source_url="https://univ.edu",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("data.csv", "abc", 1000)],
            yield_observations_available=True,
            weather_observations_available=True,
            calibration_overlap="none",
        )
        result = check_data_independence(manifest, {"cal_ds"})
        assert result.status.value == "pass"


class TestProvenancePropagation:
    """Tests that DatasetProvenance is correctly propagated through the pipeline."""

    def test_synthetic_provenance_in_report(self):
        """Synthetic provenance → BLOCKED report marks synthetic."""
        manifest = create_synthetic_manifest()
        spec = BenchmarkSpec()
        inventory = _manifest_to_inventory(manifest)
        report = produce_benchmark_report(spec, dataset_inventory=inventory)
        assert report.benchmark_status == BenchmarkStatus.BLOCKED
        assert report.dataset.provenance == DatasetProvenance.SYNTHETIC_TEST_FIXTURES

    def test_real_provenance_in_report(self):
        """Real provenance with complete protocol → READY report."""
        manifest = create_real_dataset_manifest(
            dataset_id="real_ds",
            dataset_version="1.0",
            title="Real Data",
            publisher="USDA",
            license_url="https://data.gov",
            source_url="https://data.gov",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("data.csv", "abc", 1000)],
            yield_observations_available=True,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inventory = _manifest_to_inventory(manifest)
        report = produce_benchmark_report(spec, dataset_inventory=inventory)
        assert report.benchmark_status == BenchmarkStatus.READY
        assert report.dataset.provenance == DatasetProvenance.REAL_FIELD_OBSERVATIONS


class TestBenchmarkReportWithManifestData:
    """Tests that BenchmarkReport includes manifest-derived dataset info."""

    def test_report_includes_dataset_coverage(self):
        """Report includes crop/site/season counts from manifest."""
        manifest = create_real_dataset_manifest(
            dataset_id="real_ds",
            dataset_version="1.0",
            title="Real Data",
            publisher="USDA",
            license_url="https://data.gov",
            source_url="https://data.gov",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("data.csv", "abc", 1000)],
            yield_observations_available=True,
            weather_observations_available=True,
            crop_count=5,
            site_count=20,
            season_count=3,
            observation_count=500,
        )
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inventory = _manifest_to_inventory(manifest)
        report = produce_benchmark_report(spec, dataset_inventory=inventory)

        assert report.dataset.crop_count == 5
        assert report.dataset.site_count == 20
        assert report.dataset.season_count == 3
        assert report.dataset.observation_count == 500

    def test_report_includes_input_availability(self):
        """Report includes which inputs are available."""
        manifest = create_real_dataset_manifest(
            dataset_id="real_ds",
            dataset_version="1.0",
            title="Real Data",
            publisher="USDA",
            license_url="https://data.gov",
            source_url="https://data.gov",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("data.csv", "abc", 1000)],
            yield_observations_available=True,
            weather_observations_available=True,
            par_available=True,
            lai_available=False,
            ews_inputs_available=True,
        )
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inventory = _manifest_to_inventory(manifest)
        report = produce_benchmark_report(spec, dataset_inventory=inventory)

        assert report.dataset.par_available is True
        assert report.dataset.lai_available is False
        assert report.dataset.ews_inputs_available is True


class TestNoSyntheticDataInEvaluation:
    """Critical tests: synthetic data cannot enter evaluation path."""

    def test_synthetic_manifest_blocked(self):
        """A synthetic manifest alone blocks the benchmark."""
        manifest = create_synthetic_manifest()
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inventory = _manifest_to_inventory(manifest)
        status = spec.evaluate_status(inventory)
        assert status == BenchmarkStatus.BLOCKED

    def test_mixed_no_synthetic_accepted(self):
        """A real manifest does not get blocked as synthetic."""
        manifest = create_real_dataset_manifest(
            dataset_id="real_ds",
            dataset_version="1.0",
            title="Real",
            publisher="USDA",
            license_url="https://data.gov",
            source_url="https://data.gov",
            date_acquired="2024-01-01",
            data_format="csv",
            file_hashes=[FileHash("data.csv", "abc", 1000)],
            yield_observations_available=True,
            weather_observations_available=True,
        )
        spec = BenchmarkSpec(protocol=_make_complete_protocol())
        inventory = _manifest_to_inventory(manifest)
        assert inventory.provenance != DatasetProvenance.SYNTHETIC_TEST_FIXTURES
        status = spec.evaluate_status(inventory)
        assert status == BenchmarkStatus.READY


def _manifest_to_inventory(manifest: DatasetManifest):
    """Convert a DatasetManifest to a DatasetInventory for benchmark checks."""
    from engine.hydroma.eval.benchmark import DatasetInventory

    return DatasetInventory(
        dataset_id=manifest.dataset_id,
        dataset_version=manifest.dataset_version,
        dataset_source=manifest.source_url,
        provenance=(
            DatasetProvenance.REAL_FIELD_OBSERVATIONS
            if manifest.provenance == DataProvenance.REAL_FIELD_OBSERVATIONS
            else DatasetProvenance.SYNTHETIC_TEST_FIXTURES
        ),
        observation_source=manifest.publisher,
        crop_count=manifest.crop_count,
        site_count=manifest.site_count,
        field_count=manifest.field_count,
        season_count=manifest.season_count,
        observation_count=manifest.observation_count,
        yield_observations_available=manifest.yield_observations_available,
        weather_observations_available=manifest.weather_observations_available,
        par_available=manifest.par_available,
        lai_available=manifest.lai_available,
        ews_inputs_available=manifest.ews_inputs_available,
        calibration_overlap=manifest.calibration_overlap,
    )
