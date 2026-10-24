# Stage 37 — Frozen Model

## Model Configuration Frozen

All HY-RUE and EWSI parameters are frozen in:

`engine/reports/data/stage37_frozen_model_config.json`

## Frozen Parameters (Baseline Defaults)

| Parameter | Value | Unit | Status | Source |
|---|---|---|---|---|
| epsilon | 2.2 | g/MJ IPAR | Calibratable | HYRUEParams wheat preset |
| k | 0.65 | dimensionless | Calibratable | HYRUEParams default |
| hi | 0.45 | dimensionless | Calibratable | HYRUEParams wheat preset |
| t_opt | 20.0 | °C | Calibratable | HYRUEParams wheat preset |
| t_min | 5.0 | °C | Calibratable | HYRUEParams default |
| t_max | 35.0 | °C | Calibratable | HYRUEParams default |
| lai_max | 6.0 | m²/m² | Calibratable | HYRUEParams default |
| ewsi_weight_ndmi | 0.4 | dimensionless | Calibratable | Project default |
| ewsi_weight_vpd | 0.3 | dimensionless | Calibratable | Project default |
| ewsi_weight_soil | 0.3 | dimensionless | Calibratable | Project default |
| ndmi_ref | 0.3 | dimensionless | Uncalibrated | ewsi_pipeline.py default |
| ndmi_crit | -0.2 | dimensionless | Uncalibrated | ewsi_pipeline.py default |
| vpd_low | 0.5 | kPa | Uncalibrated | ewsi_pipeline.py default |
| vpd_high | 4.0 | kPa | Uncalibrated | ewsi_pipeline.py default |
| soil_field_capacity | 0.35 | m³/m³ | Uncalibrated | EWSIInputSeries default |
| shortwave_to_par_factor | 0.5 | dimensionless | Fixed | Radiation unit contract |

## Freeze Rules

1. **Parameters MUST NOT change after freezing** — any change invalidates test results
2. **Test data is never used to justify parameter changes**
3. **If a structural error is found** (unit error, definition error), execution is invalid — parameters cannot be "tuned" to fix it
4. **Any parameter change requires a new model version** and re-execution of the entire protocol from the beginning
5. **EWSI weights must sum to 1.0** and each weight must be non-negative

## Calibration Status

Parameters are at project defaults (uncalibrated). Full calibration on development data is required before test execution.

## PAR Unit Correction

The frozen config documents that the PAR unit error (shortwave used directly as PAR) has been CORRECTED:
- `build_seasonal_climate_inputs()` applies `shortwave_to_par()` with `frac_par=0.5`
- PAR provenance is tracked as `"converted_documented"`
- `radiation_units.py` defines the unit contract

## Files

- `engine/reports/data/stage37_frozen_model_config.json`
