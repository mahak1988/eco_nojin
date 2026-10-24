# Stage 36 — Limitations

## Data Limitations

1. **Single-season verification** — Real EWSI pipeline verified for one
   season (2016-17, Buxar). Other 5 seasons and 9 districts not yet tested
   with real satellite data.

2. **Point sampling vs. field average** — CIMMYT coordinates are approximate
   (~1 km resolution). Sentinel-2 point sampling at 20 m resolution does not
   represent field-average reflectance.

3. **Weather spatial resolution** — ERA5-Land ~9 km grid cells, not
   field-specific. Soil moisture is reanalysis estimate (REANALYSIS_ESTIMATE),
   not in-situ measurement.

4. **Satellite temporal gaps** — Sentinel-2 5-day revisit with cloud cover.
   Interpolation used to fill gaps (flagged INTERPOLATED, not
   SATELLITE_RETRIEVED).

5. **Only 3 test districts** — Buxar, Muzaffarpur, Rohtas. Limited statistical
   power for bootstrap uncertainty and generalization.

## Method Limitations

1. **EWSI uncalibrated** — Weights (0.4/0.3/0.3), NDMI anchors (0.3/-0.2),
   VPD anchors (0.5/4.0 kPa), FC (0.35 m³/m³) are uncalibrated project
   defaults. Not validated against CIMMYT data.

2. **No model calibration on test data** — Per Stage 35 rule #6, HYRUE
   parameters not tuned using observed yields. LAI fixed at 3.0 m²/m²
   (typical wheat value).

3. **No uncertainty quantification on real data** — Cluster bootstrap not
   yet executed on matched pairs from full benchmark.

4. **Single point per record** — No multi-pixel aggregation or uncertainty
   from spatial sampling.

5. **Filesystem limitation** — Python cannot import from
   `engine/hydroma/models/` and `engine/hydroma/simulation/` directories,
   preventing calibration module execution.

## Generalization Limits

Results valid only for wheat in Bihar/Eastern Uttar Pradesh, India,
2016-2022. No generalization to other crops, regions, or time periods.

## Files

All Stage 36 reports.
