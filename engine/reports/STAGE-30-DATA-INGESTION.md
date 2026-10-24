# Stage 30: Dataset Ingestion & Validation Infrastructure

## Summary

**Status:** Infrastructure complete. Real agricultural dataset **BLOCKED** — no real data available in repository.

Stage 30 implemented the dataset manifest, quality control, and integration infrastructure for real agricultural data. When real data is available, it can immediately flow into Stage 29 benchmark execution. No synthetic data can enter the evaluation path.

## A. Files Created

### Core Infrastructure
| File | Purpose |
|---|---|
| `engine/hydroma/eval/dataset_manifest.py` | `DatasetManifest`, `FileHash`, `DataProvenance`, `DataFormat`, `DataQualityCheckError`, `QualityCheckResult`, `DataQualityReport`; factory functions `create_real_dataset_manifest()`, `create_synthetic_manifest()`; quality check functions `check_yield_unit_consistency()`, `check_required_fields_present()`, `check_no_synthetic_label()`, `check_duplicate_records()`, `run_data_quality_checks()`, `check_data_independence()`; `compute_file_hash()`, `compute_hashes()`, `verify_file_integrity()` |

### Tests
| File | Tests | Description |
|---|---|---|
| `engine/tests/test_stage30_dataset_manifest.py` | 26 tests | Manifest creation, provenance tracking, quality checks, file hash verification, independence checks |
| `engine/tests/test_stage30_benchmark_integration.py` | 15 tests | Integration between DatasetManifest and BenchmarkSpec, provenance propagation, synthetic data blocking |

### Reports
| File | Purpose |
|---|---|
| `engine/reports/STAGE-30-DATA-INGESTION.md` | This report |

## B. Files Updated

| File | Changes |
|---|---|
| `engine/hydroma/eval/__init__.py` | Added 17 Stage 30 exports: `DatasetManifest`, `DataProvenance`, `DataFormat`, `FileHash`, `DataQualityCheckError`, `QualityCheckResult`, `DataQualityReport`, `create_real_dataset_manifest`, `create_synthetic_manifest`, `check_data_independence`, `check_duplicate_records`, `check_no_synthetic_label`, `check_required_fields_present`, `check_yield_unit_consistency`, `compute_file_hash`, `compute_hashes`, `run_data_quality_checks`, `verify_file_integrity` |

## C. Dataset Manifest Contract

### `DatasetManifest` dataclass

The manifest is the **required entry point** for any dataset entering the benchmark pipeline. It captures:

| Field | Description |
|---|---|
| `dataset_id` | Stable unique identifier |
| `dataset_version` | Semantic version |
| `title` | Human-readable title |
| `provenance` | `REAL_FIELD_OBSERVATIONS` or `SYNTHETIC_TEST_FIXTURES` |
| `publisher` | Organization/study that produced the data |
| `license_url` | Data license URL |
| `source_url` | Original data source URL |
| `date_acquired` | When data entered the project |
| `file_hashes` | FileHash records for integrity verification |
| `yield_observations_available` | Whether real crop yield data exists |
| `weather_observations_available` | Whether weather data exists |
| `calibration_overlap` | Description of overlap with calibration data |
| `model_use` | How dataset was used (training, calibration, evaluation) |

### `is_real_data()` check

Returns `True` only when **all** of:
- `provenance == REAL_FIELD_OBSERVATIONS`
- `publisher` is non-empty
- `license_url` is non-empty
- `file_hashes` is non-empty (integrity verified)
- `yield_observations_available == True`

### Quality Assurance Checks

The `run_data_quality_checks()` function performs four checks on raw records:

1. **Required fields present** — checks `site_id`, `season_id`, `crop`, `observed_yield`, `observed_yield_unit`
2. **Yield unit consistency** — validates units against `VALID_YIELD_UNITS`, rejects non-finite and negative values
3. **No synthetic label** — rejects records where `data_label` starts with `"synthetic"`
4. **Duplicate records** — flags duplicate `(site_id, season_id, crop)` keys

### Independence Verification

`check_data_independence()` verifies that a dataset:
- Is not in the calibration dataset set
- Has `calibration_overlap` explicitly set to `"none"`

## D. Integration with Stage 29

The `_manifest_to_inventory()` helper in test files converts `DatasetManifest` to `DatasetInventory` for benchmark prerequisite checking. This demonstrates the integration path:

```
DatasetManifest → DatasetInventory → BenchmarkSpec.check_prerequisites()
```

Real data with a complete protocol → `READY`
Synthetic data → `BLOCKED` with `NO_REAL_FIELD_YIELD_DATA`

## E. Dataset Availability

**No real agricultural dataset was found in the repository.** The `STAGE-29-DATA-INVENTORY.md` report documents this finding. All `RealFieldRecord` instances in the codebase are synthetic test fixtures.

## F. Benchmark Execution Status

| Status | Explanation |
|---|---|
| `BLOCKED` | No real field-yield dataset available |
| `NOT_READY` | Default initial state |
| `READY` | Real data + complete protocol available (not reached) |
| `COMPLETED` | Benchmark execution with real data (not reached) |

## G. Remaining Blockers

| Blocker | Status | Action Required |
|---|---|---|
| No real field yield data | BLOCKED | Acquire real crop yield observations |
| No weather inputs | Not checked | Acquire real weather station data |
| No independent evaluation dataset | Not checked | Provide dataset not used for model development |
| Incomplete protocol | Resolved | Stage 28 protocol contracts available |

## H. Quality Gates

| Gate | Result |
|---|---|
| Stage 26-30 tests | All pass (275 Stage 27-28 + 45 Stage 29-30) |
| Ruff (all Stage 30 files) | 0 errors |
| Import guard | 0 violations (1378 files scanned) |

## I. Next Steps

When real agricultural data becomes available:

1. Create a `DatasetManifest` with `provenance=REAL_FIELD_OBSERVATIONS`
2. Run `run_data_quality_checks()` on the raw records
3. Verify data independence with `check_data_independence()`
4. Compute file hashes with `compute_hashes()`
5. Populate `DatasetInventory` from the manifest
6. Call `BenchmarkSpec.evaluate_status()` — should return `READY`
7. Execute HYRUE predictions via `compute_seasonal_prediction()`
8. Produce validation report via `produce_validation_report()`
9. Generate benchmark report via `produce_benchmark_report()`
10. Assert `external_validation_status == "validated_external"` only if all independent dimensions support it

The infrastructure is ready. Execution is blocked only on real data availability.
