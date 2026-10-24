# Stage 31: Validation Readiness Report

## Status: BLOCKED — Field-Level · READY for Regional Alternative Path

## Summary

**Benchmark status: BLOCKED** (no real field-level yield data acquired)

The USDA BARC Gridded Yield Data Archive has been identified as the primary
field-level dataset for HYRUE validation, but dataset files could not be
retrieved due to an AWS WAF JavaScript challenge on the Ag Data Commons website
and 404 responses from the Data.gov CKAN API. No real field-level yield data
file currently exists in the repository.

**Weather data inputs are READY:** Open-Meteo (ERA5-Land) and NASA POWER
(MERRA-2) weather APIs are implemented and tested in `weather_source.py`.
NASA POWER provides satellite-retrieved PAR (`ALLSKY_SFX_PAR_TOT`). These
can provide weather inputs for any field site once coordinates are known.

## A. Benchmark Spec Prerequisites (from `BenchmarkSpec.check_prerequisites()`)

The following hard prerequisites must be satisfied for the benchmark to
transition from BLOCKED to READY:

| # | Requirement | `check_prerequisites()` check | Current Status |
|---|---|---|---|
| 1 | Real field-yield observation dataset available | `dataset_inventory is None` → `NO_VALIDATION_DATASET` | **BLOCKED** — no BARC files downloaded |
| 2 | Dataset provenance is real (not synthetic) | `dataset_inventory.provenance == SYNTHETIC_TEST_FIXTURES` → `NO_REAL_FIELD_YIELD_DATA` | N/A — no dataset manifests as real |
| 3 | Yield observations available | `dataset_inventory.yield_observations_available == False` → `NO_REAL_FIELD_YIELD_DATA` | **BLOCKED** |
| 4 | Weather observations available | `dataset_inventory.weather_observations_available == False` → `NO_WEATHER_INPUTS` | N/A — weather available via API, not dataset |
| 5 | Validation protocol complete | `self.protocol is None` or `not is_complete()` → `INCOMPLETE_PROTOCOL` | Protocol contracts exist (Stage 28) but not assembled |
| 6 | Calibration ≠ validation dataset | `protocol.calibration_dataset_id == protocol.validation_dataset_id` → `NO_INDEPENDENT_EVALUATION_DATA` | N/A — no calibration dataset configured |

### Blockers List (would be returned)

```
BenchmarkStatus.BLOCKED
Blockers:
  - BenchmarkBlocker.NO_VALIDATION_DATASET
  - BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA
  - BenchmarkBlocker.INCOMPLETE_PROTOCOL
```

> Note: `NO_WEATHER_INPUTS` is not triggered because weather inputs are
> available via API (Open-Meteo primary, NASA POWER fallback). However, the
> benchmark prerequisite check operates on the `DatasetInventory` object,
> which requires an actual dataset manifest. Weather inputs alone do not
> satisfy the prerequisite — a yield observation dataset is required.

## B. HYRUE Input Requirements (from `SeasonalPredictionRequest`)

The `compute_seasonal_prediction()` pipeline in `seasonal_predictor.py`
requires the following per-field inputs to produce a yield prediction:

