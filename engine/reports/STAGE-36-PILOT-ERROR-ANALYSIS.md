# Stage 36 — Pilot Error Analysis

## Pilot Record

| Field | Value |
|---|---|
| Field ID | pilot_1 |
| District | Buxar |
| Year | 2016-17 |
| Coordinates | 26.33 N, 83.54 E |
| Season | 2016-11-01 to 2017-04-21 (172 days) |
| Observed yield | 6.680 t/ha |
| Predicted yield | 10.899 t/ha |
| Absolute error | +4.219 t/ha |
| Relative error | +63.16% |

## Component Issues Identified

### 1. PAR Unit Error (PRIMARY DRIVER)

Open-Meteo `shortwave_radiation_sum` (MJ/m²/day) was used directly as PAR
without the 0.5 shortwave→PAR conversion factor. Shortwave radiation includes
UV + visible + NIR; PAR (~400-700 nm) is roughly 45-50% of shortwave. Using
shortwave as PAR overestimates PAR by ~2x, directly scaling biomass upward
by ~2x.

**Status:** CONFIRMED — weather_source.py stores shortwave as
"ShortwaveRadiation" column; seasonal_predictor.py passes it to HYRUE as PAR
without conversion.

### 2. LAI Misrepresentation

LAI was fixed at 3.0 m²/m² (default) for the entire season. Wheat LAI follows
a sigmoid development curve (near zero at emergence, peaking around anthesis,
senescing before harvest). Constant LAI=3.0 gives f_IPAR =
1 - exp(-0.65 × 3.0) = 0.858, near the asymptote. Actual seasonal average
f_IPAR is likely lower.

**Status:** CONFIRMED — seasonal_predictor.py uses GDD model fallback with
lai_max=4.0, but pilot used constant LAI=3.0.

### 3. Uncalibrated EWSI Parameters

EWSI weights (0.4/0.3/0.3), NDMI anchors (0.3/-0.2), VPD anchors (0.5/4.0
kPa), and field capacity (0.35 m³/m³) are uncalibrated project defaults with
no published source for wheat in eastern India. EWSI mean of 0.4592 implies
moderate water stress (f_water = 0.5408), but the stress magnitude is
unverified.

**Status:** CONFIRMED — ewsi_pipeline.py uses hard-coded defaults.

### 4. Other Contributing Factors

- RUE (epsilon): 2.2 g/MJ IPAR from wheat preset, not calibrated to CIMMYT
- Harvest index: 0.45 from wheat preset, not calibrated
- Temperature stress: t_opt=20.0°C with hard-coded Gaussian width of 8°C

## Diagnostic Computation

| Component | Value |
|---|---|
| f_IPAR (LAI=3.0) | 0.858 |
| f_water (EWSI=0.459) | 0.541 |
| PAR as shortwave (MJ/m²/day) | ~450 |
| PAR converted (×0.5) | ~225 |
| Yield with shortwave-as-PAR | 355.47 t/ha (error: +5,221%) |
| Yield with converted PAR | 177.73 t/ha (error: +2,561%) |

Note: Even with PAR conversion, yield remains far above observed (6.68 t/ha),
indicating multiple compounding errors.

## Recommendations

1. Apply shortwave→PAR conversion factor of 0.5 (documented as estimated)
2. Replace constant LAI with crop-stage-dependent LAI (GDD model or NDVI-based)
3. Calibrate EWSI weights and anchors on development-district data only
4. Do NOT tune parameters to reduce pilot error on this single record — the
   pilot error analysis is diagnostic, not a calibration target

## Files

- `engine/hydroma/eval/pilot_error_analysis.py`
- `engine/reports/data/stage35_pilot_single.json`
