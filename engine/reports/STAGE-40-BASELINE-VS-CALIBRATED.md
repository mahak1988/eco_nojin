# Stage 40 — Baseline vs Calibrated

## The two model versions

| | Stage 39 baseline | Stage 40 calibrated |
|---|---|---|
| Model version | 2.0.0 | 2.0.1 |
| ε (g/MJ IPAR) | 2.2 | 2.6300 |
| HI | 0.45 | 0.45 |
| Other parameters | defaults | defaults |
| Calibration | none | grid search (0.1 coarse, 0.01 refine) |
| Result file | `stage39_benchmark/…` | `stage40_test_benchmark/…` |

The two result sets live in **separate directories** and are never
concatenated. The Stage 39 file is preserved unchanged; the baseline
manifest (`stage40_baseline_manifest.json`) records its state.

## Development-set comparison (identical records, identical inputs)

| Metric | Baseline | Calibrated | Change |
|---|---:|---:|---|
| n | 41 | 41 | — |
| RMSE (t/ha) | 1.0579 | 0.8054 | -0.2525 |
| MAE (t/ha) | 0.9136 | 0.6363 | -0.2773 |
| Bias (t/ha) | -0.7375 | -0.0709 | 0.6666 |
| R² | -0.1586 | 0.3284 | — |
| MAPE (%) | 22.19 | 17.19 | — |

## Held-out (leave-one-district-out) comparison

| Metric | Baseline | Calibrated |
|---|---:|---:|
| Mean validation RMSE (t/ha) | 1.0312 | 0.7743 |

Calibration improves held-out performance:
**True**

## Stage 40 test-set result (frozen calibrated model)

| Metric | Value |
|---|---:|
| n | 450 |
| RMSE (t/ha) | 1.2828 |
| MAE (t/ha) | 1.0049 |
| Bias (t/ha) | -0.4060 |
| R² | -0.4115 |
| MAPE (%) | 23.34 |

### By district

| District | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
| Buxar | 189 | 1.2742 | 0.9675 | -0.3939 | -0.3493 |
| Muzaffarpur | 110 | 1.1991 | 0.9577 | -0.1420 | -0.1540 |
| Rohtas | 151 | 1.3507 | 1.0861 | -0.6135 | -0.7485 |

Uncertainty (district-level cluster bootstrap): **OK** —
[1.199141150724862, 1.3506967865635346].

## Is the improvement attributable to the calibration?

The comparison above holds the *records* fixed (the same development
records are evaluated under both parameter sets) and the *inputs* fixed
(the cached seasonal integrals S are identical). The only difference
between the two columns is the value of ε.

Two things are **not** claimed:

* that the improvement is statistically significant — the fold count
  is small;
* that the improvement will transfer to the test districts — only the
  held-out district comparison speaks to that, and it is reported
  separately.
