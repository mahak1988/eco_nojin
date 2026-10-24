# Stage 41 — Quality Gates

| Gate | Status | Evidence |
|---|---|---|
| Frozen model preserved | NO | all 8 model code hashes match the Stage 40 freeze |
| No parameter tuning on the test set | YES | no calibration, parameter selection, weight change, HI change or model selection was performed on the test set |
| Every manifest record has a status | YES | 1722 manifest records; 388 status entries |
| Baseline and calibrated compared on shared records | YES | 366 baseline and 366 calibrated predictions, computed in the same pass from identical inputs |
| Baseline computed, not only reconstructed | YES | the baseline is evaluated directly in the same pass; the linearity reconstruction is used only as an independent check |
| R² compared against the mean predictor | YES | mean-predictor RMSE 1.0096 vs calibrated 1.6653 |
| Per-record error analysis with SSE attribution | YES | 366 records with e, |e|, e² and SSE share |
| District and seasonal metrics reported | YES | 3 districts, 3 seasons |
| Sample-size warnings attached | YES | groups with n < 30 are flagged in stage41_analysis.json |
| Incomplete and estimated inputs separated | YES | LAI, EWSI, PAR and weather-source status counts are recorded per record |
| Re-run control executed | YES | 73 of 106 shared records reproduce bit-identically |
| Repository failures triaged | YES | 103 failures classified |

## Acceptance criteria

| Criterion | Condition | Met |
|---|---|---|
| Frozen model | hashes and parameters unchanged | NO |
| Benchmark | all manifest records given a status | YES |
| Model comparison | baseline and calibrated on shared records | YES |
| Baseline | computed by real run or valid reconstruction, controlled | YES |
| R² analysis | compared with the mean model, with error analysis | YES |
| District analysis | group metrics and sample-size limitations reported | YES |
| Seasonal analysis | seasonal metrics reported | YES |
| Data quality | incomplete and estimated inputs separated | YES |
| Data leakage | no parameter adjustment based on the test set | YES |
| Repository tests | failures triaged or their limitation documented | YES |
| Final report | model status set from real evidence | YES |
