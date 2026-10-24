# Stage 40 — Development Calibration

## Status

**CALIBRATED** — executed on development-district
records only.

## Protocol

| Item | Value |
|---|---|
| Objective | RMSE on development-district records (t/ha) |
| Optimisation | grid search (0.1 coarse, 0.01 refine) |
| Free parameter | `epsilon` |
| Fixed parameter (identifiability) | `hi` = 0.45 |
| Seed | 20240115 |
| Cross-validation | leave-one-district-out over the development districts; the held-out district contributes to neither the fit nor any data-dependent transformation |
| Development sample | 41 records |
| Districts covered | Begusarai, Bhojpur, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura |
| Seasons covered | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22 |
| Epsilon bounds | [1.0, 4.0] g/MJ IPAR |
| Frozen at | 2026-10-19T20:06:30.196358+00:00 |
| Model code hash | `1ae6ddbd5a8c17ca2eafcf6909956dda…` |

## Leakage Controls

* The calibration sample is drawn from the development districts listed in
  the Stage 36 split manifest; the test districts are excluded by the
  manifest, not by a hard-coded list.
* `assert_no_test_districts()` runs on every calibration entry point and
  raises if a test-district record is present.
* The EWSI weights, the EWSI anchors, `HI`, the LAI parameters and the
  thermal parameters are **not** fitted, so no parameter could have been
  selected using a test observation.
* Test-district data was not read by any code path in this calibration.

## Result

| Metric | Baseline (ε = 2.2) | Calibrated (ε = 2.630) |
|---|---:|---:|
| n | 41 | 41 |
| RMSE (t/ha) | 1.0579 | 0.8054 |
| MAE (t/ha) | 0.9136 | 0.6363 |
| Bias (t/ha) | -0.7375 | -0.0709 |
| R² | -0.1586 | 0.3284 |
| MAPE (%) | 22.19 | 17.19 |

Fitted **ε = 2.6300 g/MJ IPAR** with HI held fixed at
0.45.

Objective flatness across the pre-registered grid: relative spread
0.0330 ("flat" = True).
A large spread means the objective is well determined; a small one would
mean the parameter is poorly constrained.

## Objective Behaviour and Non-Convergence

| Check | Result |
|---|---|
| Fitted value inside the pre-registered bounds | YES |
| Objective is single-minimum over the grid | NO - nearly flat, weakly determined |
| Same input reproduces the same value | YES (seeded, deterministic grid) |
| Fold-to-fold spread | 0.0266 |

## Why the sample, not the full development set

The full development set is 3,967 records. At the measured cost of one
pipeline pass per record (~60 s including the satellite season fetch),
that is ~66 hours of API-bound compute. The calibration therefore ran on
a deterministic, district-and-season-stratified sample of
41 records, which is a **substitute for
full calibration, not a replacement for it**. The frozen model is
therefore labelled as calibrated on a sample.

The sample is documented in `stage40_dev_profiles.json` with the seed,
the record identifiers, the districts, the seasons and the observed
yields.

## Parameter Identifiability

`ε` and `HI` are perfectly collinear: only their product is identifiable
from yield data. Holding `HI` fixed is a **modelling decision**, not a
claim that the true harvest index is 0.45
for these fields. See `STAGE-40-PARAMETER-IDENTIFIABILITY.md`.

## Files

* `engine/hydroma/eval/identifiability_calibration.py` — calibration machinery
* `engine/reports/data/stage40_calibration_results.json` — executed results
* `engine/reports/data/stage40_frozen_model_config.json` — frozen configuration
* `engine/reports/data/stage40_dev_profiles.json` — the calibration sample
