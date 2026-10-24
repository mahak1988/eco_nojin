# Stage 40 — Validation Metrics

## Test-set result (frozen calibrated model)

| Metric | Value | Unit |
|---|---:|---|
| n | 450 | records |
| RMSE | 1.2828 | t/ha |
| MAE | 1.0049 | t/ha |
| Bias | -0.4060 | t/ha |
| R² | -0.4115 | dimensionless |
| MAPE | 23.34 | % |
| MAPE exclusions | 0 | records |

### By test district

| District | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
| Buxar | 189 | 1.2742 | 0.9675 | -0.3939 | -0.3493 |
| Muzaffarpur | 110 | 1.1991 | 0.9577 | -0.1420 | -0.1540 |
| Rohtas | 151 | 1.3507 | 1.0861 | -0.6135 | -0.7485 |

### By season

| Season | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
| 2016-17 | 59 | 0.9479 | 0.7199 | 0.1635 | -0.0631 |
| 2017-18 | 113 | 1.4316 | 1.1022 | -0.9150 | -1.1780 |
| 2018-19 | 129 | 1.2631 | 1.0274 | -0.4434 | -0.3934 |
| 2019-20 | 101 | 1.3030 | 0.9804 | 0.0795 | 0.0442 |
| 2020-21 | 37 | 1.3110 | 1.1399 | -0.9988 | -1.7225 |
| 2021-22 | 11 | 1.1698 | 1.0398 | -0.2579 | -1.0119 |

### By input quality

| Input quality | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
| complete | 450 | 1.2828 | 1.0049 | -0.4060 | -0.4115 |

## Development-set result (for comparison, not a test metric)

| Metric | Baseline | Calibrated |
|---|---:|---:|
| RMSE (t/ha) | 1.0579 | 0.8054 |
| MAE (t/ha) | 0.9136 | 0.6363 |
| Bias (t/ha) | -0.7375 | -0.0709 |
| R² | -0.1586 | 0.3284 |
| MAPE (%) | 22.19 | 17.19 |

## Like-for-like test-set comparison

The Stage 39 baseline run covered only **40** test records, all from the
2016-17 season. Comparing that against a full calibrated run would
compare different record sets, so both parameter sets are evaluated on
the **same** records here.

HYRUE's seasonal yield is exactly linear in `ε` (`Y = ε · S · HI / 100`),
so the baseline prediction for a record is the calibrated prediction
scaled by `ε_base / ε_cal`. That identity is validated below against
the records for which a real baseline prediction exists.

| Identity check | Value |
|---|---|
| Real baseline records available | 13 |
| Records matching within 1e-9 | 13 |
| Max absolute difference | 0.000000000000 t/ha |
| Identity validated | True |

| Metric | Baseline (same records) | Calibrated | Δ |
|---|---:|---:|---:|
| n | 450 | 450 | - |
| RMSE (t/ha) | 1.5547 | 1.2828 | -0.2719 |
| MAE (t/ha) | 1.2970 | 1.0049 | -0.2921 |
| Bias (t/ha) | -1.0767 | -0.4060 | 0.6707 |
| R² | -1.0733 | -0.4115 | 0.6618 |
| MAPE (%) | 28.21 | 23.34 | -4.87 |

## Metric definitions and guard conditions

| Metric | Definition | Guard |
|---|---|---|
| RMSE | `sqrt((1/n) Σ (ŷ−y)²)` | — |
| MAE | `(1/n) Σ \|ŷ−y\|` | — |
| Bias | `(1/n) Σ (ŷ−y)` | — |
| R² | `1 − Σ(y−ŷ)² / Σ(y−ȳ)²` | reported `null` with a reason when the yields have zero variance |
| MAPE | `(100/n) Σ \|ŷ−y\|/\|y\|` | observations with \|y\| ≤ 1e-6 are excluded and counted |

## Reading the numbers

The calibration **improved** the external result on the same records:
RMSE fell from 1.5547 to 1.2828 t/ha and R² rose
from -1.0733 to -0.4115.

**The calibrated R² is still negative.** That means the sum of squared
prediction errors exceeds the sum of squared deviations of the observed
yields from their own mean — i.e. predicting each district's mean
observed yield for every field would score a better R² than this model
does. The calibration reduced the error and removed much of the bias;
it did not make the model a good predictor of district-level yield on
these three held-out districts.

This is reported as measured. A negative R² is not a rounding artefact
and is not suppressed anywhere in this report set.

The test set has **three districts**. Metrics computed on them describe
those three districts; they do not establish generalisation beyond
them.