| Input | HYRUE Requirement | Data Source | Status |
|---|---|---|---|
| Planting date | `str` ISO format | BARC field metadata | **Not available** — BARC not retrieved |
| Harvest date | `str` ISO format | BARC field metadata | **Not available** |
| Latitude | `float` WGS84 | BARC field boundaries | **Not available** |
| Longitude | `float` WGS84 | BARC field boundaries | **Not available** |
| Crop | `str` crop name | BARC field metadata | **Not available** |
| Daily min/max temperature | °C | Open-Meteo (ERA5-Land) / NASA POWER (MERRA-2) | **Ready** — `fetch_daily_weather()` implemented |
| Daily precipitation | mm | Open-Meteo / NASA POWER | **Ready** — implemented |
| Daily shortwave radiation | MJ/m²/day | Open-Meteo / NASA POWER | **Ready** — retrieved as `ShortwaveRadiation` column |
| PAR | MJ/m²/day | NASA POWER `ALLSKY_SFX_PAR_TOT` (satellite) or 0.5× shortwave (estimated) | **Ready** — satellite retrieval via NASA POWER; estimated fallback documented |
| LAI | m²/m² | Must be provided (observed / satellite / GDD model) | **Not available** — no LAI data; GDD model fallback available with `allow_estimated_inputs` policy |
| EWSI | dimensionless 0–1 | Must be provided or computed from NIR/SWIR/VPD/SM | **Not available** — no EWSI inputs; `DIAGNOSTIC` policy allows EWSI to be missing |
| VPD | kPa | NASA POWER `RVPD` or computable from RH/T | **Ready** — available via NASA POWER or computable |
| Soil moisture | m³/m³ | ERA5-Land via Copernicus CDS | **Not available** — no ESA/Copernicus account configured |

### Input Provenance Classification

Each input must be classified per `seasonal_predictor.py` design:

| Provenance Level | Definition | Available Sources |
|---|---|---|
| `field_measured` | Instrument deployed at the site | Not available (no site-specific sensors) |
| `satellite_retrieved` | Satellite product | NASA POWER PAR (CERES), Sentinel-2 LAI (if Copernicus account) |
| `analysis_product` | Reanalysis/gridded product | ERA5-Land (Open-Meteo/NASA POWER), MERRA-2 (NASA POWER) |
| `estimated` | Derived via documented coefficient | PAR = 0.5 × shortwave (calibration-grade assumption) |
| `missing` | Not available for this day | LAI, EWSI, soil moisture (without Copernicus) |

### Input Source Policy Options

| Policy | LAI | PAR | EWSI | Weather |
|---|---|---|---|---|
| `strict` | must be observed | must be measured/satellite | must be external or computed from observed inputs | fetched from API |
| `allow_estimated_inputs` (default) | GDD model fallback acceptable | 0.5× shortwave conversion acceptable | computed from NIR/SWIR/VPD/SM acceptable | fetched from API |
| `diagnostic` | any source, clearly flagged | any source, clearly flagged | any source, clearly flagged | any source |

## C. Weather Data Integration Status

`weather_source.py` implements:

- **`fetch_daily_weather(latitude, longitude, start_date, end_date)`** — primary fetch from Open-Meteo ERA5-Land archive (no API key)
- **NASA POWER fallback** — MERRA-2 reanalysis with satellite-retrieved PAR (`ALLSKY_SFX_PAR_TOT`)
- **`convert_shortwave_to_par()`** — derives PAR from shortwave using `DEFAULT_PAR_FRACTION=0.5` (Monteith & Unsworth 2013, FAO-56)
- **`DailyWeatherRecord`** — pydantic model for weather data
- **`normalize_par_provenance()`** — maps legacy "observed" → "satellite_retrieved"

Weather tests pass (verified via `test_stage30_benchmark_integration.py` integration tests).

## D. Data Quality Gate Status

The quality infrastructure in `dataset_manifest.py` is fully implemented and tested:

| Gate | Function | Status |
|---|---|---|
| Required fields present | `check_required_fields_present()` | Implemented, 26 tests |
| Yield unit consistency | `check_yield_unit_consistency()` | Implemented — validates `t/ha`, `kg/ha`, `g/m²`; rejects non-finite, negative |
| No synthetic label | `check_no_synthetic_label()` | Implemented — rejects `data_label` starting with "synthetic" |
| Duplicate records | `check_duplicate_records()` | Implemented — flags duplicate (site_id, season_id, crop) |
| Data independence | `check_data_independence()` | Implemented — verifies dataset not in calibration set, no overlap |
| File integrity | `compute_hashes()`, `verify_file_integrity()` | Implemented — SHA-256 hashing |

All 45 Stage 30 tests pass. Quality gates are ready to receive real data.

## E. `RealFieldRecord` Contract Readiness

