# Stage 41 — Final Status after Stage 41-E live-input rerun

## Verdict

`INCOMPLETE`

Stage 41-E completed a fresh live-input pass across all 1,722 source records.
This closes the missing-row accounting gap for the new run, but it does not
establish scientific comparability with Stage 40: the Stage 40 code revision
is still unverified, the run used live external data, and the earlier 33/106
reproducibility discrepancies remain unresolved. Stage 41-D evidence below
describes the legacy Stage 41 shard set and is retained as historical audit
context, not as the current run's status.

## Stage 41-E live-run accounting

Run directory: `engine/reports/data/stage41e_live_rerun/`.
Machine-readable audit: `engine/reports/data/stage41e_live_rerun/stage41e_audit.json`.
Full report: `engine/reports/STAGE-41E-LIVE-RERUN.md`.

| Status | Count |
|---|---:|
| COMPUTED | 1700 |
| FAILED | 1 |
| BLOCKED | 21 |
| PARTIAL_INPUTS | 0 |
| MISSING | 0 |
| **Total** | **1722** |

The finalizer verified 1,722 result rows, 1,722 unique source IDs, no duplicate
IDs, no missing or unexpected IDs, and captured resolved inputs for all 1,700
computed records. The run used ε=2.63 and HI=0.45. It also recorded the current
pipeline code hash; `stage40_code_freeze_proven` is false. The workbook SHA-256
is `919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde`; the
sorted source-ID hash is
`c90dee1be1342cd200e8dfc902ccf64c78f684fb733aa9adc92366eab82189c0`.
The run identity hash `dd3527db92c073a03ceb6d73fee375990f655f982cdab3321e252cb34401f3c9`
differs from the Stage 40 frozen aggregate hash
`1ae6ddbd5a8c17ca2eafcf6909956dda7e0744633f70744e19a65069c2c1e3f6`.
File-level comparison also shows both `seasonal_predictor.py` and
`identifiability_calibration.py` differ from their frozen SHA-256 values;
`weather_source.py`, `par_pipeline.py`, and `hyrue.py` match. This does not
prove whether the changed files alter scientific calculations, so
`scientific_change` remains **UNPROVEN**, not false. Exact hashes are in the
Stage 41-E audit/report.

### Stage 41-E metrics (computed rows only)

| Metric | Baseline ε=2.2 | Calibrated ε=2.63 | Mean predictor |
|---|---:|---:|---:|
| n | 1700 | 1700 | 1700 |
| RMSE (t/ha) | 2.88617818088 | 2.83768875273 | 1.09667103450 |
| MAE (t/ha) | 2.39244059001 | 2.30859337006 | 0.898455671993 |
| Bias (t/ha) | -2.20341624843 | -1.83826852975 | approximately 0 |
| R² | -5.92617614792 | -5.69540375927 | 0 |
| MAPE (%) | 53.6571437525 | 52.7911869019 | 23.6654480417 |

Calibrated RMSE improves on the baseline by 0.04848942814 t/ha, but is
1.74101771823 t/ha worse than the within-frame mean predictor. This is a
descriptive evaluation only; no parameter selection or calibration was done.
The result is not directly comparable to the Stage 40 RMSE because Stage 41-E
used current code and live inputs, and the historical Stage 40 code freeze is
not proven.

The driver logs contain Open-Meteo HTTP 429 messages followed by messages saying
NASA POWER fallback was attempted. The finalized result rows identify 1,701
weather-source entries as `open_meteo_era5` and 21 as unknown. Inspection
confirmed the source-labeling defect: `resumable_benchmark_runner.py` reads
`weather_df.attrs["source"]`, but the Open-Meteo and NASA POWER fetch paths do
not set that attribute. The runner therefore defaults successful rows to
`open_meteo_era5`, even where a fallback may have supplied the data. The exact
per-record source split is not proven by the result rows.

