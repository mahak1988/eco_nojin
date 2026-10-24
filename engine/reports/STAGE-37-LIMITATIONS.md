# Stage 37 — Limitations

## Data Limitations

1. **Single-record verification** — Pipeline verified with real data on 1 test record (Buxar, 2016-17). Other 5 seasons and 9 districts not yet tested with real satellite data.

2. **Only 3 test districts** — Buxar, Muzaffarpur, Rohtas. Limited statistical power for bootstrap uncertainty and generalization.

3. **Point sampling vs. field average** — CIMMYT coordinates are approximate (~1 km resolution). Sentinel-2 point sampling at 20 m resolution does not represent field-average reflectance.

4. **Weather spatial resolution** — ERA5-Land ~9 km grid cells, not field-specific. Soil moisture is reanalysis estimate (REANALYSIS_ESTIMATE), not in-situ measurement.

5. **Satellite temporal gaps** — Sentinel-2 5-day revisit with cloud cover. Interpolation used to fill gaps (flagged INTERPOLATED, not SATELLITE_RETRIEVED).

## Method Limitations

1. **EWSI uncalibrated** — Weights (0.4/0.3/0.3), NDMI anchors (0.3/-0.2), VPD anchors (0.5/4.0 kPa), FC (0.35 m³/m³) are uncalibrated project defaults. Not validated against CIMMYT data.

2. **No model calibration on test data** — Per Stage 35 rule #6, HYRUE parameters not tuned using observed yields. LAI handled through observed/NDVI/GDD/missing pipeline (no constant fallback).

3. **No uncertainty quantification on real data** — Cluster bootstrap not yet executed on matched pairs from full benchmark.

4. **Execution time** — Full benchmark on 1,722 test records estimated at 21-57 hours of API calls. Time-prohibitive in a single session.

## Generalization Limits

Results valid only for wheat in Bihar/Eastern Uttar Pradesh, India, 2016-2022. No generalization to other crops, regions, or time periods.

## Files

All Stage 37 reports.
