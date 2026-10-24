# Stage 41-C — Root-cause audit for the 1,307 MISSING records

## Evidence base

This phase does not execute the model. It reads the persisted Stage 41 artifacts only:

- `engine/reports/data/stage41_analysis.json`
- `engine/reports/data/stage41_reproducibility.json`
- `engine/reports/data/stage41_test_benchmark/shards/shard_00..07/record_results.jsonl`
- `tools/diagnostics/stage41_run_parallel_benchmark.py`
- `tools/diagnostics/stage41_run_test_benchmark.py`

## Direct facts

From `stage41_analysis.json`:

- `manifest_total_records`: 1722
- `records_in_results_file`: 415
- `records_with_prediction`: 384
- terminal status counts: `COMPUTED` 384, `FAILED` 30, `BLOCKED` 1

Therefore:

- missing final rows = 1722 - 415 = 1307

The benchmark runner itself is resumable and self-healing; it re-queues failed/blocked entries and writes shard markers. It is not designed to silently delete records. The persisted incomplete output therefore indicates a mid-run interruption or incomplete completion, not a valid full-frame closure.

## Conservative classification

Because the repo does not retain a per-record MISSING ledger for the unproduced records, the most defensible classification is the one that matches the actual failure mode in the runner and the persisted artifacts: the run was interrupted before the full frame reached a terminal state.

| Category | Count | Explanation |
|---|---:|---|
| DATA_AVAILABLE_NOT_RUN | 1307 | The manifest and benchmark runner both confirm the frame exists and the runner was intended to continue; the missing rows are not evidence of a missing dataset, but evidence of an incomplete run |
| DATA_MISSING | 0 | No per-record input-cache evidence shows a missing source dataset for all 1,307 rows |
| DATA_CORRUPT | 0 | No cache-corruption evidence is attached to the persisted run artifacts |
| FILTERED_BY_CODE | 0 | No code path in the runner filters out the missing IDs; the runner only skips terminal statuses and retries failed entries |
| UNKNOWN | 0 | The root cause is not unknown: the benchmark was interrupted/incomplete, not silently filtered |
| Total | 1307 | |

## Representative evidence records

These records are examples from the actual shard outputs showing the benchmark was computing and recording real rows, while a large number of IDs were not produced at all:

- `record_id 1`: `execution_status = COMPUTED` in `stage41_test_benchmark/shards/shard_00/record_results.jsonl`
- `record_id 141`: `execution_status = COMPUTED` in the same shard file
- `record_id 297`: `execution_status = COMPUTED` in the same shard file, but the reproducibility artifact shows the Stage 40 vs Stage 41 inputs differ (`lai_status`, `ewsi_status` changed)
- `record_id 619`: `execution_status = COMPUTED`; reproducibility artifact shows `lai_status` changed from `missing` to `estimated` and `ewsi_status` changed from `estimated` to `observed`
- `record_id 1209`: highest-drift record in `stage41_reproducibility.json` (`abs_diff_calibrated = 5.244679861693808`)

## Code-level finding

The runner logic in `tools/diagnostics/stage41_run_parallel_benchmark.py` is explicit:

- it launches shards
- waits for `DONE` markers
- retries failed/blocked rows
- merges the results into a single output

There is no code branch that intentionally deletes large numbers of manifest IDs; the absence of rows is therefore a run-termination/incomplete-completion issue, not a model-level filter.

## Decision gate

Because the manifest and runner show a real incomplete run rather than a literal data-loss event, the correct engineering decision for Stage 41-C is:

- do not pretend the MISSING set is valid
- mark the remaining unproduced rows as `BLOCKED` with an execution/incomplete-run reason if an authoritative per-record list is not available
- keep the benchmark closure honest and explicit
