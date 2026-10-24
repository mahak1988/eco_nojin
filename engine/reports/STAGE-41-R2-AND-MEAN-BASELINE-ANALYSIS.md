# Stage 41 — R² and Mean-Baseline Analysis

## The question

The calibrated model's R² on the held-out districts is
-1.7205. A negative R² means the sum of squared prediction
errors exceeds the sum of squared deviations of the observations from
their own mean - in plain terms, **predicting every field's yield as
the mean observed yield of the evaluation set would score a better R²
than HYRUE does**.

## Two distinct reference points

They answer different questions and are kept separate.

| Reference | RMSE (t/ha) | R² | What it answers |
|---|---:|---:|---|
| HYRUE calibrated | 1.6653 | -1.7205 | How does the model do? |
| HYRUE baseline (ε=2.2) | 1.8947 | -2.5216 | Did calibration help? |
| **Mean predictor** (ŷ = ȳ of the evaluation set) | **1.0096** | **0.0 by construction** | Does the model beat a trivial predictor? |
| HYRUE calibrated ÷ mean predictor | 1.649× | — | Skill relative to the trivial predictor |

The mean predictor is a **diagnostic reference only**. The evaluation
mean was not used to fit, tune, select or adjust anything in HYRUE; it
is used here solely to compute the reference row above. A *practical*
baseline would have to be an operational forecast, which this repository
does not contain - that is a separate gap, not something Stage 41
invents.

## Observed-yield distribution

| Statistic | Value |
|---|---|
| n | 366 |
| Mean | 4.5673 t/ha |
| Median | 4.7200 t/ha |
| Standard deviation | 1.0110 t/ha |
| Minimum | 2.0300 t/ha |
| Maximum | 6.6800 t/ha |
| Q1 | 3.7300 t/ha |
| Q3 | 5.4225 t/ha |
| IQR | 1.6925 t/ha |
| Exact zeros | 0 |
| Below 0.5 t/ha | 0 |
| Beyond 3σ | 0 |

The observed yields are **not** pathologically narrow or wide: the IQR
is 1.6925 t/ha on a mean of 4.5673 t/ha,
and only 0 observations are exactly zero. So
the negative R² is not an artefact of a degenerate response variable -
the evaluation set contains real yield variation, and the model is
simply not tracking it.

## Structural error checks

| Check | Value | Reading |
|---|---|---|
| Predicted mean | 3.7803 t/ha | vs observed mean 4.5673 |
| Predicted SD | 1.6084 | vs observed SD 1.0110 |
| Predicted range | 0.1563 – 7.4197 | vs observed 2.0300 – 6.6800 |
| Pearson r (predicted, observed) | 0.4457 | Weak correspondence |
| Over-predicted records | 104 | |
| Under-predicted records | 262 | |

The model's predictions span a **narrower range** than the observations
and correlate only weakly with them. That is the signature of a model
whose output is dominated by a season-level scale factor rather than by
the field-level variation that actually differentiates the yields.

## Bias by observed-yield band

| Observed band | n | Bias | RMSE | R² | Mean observed | Mean predicted |
|---|---:|---:|---:|---:|---:|---:|
| <= 3.5 | 68 | -0.2550 |
| <= 5.0 | 150 | -0.7623 |
| <= 7.0 | 148 | -1.0566 |

Full detail (RMSE, R², means) is in `stage41_analysis.json` under
`structural_error.bias_by_observed_band`.

## What this establishes

* The negative R² is **real** and is not an artefact of a degenerate
  response, a broken pipeline, or a metric bug. The mean predictor
  beats HYRUE by a factor of 1.65 in RMSE.
* The **calibration did help**: it moved the model from
  R² = -2.5216 to R² = -1.7205 on the same records
  with the same inputs. The problem is the starting point, not the
  calibration.
* The model is **not yet fit for operational use**, and no amount of
  additional benchmarking of the current model will change that.
