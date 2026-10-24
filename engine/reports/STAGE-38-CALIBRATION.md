# Stage 38 — Calibration Verification

## Calibration Status

**Status: NOT EXECUTED**

Full calibration on development-district data has not been performed. Calibration requires real weather + satellite data for each development-district record (3,967 records), which is time-prohibitive (~66-132 hours).

## Calibration Module

`engine/hydroma/eval/hyrue_calibration.py` implements:
- Loads dev records from `stage36_benchmark_split_manifest.json`
- For each dev record: fetches weather, computes EWSI, runs HYRUE
- Computes error metrics (RMSE, MAE, Bias, R², MAPE) on dev data
- Supports grid search / coordinate descent on dev data only
- Records calibration method, dataset, and version per parameter

## Calibration Constraints (Non-Negotiable)

1. Test data is NEVER used for calibration
2. EWSI weights must sum to 1.0 and be non-negative
3. Parameter values must stay within allowed bounds
4. Number of calibrated parameters must be reasonable relative to dev data size
5. Grouped cross-validation (leave-one-district-out) recommended

## Parameters Eligible for Calibration

| Parameter | Current Value | Status |
|---|---|---|
| epsilon | 2.2 g/MJ IPAR | Calibratable |
| k | 0.65 dimensionless | Calibratable |
| hi | 0.45 dimensionless | Calibratable |
| t_opt | 20.0 °C | Calibratable |
| t_min | 5.0 °C | Calibratable |
| t_max | 35.0 °C | Calibratable |
| lai_max | 6.0 m²/m² | Calibratable |
| ewsi_weight_ndmi | 0.4 | Calibratable |
| ewsi_weight_vpd | 0.3 | Calibratable |
| ewsi_weight_soil | 0.3 | Calibratable |

## Parameters NOT Calibratable

| Parameter | Current Value | Status |
|---|---|---|
| thermal_gaussian_width | 8.0 °C | Uncalibrated (no source) |
| ndmi_ref | 0.3 | Uncalibrated (no source) |
| ndmi_crit | -0.2 | Uncalibrated (no source) |
| vpd_low | 0.5 kPa | Uncalibrated (no source) |
| vpd_high | 4.0 kPa | Uncalibrated (no source) |
| soil_field_capacity | 0.35 m³/m³ | Uncalibrated (not site-specific) |
| shortwave_to_par_factor | 0.5 | Fixed (unit conversion) |

## Before Test Benchmark Execution

Before running the test benchmark:
1. Resolve satellite SSL infrastructure issue
2. Run calibration on development-district sample (20-50 records)
3. Freeze calibrated parameters in `stage38_frozen_model_config.json`
4. Execute benchmark on test districts with frozen parameters

## Files

- `engine/hydroma/eval/hyrue_calibration.py` — calibration module
- `engine/hydroma/eval/calibration_parameter_registry.py` — parameter registry
- `engine/reports/data/stage36_calibration_results.json` — calibration results (when available)
