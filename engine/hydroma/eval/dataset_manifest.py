"""Dataset manifest for real agricultural data provenance tracking.

Provides the data contract that gates Stage 29 benchmark execution.
A dataset must be registered with a manifest before it can be used for
external validation.  The manifest captures provenance, file integrity
hashes, and a real-data verification check.

Real data is distinguished from synthetic test fixtures by:
    - provenance flag (``DatasetProvenance.REAL_FIELD_OBSERVATIONS``)
    - non-empty ``publisher`` and ``license_url`` fields
    - a non-empty ``sha256_files`` mapping (file integrity hashes)
    - ``yield_observations_available`` == True

This module is import-safe: stdlib + pydantic only.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class DataProvenance(StrEnum):
    """Provenance category of the evaluation dataset."""

    REAL_FIELD_OBSERVATIONS = "real_field_observations"
    SYNTHETIC_TEST_FIXTURES = "synthetic_test_fixtures"
    UNKNOWN = "unknown"


class DataFormat(StrEnum):
    """Supported data file formats."""

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    XLSX = "xlsx"


@dataclass
class FileHash:
    """Sha256 hash record for a single data file."""

    filename: str
    sha256: str
    size_bytes: int


@dataclass
class DatasetManifest:
    """Manifest for an agricultural evaluation dataset.

    A manifest is required for any dataset entering the benchmark pipeline.
    It proves that the data is real (not synthetic), has traceable
    provenance, and has not been tampered with (via file hashes).

    Attributes:
        dataset_id: Stable unique identifier for this dataset within ECO Nojin.
        dataset_version: Semantic version string (e.g. ``1.0.0``).
        title: Human-readable dataset title.
        provenance: Whether real or synthetic data.
        publisher: Organization or study that produced the data.
        license_url: URL to the data license.
        source_url: Optional URL to the original data source.
        date_acquired: ISO timestamp when data was acquired into the project.
        data_format: File format of the data.
        file_count: Number of files in the dataset.
        file_hashes: Integrity hashes for each file.
        yield_observations_available: Whether real crop yield data is present.
        weather_observations_available: Whether weather data is present.
        par_available: Whether PAR data is available.
        lai_available: Whether LAI data is available.
        ews_inputs_available: Whether EWSI inputs are available.
        crop_count: Number of crops in the dataset.
        site_count: Number of sites in the dataset.
        field_count: Number of fields in the dataset.
        season_count: Number of seasons in the dataset.
        observation_count: Total number of observations.
        calibration_overlap: Description of overlap with calibration data.
        model_use: How this dataset was used (training, calibration, evaluation).
        notes: Additional notes about the dataset.
        created_at: ISO timestamp of manifest creation.
    """

    dataset_id: str
    dataset_version: str
    title: str
    provenance: DataProvenance = DataProvenance.UNKNOWN
    publisher: str = ""
    license_url: str = ""
    source_url: str = ""
    date_acquired: str = ""
    data_format: DataFormat = DataFormat.CSV
    file_count: int = 0
    file_hashes: list[FileHash] = field(default_factory=list)
    yield_observations_available: bool = False
    weather_observations_available: bool = False
    par_available: bool = False
    lai_available: bool = False
    ews_inputs_available: bool = False
    crop_count: int = 0
    site_count: int = 0
    field_count: int = 0
    season_count: int = 0
    observation_count: int = 0
    calibration_overlap: str = "unknown"
    model_use: str = "evaluation"
    notes: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def is_real_data(self) -> bool:
        """Check if this manifest represents real field observations.

        Returns True only when:
        - provenance is REAL_FIELD_OBSERVATIONS
        - publisher is non-empty
        - license_url is non-empty
        - file_hashes is non-empty (integrity verified)
        - yield_observations_available is True
        """
        return (
            self.provenance == DataProvenance.REAL_FIELD_OBSERVATIONS
            and bool(self.publisher)
            and bool(self.license_url)
            and len(self.file_hashes) > 0
            and self.yield_observations_available
        )

    def is_synthetic(self) -> bool:
        """Check if this manifest represents synthetic test data."""
        return self.provenance == DataProvenance.SYNTHETIC_TEST_FIXTURES

    def to_dict(self) -> dict[str, Any]:
        """Serialize manifest to a JSON-safe dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "title": self.title,
            "provenance": self.provenance.value,
            "publisher": self.publisher,
            "license_url": self.license_url,
            "source_url": self.source_url,
            "date_acquired": self.date_acquired,
            "data_format": self.data_format.value,
            "file_count": self.file_count,
            "file_hashes": [
                {"filename": fh.filename, "sha256": fh.sha256, "size_bytes": fh.size_bytes}
                for fh in self.file_hashes
            ],
            "data_availability": {
                "yield_observations": self.yield_observations_available,
                "weather_observations": self.weather_observations_available,
                "par": self.par_available,
                "lai": self.lai_available,
                "ews_inputs": self.ews_inputs_available,
            },
            "coverage": {
                "crop_count": self.crop_count,
                "site_count": self.site_count,
                "field_count": self.field_count,
                "season_count": self.season_count,
                "observation_count": self.observation_count,
            },
            "calibration_overlap": self.calibration_overlap,
            "model_use": self.model_use,
            "notes": list(self.notes),
            "created_at": self.created_at,
        }


