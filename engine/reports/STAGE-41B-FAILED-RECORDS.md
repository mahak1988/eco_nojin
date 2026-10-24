# Stage 41-B — Failed-record analysis

The actual result ledger contains 30 FAILED records and one BLOCKED record. These are the records that did not complete successfully.

## Failure pattern

The underlying execution trace and summary artifact indicate that the dominant failure mode is not a Python exception in the model equations themselves, but a pipeline/inputs issue:

- weather coverage is zero or effectively missing in many records;
- PAR is missing or unresolved;
- LAI status shifts between missing and estimated; 
- EWSI status shifts between estimated and observed depending on upstream data availability;
- the model falls back to GDD-driven or estimated LAI / EWSI paths instead of a reliable observed series.

## Categorized reason table

| Failure category | Count | Input incomplete or code bug? | Primary module(s) |
|---|---:|---|---|
| Weather / valid-day coverage missing | 10 | Input incomplete | `engine/hydroma/simulation/weather_source.py`, `engine/hydroma/simulation/par_pipeline.py` |
| GDD / LAI fallback path activated | 5 | Input incomplete | `engine/hydroma/simulation/lai_model.py`, `engine/hydroma/simulation/par_pipeline.py` |
| EWSI quality mismatch / estimated-only fallback | 12 | Input incomplete | `engine/hydroma/simulation/ewsi_pipeline.py` |
| Real code-path failure / contract mismatch | 3 | Likely code bug or contract issue | provenance / pipeline validation layer |
| Total failed | 30 | — | — |

## What this means

The primary systematic issue is not a numerical regression in HYRUE itself. The failures are dominated by missing or weak upstream inputs, especially weather, LAI, and EWSI. From the repository audit, this is consistent with the Stage 41 summary: provenance contract / weather input / GDD fallback / EWSI contract issues are the reason the benchmark is partial and non-comparable.

This is a genuine blocker for a clean Stage 41 close-out because it prevents a full, valid comparison against the Stage 40 frozen run.
