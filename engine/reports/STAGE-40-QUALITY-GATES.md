# Stage 40 — Quality Gates

Every gate below is checked against an executed artifact, not asserted.

| Gate | Status | Evidence |
|---|---|---|
| No test-district record used in the calibration | PASS | leakage guard asserted before the fit; 7 LODO folds, all development-only |
| Calibration parameters frozen before external evaluation | PASS | frozen config written before the test run; the run manifest records the parameter set used |
| Explicit parameters reach the model (not the crop preset) | PASS | regression test: a supplied parameter set changes the prediction by exactly the epsilon ratio |
| Calibration formula identical to the evaluated model | PASS | regression test: analytical yield == HYRUE.compute to rel 1e-12 |
| Calibration and evaluation share one input basis | PASS | profiles built by the benchmark runner itself; daily arrays captured from the live pipeline |
| Stage 39 baseline unchanged by the Stage 40 code changes | PASS | 26/26 predictions identical, max diff 0.0 t/ha |
| Baseline compared on the same records as the calibrated model | PASS | linearity identity validated against the real Stage 39 predictions; see the validation-metrics report |
| Every record accounted for (no silent drops) | PASS | 450 records processed, each with an execution status; blocked and failed records are written to failed_records.jsonl |
| Uncertainty reported with its coverage stated | PASS | district-level cluster bootstrap; the components it does not cover are listed explicitly |
| No VALIDATED_EXTERNAL claim without the supporting evidence | PASS | status is PARTIAL; the conditions for VALIDATED_EXTERNAL are listed in the final-status report |

## The two defects this stage caught

Stage 40 did not begin clean. Two defects were found by review, both of
which would have produced a **misleading** Stage 40 result rather than
a failing one:

1. **The frozen parameters never reached the model.** `HYRUE.__init__`
   applied the crop preset whenever a crop name was given, overwriting
   any explicit `HYRUEParams`. The calibrated benchmark would have been
   numerically identical to the baseline. The first run was aborted on
   finding this; the run was restarted only after the plumbing was
   fixed and covered by regression tests.

2. **The calibration was fitted against a different input basis from the
   one it was evaluated on.** The first profile builder used a synthetic
   sigmoid LAI and a hard-coded PAR factor, while the benchmark resolves
   LAI with the GDD model and PAR with the weather source's own factor.
   Correcting this changed the fitted ε from 2.570 to
   2.630 and changed the
   development R² accordingly.

Neither defect would have shown up as a test failure. Both were found by
reading the code path rather than by running it. The gate table above
exists so that the next stage does not have to rediscover them.

## What these gates do *not* cover

* They do not verify the scientific correctness of the uncalibrated
  parameters (LAI model, EWSI weights, thermal width, soil moisture
  field capacity). Those remain unsourced or default-valued.
* They do not verify the external *coverage* of the test set. The
  evaluation is on a documented stratified sample of the test districts,
  not the full set.
* They do not bound the calibration uncertainty inside the reported
  intervals.
