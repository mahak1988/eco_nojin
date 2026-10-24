"""Tests for Stage 30: Dataset manifest and provenance tracking.

Tests cover:
- DatasetManifest creation and defaults
- is_real_data() / is_synthetic() checks
- create_real_dataset_manifest enforces provenance fields
- create_synthetic_manifest is explicitly synthetic
- compute_file_hash and verify_file_integrity
- DatasetProvenance enum
- to_dict() serialization
"""

from __future__ import annotations

import pytest

from engine.hydroma.eval.dataset_manifest import (
    DataFormat,
    DataProvenance,
    DataQualityCheckError,
    DatasetManifest,
    FileHash,
    check_data_independence,
    check_duplicate_records,
    check_no_synthetic_label,
    check_required_fields_present,
    check_yield_unit_consistency,
    compute_file_hash,
    compute_hashes,
    create_real_dataset_manifest,
    create_synthetic_manifest,
    run_data_quality_checks,
    verify_file_integrity,
)


class TestDataProvenance:
    def test_enum_values(self):
        assert DataProvenance.REAL_FIELD_OBSERVATIONS.value == "real_field_observations"
        assert DataProvenance.SYNTHETIC_TEST_FIXTURES.value == "synthetic_test_fixtures"
        assert DataProvenance.UNKNOWN.value == "unknown"


class TestDataFormat:
    def test_enum_values(self):
        assert DataFormat.CSV.value == "csv"
        assert DataFormat.JSON.value == "json"
        assert DataFormat.PARQUET.value == "parquet"


class TestDatasetManifest:
    def test_default_manifest(self):
        manifest = DatasetManifest(
            dataset_id="test_ds",
            dataset_version="1.0",
            title="Test Dataset",
            provenance=DataProvenance.UNKNOWN,
        )
        assert manifest.dataset_id == "test_ds"
        assert manifest.provenance == DataProvenance.UNKNOWN
        assert manifest.file_count == 0
        assert manifest.file_hashes == []
        assert manifest.yield_observations_available is False

    def test_is_synthetic_defaults(self):
        """Default dataset is not real."""
        manifest = DatasetManifest(
            dataset_id="test", dataset_version="1.0", title="test",
        )
        assert manifest.is_real_data() is False
        assert manifest.is_synthetic() is False

    def test_is_real_data_complete(self):
        """Real data with all fields → is_real_data() True."""
        manifest = create_real_dataset_manifest(
            dataset_id="real_ds",
            dataset_version="1.0",
            title="Real Field Data",
            publisher="USDA",
            license_url="https://data.gov/license",
            source_url="https://data.gov/dataset",
            date_acquired="2024-01-01",
            data_format=DataFormat.CSV,
            file_hashes=[FileHash("yield_data.csv", "abc123", 1000)],
        )
        assert manifest.is_real_data() is True
        assert manifest.is_synthetic() is False

    def test_is_real_data_missing_publisher(self):
        """Missing publisher → not real."""
        manifest = DatasetManifest(
            dataset_id="ds",
            dataset_version="1.0",
            title="test",
            provenance=DataProvenance.REAL_FIELD_OBSERVATIONS,
            file_hashes=[FileHash("f.csv", "abc", 100)],
            yield_observations_available=True,
        )
        assert manifest.is_real_data() is False

    def test_to_dict(self):
        manifest = create_real_dataset_manifest(
            dataset_id="real_ds",
            dataset_version="1.0",
            title="Real Data",
            publisher="USDA",
            license_url="https://data.gov/license",
            source_url="https://data.gov",
            date_acquired="2024-01-01",
            data_format=DataFormat.CSV,
            file_hashes=[FileHash("data.csv", "abc", 1000)],
            crop_count=3,
            site_count=12,
        )
        d = manifest.to_dict()
        assert d["dataset_id"] == "real_ds"
        assert d["provenance"] == "real_field_observations"
        assert d["file_hashes"][0]["filename"] == "data.csv"
        assert d["coverage"]["site_count"] == 12


