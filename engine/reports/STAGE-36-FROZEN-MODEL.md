# Stage 36 — Frozen Model

## Model Configuration Frozen

Before any test-district execution, all HY-RUE and EWSI parameters have been
frozen in:

`engine/reports/data/stage36_frozen_model_config.json`

## Frozen Parameters

All 17 parameters are at project defaults (uncalibrated):

| Parameter | Value | Unit | Status |
|---|---|---|---|
| epsilon | 2.2 | g/MJ IPAR | Calibratable |
| k | 0.65 | dimensionless | Calibratable |
| hi | 0.45 | dimensionless | Calibratable |
| t_opt | 20.0 | degC | Calibratable |
| t_min | 5.0 | degC | Calibratable |
| t_max | 35.0 | degC | Calibratable |
| lai_max | 6.0 | m²/m² | Calibratable |
| ewsi_weight_ndmi | 0.4 | dimensionless | Calibratable |
| ewsi_weight_vpd | 0.3 | dimensionless | Calibratable |
| ewsi_weight_soil | 0.3 | dimensionless | Calibratable |
| ndmi_ref | 0.3 | dimensionless | Uncalibrated |
| ndmi_crit | -0.2 | dimensionless | Uncalibrated |
| vpd_low | 0.5 | kPa | Uncalibrated |
| vpd_high | 4.0 | kPa | Uncalibrated |
| soil_field_capacity | 0.35 | m³/m³ | Uncalibrated |
| shortwave_to_par_factor | 0.5 | dimensionless | Fixed |
| thermal_gaussian_width | 8.0 | degC | Uncalibrated |

## Freeze Rules

1. Parameters MUST NOT change after freezing
2. If test execution reveals a structural error (unit error, definition
   error), execution is invalid — parameters cannot be "tuned" to fix it
3. Any parameter change requires a new model version and re-execution of
   the entire protocol from the beginning
4. Test-district data is never used to justify parameter changes

## Files

- `engine/reports/data/stage36_frozen_model_config.json`
