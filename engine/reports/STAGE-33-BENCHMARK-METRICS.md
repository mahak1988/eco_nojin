# Stage 33: Benchmark Metrics Report

## A. Metrics Formulas

| Metric | Formula | Unit |
|---|---|---|
| RMSE | sqrt((1/n) * sum((Y_i - Y_hat)^2)) | t/ha |
| MAE | (1/n) * sum(abs(Y_i - Y_hat)) | t/ha |
| Bias | (1/n) * sum(Y_hat - Y_i) | t/ha |
| R^2 | 1 - SS_res / SS_tot | dimensionless |

Positive Bias = model overestimates. Negative Bias = model underestimates.
R^2 is `None` when observed variance is zero (all observations identical).
MAPE is `None` when any observed value is zero.

## B. STRICT Policy Metrics (Primary Evaluation)

| Metric | Value | Unit |
|---|---|---|
| RMSE | None | t/ha |
| MAE | None | t/ha |
| Bias | None | t/ha |
| R^2 | None | dimensionless |
| N valid pairs | 0 | — |

**Status:** BLOCKED — no predictions produced. Metrics cannot be computed.

## C. ALLOW_ESTIMATED_INPUTS Policy Metrics (Secondary Evaluation)

| Metric | Value | Unit |
|---|---|---|
| RMSE | None | t/ha |
| MAE | None | t/ha |
| Bias | None | t/ha |
| R^2 | None | dimensionless |
| N valid pairs | 0 | — |

**Status:** BLOCKED — no predictions produced. Metrics cannot be computed.

## D. DIAGNOSTIC Policy Metrics (Supplementary Only — NOT Validation-Grade)

| Metric | Value | Unit |
|---|---|---|
| RMSE | 1.8572 | t/ha |
| MAE | 1.6364 | t/ha |
| Bias | 1.5004 | t/ha |
| R^2 | -2.816 | dimensionless |
| MAPE | 42.2445 | % |
| N valid pairs | 80 | — |
| Mean observed | 4.4336 | t/ha |
| Mean predicted | 5.934 | t/ha |

**WARNING:** These metrics are computed from `legacy_constant` mode predictions
which use scalar mean inputs. They overstate seasonal totals and are NOT
suitable for validation claims.

## E. Baseline Comparison

| Metric | Value | Unit |
|---|---|---|
| Baseline type | mean_observed_yield_from_development_set | — |
| Baseline value | 4.0096 | t/ha |
| Dev mean yield | 4.0096 | t/ha |
| Dev std yield | 0.98 | t/ha |
| Dev N | 3967 | — |
| Test mean yield | 4.4562 | t/ha |
| Test N | 1722 | — |
| Baseline RMSE | 1.1831 | t/ha |
| Baseline MAE | 1.0017 | t/ha |
| Baseline Bias | -0.4466 | t/ha |
| Baseline R^2 | -0.1662 | dimensionless |

Since the baseline (mean observed yield from development districts) is the
simplest possible predictor, any model that outperforms it demonstrates
predictive skill. Both STRICT and ALLOW_ESTIMATED evaluations were unable to
produce predictions for comparison.

## F. Unit Verification

All yield values are in **t/ha** (metric tons per hectare), verified against
`VALID_YIELD_UNITS` in `field_validation.py`. The CIMMYT GrainYield column
has unit `t/ha` per the dataset variable dictionary, with a conversion
factor of 1.0 to the HYRUE canonical unit. No unit conversion was needed.
