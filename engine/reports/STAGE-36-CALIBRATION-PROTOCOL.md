# Stage 36 — Calibration Protocol

## Objective

Calibrate HY-RUE and EWSI parameters using ONLY development-district data.
Test-district records are never used for parameter estimation.

## Development / Test Split

| Set | Districts | Records |
|---|---|---|
| Development | Begusarai, Bhojpur, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura | 3,967 |
| Test | Buxar, Muzaffarpur, Rohtas | 1,722 |

Split manifest: `engine/reports/data/stage36_benchmark_split_manifest.json`

## Calibration Rules (Non-Negotiable)

1. **No test data in calibration.** Test-district records are never passed to
   calibration functions, used for parameter selection, or used for early
   stopping decisions.
2. **No parameter tuning to match test performance.** Parameters are estimated
   from development data only using a documented method.
3. **All parameter changes go through the registry.** Every change records
   rationale, method, dataset, and version.
4. **If insufficient dev data, report BLOCKED.** If fewer than 5 dev records
   have successful EWSI computation, calibration is blocked.
5. **Freeze before test.** Parameters are frozen (frozen_model_config.json)
   before any test-district execution.

## Calibration Method

Given the time-prohibitive nature of real weather+satellite data acquisition
for all 3,967 dev records, calibration is performed on a sampled subset:

1. Sample N dev records (recommended: 20-50 for feasibility)
2. For each record: fetch weather, compute EWSI, run HYRUE
3. Compute error metrics (RMSE, MAE, Bias, R², MAPE) on dev data
4. Optionally run grid search or coordinate descent on dev data only
5. Record calibrated parameters with full traceability

## Parameter Calibration Status

| Parameter | Value | Status | Calibratable? |
|---|---|---|---|
| epsilon | 2.2 | Calibratable | Yes |
| k | 0.65 | Calibratable | Yes |
| hi | 0.45 | Calibratable | Yes |
| t_opt | 20.0 | Calibratable | Yes |
| t_min | 5.0 | Calibratable | Yes |
| t_max | 35.0 | Calibratable | Yes |
| lai_max | 6.0 | Calibratable | Yes |
| ewsi_weight_ndmi | 0.4 | Calibratable | Yes |
| ewsi_weight_vpd | 0.3 | Calibratable | Yes |
| ewsi_weight_soil | 0.3 | Calibratable | Yes |
| thermal_gaussian_width | 8.0 | Uncalibrated | No (no source) |
| ndmi_ref | 0.3 | Uncalibrated | No (no source) |
| ndmi_crit | -0.2 | Uncalibrated | No (no source) |
| vpd_low | 0.5 | Uncalibrated | No (no source) |
| vpd_high | 4.0 | Uncalibrated | No (no source) |
| soil_field_capacity | 0.35 | Uncalibrated | No (no source) |
| shortwave_to_par_factor | 0.5 | Fixed | No (unit conversion) |

## Files

- `engine/hydroma/eval/calibration_parameter_registry.py`
- `engine/hydroma/eval/hyrue_calibration.py`
- `engine/reports/data/stage36_frozen_model_config.json`
- `engine/reports/data/stage36_benchmark_split_manifest.json`