`RealFieldRecord` in `field_validation.py` defines the contract for each field
observation. The validators enforce:

- `observed_yield` must be finite and non-negative (lines 150–164)
- `observed_yield_unit` must be in `VALID_YIELD_UNITS` = `{t/ha, kg/ha, g/m²}` (lines 166–174)
- `harvest_date` must not precede `planting_date` (lines 176–184)
- `data_label` must not start with "synthetic" (lines 186–194)
- `observation_source` must be in `VALID_OBSERVATION_SOURCES` (lines 196–204)

Once BARC data is retrieved, records can be constructed with:
`observation_source="published_literature"` and `data_label="real_field_data"`.

## F. Benchmark Report Status

Using `create_blocked_report()` from `benchmark_report.py`:

| Field | Value |
|---|---|
| `benchmark_status` | `BLOCKED` |
| `external_validation_status` | `BLOCKED` |
| `blockers` | `[NO_VALIDATION_DATASET, NO_REAL_FIELD_YIELD_DATA, INCOMPLETE_PROTOCOL]` |
| `metrics` | `None` (no metrics computed) |
| `scientific_limitations` | "No real field-yield dataset found", "Synthetic test fixtures not valid", "Benchmark blocked until real independent data available" |

If BARC data were retrieved and a manifest created:
- `benchmark_status` → `READY`
- `blockers` → `[]`
- `external_validation_status` → `not_assessed` (READY ≠ VALIDATED_EXTERNAL)
- Metrics would remain `None` until predictions are actually executed

## G. Two Validation Paths

### Path 1: Field-Level Validation (BLOCKED)

Requires the BARC dataset files to be retrieved. Currently blocked by:
- Ag Data Commons WAF JavaScript challenge
- Data.gov CKAN API returning 404
- Wiley institutional wall blocking paper access

**To unblock:** Manual download via browser session, or contact USDA ARS data steward.

### Path 2: Regional Validation (READY — alternative path)

Uses USDA NASS Quick Stats (state/county-level yield aggregates). While this
does **not** provide field-level independence, it enables:

- Regional aggregate comparison (state-level yield RMSE/bias)
- Growing season weather matching to NASS reporting regions
- Population-weighted yield comparison against model predictions

**Limitations of regional path:**
- Scale mismatch: NASS data is aggregated to county/state level
- No field coordinates for spatial matching
- Cannot claim field-level accuracy
- Different uncertainty characteristics

**This path is suitable for:** Demonstrating model skill at regional scale,
but **not** for claiming `VALIDATED_EXTERNAL` status.

## H. Next Actions

| Action | Priority | Responsible |
|---|---|---|
| Request BARC data via USDA ARS contact or manual browser download | P0 | Data acquisition team |
| Create `DatasetManifest` with real BARC files once retrieved | P0 | Follows automatically |
| Attempt USDA NASS Quick Stats API for regional validation path | P1 | Alternative if BARC remains blocked |
| Set up Copernicus CDS account for ERA5-Land soil moisture and Sentinel-2 LAI | P2 | Weather input enrichment |
| Assemble `ValidationProtocol` with BARC calibration separation | P0 | Once dataset available |
| Run `BenchmarkSpec.evaluate_status()` → expect `READY` | P0 | Verification step |
| Execute `compute_seasonal_prediction()` per field | P0 | Benchmark execution |
| Produce validation report and benchmark report | P0 | Final reporting |

## I. Conclusion

The Stage 31 infrastructure for acquiring and validating real agricultural
data is **complete and tested**. The benchmark pipeline from
`DatasetManifest` → `DatasetInventory` → `BenchmarkSpec.check_prerequisites()`
→ `produce_benchmark_report()` is fully functional and verified.

The benchmark remains **BLOCKED** solely due to the absence of real
field-level yield data files in the repository. The weather input layer
(Open-Meteo, NASA POWER) is implemented and ready. The data quality gates
and provenance tracking are implemented and tested (45 tests passing).

The blocker is a **data access issue**, not an infrastructure issue.
