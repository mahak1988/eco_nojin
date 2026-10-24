# Stage 41-B — Baseline-vs-calibrated-vs-mean comparison

This comparison is read directly from `engine/reports/data/stage41_analysis.json` for the records with a real prediction in the Stage 41 run.

## Shared-record comparison table

| Version | n | R² | RMSE (t/ha) | MAE (t/ha) | Bias (t/ha) |
|---|---:|---:|---:|---:|---:|
| Baseline (ε = 2.2) | 384 | -3.1810 | 2.0859 | 1.6711 | -1.5409 |
| Calibrated (ε = 2.63) | 384 | -2.3826 | 1.8762 | 1.3845 | -0.9455 |
| Mean predictor | 384 | 0.0000 | 1.0201 | 0.8732 | 0.0000 |

## Direct answers

- Did the calibrated model beat the baseline?
  - Yes. The calibrated model improves RMSE from 2.0859 to 1.8762 t/ha, an improvement of 0.2097 t/ha or about 10.1%.

- Did the calibrated model beat the mean predictor?
  - No. The mean predictor still wins with RMSE 1.0201 vs 1.8762 and R² 0.0 vs -2.3826.

- Is the Stage 40 improvement retained on the shared records?
  - The same fundamental direction remains present: the calibrated model is better than the baseline, but it remains worse than the mean predictor. However, the full Stage 41 benchmark is not cleanly comparable with Stage 40 because 33 records diverged under the re-run control and the upstream input state shifted.

## Conclusion

The calibrated model is numerically better than the baseline on the same Stage 41 input set, but the benchmark is still structurally weak and still loses to the mean predictor. This is not evidence of a scientifically improved model, only a relative improvement within the current, incomplete benchmark.