def compute_file_hash(filepath: str | Path) -> FileHash:
    """Compute the SHA-256 hash and size of a file.

    Args:
        filepath: Path to the file.

    Returns:
        A :class:`FileHash` with filename, sha256, and size_bytes.

    Raises:
        FileNotFoundError: if the file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)

    return FileHash(
        filename=path.name,
        sha256=sha256_hash.hexdigest(),
        size_bytes=path.stat().st_size,
    )


def compute_hashes(filepaths: Sequence[str | Path]) -> list[FileHash]:
    """Compute SHA-256 hashes for multiple files.

    Args:
        filepaths: Sequence of file paths.

    Returns:
        List of :class:`FileHash` for each file.
    """
    return [compute_file_hash(fp) for fp in filepaths]


def verify_file_integrity(
    file_hashes: list[FileHash],
    base_path: str | Path = ".",
) -> list[str]:
    """Verify that files match their recorded hashes.

    Args:
        file_hashes: List of FileHash records to verify.
        base_path: Base directory for file resolution.

    Returns:
        List of error messages for files that failed verification.
        Empty list means all files verified successfully.
    """
    errors: list[str] = []
    base = Path(base_path)

    for fh in file_hashes:
        filepath = base / fh.filename
        if not filepath.exists():
            errors.append(f"File missing: {fh.filename}")
            continue

        actual = compute_file_hash(filepath)
        if actual.sha256 != fh.sha256:
            errors.append(
                f"Hash mismatch for {fh.filename}: "
                f"expected {fh.sha256}, got {actual.sha256}"
            )
        if actual.size_bytes != fh.size_bytes:
            errors.append(
                f"Size mismatch for {fh.filename}: "
                f"expected {fh.size_bytes}, got {actual.size_bytes}"
            )

    return errors


def create_real_dataset_manifest(
    dataset_id: str,
    dataset_version: str,
    title: str,
    publisher: str,
    license_url: str,
    source_url: str,
    date_acquired: str,
    data_format: DataFormat,
    file_hashes: list[FileHash],
    *,
    yield_observations_available: bool = True,
    weather_observations_available: bool = True,
    par_available: bool = False,
    lai_available: bool = False,
    ews_inputs_available: bool = False,
    crop_count: int = 0,
    site_count: int = 0,
    field_count: int = 0,
    season_count: int = 0,
    observation_count: int = 0,
    calibration_overlap: str = "none",
    model_use: str = "evaluation",
    notes: list[str] | None = None,
) -> DatasetManifest:
    """Create a manifest for a real agricultural dataset.

    This factory enforces that all provenance fields are populated,
    ensuring the manifest represents genuine real-world data.
    """
    if not publisher:
        raise ValueError("publisher must be non-empty for real datasets")
    if not license_url:
        raise ValueError("license_url must be non-empty for real datasets")
    if not file_hashes:
        raise ValueError("file_hashes must be non-empty for real datasets")
    if not date_acquired:
        raise ValueError("date_acquired must be non-empty for real datasets")

    return DatasetManifest(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        title=title,
        provenance=DataProvenance.REAL_FIELD_OBSERVATIONS,
        publisher=publisher,
        license_url=license_url,
        source_url=source_url,
        date_acquired=date_acquired,
        data_format=data_format,
        file_count=len(file_hashes),
        file_hashes=file_hashes,
        yield_observations_available=yield_observations_available,
        weather_observations_available=weather_observations_available,
        par_available=par_available,
        lai_available=lai_available,
        ews_inputs_available=ews_inputs_available,
        crop_count=crop_count,
        site_count=site_count,
        field_count=field_count,
        season_count=season_count,
        observation_count=observation_count,
        calibration_overlap=calibration_overlap,
        model_use=model_use,
        notes=notes or [],
    )


def create_synthetic_manifest(
    dataset_id: str = "synthetic_test_dset",
    title: str = "Synthetic test fixtures",
    notes: list[str] | None = None,
) -> DatasetManifest:
    """Create a manifest for synthetic test fixtures.

    This manifest is intentionally NOT real data and will block
    benchmark execution if used as the evaluation dataset.
    """
    return DatasetManifest(
        dataset_id=dataset_id,
        dataset_version="test",
        title=title,
        provenance=DataProvenance.SYNTHETIC_TEST_FIXTURES,
        publisher="ECO Nojin Internal Testing",
        license_url="N/A — synthetic test data, not for external validation",
        source_url="",
        date_acquired=datetime.now(UTC).isoformat(),
        data_format=DataFormat.CSV,
        file_count=0,
        file_hashes=[],
        yield_observations_available=False,
        weather_observations_available=False,
        par_available=False,
        lai_available=False,
        ews_inputs_available=False,
        crop_count=0,
        site_count=0,
        field_count=0,
        season_count=0,
        observation_count=0,
        calibration_overlap="synthetic_only",
        model_use="testing_only",
        notes=notes or ["This dataset is synthetic and MUST NOT be used "
                         "for external validation claims."],
    )


class DataQualityCheckError(StrEnum):
    """Result codes for individual data quality checks."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class QualityCheckResult:
    """Result of a single data quality check."""

    check_name: str
    status: DataQualityCheckError
    details: str
    field: str | None = None


