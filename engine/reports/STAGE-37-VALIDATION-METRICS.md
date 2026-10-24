# Stage 37 — Validation Metrics

## Metrics Status

**Status: NOT COMPUTED**

Full validation metrics have not been computed because the benchmark has not been executed on test districts (1,722 records). Execution is time-prohibitive (~21-57 hours of API calls).

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

## Pilot Result (1 Record)

| Metric | Value |
|---|---|
| Predicted yield | 4.807 t/ha |
| Observed yield | 6.680 t/ha |
| Absolute error | −1.873 t/ha |
| Relative error | −28.0% |

This single-record result is NOT a validation metric — it is a pipeline smoke test.

## Files

- `engine/reports/data/stage36_calibration_results.json` (dev metrics, when available)