class TestCreateRealDatasetManifest:
    def test_requires_publisher(self):
        with pytest.raises(ValueError, match="publisher"):
            create_real_dataset_manifest(
                dataset_id="ds", dataset_version="1.0", title="t",
                publisher="", license_url="https://x",
                source_url="https://x", date_acquired="2024-01-01",
                data_format=DataFormat.CSV,
                file_hashes=[FileHash("f.csv", "abc", 100)],
            )

    def test_requires_license_url(self):
        with pytest.raises(ValueError, match="license_url"):
            create_real_dataset_manifest(
                dataset_id="ds", dataset_version="1.0", title="t",
                publisher="USDA", license_url="",
                source_url="https://x", date_acquired="2024-01-01",
                data_format=DataFormat.CSV,
                file_hashes=[FileHash("f.csv", "abc", 100)],
            )

    def test_requires_file_hashes(self):
        with pytest.raises(ValueError, match="file_hashes"):
            create_real_dataset_manifest(
                dataset_id="ds", dataset_version="1.0", title="t",
                publisher="USDA", license_url="https://x",
                source_url="https://x", date_acquired="2024-01-01",
                data_format=DataFormat.CSV,
                file_hashes=[],
            )


class TestCreateSyntheticManifest:
    def test_is_synthetic(self):
        manifest = create_synthetic_manifest()
        assert manifest.is_synthetic() is True
        assert manifest.is_real_data() is False

    def test_custom_dataset_id(self):
        manifest = create_synthetic_manifest(
            dataset_id="my_synth",
            title="My Test Data",
        )
        assert manifest.dataset_id == "my_synth"
        assert manifest.title == "My Test Data"


class TestFileHash:
    def test_compute_hash(self, tmp_path):
        """compute_file_hash returns correct hash and size."""
        test_file = tmp_path / "test.csv"
        content = b"site_id,season,crop,yield\nS1,s1,wheat,5.0\n"
        test_file.write_bytes(content)

        fh = compute_file_hash(test_file)
        assert fh.filename == "test.csv"
        assert fh.size_bytes == len(content)
        assert len(fh.sha256) == 64

    def test_compute_file_hash_missing_file(self):
        with pytest.raises(FileNotFoundError):
            compute_file_hash("/nonexistent/path/file.csv")

    def test_compute_hashes_multiple(self, tmp_path):
        f1 = tmp_path / "f1.csv"
        f1.write_bytes(b"data1")
        f2 = tmp_path / "f2.csv"
        f2.write_bytes(b"data2")

        hashes = compute_hashes([f1, f2])
        assert len(hashes) == 2
        assert hashes[0].filename == "f1.csv"
        assert hashes[1].filename == "f2.csv"

    def test_verify_integrity_ok(self, tmp_path):
        test_file = tmp_path / "test.csv"
        content = b"test data content"
        test_file.write_bytes(content)

        fh = compute_file_hash(test_file)
        errors = verify_file_integrity([fh], base_path=tmp_path)
        assert errors == []

    def test_verify_integrity_missing_file(self):
        fh = FileHash("missing.csv", "abc123", 100)
        errors = verify_file_integrity([fh])
        assert len(errors) == 1
        assert "missing" in errors[0].lower()

    def test_verify_integrity_corrupted(self, tmp_path):
        test_file = tmp_path / "test.csv"
        test_file.write_bytes(b"original content")

        fh = FileHash("test.csv", "wrong_hash_value_here", 100)
        errors = verify_file_integrity([fh], base_path=tmp_path)
        assert len(errors) >= 1


