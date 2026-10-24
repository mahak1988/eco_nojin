# Stage 41-C context recovery

## Source artifacts read

This phase used only the persisted Stage 41 artifacts already in the repo:

- `engine/reports/data/stage41_frozen_model_manifest.json`
- `engine/reports/data/stage41_analysis.json`
- `engine/reports/data/stage41_reproducibility.json`
- `engine/reports/data/stage41_test_benchmark/`
- `engine/reports/STAGE-41-*.md`

## Q1 — test-manifest path and SHA256

The test frame is anchored to the Stage 41 frozen manifest, which names the full benchmark frame as:

- `D:\HyDroMA\engine\reports\data\stage40_test_sample.json`

The same manifest records the frame size as:

- `frame_record_count: 1722`
- `sha256: dfc57da5adfa21b135d49213fa6867e76506857ccf2ecb38746d7ad9b0777320`

This is the authoritative full-frame manifest used for Stage 41.

## Q2 — benchmark executor path and timeout/retry policy

The Stage 41 benchmark driver is:

- `D:\HyDroMA\tools\diagnostics\stage41_run_parallel_benchmark.py`

The sharded worker is:

- `D:\HyDroMA\tools\diagnostics\stage41_run_test_benchmark.py`

The executor is resumable and self-healing. It does the following in code:

- creates 8 sharded workers (`--shards` default 8)
- writes a `DONE` marker under each shard directory when the shard finishes
- re-queues `FAILED` / `BLOCKED` records in the next pass via `_retry_failed()`
- loops for up to `--max-passes` (default 10)
- waits up to 3600 seconds for a shard completion marker before moving on

Relevant facts from the code:

- `PYTHON = Path(r"D:\eco_nojin\.venv\Scripts\python.exe")`
- `_retry_failed()` deletes rows with status `FAILED` or `BLOCKED` from the shard SQLite state so they are retried
- shard execution is guarded by a lock file `driver.lock`
- stage41 worker code writes `DONE` when the shard is done

## Evidence summary

The actual Stage 41 result ledger in `stage41_analysis.json` says:

- `manifest_total_records`: 1722
- `records_in_results_file`: 415
- `records_with_prediction`: 384
- `execution_status_counts`: COMPUTED 384, FAILED 30, BLOCKED 1

That confirms the real run did not produce a full 1,722-record terminal ledger. These gaps are exactly why Stage 41 is still not closed.

## Operational note

This environment blocks direct Python / Git execution for this repo. Therefore Phase 2A rerun and any Git-based diff/commit commands are marked `NOT EXECUTED` with that reason, and the report remains evidence-based on the persisted artifacts rather than a fresh run.
