# Stage 38 — Validation Metrics

## Metrics Status

**Status: NOT COMPUTED**

Full validation metrics have not been computed because the benchmark has not been executed on test districts.

## Estimated Runtime

Full benchmark execution on 1,722 test records is estimated at ~15.3 hours based on profiling (32s per record). With persistent caching, this could be reduced to ~8.6 minutes.

## Planned Metrics

For matched prediction-observation pairs on test districts:

| Metric | Formula | Unit |
|---|---|---|
| RMSE | sqrt(mean((observed − predicted)²)) | t/ha |
| MAE | mean(\|observed − predicted\|) | t/ha |
| Bias | mean(predicted − observed) | t/ha |
| R² | 1 − Σ(obs−pred)² / Σ(obs−mean_obs)² | dimensionless |
| MAPE | mean(\|obs−pred\|/\|obs\|) × 100 | % |

## Baseline

Naive baseline: mean grain yield from development districts (3,967 records). Computed on dev data only — no test data used.

## Reporting Rules

- Metrics computed only on records with successful computation
- Records with BLOCKED/FAILED status are reported but excluded from metrics
- R² undefined when SS_tot = 0 (reported as null)
- MAPE undefined when observed = 0 (those records excluded from MAPE)
- Development and test metrics reported separately
- Sample size reported for each metric

## Pilot Result (1 Record)

| Metric | Value |
|---|---|
| Record | Buxar field_1, 2016-17 |
| Predicted yield | 4.807 t/ha |
| Observed yield | 6.680 t/ha |
| Absolute error | −1.873 t/ha |
| Relative error | −28.0% |

This single-record result is a pipeline smoke test, NOT a validation metric.

## Files

- `engine/reports/data/stage38_benchmark_results.jsonl` — results (when benchmark executed)
