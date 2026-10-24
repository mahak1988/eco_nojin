# Stage 40 — Leave-One-District-Out Cross-Validation

## What this is, and what it is not

This is **internal grouped cross-validation on the development set**. It
estimates how well the calibration transfers to a district the fit never
saw. It is **not** external validation: the held-out districts are
development districts, and the test districts are untouched.

## Protocol

For each of the 7 development districts:

1. The district is held out.
2. `ε` is fitted on the remaining development districts only
   (objective: RMSE on development-district records (t/ha)).
3. The fitted model is evaluated on the held-out district.
4. The baseline (`ε` = 2.2) is evaluated on the same held-out records
   for a like-for-like comparison.

The held-out district contributes to **neither** the fit nor any
data-dependent transformation. No data-dependent normalisation is applied
anywhere in the pipeline, so there is no statistic to leak.

## Folds

| Held-out district | n train | n val | fitted ε | base RMSE | cal. RMSE | better? |
|---|---:|---:|---:|---:|---:|---|
| Begusarai | 35 | 6 | 2.660 | 0.8310 | 0.7987 | yes |
| Bhojpur | 35 | 6 | 2.620 | 1.2789 | 0.9861 | yes |
| Deoria | 35 | 6 | 2.590 | 1.1558 | 0.6304 | yes |
| EastChamparan | 35 | 6 | 2.650 | 1.2985 | 1.1367 | yes |
| Kushinagar | 35 | 6 | 2.640 | 1.0886 | 0.8955 | yes |
| Lakhisarai | 35 | 6 | 2.630 | 0.7305 | 0.3836 | yes |
| Madhepura | 36 | 5 | 2.630 | 0.8350 | 0.5890 | yes |

## Skipped folds

* (none)

## Aggregate

| Quantity | Value |
|---|---|
| Folds run | 7 |
| Mean validation RMSE, calibrated | 0.7743 |
| Mean validation RMSE, baseline | 1.0312 |
| Calibration improves validation | **True** |

## Reading of the result

The decision criterion is the **held-out** comparison, not the
in-sample fit. A calibrated model that is better on the training
districts but worse on the held-out ones is a sign of overfitting, and
is reported as such.

## Why three (or few) districts is a weak basis

The development set has 7 districts, so each
fold's training set excludes one of them. The fold-to-fold spread of the
fitted ε (see `STAGE-40-PARAMETER-STABILITY.md`) is the diagnostic for
whether the estimate is stable enough to be trusted.

This is **internal** validation. It cannot support a claim about
generalisation to regions outside the development districts, and it does
not replace the test-set evaluation.

## Files

* `engine/hydrama/eval/identifiability_calibration.py::leave_one_district_out`
* `engine/reports/data/stage40_calibration_results.json`
