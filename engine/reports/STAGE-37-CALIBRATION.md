# Stage 37 — Calibration

## Calibration Protocol

Calibration is performed using ONLY development-district records (7 districts: Begusarai, Bhojpur, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura — 3,967 records). Test-district records (Buxar, Muzaffarpur, Rohtas — 1,722 records) are NEVER used for parameter estimation.

## Calibration Module

`engine/hydroma/eval/hyrue_calibration.py` implements:

1. Loads dev records from `stage36_benchmark_split_manifest.json`
2. For each dev record: fetches weather, computes EWSI, runs HYRUE
3. Computes error metrics (RMSE, MAE, Bias, R², MAPE) on dev data
4. Supports grid search / coordinate descent on dev data only
5. Records calibration method, dataset, and version per parameter

## Calibration Status

**Status: NOT EXECUTED**

Full calibration has not been run because real data acquisition for 3,967 dev records is time-prohibitive (~66-132 hours).

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

| Parameter | Current Value | Status | Reason |
|---|---|---|---|
| thermal_gaussian_width | 8.0 °C | Uncalibrated | No published source |
| ndmi_ref | 0.3 | Uncalibrated | No published source |
| ndmi_crit | -0.2 | Uncalibrated | No published source |
| vpd_low | 0.5 kPa | Uncalibrated | No published source |
| vpd_high | 4.0 kPa | Uncalibrated | No published source |
| soil_field_capacity | 0.35 m³/m³ | Uncalibrated | Not site-specific |
| shortwave_to_par_factor | 0.5 | Fixed | Unit conversion, not a model parameter |

## Calibration Constraints

1. Test data is NEVER used for calibration
2. EWSI weights must sum to 1.0 and be non-negative
3. Parameter values must stay within allowed bounds
4. Number of calibrated parameters must be reasonable relative to dev data size
5. Grouped cross-validation (leave-one-district-out) recommended for internal evaluation

## Files

- `engine/hydroma/eval/hyrue_calibration.py` — calibration implementation
- `engine/hydroma/eval/calibration_parameter_registry.py` — parameter registry
- `engine/reports/data/stage36_calibration_results.json` — calibration results (when available)
