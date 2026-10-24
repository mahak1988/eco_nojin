# Stage 41-D — Metrics recomputed from shard JSONL

Source: Stage 41 shard JSONL; computed rows = 1081 of 1722 manifest records.
This is a fresh calculation from shard records; it is distinct from the older `stage41_analysis.json` summary.

| Metric | Baseline (ε=2.2) | Calibrated (ε=2.63) | Mean predictor |
|---|---:|---:|---:|
| R² | -12.0704276131 | -11.4135769927 | 0 |
| RMSE (t/ha) | 4.01298347921 | 3.91084807138 | 1.10999870908 |
| MAE (t/ha) | 3.8635098252 | 3.75636495599 | 0.927716139765 |
| Bias (t/ha) | -3.8635098252 | -3.75636495599 | -4.84759729531e-17 |
| MAPE (%) | 86.9736088611 | 84.4275415022 | 24.9463820607 |
| n | 1081 | 1081 | 1081 |

- Calibrated RMSE minus baseline RMSE: -0.102135407824 t/ha (negative means calibrated is better).
- Calibrated RMSE minus mean-predictor RMSE: 2.8008493623 t/ha.
- Stage 40 reference RMSE = 1.2828; Stage 41 calibrated minus Stage 40 = 2.62804807138 t/ha.
- No parameters were changed and no model was run by this audit.


## Stage 40 comparison on shared IDs (294 records)

| Metric | Stage 40 calibrated | Stage 41 baseline | Stage 41 calibrated | Mean predictor |
|---|---:|---:|---:|---:|
| R² | -0.321015343418 | -11.9019686417 | -11.2384423249 | 0 |
| RMSE (t/ha) | 1.30019939268 | 4.06334800374 | 3.95748338903 | 1.13124332046 |
| MAE (t/ha) | 1.02415258779 | 3.9212530989 | 3.81270164059 | 0.933374288491 |
| Bias (t/ha) | -0.496547400169 | -3.9212530989 | -3.81270164059 | 5.46803720972e-16 |
| MAPE (%) | 23.3853606209 | 87.2710274192 | 84.7830918693 | 25.2394207735 |
| n | 294 | 294 | 294 | 294 |

This is the like-for-like Stage 40 comparison. It excludes IDs whose observed yield differs between stored runs.