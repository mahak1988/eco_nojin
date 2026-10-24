# Stage 35 — Benchmark Metrics

## Metrics Not Yet Computed

Full benchmark execution on test districts (Buxar, Muzaffarpur, Rohtas — 1,722 records) has not been completed. No RMSE, MAE, Bias, R², or MAPE values are available.

### Planned Metrics

For matched prediction-observation pairs on test districts:

| Metric | Formula | Unit |
|---|---|---|
| RMSE | sqrt(mean((observed - predicted)²)) | t/ha |
| MAE | mean(|observed - predicted|) | t/ha |
| Bias | mean(predicted - observed) | t/ha |
| R² | 1 - sum((obs - pred)²) / sum((obs - mean_obs)²) | dimensionless |
| MAPE | mean(|obs - pred| / |obs|) × 100 | % |

### Baseline

Naive baseline: mean grain yield from development districts (7 districts, 3,967 records). Computed on dev data only — no test data used.

### Uncertainty

Cluster bootstrap at district level (10 independent sites). 10 districts meets the minimum (≥3) for spatial generalization per `validation_uncertainty.py`.

### Status

**No metrics computed** — awaiting full benchmark execution and EWSI calibration.
