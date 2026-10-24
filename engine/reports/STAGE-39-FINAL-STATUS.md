# Stage 39 — Final Status

## Overall Status: PARTIALLY_EVALUATED

The status is unchanged from Stage 37. It must not be raised to
`COMPLETED` or `VALIDATED_EXTERNAL`.

## What Was Actually Done

| Item | Done? | Evidence |
|---|---|---|
| Diagnosed the "filesystem" problem | **Yes** | It was never a filesystem-visibility problem: it was (a) OS path-cache poisoning, (b) a duplicated editable-install `.pth`, (c) a genuine import cycle. All three fixed. |
| Repaired the runtime so the engine imports deterministically | **Yes** | `engine/hydroma/eval/runtime_bootstrap.py`; 12 critical modules load; 176 tests pass |
| Audited the PAR unit chain | **Yes** | `STAGE-39-PAR-UNIT-AUDIT.md`; new `radiation_units.py` contract; double-conversion prevented; double-conversion test passes |
| Audited the LAI input path | **Yes** | `STAGE-39-LAI-INPUT-AUDIT.md`; no constant fallback in the benchmark main path |
| Implemented the development-only calibration with a leakage guard | **Yes** | `stage39_benchmark.py::run_development_calibration()`; guard tested |
| **Executed** the development calibration | **No** | Time: ~33 h for the development set. Parameters remain at defaults. |
| Froze the model | **Yes** | `stage37_frozen_model_config.json` — 17 parameters, baseline, `calibration_status: baseline_only` |
| Started the full test benchmark | **Yes** | Running against the frozen model; resumable; incremental output; 26 records computed, 0 blocked, 0 failed |
| **Completed** the full test benchmark (1,722 records) | **No** | ~14 h remaining; the run continues in the background |
| Computed validation metrics | **Yes (partial)** | On the 26 records completed so far: RMSE 1.132, MAE 0.959, Bias −0.686, **R² −1.099**, MAPE 18.12 % |
| Documented uncertainty | **Yes** | `STAGE-39-UNCERTAINTY-ANALYSIS.md` — district-level cluster bootstrap, 3-cluster limitation stated |
| Fixed the satellite-sampling performance defect | **Yes** | Windowed read: a full season went from >10 min to 52.3 s |

## Real Numbers

### Benchmark snapshot (26 of 1,722 test records, 2016-17 season)

| Metric | Value |
|---|---|
| CIMMYT records | 5,689 |
| Development records | 3,967 (7 districts) |
| Test records | 1,722 (3 districts) |
| Test records computed so far | 26 (run in progress) |
| Execution status | 26 × `COMPUTED`, 0 blocked, 0 failed |
| RMSE | 1.132 t/ha |
| MAE | 0.959 t/ha |
| Bias | −0.686 t/ha (systematic under-prediction) |
| **R²** | **−1.099** (worse than a mean-predictor) |
| MAPE | 18.12 % |
| Bootstrap RMSE mean | 1.158 t/ha, 95 % CI [0.924, 1.712] |

### The headline result is negative

**R² = −1.10.** With the uncalibrated default parameters, the model is
currently *worse* than predicting the mean observed yield of the
evaluation set. The mechanism is the identifiability problem: the scale of
the prediction is set by the product ε·HI, both uncalibrated defaults,
and a uniform scale error shifts every prediction in the same direction
without improving the fit.

This is a genuine, reportable result — not a failure to produce a number.
It is also the strongest argument yet for executing the development
calibration before any validation claim is made.

### Pipeline

| Quantity | Value |
|---|---|
| Pilot predicted yield | 4.807 t/ha (reproduced exactly in Stage 39) |
| Pilot observed yield | 6.680 t/ha |
| Pilot absolute error | −1.873 t/ha |
| Pilot relative error | −28.0% |
| Stage 35 error before the PAR fix | +63.2% |
| Weather API calls | 1 per record (~4 s) |
| Satellite COG reads | 3 per acquisition (B8A, B11, SCL) — windowed, ~2.5 s each |
| Season fetch (cold) | ~52.3 s |
| Season fetch (cached) | ~2 s |
| Projected full test runtime | ~14 h (run in progress) |


## Explicitly Not Claimed

* That HYRUE is a validated model.
* That the residual error is understood or attributable to a single cause.
* That any parameter was empirically identified.
* That the results generalise beyond wheat in Bihar/eastern Uttar Pradesh
  in 2016-2022.
* That a green test suite demonstrates scientific correctness. It
  demonstrates that the code runs as specified — nothing more.

**In particular, the measured R² of −1.10 means the uncalibrated model
is currently worse than a mean-predictor on the records evaluated so
far.** That is a negative result, and it is reported as one.

## Remaining Blockers

| Blocker | Severity | Blocks |
|---|---|---|
| Development calibration not executed | High | Any claim that the parameters are fitted rather than assumed; the error decomposition (ε vs HI vs EWSI) |
| Full test benchmark not complete | High | Validation-grade metrics over the whole test set |
| Test set has only 3 districts | Medium | Any spatial-generalisation claim; stable uncertainty intervals |
| EWSI weights/anchors unsourced | Medium | Physiological interpretation of the EWSI index |
| LAI is model-generated | Medium | A large share of the residual error is attributable to it and it is not independently constrained |
| Coordinate-cell overlap dev/test | Low | Weakens test independence; does not invalidate the split |
| API rate limit not measured | Low | Parallel execution remains disabled |

## Recommended Next Actions (Stage 40)

1. **Execute the development calibration** on a representative
   development sample (20-50 records across all 7 districts) using the
   identifiability-constrained design: fit `epsilon` with `HI` fixed,
   then `k`, then optionally `t_opt` — never more than three free
   parameters at once, validated leave-one-district-out.
2. **Freeze a calibrated model version** with the calibration method,
   dataset, record IDs, seed and fold results recorded.
3. **Complete the test benchmark** with the calibrated model and compare
   against the Stage 39 baseline run.
4. **Report the error decomposition** (district, season, input quality,
   satellite coverage, yield band) as a diagnostic — not as licence to
   tune on test data.
5. **Measure the API rate limits** and only then consider bounded
   parallel execution for the remaining records.

## Files

| Path | Content |
|---|---|
| `engine/hydroma/eval/runtime_bootstrap.py` | deterministic engine import (new) |
| `engine/hydroma/eval/stage39_benchmark.py` | metrics, bootstrap, calibration entry point (new) |
| `engine/hydroma/simulation/radiation_units.py` | radiation unit contract (Stage 37) |
| `engine/hydroma/simulation/data_cache.py` | persistent cache (Stage 38) |
| `engine/hydroma/eval/resumable_benchmark_runner.py` | resumable runner (fixed) |
| `engine/hydroma/simulation/remote_sensing/satellite_source.py` | windowed read + cache (fixed) |
| `engine/hydroma/simulation/par_pipeline.py` | import cycle broken (fixed) |
| `engine/hydroma/simulation/weather_source.py` | constants from unit contract (fixed) |
| `engine/reports/data/stage37_frozen_model_config.json` | frozen model |
| `engine/reports/data/stage39_benchmark/` | benchmark run outputs |
| `engine/tests/test_stage39_science.py` | 41 Stage 39 tests (new) |
| `tools/stage39_run_benchmark.py` | benchmark runner script (new) |
