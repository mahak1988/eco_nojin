# Stage 41-D — Six-item evidence audit

This is a read-only evidence audit. The model was not executed and no parameters or scientific code were changed.

## 1. Preserve baseline and inspect the current tree

- Frozen Stage 40 parameters remain ε = 2.630 and HI = 0.45 in the Stage 41 manifest.
- The test-frame manifest file's actual SHA-256 matches the frozen manifest: `dfc57da5adfa21b135d49213fa6867e76506857ccf2ecb38746d7ad9b0777320`.
- The source workbook exists and has 1,722 test-district record IDs.
- Git and the explicit repository venv are usable through VS Code tasks; bare `python`/`python3` and `which jq` probes failed. See `STAGE-41D-ENV-PROBE.md`.

## 2. Audit all current shards and state databases

`tools/diagnostics/stage41d_audit.py` parsed all eight shard JSONL files and SQLite state files:

- 1,082 unique result rows: 1,081 COMPUTED and 1 FAILED.
- Eight additional records are left `RUNNING` in SQLite with no result row.
- 632 source-frame IDs have no shard state.
- 640 total IDs have no result JSONL row; no duplicates were found.
- The merged Stage 41 result file is absent.
- The older `stage41_analysis.json` count of 384 computed / 415 total rows does not describe the current shard contents.

Exact IDs, shard sizes, result paths, per-shard status counts, failure reason, and Stage 40 hash checks are in `engine/reports/data/stage41d_audit.json`.

The existing Stage 41-C blocked ledger has only five entries, and all five IDs overlap current computed shard records. It does not classify any of the 640 no-result IDs.

## 3. Recompute metrics from current shard output

Fresh metrics for 1,081 COMPUTED records are in `STAGE-41D-METRICS.md` and `engine/reports/data/stage41d_metrics.json`. Calibrated RMSE is `3.91084807138`, baseline RMSE `4.01298347921`, and mean RMSE `1.10999870908`.

On 294 Stage 40/Stage 41 shared IDs with equal observed yields, Stage 40 calibrated RMSE is `1.30019939268`; Stage 41 calibrated RMSE is `3.95748338903`. Stage 41 does not preserve Stage 40 performance on this common subset.

## 4. Compare model source hashes

There is no `stage40-frozen` tag. No available Git-history revision for either changed model file matches the Stage 40 SHA-256 recorded in the Stage 41 manifest. `scientific_change` remains `UNPROVEN`; the manifest's metadata-only assertion cannot substitute for a diff against the frozen revision. Details are in `STAGE-41D-MODEL-DIFF.md`.

## 5. Audit reproducibility and actual failure evidence

- 33 of 106 reproduction records have nonzero prediction differences.
- All 33 show LAI and EWSI status differences; the saved artifacts do not include paired daily input arrays or external response hashes to assign a definitive source-data/code/bug cause.
- Current failed record 1533 identifies a runner defect: `baseline_predicted_yield` is read before assignment when the earlier prediction path throws.
- The Stage 38 scientific cache exists but has zero entries; current shard rows show zero cache hits.

Details and all 33 record IDs are in `STAGE-41D-REPRO-ROOT-CAUSE.md`. No causal classification is invented.

## 6. Decide on rerun, verdict, and readiness

No rerun was performed. With no captured input cache, rerunning the missing IDs would reacquire live external inputs and not reproduce the prior basis; it would require a separately authorized, input-capturing benchmark run. The runner error has since been corrected and regression-tested; see the
post-audit correction in `STAGE-41-FINAL-STATUS.md`. A rerun still requires
captured inputs and a verifiable frozen model revision.

The final status is `INCOMPLETE`; Stage 42 is `NOT READY`. Evidence: 640 records lack a result row, the full BLOCKED ledger is invalid, the Stage 40 model revision cannot be proven, and the 33-record root cause remains unproven.

## Validation

- Read-only audit script completed using `D:\eco_nojin\.venv\Scripts\python.exe`.
- The focused frozen-equivalence test controller reported 5 passed.
- Full pytest was not run in this audit pass.

## Post-audit code correction

`baseline_predicted_yield` is initialized before the prediction branch to
prevent a failed HYRUE call from masking the original failure with an
`UnboundLocalError`. The focused Stage 40/41 regression suite subsequently
passed: **25 passed**. No benchmark/model execution was performed.