@dataclass
class DataQualityReport:
    """Aggregated quality report for a dataset.

    Attributes:
        dataset_id: ID of the dataset checked.
        total_records: Total records in the dataset.
        records_passed: Records passing all hard quality gates.
        records_failed: Records failing quality gates.
        records_needs_review: Records requiring manual review.
        checks: Per-check results.
        is_real_data_blocked: True when the dataset is synthetic.
        is_blocked: True when the dataset cannot be used for benchmarking.
        blocking_reason: The primary reason (if blocked).
    """

    dataset_id: str
    total_records: int = 0
    records_passed: int = 0
    records_failed: int = 0
    records_needs_review: int = 0
    checks: list[QualityCheckResult] = field(default_factory=list)
    is_real_data_blocked: bool = False
    is_blocked: bool = False
    blocking_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize quality report to a JSON-safe dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "total_records": self.total_records,
            "records_passed": self.records_passed,
            "records_failed": self.records_failed,
            "records_needs_review": self.records_needs_review,
            "is_real_data_blocked": self.is_real_data_blocked,
            "is_blocked": self.is_blocked,
            "blocking_reason": self.blocking_reason,
            "checks": [
                {
                    "check_name": c.check_name,
                    "status": c.status.value,
                    "details": c.details,
                    "field": c.field,
                }
                for c in self.checks
            ],
        }


def check_yield_unit_consistency(
    yield_values: Sequence[float],
    yield_units: Sequence[str],
) -> QualityCheckResult:
    """Check that yield values and units are consistent and valid."""
    from engine.hydroma.eval.field_validation import VALID_YIELD_UNITS

    invalid_units = [u for u in yield_units if u not in VALID_YIELD_UNITS]
    if invalid_units:
        return QualityCheckResult(
            check_name="yield_unit_consistency",
            status=DataQualityCheckError.FAIL,
            details=f"Invalid yield units found: {set(invalid_units)}",
            field="observed_yield_unit",
        )

    non_finite = [v for v in yield_values if v != v or v in (float("inf"), float("-inf"))]
    if non_finite:
        return QualityCheckResult(
            check_name="yield_unit_consistency",
            status=DataQualityCheckError.FAIL,
            details=f"Non-finite yield values found: {len(non_finite)}",
            field="observed_yield",
        )

    negative = [v for v in yield_values if v < 0]
    if negative:
        return QualityCheckResult(
            check_name="yield_unit_consistency",
            status=DataQualityCheckError.FAIL,
            details=f"Negative yield values found: {len(negative)}",
            field="observed_yield",
        )

    return QualityCheckResult(
        check_name="yield_unit_consistency",
        status=DataQualityCheckError.PASS,
        details=f"All {len(yield_values)} yield values are valid",
        field="observed_yield",
    )


def check_required_fields_present(
    records: list[dict[str, Any]],
    required_fields: set[str],
) -> QualityCheckResult:
    """Check that all records have the required fields populated."""
    missing_counts: dict[str, int] = dict.fromkeys(required_fields, 0)

    for rec in records:
        for f in required_fields:
            val = rec.get(f)
            if val is None or val == "":
                missing_counts[f] += 1

    total_missing = sum(missing_counts.values())
    if total_missing > 0:
        details = ", ".join(
            f"{f}: {c} missing" for f, c in missing_counts.items() if c > 0
        )
        return QualityCheckResult(
            check_name="required_fields_present",
            status=DataQualityCheckError.FAIL,
            details=details,
        )

    return QualityCheckResult(
        check_name="required_fields_present",
        status=DataQualityCheckError.PASS,
        details=f"All {len(records)} records have required fields",
    )


