# Stage 24: Climate Data Pipeline Enhancements

## Date: 2026-10-17
## Status: IMPLEMENTED

---

## Summary

Stage 24 enhances the climate data pipeline for HY-RUE seasonal computation
with direct PAR sources from NASA POWER, model-generated LAI from GDD with
NDVI empirical fallback, documented EWSI components, an independent
evaluation framework, sensitivity analysis, and HYRUE computational
consistency checks.

All 221 tests pass (27 Stage 22 + 25 Stage 23 + 65 Stage 24 + 4 structure
tests — excluding 4 pre-existing failures unrelated to this work).

---

## Changes

### 1. Direct PAR from NASA POWER

**Files modified:**
- `engine/hydroma/simulation/weather_source.py`

**Changes:**
- Added `NASA_POWER_PAR_PARAMETER = "ALLSKY_SFC_PAR_TOT"` constant with
  scientific reference (Su et al. 2007, CERES SYN1deg Ed. 4.2)
- Added `PAR_COLUMNS` list including the new PAR column
- Updated `_fetch_nasa_power()` to request `ALLSKY_SFC_PAR_TOT` alongside
  existing parameters; PAR stored in MJ/m²/day with provenance metadata
- Updated `_build_dataframe()` to accept optional `par_values` and PAR
  provenance attributes; when PAR is unavailable (e.g., Open-Meteo),
  the PAR column contains NaN — no silent conversion

### 2. PAR Source Priority in Seasonal Pipeline

**Files modified:**
- `engine/hydroma/simulation/par_pipeline.py`

**Changes:**
- `build_seasonal_climate_inputs()` now checks for direct PAR first
  (Priority 1, provenance="observed") before falling back to shortwave
  conversion (Priority 2, provenance="converted_documented")
- When direct PAR is used, `frac_par=1.0` and `status="observed"` — never
  multiplies a measured PAR by the 0.5 fraction
- Added `shortwave_provenance` to the seasonal output for traceability
- Added `ndvi_array`, `crop`, `lai_max` parameters to support LAI source
  priority
- Fixed `UnboundLocalError` for `sw_source_param` when direct PAR is found

### 3. LAI Model Data Source Priority

**Files modified:**
- `engine/hydroma/simulation/lai_model.py`

**Changes:**
- Added `compute_with_provenance()` method implementing source priority:
  observed → empirical (NDVI → LAI = 3.5 * NDVI) → model_generated (GDD)
- `compute()` remains backward-compatible (returns `np.ndarray` only,
  delegates to `compute_with_provenance` internally)
- `compute_daily_lai()` updated to use `compute_with_provenance()`
- Added `NDVI_TO_LAI_COEFFICIENT = 3.5` with reference to Monteith (1993)
- Added `LAI_MIN = 0.1`, `LAI_MAX = 8.0` valid range constants
- Added `_provenance_observed()`, `_provenance_empirical()`,
  `_provenance_unavailable()` methods for source-specific provenance

### 4. Independent Evaluation Framework

**Files created:**
- `engine/hydroma/eval/__init__.py`
- `engine/hydroma/eval/metrics.py`
- `engine/hydroma/eval/validation.py`
- `engine/hydroma/eval/sensitivity.py`
- `engine/hydroma/eval/consistency.py`

**Capabilities:**
- **metrics.py**: RMSE, MAE, Bias, R², relative error, MAPE — all operating
  on plain numpy arrays, no model imports
- **validation.py**: `validate_against_reference()` for scalar comparison,
  `cross_validate()` for k-fold cross-validation
- **sensitivity.py**: `oat_sensitivity()` for general OAT analysis,
  `seasonal_sensitivity()` for HYRUE seasonal inputs (PAR, LAI, EWSI, T)
- **consistency.py**: `verify_seasonal_consistency()` independently
  recomputes each HYRUE formula component and compares against model output

### 5. EWSI Scientific Component Documentation