class TestDataQualityChecks:
    def test_yield_unit_consistency_valid(self):
        result = check_yield_unit_consistency(
            [5.0, 6.0, 7.0], ["t/ha", "kg/ha", "t/ha"]
        )
        assert result.status == DataQualityCheckError.PASS

    def test_yield_unit_consistency_invalid_unit(self):
        result = check_yield_unit_consistency(
            [5.0], ["invalid_unit"]
        )
        assert result.status == DataQualityCheckError.FAIL

    def test_yield_unit_consistency_negative(self):
        result = check_yield_unit_consistency(
            [-1.0], ["t/ha"]
        )
        assert result.status == DataQualityCheckError.FAIL

    def test_yield_unit_consistency_non_finite(self):
        result = check_yield_unit_consistency(
            [float("nan")], ["t/ha"]
        )
        assert result.status == DataQualityCheckError.FAIL

    def test_required_fields_present_ok(self):
        records = [{"site_id": "S1", "season_id": "s1", "crop": "wheat",
                    "observed_yield": 5.0, "observed_yield_unit": "t/ha"}]
        result = check_required_fields_present(records, {"site_id", "season_id", "crop"})
        assert result.status == DataQualityCheckError.PASS

    def test_required_fields_present_missing(self):
        records = [{"site_id": "S1", "season_id": "", "crop": "wheat",
                    "observed_yield": 5.0, "observed_yield_unit": "t/ha"}]
        result = check_required_fields_present(records, {"site_id", "season_id"})
        assert result.status == DataQualityCheckError.FAIL

    def test_no_synthetic_label_ok(self):
        records = [{"data_label": "real_field_data"}, {"data_label": "field_station"}]
        result = check_no_synthetic_label(records)
        assert result.status == DataQualityCheckError.PASS

    def test_no_synthetic_label_detected(self):
        records = [{"data_label": "real_data"}, {"data_label": "synthetic_test"}]
        result = check_no_synthetic_label(records)
        assert result.status == DataQualityCheckError.FAIL

    def test_duplicate_records_ok(self):
        records = [
            {"site_id": "S1", "season_id": "s1", "crop": "wheat"},
            {"site_id": "S2", "season_id": "s1", "crop": "wheat"},
        ]
        result = check_duplicate_records(records)
        assert result.status == DataQualityCheckError.PASS

    def test_duplicate_records_detected(self):
        records = [
            {"site_id": "S1", "season_id": "s1", "crop": "wheat"},
            {"site_id": "S1", "season_id": "s1", "crop": "wheat"},
        ]
        result = check_duplicate_records(records)
        assert result.status == DataQualityCheckError.WARNING


class TestRunDataQualityChecks:
    def test_real_data_passes(self):
        """Real data records should pass quality checks."""
        records = [
            {"site_id": "S1", "season_id": "s1", "crop": "wheat",
             "observed_yield": 5.0, "observed_yield_unit": "t/ha",
             "data_label": "real_field_data"},
            {"site_id": "S2", "season_id": "s1", "crop": "wheat",
             "observed_yield": 6.0, "observed_yield_unit": "t/ha",
             "data_label": "real_field_data"},
        ]
        report = run_data_quality_checks(records, dataset_id="real_ds")
        assert report.is_blocked is False
        assert report.is_real_data_blocked is False

    def test_synthetic_data_blocked(self):
        """Records with synthetic labels → blocked."""
        records = [
            {"site_id": "S1", "season_id": "s1", "crop": "wheat",
             "observed_yield": 5.0, "observed_yield_unit": "t/ha",
             "data_label": "synthetic_test"},
        ]
        report = run_data_quality_checks(records, dataset_id="synth_ds")
        assert report.is_blocked is True
        assert report.is_real_data_blocked is True

    def test_quality_report_to_dict(self):
        records = [
            {"site_id": "S1", "season_id": "s1", "crop": "wheat",
             "observed_yield": 5.0, "observed_yield_unit": "t/ha",
             "data_label": "real_data"},
        ]
        report = run_data_quality_checks(records, dataset_id="real_ds")
        d = report.to_dict()
        assert d["dataset_id"] == "real_ds"
        assert d["is_blocked"] is False
        assert "checks" in d


class TestCheckDataIndependence:
    def test_independent_passes(self):
        manifest = DatasetManifest(
            dataset_id="eval_ds",
            dataset_version="1.0",
            title="Eval Data",
            provenance=DataProvenance.REAL_FIELD_OBSERVATIONS,
        )
        result = check_data_independence(manifest, {"cal_ds"})
        assert result.status == DataQualityCheckError.PASS

    def test_same_as_calibration_fails(self):
        manifest = DatasetManifest(
            dataset_id="cal_ds",
            dataset_version="1.0",
            title="Cal Data",
            provenance=DataProvenance.REAL_FIELD_OBSERVATIONS,
        )
        result = check_data_independence(manifest, {"cal_ds"})
        assert result.status == DataQualityCheckError.FAIL

    def test_full_overlap_fails(self):
        manifest = DatasetManifest(
            dataset_id="shared_ds",
            dataset_version="1.0",
            title="Shared Data",
            provenance=DataProvenance.REAL_FIELD_OBSERVATIONS,
            calibration_overlap="full",
        )
        result = check_data_independence(manifest, {"cal_ds"})
        assert result.status == DataQualityCheckError.FAIL
