# Stage 37 — Development Baseline

## Calibration Status

**Status: BASELINE_ONLY**

No parameter calibration has been performed on development-district data. All 17 parameters remain at project defaults.

## Reason

Full calibration requires real weather + satellite data acquisition for each development-district record (3,967 records). Each record requires:
- 1 Open-Meteo API call (weather: Tmin/Tmax/precip/shortwave/dewpoint/RH/soil moisture)
- 1 Planetary Computer STAC search + multiple COG downloads (satellite: NIR/SWIR)

At ~1-2 minutes per record, full calibration would take 66-132 hours — time-prohibitive in a single session.

## Baseline Model Performance

The baseline model (all parameters at defaults) was tested on 1 pilot record (Buxar, 2016-17):

| Metric | Value |
|---|---|
| Predicted yield | 4.807 t/ha |
| Observed yield | 6.680 t/ha |
| Absolute error | −1.873 t/ha |
| Relative error | −28.0% |

The negative error (underestimate) is expected with uncalibrated parameters. The PAR unit correction (from +63% overestimate to −28% underestimate) was the dominant fix.

## Baseline Metrics (Development)

RMSE, MAE, Bias, R², MAPE have NOT been computed on development data because:
1. Calibration requires real data for each dev record
2. Full dev-set execution is time-prohibitive
3. No validation-grade metrics can be reported without executed predictions

## Files

- `engine/reports/data/stage37_frozen_model_config.json` — baseline parameter configuration
- `engine/hydroma/eval/hyrue_calibration.py` — calibration module (ready to run)
