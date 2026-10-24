# Stage 40 — Test Benchmark

## Execution Status

| Item | Value |
|---|---|
| Model version | 2.0.1 |
| Calibration status | calibrated |
| Free parameter | `epsilon` = 2.6300 g/MJ IPAR |
| Test districts | Buxar, Muzaffarpur, Rohtas |
| Test records in manifest | 1,722 |
| Records evaluated | 450 |
| Results file | `engine/reports/data/stage40_test_benchmark/record_results.jsonl` |
| State file | `engine/reports/data/stage40_test_benchmark/execution_state.sqlite` |

## Sampling design

The upstream Sentinel-2 COG reads dominate the benchmark cost and the
APIs throttle beyond roughly eight concurrent readers, so the
evaluation was run on a **documented stratified sample** of the test
set rather than all 1,722 records.

| Item | Value |
|---|---|
| Design | stratified simple random sample without replacement |
| Frame | all 1722 test-district records |
| Strata | district x season (18 strata) |
| Allocation | proportional to stratum size, floor of min_per_stratum, capped at the stratum size |
| Sample size | 450 |
| Seed | 20240115 |
| Sample ids hash | `7115553b4ca97849a8c18f76…` |
| Frame ids hash | `5136319fcba6ef6b32469e2f…` |

The sample manifest, including the per-stratum allocation and the
selected record ids, is `engine/reports/data/stage40_test_sample.json`.
The sample is reproducible from the seed and the frame.

**This is a sample, and the reported metrics describe the sample.**
The sampling design is stated so that the reader can judge it; the
full 1,722-record run was not performed.

### Realised coverage

_No coverage data._

## Separation from the baseline

The Stage 40 run writes to `stage40_test_benchmark/`. The Stage 39
baseline results in `stage39_benchmark/` are **not** modified and **not**
concatenated. The baseline state is preserved in
`stage40_baseline_manifest.json`
(40 records,
model code hash `75fde7d2ce0fa0ba…`).

## Execution statuses

| Status | Count |
|---|---:|
| COMPUTED | 450 |
| PARTIAL_INPUTS | 0 |
| BLOCKED | 0 |
| FAILED | 0 |
| **Records with a prediction** | **450** |

Input quality breakdown:
{
  "complete": 450
}

EWSI status breakdown:
{
  "observed": 434,
  "estimated": 16
}

## Rules observed during the run

* Parameters were frozen before the run and were not modified during it.
* The run was executed in 8 parallel
  shards over a disjoint, deterministic interleave of the selected
  records; each shard had its own state database, and the merged
  result set is de-duplicated by record id.
* No record was deleted; blocked and failed records are written to
  `failed_records.jsonl` with their reason.
* Records with incomplete inputs are **not** counted as valid
  scientific predictions; the breakdown above separates them.
* The model version and code hash are recorded with every result.
* The test set was not used to select the model, the parameters, or any
  other decision.

## Runner

`engine/hydroma/eval/resumable_benchmark_runner.py`, reusing the Stage 38
resumable runner. State is held per record in SQLite, so a re-run skips
records already in a terminal status. The Stage 40 run uses a separate
state database, so the baseline and calibrated runs never share state.
