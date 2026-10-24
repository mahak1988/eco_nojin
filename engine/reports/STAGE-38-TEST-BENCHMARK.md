# Stage 38 — Test Benchmark

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
2. Fetch weather data from Open-Meteo ERA5-Land
3. Fetch satellite data from Planetary Computer STAC (Sentinel-2 L2A NIR/SWIR)
4. Compute NDMI from NIR/SWIR reflectance
5. Compute EWSI from NDMI + VPD + soil moisture
6. Run HYRUE seasonal with frozen parameters
7. Record prediction vs observed yield
8. Record per-record execution status

## Resumable Runner

`engine/hydroma/eval/resumable_benchmark_runner.py` implements:
- Record-level state tracking in SQLite
- Incremental JSONL results output
- Run manifest with aggregate statistics
- Skip already-processed records on resume

## Estimated Runtime

| Scenario | Per Record | Total (1,722 records) |
|---|---|---|
| No cache | 32.0s | 15.3 hours |
| Weather cache only | 18.9s | 9.0 hours |
| STAC cache only | 13.3s | 6.4 hours |
| Both caches | 0.3s | 8.6 minutes |

## Satellite SSL Issue

During profiling, Planetary Computer STAC API returned SSL errors:
```
SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol')
```

This prevents satellite data acquisition and therefore EWSI computation and HYRUE execution. The signing service works correctly, but the STAC search endpoint has intermittent SSL connectivity.

## Metrics (When Executed)

For matched prediction-observation pairs on test districts:

| Metric | Formula | Unit |
|---|---|---|
| RMSE | sqrt(mean((obs − pred)²)) | t/ha |
| MAE | mean(\|obs − pred\|) | t/ha |
| Bias | mean(pred − obs) | t/ha |
| R² | 1 − Σ(obs−pred)² / Σ(obs−mean_obs)² | dimensionless |
| MAPE | mean(\|obs−pred\|/\|obs\|) × 100 | % |

## Files

- `engine/hydroma/eval/resumable_benchmark_runner.py` — runner module
- `engine/reports/data/stage36_benchmark_split_manifest.json` — test/dev split
- `engine/reports/data/stage37_frozen_model_config.json` — frozen model config