The 21 `BLOCKED` rows all failed while fetching weather with
`float() argument must be a string or a real number, not 'NoneType'`. The one
`FAILED` row is record `4238`, which raised the same TypeError during HYRUE
computation. These statuses are accounted, but they are not resolved; the
weather-source/null handling path requires a focused root-cause investigation.
The exact record IDs are in
`engine/reports/data/stage41e_live_rerun/stage41e_audit.json`. The historical
Stage 41-D sections below refer to the older shard set and must not be
conflated with this live run.

The prior `COMPLETE_WITH_DOCUMENTED_BLOCKERS` claim is not supported. The Stage 41-C blocked ledger has only five rows, all overlap records computed in shards, and it does not account for the unprocessed part of the frame. Stage 41-D audited the current raw shards and refreshed metrics without running the scientific model.

## Historical Stage 41-D record accounting (legacy shards)

The source frame contains 1,722 unique test-district records. Current shard state:

| Status | Count |
|---|---:|
| COMPUTED | 1081 |
| FAILED | 1 |
| BLOCKED | 0 |
| PARTIAL_INPUTS | 0 |
| RUNNING (stale SQLite state; no active benchmark worker) | 8 |
| UNSTARTED (no shard state/result) | 632 |
| **Total** | **1722** |

There are 640 records without a result JSONL row: 8 stale `RUNNING` states and 632 not started. The merged Stage 41 result file is absent. The prior `stage41_analysis.json` summary (384 computed, 415 rows) is stale relative to the current shard files (1,081 computed, 1,082 rows).

The actual source manifest path recorded in the frozen manifest is `engine/reports/data/stage40_test_sample.json`; its SHA-256 was independently recomputed and matches `dfc57da5adfa21b135d49213fa6867e76506857ccf2ecb38746d7ad9b0777320`. This sample manifest selects 450 rows from a 1,722-record frame. The source Excel file exists and its 1,722 test-district record IDs were read during the audit.

## Historical Stage 41-D metrics (legacy shard set)

These values were calculated from the 1,081 `COMPUTED` shard rows by `tools/diagnostics/stage41d_audit.py`; no model was run.

| Metric | Baseline (ε=2.2) | Calibrated (ε=2.63) | Mean predictor |
|---|---:|---:|---:|
| n | 1081 | 1081 | 1081 |
| R² | -12.0704276131 | -11.4135769927 | 0 |
| RMSE (t/ha) | 4.01298347921 | 3.91084807138 | 1.10999870908 |
| MAE (t/ha) | 3.8635098252 | 3.75636495599 | 0.927716139765 |
| Bias (t/ha) | -3.8635098252 | -3.75636495599 | approximately 0 |
| MAPE (%) | 86.9736088611 | 84.4275415022 | 24.9463820607 |

Calibrated RMSE is lower than baseline by `0.102135407824 t/ha`, but remains `2.80084936230 t/ha` worse than the mean predictor.

## Historical Stage 40 shared-record comparison

On the 294 IDs whose Stage 40 and current Stage 41 computed rows share the same observed yield:

| Metric | Stage 40 calibrated | Stage 41 baseline | Stage 41 calibrated | Mean predictor |
|---|---:|---:|---:|---:|
| n | 294 | 294 | 294 | 294 |
| R² | -0.321015343418 | -11.9019686417 | -11.2384423249 | 0 |
| RMSE (t/ha) | 1.30019939268 | 4.06334800374 | 3.95748338903 | 1.13124332046 |
| MAE (t/ha) | 1.02415258779 | 3.9212530989 | 3.81270164059 | 0.933374288491 |
| Bias (t/ha) | -0.496547400169 | -3.9212530989 | -3.81270164059 | approximately 0 |
| MAPE (%) | 23.3853606209 | 87.2710274192 | 84.7830918693 | 25.2394207735 |

On this shared subset the Stage 41 calibrated result does **not** preserve Stage 40 performance: RMSE is `3.9575` vs Stage 40 `1.3002`. This is a severe input/run comparability warning, not evidence for recalibration.

## Historical Stage 41-D model and input lock

