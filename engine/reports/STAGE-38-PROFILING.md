# Stage 38 — Runtime Profiling

## Profiling Method

Profiled the full HYRUE pipeline on 1 development-district record (Deoria, 2016-17) using `BenchmarkProfiler` (`engine/hydroma/eval/benchmark_profiler.py`). Each pipeline operation was timed individually.

## Per-Record Timing Breakdown

| Operation | Duration | Calls |
|---|---|---|
| satellite_stac_search | 18.7s | 1 |
| weather_api_request | 13.1s | 1 |
| raster_processing | 0.1s | 1 |
| hyrue_computation | 0.1s | 1 |
| ewsi_computation | 0.0s | 1 |
| result_serialization | 0.0s | 1 |
| satellite_asset_download | 0.0s | 1 |
| **Total per record** | **~32.0s** | |

## Extrapolation to Full Test Set

| Metric | Value |
|---|---|
| Test records | 1,722 |
| Records per minute | ~1.9 |
| Estimated total time | ~15.3 hours (916 minutes) |
| Weather API calls | 1,722 |
| STAC searches | 1,722 |
| Satellite downloads | 1,722 |

## Bottleneck Analysis

1. **STAC search (18.7s, 58% of time)** — Planetary Computer STAC search with SSL connection issues. This is the dominant bottleneck.
2. **Weather API (13.1s, 41% of time)** — Open-Meteo ERA5 archive request per record.
3. **Local computation (<1s)** — EWSI, HYRUE, raster processing are negligible.

## Optimization Opportunities

| Optimization | Potential Savings |
|---|---|
| Persistent weather cache | ~13s/record (41%) — same coordinates/date range across records |
| Persistent STAC cache | ~18.7s/record (58%) — same coordinates/date range across records |
| Deduplicate coordinates | Reduces API calls when multiple records share coordinates |
| Batch processing | Reduces connection overhead |

## Files

- `engine/hydroma/eval/benchmark_profiler.py` — profiling module
- `tools/diagnostics/stage38_profile_single.py` — profiling script
- `engine/reports/data/stage38_profiling_results.json` — profiling results
