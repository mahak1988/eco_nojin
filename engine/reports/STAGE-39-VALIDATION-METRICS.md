# Stage 39 — Validation Metrics

## Metrics Status

Metrics are computed from the benchmark run and written to
`engine/reports/data/stage39_benchmark/benchmark_summary.json`.

The method is implemented and unit-tested; the numbers below are a
**snapshot** taken while the run was still in progress (26 of 1,722
records complete, all from the 2016-17 season). They are reported to
document the state of the run, not as a final result.

## Snapshot (26 of 1,722 records, 2016-17 season only)

| Metric | Value |
|---|---|
| n | 26 |
| RMSE | 1.132 t/ha |
| MAE | 0.959 t/ha |
| Bias | −0.686 t/ha |
| R² | **−1.099** |
| MAPE | 18.12 % (0 excluded) |

### By district

| District | n | RMSE | Bias | R² |
|---|---|---|---|---|
| Buxar | 4 | 1.712 | −0.235 | −0.684 |
| Muzaffarpur | 14 | 1.027 | −0.797 | −18.375 |
| Rohtas | 8 | 0.924 | −0.716 | 0.121 |

### Uncertainty (district-level cluster bootstrap)

| Quantity | Value |
|---|---|
| Status | OK (3 districts) |
| RMSE mean | 1.158 t/ha |
| RMSE 95 % CI | [0.924, 1.712] t/ha |

## The R² Value Is Negative — What It Means

**R² = −1.10 means the model is worse than predicting the mean observed
yield of the evaluation set.** A negative R² is not a rounding artefact
and not a bug; it is the direct consequence of a systematic
under-prediction (Bias = −0.686 t/ha) combined with predictions that
are not tracking the record-to-record variation.

The most likely mechanism is the identifiability problem described in
`STAGE-39-PARAMETER-IDENTIFIABILITY.md`: the *scale* of the prediction
is set by the product ε·HI, and both are uncalibrated project
defaults. A uniform scale error shifts every prediction in the same
direction, which inflates the error without improving the fit. The
model currently has enough systematic bias to be worse than a
constant.

The R² for Muzaffarpur (−18.4) is driven by a small sample (n = 14)
with a narrow observed-yield range; it is not evidence of a
catastrophic failure in that district.

**This result must not be reported as validation of the model.** It is
evidence that the *uncalibrated* model is not yet at the level where a
negative R² is avoidable, and it is a direct argument for executing the
development calibration before the test set is used for any claim.

## Metric Definitions


With `e_i = y_hat_i - y_i`:

| Metric | Definition | Unit |
|---|---|---|
| RMSE | `sqrt( (1/n) * sum_i e_i^2 )` | t/ha |
| MAE | `(1/n) * sum_i \|e_i\|` | t/ha |
| Bias | `(1/n) * sum_i e_i` | t/ha |
| R² | `1 - sum_i (y_i - y_hat_i)^2 / sum_i (y_i - y_bar)^2` | dimensionless |
| MAPE | `(100/n) * sum_i \|e_i / y_i\|` | % |

### Guard conditions

* **R²** is reported as `null` when `sum_i (y_i - y_bar)^2` is zero or
  near zero (zero variance in the observed yields), with the reason
  recorded in `r2_undefined_reason`. A misleading number is never
  reported.
* **MAPE** excludes records whose observed yield is zero or below
  `1e-6`; the excluded count is reported in `mape_excluded`. MAE and
  RMSE remain the primary metrics because they are defined for every
  record.
* Only records with **both** a prediction and an observation contribute.
  Blocked and failed records are counted and reported, not silently
  dropped.

## Grouping

Metrics are computed for:

1. All qualifying test records.
2. By district (Buxar, Muzaffarpur, Rohtas).
3. By season (2016-17 … 2021-22).
4. By input quality (`complete` / `partial` / `unavailable`).
5. By EWSI provenance (complete vs. estimated components).

The sample size (`n`) is reported for every group so that a metric
computed on a handful of records cannot be mistaken for a robust
estimate.

## Baseline

The naive baseline is the mean observed grain yield of the **development**
districts (3,967 records). It is computed on development data only; no
test observation enters it.

## Interpretation Constraints

The frozen model carries **uncalibrated default parameters** (see
`STAGE-39-CALIBRATION-REPORT.md`). Metrics from this run therefore
characterise the *default* model, not a calibrated one. They must be
reported as such, and a low RMSE must not be read as evidence that the
parameters are correct — a degenerate model that predicts the mean would
score a low RMSE as well.

Three test districts are too few for a stable spatial-generalisation
claim. The cluster bootstrap (below) is reported with that limitation
stated explicitly.
