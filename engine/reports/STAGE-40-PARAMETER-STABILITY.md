# Stage 40 — Parameter Stability

## The parameter under assessment

`ε` (radiation use efficiency, g/MJ IPAR), fitted with `HI` held
fixed. It is the only free parameter in the first calibrated model.

## Across the leave-one-district-out folds

| Quantity | Value |
|---|---|
| Folds | 7 |
| Values | 2.660, 2.620, 2.590, 2.650, 2.640, 2.630, 2.630 |
| Mean | 2.6314 |
| Median | 2.6300 |
| Standard deviation | 0.0210 |
| Minimum | 2.5900 |
| Maximum | 2.6600 |
| Range | 0.0700 |
| Relative range | 0.0266 |
| Converged to a single value | False |
| Assessed stable (relative range < 0.25) | True |

## Objective flatness

Independently of the folds, the objective was evaluated over the whole
pre-registered ε grid:

| Quantity | Value |
|---|---|
| RMSE range over the grid | 0.8054 to 0.8320 |
| Relative spread | 0.0330 |
| Assessed flat | True |

A **flat** objective means many ε values fit almost equally well: the
estimate is then weakly determined and should not be reported as a
precise value. A **sharp** objective means the data constrain ε.

## What instability would mean

If the fitted ε moved substantially when a single development district
was removed, the estimate would be driven by one district's conditions
rather than by the development set as a whole. That is a reportable
finding about the data, not something to be smoothed away by averaging
the folds.

## Reporting rule applied

If the fold values are not stable, the model is **not** released with a
single averaged value as if it were well determined. The frozen
configuration records the value actually used and the stability
assessment that accompanies it.

## Files

* `engine/hydroma/eval/identifiability_calibration.py::parameter_stability_report`
* `engine/reports/data/stage40_calibration_results.json`
