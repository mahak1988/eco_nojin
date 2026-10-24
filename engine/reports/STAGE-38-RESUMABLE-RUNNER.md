# Stage 38 — Resumable Benchmark Runner

## Runner Architecture

`ResumableBenchmarkRunner` (`engine/hydroma/eval/resumable_benchmark_runner.py`) processes test-district records one at a time with persistent state tracking.

## State Persistence

Two-layer persistence:

1. **SQLite database** (`engine/reports/data/stage38_runner.sqlite`) — Tracks record-level execution state:
   - record_id, district_id, season, status, processed_at, failure_reason, processing_seconds, cache_hits, api_calls

2. **JSONL results file** (`engine/reports/data/stage38_benchmark_results.jsonl`) — Appends one JSON object per record with full result details.

3. **Manifest file** (`engine/reports/data/stage38_run_manifest.json`) — Run-level summary with run_id, timestamps, and aggregate statistics.

## Execution Statuses

| Status | Meaning |
|---|---|
| COMPUTED | Record successfully processed with all inputs |
| PARTIAL_INPUTS | Record processed with missing/incomplete inputs |
| BLOCKED | Record cannot be processed (missing critical inputs) |
| FAILED | Record processing encountered an error |

## Resumability

- Completed records (terminal status) are skipped on re-run
- Failed records are tracked with their error reason
- Execution can be paused and resumed without losing progress
- JSONL file is append-only, never overwritten

## Runner Test

Tested with 1 record (Buxar, 2016-17). Runner correctly:
1. Called `compute_seasonal_prediction`
2. Captured the result (FAILED due to satellite SSL issues)
3. Persisted state to SQLite
4. Appended result to JSONL

## Files

- `engine/hydroma/eval/resumable_benchmark_runner.py` — runner module
- `engine/reports/data/stage38_runner.sqlite` — state database
- `engine/reports/data/stage38_benchmark_results.jsonl` — results log
- `engine/reports/data/stage38_run_manifest.json` — run manifest