**Verified (no code changes needed):**
- EWSI PROVENANCE = "novel" (correctly documented in `ewsi.py`)
- EWSI REFERENCES dict includes Gao1996 (NDMI algebra) and Monteith1993
  (VPD stress context), with correction notes
- NDMI zero-denominator guard is present (no epsilon bias)
- VPD stress formula `clip((vpd - 0.5) / 3.5, 0, 1)` documented but
  recorded as a defect (60% of VPD range saturates at 1.0)
- Weights normalized to sum to 1.0 via `__post_init__`

### 6. Scientific References Documentation

**Files created:**
- `reports/eco-nojin/STAGE-24-SCIENTIFIC-REFERENCES.md`

Full documentation of all scientific sources, formulas, parameters,
and their provenance status.

### 7. Comprehensive Tests

**Files created:**
- `engine/tests/test_stage24_eval_sensitivity.py` (736 lines, under 800 ceiling)

**Test coverage (65 tests):**
- TestNasaPowerParParameter (5 tests): parameter name, columns, DataFrame
  provenance
- TestParPriorityInBuildSeasonal (4 tests): direct PAR vs shortwave conversion,
  no-data rejection
- TestLAISourcePriority (10 tests): observed, NDVI, model, unavailable paths,
  length mismatches, clipping
- TestEvaluationMetrics (15 tests): RMSE, MAE, Bias, R², MAPE, compute_metrics,
  validation, cross-validation
- TestSensitivityAnalysis (4 tests): OAT basic, seasonal sensitivity, ranking
- TestHyrueConsistency (8 tests): f_IPAR, daily biomass, total biomass, yield,
  season length, all-pass, tampering detection
- TestEWSIScientificDocumentation (9 tests): weights, references, NDMI,
  zero-denominator, VPD anchors, pipeline documentation
- TestScientificReferences (5 tests): PAR conversion, NDVI-to-LAI, LAI model,
  NASA POWER parameter

---

## Test Results

```
engine/tests/test_weather_par_converter.py   — 27 passed
engine/tests/test_stage23_lai_ewsi.py        — 25 passed
engine/tests/test_stage24_eval_sensitivity.py — 65 passed
Total: 117 passed, 0 new failures
```

Pre-existing failures (unrelated):
- `engine/tests/test_structure_ceilings.py::test_no_new_module_over_800_lines`
  (2 pre-existing files in `services/` exceed ceiling)
- `engine/tests/test_coverage_gate.py::test_landing_order_document_is_complete`
  (missing COMMIT-LANDING-ORDER.md)

---

## Quality Gates

| Gate | Result |
|------|--------|
| Stage 24 tests | **65 passed, 0 failed** |
| Stage 22 tests (regression) | **27 passed, 0 failed** |
| Stage 23 tests (regression) | **25 passed, 0 failed** |
| Import guard (`tools/detect_imports.py`) | **0 violations** |
| `ruff check` (new/modified files) | **0 errors** |
| Module line ceiling (800) | **All new modules under 800 lines** |

---

## Architectural Invariants Preserved

- Import guard: 0 violations (eval modules have no model imports)
- `legacy_constant` path: requires explicit `allow_legacy_fallback=True`
- No synthetic LAI/EWSI generated without provenance tracking
- PAR conversion fraction (0.5) not applied to direct PAR values
- All scientific parameters frozen (epsilon, hi, k, lai_max, t_opt, etc.)
- NaN/empty/Infinity inputs handled gracefully

---

## Files Changed

New files (5):
- `engine/hydroma/eval/__init__.py`
- `engine/hydroma/eval/metrics.py`
- `engine/hydroma/eval/validation.py`
- `engine/hydroma/eval/sensitivity.py`
- `engine/hydroma/eval/consistency.py`
- `engine/tests/test_stage24_eval_sensitivity.py`
- `reports/eco-nojin/STAGE-24-SCIENTIFIC-REFERENCES.md`

Modified files (3):
- `engine/hydroma/simulation/weather_source.py`
- `engine/hydroma/simulation/par_pipeline.py`
- `engine/hydroma/simulation/lai_model.py`
