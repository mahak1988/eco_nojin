# Stage 37 — Test Benchmark

## Benchmark Status

**Status: NOT EXECUTED**

Full benchmark execution on test districts (Buxar, Muzaffarpur, Rohtas — 1,722 records) has NOT been completed.

## Test Districts

| District | Records |
|---|---|
| Buxar | 709 |
| Muzaffarpur | 427 |
| Rohtas | 586 |
| **Total** | **1,722** |

## Execution Protocol

For each test record:

1. Load record from CIMMYT dataset (Field_ID, District, coordinates, dates, observed yield)
2. Fetch weather data from Open-Meteo ERA5-Land (Tmin/Tmax/precip/shortwave/dewpoint/RH/soil moisture)
3. Fetch satellite data from Planetary Computer STAC (Sentinel-2 L2A NIR/SWIR)
4. Compute NDMI from NIR/SWIR reflectance
5. Compute EWSI from NDMI + VPD + soil moisture
6. Run HYRUE seasonal with frozen parameters
7. Record prediction vs observed yield
8. Record per-record status (SUCCESS/PARTIAL/BLOCKED/FAILED)

## Time Estimate

| Operation | Time per record | Time for 1,722 records |
|---|---|---|
| Weather API call | ~10-30 seconds | ~5-8 hours |
| Satellite STAC search + COG download | ~30-90 seconds | ~14-43 hours |
| EWSI + HYRUE computation | < 1 second | < 30 minutes |
| **Total** | **~45-120 seconds** | **~21-57 hours** |

Full execution is time-prohibitive in a single session.

## Pilot Validation (1 Record)

| Metric | Value |
|---|---|
| Record | Buxar field_1, 2016-17 |
| Weather | 172 days, 100% coverage |
| Satellite | 7 cloud-free acquisitions |
| EWSI | mean=0.4592, all 3 components present |
| HYRUE predicted | 4.807 t/ha |
| Observed | 6.680 t/ha |
| Error | −1.873 t/ha (−28.0%) |

## Metrics (When Executed)

| Metric | Formula | Unit |
|---|---|---|
| RMSE | sqrt(mean((obs − pred)²)) | t/ha |
| MAE | mean(\|obs − pred\|) | t/ha |
| Bias | mean(pred − obs) | t/ha |
| R² | 1 − Σ(obs−pred)² / Σ(obs−mean_obs)² | dimensionless |
| MAPE | mean(\|obs−pred\|/\|obs\|) × 100 | % |

## Files

- `engine/reports/data/stage37_frozen_model_config.json`
- `engine/reports/data/stage36_benchmark_split_manifest.json`
