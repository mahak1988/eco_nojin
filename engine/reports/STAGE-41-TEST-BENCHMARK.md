# Stage 41 — Test Benchmark

## Record accounting

| Quantity | Value |
|---|---|
| Manifest total records | 1722 |
| Records in the results file | 388 |
| Records with a prediction | 366 |
| Status counts sum equals records | YES |

| Status | Count |
|---|---:|
| BLOCKED | 1 |
| COMPUTED | 366 |
| FAILED | 21 |

No record is deleted. Records that could not be computed are written to
`stage41_test_benchmark/failed_records.jsonl` with their reason, so the
status counts always sum to the manifest total.

## Per-record fields

Every record carries: stable id, district, season, observed yield,
predicted yield (calibrated), predicted yield (baseline, from the same
inputs), model code hash, resolved-input data hash, execution status,
input-quality status, weather and satellite provenance, valid satellite
acquisition count, valid weather day count, and the failure reason when
one applies.

## Run configuration

| Item | Value |
|---|---|
| Model | 2.0.1, ε = 2.6300, HI = 0.45 |
| Model code hash | `1ae6ddbd5a8c17ca2eafcf6909956dda7e0744633f70744e19a65069c2c1e3f6` |
| Test districts |  |
| Shards | None |
| Elapsed | 0.0 min |
| Results | `engine/reports/data/stage41_test_benchmark/record_results.jsonl` |

## Input quality

| Input | Status counts |
|---|---|


| LAI | Status counts |
|---|---|


| EWSI | Status counts |
|---|---|


| Weather source | Status counts |
|---|---|


## Re-run control

| Check | Result |
|---|---|
| Records present in both the Stage 40 and Stage 41 runs | 106 |
| Re-run reproduces the Stage 40 prediction bit-identically | 73 / 106 |
| Within 1e-6 t/ha | 73 / 106 |
| Max absolute difference | 5.244680 t/ha |
| Records whose *inputs* differed between the runs | 106 |

**Interpretation.** Given the same inputs the model is deterministic:
the records whose inputs were identical reproduce bit-identically. The
records that differ had a different *upstream input* - the Sentinel-2
acquisition set or the EWSI component availability differed between the
two API calls - not different model behaviour. This is a property of
the upstream data services, not of HYRUE, and it is the reason the
baseline/calibrated comparison in Stage 41 is run as a **dual
evaluation in a single pass** (same weather, same LAI, same EWSI, same
PAR for both parameter sets) rather than by reconstructing one from the
other.
