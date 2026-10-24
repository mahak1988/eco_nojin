# Stage 40 — Final Status

## Status: `PARTIAL`

| Field | Value |
|---|---|
| Model | HYRUE 2.0.1 |
| External validation status | **PARTIAL** |
| Scientific support status | **PARTIAL** |
| Calibrated | yes, on development districts only |
| Frozen | yes, before external evaluation |
| Test districts | Buxar, Muzaffarpur, Rohtas (held out from calibration) |
| Records evaluated | 450 of 450 sampled (of 1,722 test records) |

`VALIDATED_EXTERNAL` is **not** claimed. The reasons are specific, not
rhetorical:

| Requirement for `VALIDATED_EXTERNAL` | Met? | Evidence |
|---|---|---|
| Calibrated on data disjoint from the evaluation set | Yes | 7 dev districts; leakage guard asserted |
| Parameters frozen before evaluation | Yes | frozen config written before the run |
| Evaluation on genuinely external districts | Yes | Buxar, Muzaffarpur, Rohtas |
| Evaluation covers the full external set | No | 450 of 1,722, stratified sample |
| Spatial replication | No | three districts; the bootstrap has three clusters |
| Performance is strong enough to claim validity | No | test R² = -0.4115 |
| Uncertainty covers the total error budget | No | calibration and input components excluded |
| Model identified from the data | No | `epsilon`/`HI` collinear; objective nearly flat |

## What Stage 40 established

* The uncalibrated model was **substantially biased** on these data
  (baseline R² = -1.0733 on the same records). A single
  calibrated parameter, fitted on development districts only, moved the
  test R² to -0.4115 — an improvement of
  0.662 in R².
* **The calibrated model still does not beat the mean predictor on the
  test districts.** A negative R² means the sum of squared prediction
  errors exceeds the sum of squared deviations of the observations from
  their own mean: predicting the district's average observed yield for
  every field would score a better R² than this model does. The
  calibration moved the model in the right direction and cut RMSE from
  1.5547 to 1.2828 t/ha
  on the same records, but it has not made the model a good predictor of
  district-level yields.
* The improvement is **not** an artefact of tuning on the evaluation
  set: the leave-one-district-out validation on the development
  districts shows the same direction
  (1.0312 -> 0.7743 t/ha
  mean validation RMSE), and the fitted `epsilon` is stable across all
  7 folds (relative range
  0.0266).
* The model is **not** fit for operational use. A test R² of
  -0.4115 on three districts is a research result, not a
  production claim.

## What Stage 40 did not establish

* That the model generalises beyond these three districts.
* That `epsilon` = 2.630 is the
  true radiation use efficiency of wheat in Bihar. It is the scale the
  development set implies, given the other parameters.
* That the remaining error is random. The error sources that remain
  open (LAI, EWSI, thermal width, soil moisture) are **systematic**, and
  systematic error does not average out.
* That the model is ready for decision-making. It is not.

## The two defects found

Recorded in full in `STAGE-40-QUALITY-GATES.md`, and repeated here
because they change how the numbers should be read:

1. The first benchmark run would have evaluated the **uncalibrated**
   model, because the crop preset silently overrode the explicit
   parameters. It was aborted.
2. The first calibration was fitted against a **different input basis**
   from the one used at evaluation time. Correcting it moved the fitted
   `epsilon` from 2.570 to 2.630.

The numbers in this report are the ones produced **after** both fixes.

## Recommended next step

Stage 41 should target the **identifiability** problem rather than more
benchmarking: obtain observed LAI (or a published EWSI weighting) so
that `epsilon` and `HI` can be separated, then re-run this stage
end-to-end. More benchmark records on the current model would not change
the status.
