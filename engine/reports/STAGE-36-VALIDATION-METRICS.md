# Stage 36 — Validation Metrics

## Metrics Status

**Status: NOT COMPUTED**

Full validation metrics (RMSE, MAE, Bias, R², MAPE) have not been computed
because the benchmark has not been executed on test districts.

## Planned Metrics

For matched prediction-observation pairs on test districts:

| Metric | Formula | Unit |
|---|---|---|
| RMSE | sqrt(mean((observed - predicted)²)) | t/ha |
| MAE | mean(|observed - predicted|) | t/ha |
| Bias | mean(predicted - observed) | t/ha |
| R² | 1 - Σ(obs-pred)² / Σ(obs-mean_obs)² | dimensionless |
| MAPE | mean(|obs-pred|/|obs|) × 100 | % |

## Baseline

Naive baseline: mean grain yield from development districts (3,967 records).
Computed on dev data only — no test data used.

## Reporting Rules

- Metrics computed only on records with successful computation
- Records with BLOCKED/FAILED status are reported but excluded from metrics
- R² undefined when SS_tot = 0 (reported as null)
- MAPE undefined when observed = 0 (those records excluded from MAPE)
- Development and test metrics reported separately

## Files

- `engine/reports/data/stage36_calibration_results.json` (dev metrics, when available)