- Frozen parameters in the Stage 41 manifest remain ε = 2.630 and HI = 0.45.
- `scientific_change = UNPROVEN`. The two Stage 40 file hashes in the frozen manifest do not match the current file hashes or any candidate Git-history revision found for those paths. There is no verified `stage40-frozen` tag or Git revision for a line-by-line comparison. See `STAGE-41D-MODEL-DIFF.md`.
- The tracked LAI/EWSI/PAR/weather module hashes match the manifest values, but external input/cache identity is not proved. The 33 non-reproducing records have changed LAI/EWSI status fields, but paired numeric inputs and data-source hashes are absent.

## Historical Stage 41-D reproducibility and failure

- Reproduced within 1e-12: 73 / 106.
- Did not reproduce within 1e-12: 33 / 106.
- All 33 have recorded differences in `lai_status` and `ewsi_status`; the specific source-data versus code-path cause remains unproven.
- The single failed record in the legacy Stage 41 shard set was ID `1533`:
  `cannot access local variable 'baseline_predicted_yield' where it is not
  associated with a value`. This identified the runner bug corrected below;
  it is distinct from Stage 41-E's current failed record `4238`.

## Historical Stage 41-D missing-input cache and rerun decision

`engine/reports/data/stage38_cache.sqlite` exists but has **zero cache entries**, and all legacy shard records report zero cache hits. The source workbook exists, but a deterministic rerun cannot recover the original weather/satellite inputs from cache.

**No rerun was executed during Stage 41-D.** Its audit was intended to inspect
the legacy evidence, not to run the model. The later Stage 41-E full-frame run
used live external data and is reported separately above. Stage 41-D audit
outputs are persisted in `engine/reports/data/stage41d_audit.json` and
`engine/reports/data/stage41d_metrics.json`.

## Validation and Stage 42 readiness

- The focused Stage 40/41 regression set passed: **25 passed** across
  `test_stage41_runner_failure_path.py`,
  `test_stage41_provenance_contract.py`,
  `test_stage41b_frozen_equivalence.py`, and
  `test_stage40_parameter_plumbing.py`.
- The full repository pytest audit remains incomplete: the `--timeout=300`
  attempt could not start because `pytest-timeout` was unavailable and package
  installation failed due DNS/network access. A later unconfigured run stopped
  before producing a complete failure summary, so its observed failures cannot
  be classified reliably.
- Stage 42: **NOT READY**.

Remaining blockers:

1. Root-cause the `NoneType` conversion failures for 21 `BLOCKED` records and
   record `4238` (`FAILED`); decide whether a narrowly scoped input-handling fix
   is justified, then rerun only if that fix preserves the frozen model.
2. Resolve the conflict between HTTP 429/fallback log messages and the
   `open_meteo_era5` provenance labels before claiming source equivalence.
3. Restore a verifiable Stage 40 source revision and complete the line-level
   model diff; the live run's model code hash does not prove Stage 40 identity.
4. Root-cause the historical 33/106 reproducibility discrepancies. The new run
   captures inputs for computed records, but does not reconstruct the old
   Stage 40/41 input pairs.
5. Complete the full-suite test audit and classify every failure; the available
   attempts did not produce a complete, reliable failure inventory.
6. Treat the poor metrics as an evaluation finding, not a tuning target:
   calibrated R² is -5.6954 and RMSE 2.8377 t/ha versus the frame mean's
   R² 0 and RMSE 1.0967 t/ha. No calibration is authorized in this phase.

## Post-audit runner correction

The uninitialized `baseline_predicted_yield` variable was initialized to `None`
before the prediction branch in `engine/hydroma/eval/resumable_benchmark_runner.py`.
This preserves the existing failure status and reason while allowing the failed
record to be serialized instead of raising a second `UnboundLocalError`.

This code fix does not recover any missing records, captured inputs, or a
verifiable Stage 40 source revision. It does not change ε/HI or any scientific
calculation, and it does not change the `INCOMPLETE` verdict or Stage 42
readiness.

The Stage 41-E audit also confirms complete record accounting and input
capture for all computed rows. It does not remove the outstanding data,
provenance, model-freeze, reproducibility, and full-test blockers above.
