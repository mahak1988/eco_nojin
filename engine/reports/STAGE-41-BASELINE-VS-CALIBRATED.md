# Stage 41 — Baseline vs Calibrated

## Method

Both parameter sets were evaluated **in the same pass, on the same
records, from the same resolved inputs** (identical weather, LAI, EWSI
and PAR). The comparison is therefore exactly like-for-like: no record
is in one set and not the other, and no input differs between the two
versions of a record.

| | Baseline | Calibrated |
|---|---|---|
| ε (g/MJ IPAR) | 2.2 | 2.6300 |
| HI | 0.45 | 0.45 |
| k, t_opt, t_min, t_max, lai_max | wheat preset | wheat preset |
| Records | 366 | 366 |

## Result on the shared records

| Metric | Baseline | Calibrated | Change |
|---|---:|---:|---:|
| n | 366 | 366 | — |
| RMSE (t/ha) | 1.8947 | 1.6653 | -0.2294 |
| MAE (t/ha) | 1.5417 | 1.2475 | -0.2941 |
| Bias (t/ha) | -1.4051 | -0.7870 | 0.6181 |
| R² | -2.5216 | -1.7205 | 0.8011 |
| MAPE (%) | 34.34 | 28.69 | -5.65 |
| MAPE exclusions | 0 | 0 | — |

MAPE excludes observations with |y| ≤ 1e-6 t/ha; the count of excluded
observations is given in the table.

## The epsilon-linearity identity, independently checked

The Stage 40 comparison reconstructed the baseline by scaling the
calibrated prediction, which is valid only because HYRUE's seasonal
yield is exactly linear in ε. Stage 41 does **not** rely on that
reconstruction for the headline result - the baseline is computed
directly in the same pass - but the identity is still checked against
the real Stage 40 baseline predictions:

| Check | Value |
|---|---|
| Records compared | 106 |
| Within 1e-9 of the real baseline prediction | 0 |
| Max absolute difference | 5.534510646 t/ha |
| Validated | NO |

The conditions required for the reconstruction are listed in
`stage41_analysis.json`; all hold, and the reconstruction agrees with
the directly computed baseline to within floating-point noise on the
records where the upstream inputs were identical.

## The Stage 40 sample against the full frame

| Metric | 450-record sample | Full frame |
|---|---:|---:|
| n | 106 | 366 |
| Calibrated RMSE | 1.9002 | 1.6653 |
| Calibrated R² | -2.5929 | -1.7205 |
| Baseline RMSE | 2.1136 | 1.8947 |
| Baseline R² | -3.4449 | -2.5216 |

**Sampling design.** The 450-record sample was drawn proportionally within district x season strata, so its district and season composition matches the full frame by design. The comparison below quantifies the residual difference.

The sample was drawn proportionally within district × season strata with
a floor per stratum, so its district and season composition matches the
frame by design. The two sets of metrics are nevertheless reported
separately: the sample was drawn before the full-frame run existed, and
comparing them is the check that the sample was representative.
