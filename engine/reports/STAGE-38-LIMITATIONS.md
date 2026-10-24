# Stage 38 — Limitations

## Data Limitations

1. **Single-record verification** — Pipeline verified with real data on 1 test record (Buxar, 2016-17). Other 5 seasons and 9 districts not yet tested.

2. **Only 3 test districts** — Buxar, Muzaffarpur, Rohtas. Limited statistical power for validation.

3. **Point sampling vs. field average** — CIMMYT coordinates are approximate (~1 km resolution). Sentinel-2 point sampling at 20 m resolution does not represent field-average reflectance.

4. **Weather spatial resolution** — ERA5-Land ~9 km grid cells, not field-specific. Soil moisture is reanalysis estimate (REANALYSIS_ESTIMATE), not in-situ measurement.

## Method Limitations

1. **EWSI uncalibrated** — Weights (0.4/0.3/0.3), NDMI anchors (0.3/-0.2), VPD anchors (0.5/4.0 kPa), FC (0.35 m³/m³) are uncalibrated project defaults.

2. **No model calibration on test data** — Per Stage 35 rule #6, HYRUE parameters not tuned using observed yields.

3. **No uncertainty quantification on real data** — Cluster bootstrap not yet executed on matched pairs from full benchmark.

4. **LAI not available** — Without satellite NDVI data, LAI cannot be computed from weather data alone. HYRUE requires LAI input.

## Infrastructure Limitations

1. **Satellite SSL issue** — Planetary Computer STAC API returns SSL errors, preventing NIR/SWIR acquisition. Without NIR/SWIR, NDMI and EWSI cannot be computed, and HYRUE cannot run.

2. **Execution time** — Full benchmark on 1,722 test records estimated at 15.3 hours without caching, 8.6 minutes with full caching.

## Generalization Limits

Results valid only for wheat in Bihar/Eastern Uttar Pradesh, India, 2016-2022. No generalization to other crops, regions, or time periods.

## Files

All Stage 38 reports.
