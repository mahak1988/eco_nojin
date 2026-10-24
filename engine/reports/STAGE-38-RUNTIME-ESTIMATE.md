# Stage 38 — Runtime Estimate

## Profiling Results

Profiled 1 development-district record (Deoria, 2016-17) using `BenchmarkProfiler`.

| Operation | Duration | % of Time |
|---|---|---|
| satellite_stac_search | 18.7s | 58% |
| weather_api_request | 13.1s | 41% |
| raster_processing | 0.1s | <1% |
| hyrue_computation | 0.1s | <1% |
| ewsi_computation | 0.0s | <1% |
| result_serialization | 0.0s | <1% |
| satellite_asset_download | 0.0s | <1% |
| **Total per record** | **32.0s** | **100%** |

## Extrapolation to Full Test Set

| Metric | Value |
|---|---|
| Test records | 1,722 (Buxar: 709, Muzaffarpur: 427, Rohtas: 586) |
| Records per minute | ~1.9 |
| Estimated total time | **~15.3 hours** (916 minutes) |
| Weather API calls | 1,722 |
| STAC searches | 1,722 |
| Satellite downloads | 1,722 |

## Bottleneck Analysis

**STAC search (58%)** and **weather API (41%)** dominate runtime. Local computation (EWSI, HYRUE, raster processing) is negligible (<1%).

## Cache Impact

With persistent caching:
- Weather cache hit: saves ~13s/record (41%)
- STAC cache hit: saves ~18.7s/record (58%)
- Combined: could reduce per-record time from 32s to ~0.3s (99% reduction)

## Estimated Runtime with Caching

| Cache Scenario | Per Record | Total (1,722 records) |
|---|---|---|
| No cache | 32.0s | 15.3 hours |
| Weather cache only | 18.9s | 9.0 hours |
| STAC cache only | 13.3s | 6.4 hours |
| Both caches | 0.3s | 8.6 minutes |

## Files

- `engine/hydroma/eval/benchmark_profiler.py` — profiling module
- `engine/reports/data/stage38_profiling_results.json` — profiling results
