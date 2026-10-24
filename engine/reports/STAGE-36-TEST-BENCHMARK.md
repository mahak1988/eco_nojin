# Stage 36 — Test Benchmark

## Benchmark Status

**Status: NOT EXECUTED**

Full benchmark execution on test districts (Buxar, Muzaffarpur, Rohtas —
1,722 records) has NOT been completed.

## Reason

Full benchmark execution requires:
1. Real weather data for each test record (Open-Meteo API calls)
2. Real satellite data for each test record (Planetary Computer STAC)
3. EWSI computation for each test record
4. HYRUE computation for each test record

Each record requires multiple API calls and raster downloads. Processing
1,722 test records is time-prohibitive in a single session.

## Pilot Validation

Stage 35 verified the pipeline on 1 pilot record (Buxar, 2016-17):

| Metric | Value |
|---|---|
| Weather data | 172 days, 100% coverage |
| Satellite acquisitions | 7 cloud-free Sentinel-2 |
| EWSI mean | 0.4592 (all 3 components present) |
| HYRUE predicted yield | 10.899 t/ha |
| Observed yield | 6.680 t/ha |
| Error | +4.219 t/ha (+63.16%) |

The pilot error analysis (Stage 36) identified the primary error sources:
PAR unit error (shortwave used as PAR without 0.5 conversion), constant LAI,
and uncalibrated EWSI parameters.

## Planned Benchmark Execution

When executed, the benchmark will:

1. Load test-district records from the split manifest
2. For each record: fetch weather, compute EWSI, run HYRUE with frozen params
3. Compute validation metrics (RMSE, MAE, Bias, R², MAPE)
4. Compare against development-set baseline
5. Record per-record status (SUCCESS/PARTIAL/BLOCKED/FAILED)
6. No records will be deleted from the report

## Files

- `engine/reports/data/stage36_frozen_model_config.json`
- `engine/reports/data/stage36_benchmark_split_manifest.json`