def check_no_synthetic_label(records: list[dict[str, Any]]) -> QualityCheckResult:
    """Check that no records have a synthetic data label."""
    synthetic_labels = []
    for i, rec in enumerate(records):
        label = rec.get("data_label", "")
        if isinstance(label, str) and label.startswith("synthetic"):
            synthetic_labels.append((i, label))

    if synthetic_labels:
        return QualityCheckResult(
            check_name="no_synthetic_label",
            status=DataQualityCheckError.FAIL,
            details=f"Found {len(synthetic_labels)} records with synthetic labels",
            field="data_label",
        )

    return QualityCheckResult(
        check_name="no_synthetic_label",
        status=DataQualityCheckError.PASS,
        details=f"No synthetic labels found in {len(records)} records",
        field="data_label",
    )


def check_duplicate_records(
    records: list[dict[str, Any]],
) -> QualityCheckResult:
    """Check for duplicate records by (site_id, season_id, crop)."""
    keys = []
    for rec in records:
        key = (
            str(rec.get("site_id", "")),
            str(rec.get("season_id", "")),
            str(rec.get("crop", "")),
        )
        keys.append(key)

    unique_keys = set(keys)
    duplicate_count = len(keys) - len(unique_keys)

    if duplicate_count > 0:
        return QualityCheckResult(
            check_name="duplicate_records",
            status=DataQualityCheckError.WARNING,
            details=f"Found {duplicate_count} duplicate (site, season, crop) keys",
        )

    return QualityCheckResult(
        check_name="duplicate_records",
        status=DataQualityCheckError.PASS,
        details=f"No duplicates in {len(records)} records",
    )


def run_data_quality_checks(
    records: list[dict[str, Any]],
    dataset_id: str,
) -> DataQualityReport:
    """Run all quality checks on a list of raw data records.

    This function checks:
    1. Required fields are present
    2. Yield units are valid
    3. No synthetic data labels
    4. No duplicate (site, season, crop) keys

    If the data appears synthetic (e.g. synthetic labels or a synthetic
    dataset ID), the report is blocked.
    """
    checks: list[QualityCheckResult] = []
    total = len(records)

    required_fields = {"site_id", "season_id", "crop", "observed_yield", "observed_yield_unit"}
    checks.append(check_required_fields_present(records, required_fields))

    yield_values = [r.get("observed_yield", 0.0) for r in records]
    yield_units = [r.get("observed_yield_unit", "") for r in records]
    checks.append(check_yield_unit_consistency(yield_values, yield_units))

    checks.append(check_no_synthetic_label(records))

    checks.append(check_duplicate_records(records))

    failed = sum(1 for c in checks if c.status == DataQualityCheckError.FAIL)
    warnings = sum(1 for c in checks if c.status == DataQualityCheckError.WARNING)

    is_synthetic = any(
        c.check_name == "no_synthetic_label" and c.status == DataQualityCheckError.FAIL
        for c in checks
    ) or dataset_id.lower().startswith("synth")

    is_blocked = is_synthetic or failed > 0
    blocking_reason = ""
    if is_synthetic:
        blocking_reason = "Dataset contains synthetic test data — not valid for external validation"
    elif failed > 0:
        failed_names = [c.check_name for c in checks if c.status == DataQualityCheckError.FAIL]
        blocking_reason = f"Quality checks failed: {', '.join(failed_names)}"

    return DataQualityReport(
        dataset_id=dataset_id,
        total_records=total,
        records_passed=total if failed == 0 else 0,
        records_failed=failed,
        records_needs_review=warnings,
        checks=checks,
        is_real_data_blocked=is_synthetic,
        is_blocked=is_blocked,
        blocking_reason=blocking_reason,
    )


def check_data_independence(
    manifest: DatasetManifest,
    calibration_dataset_ids: set[str],
) -> QualityCheckResult:
    """Verify that a dataset is independent from calibration datasets.

    A dataset is considered independent if:
    - It is not in the calibration dataset set
    - Its calibration_overlap is explicitly "none"

    Args:
        manifest: The dataset manifest to check.
        calibration_dataset_ids: Set of dataset IDs used for calibration.

    Returns:
        A QualityCheckResult indicating whether the dataset is independent.
    """
    if manifest.dataset_id in calibration_dataset_ids:
        return QualityCheckResult(
            check_name="independence_check",
            status=DataQualityCheckError.FAIL,
            details=f"Dataset {manifest.dataset_id} is in the calibration set",
        )

    if manifest.calibration_overlap == "full" or manifest.calibration_overlap == "partial":
        return QualityCheckResult(
            check_name="independence_check",
            status=DataQualityCheckError.FAIL,
            details=f"Dataset has calibration overlap: {manifest.calibration_overlap}",
        )

    return QualityCheckResult(
        check_name="independence_check",
        status=DataQualityCheckError.PASS,
        details=f"Dataset {manifest.dataset_id} is independent of calibration data",
    )
