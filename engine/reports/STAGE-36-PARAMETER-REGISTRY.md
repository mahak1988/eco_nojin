# Stage 36 — Parameter Registry

## Overview

The calibration parameter registry (`engine/hydroma/eval/calibration_parameter_registry.py`)
registers all 17 parameters that affect HY-RUE yield predictions and EWSI
computation. Each parameter has metadata about source, status, allowed range,
and calibration method.

## Parameter Summary

| Group | Count | Parameters |
|---|---|---|
| HY-RUE biomass | 4 | epsilon, k, lai_max, thermal_gaussian_width |
| HY-RUE thermal | 4 | t_opt, t_min, t_max, thermal_gaussian_width |
| HY-RUE harvest | 1 | hi |
| EWSI weights | 3 | ewsi_weight_ndmi, ewsi_weight_vpd, ewsi_weight_soil |
| EWSI anchors | 4 | ndmi_ref, ndmi_crit, vpd_low, vpd_high |
| EWSI soil | 1 | soil_field_capacity |
| Unit conversion | 1 | shortwave_to_par_factor |

## Status Summary

| Status | Count | Parameters |
|---|---|---|
| Calibratable | 10 | epsilon, k, hi, t_opt, t_min, t_max, lai_max, ewsi_weight_ndmi, ewsi_weight_vpd, ewsi_weight_soil |
| Uncalibrated | 6 | thermal_gaussian_width, ndmi_ref, ndmi_crit, vpd_low, vpd_high, soil_field_capacity |
| Fixed | 1 | shortwave_to_par_factor |

## Parameter Details

Each parameter entry includes: name, value, unit, model component, group,
status, source, allowed range, calibration method, calibration dataset,
calibration version, last updated, and rationale.

## Files

- `engine/hydroma/eval/calibration_parameter_registry.py`
