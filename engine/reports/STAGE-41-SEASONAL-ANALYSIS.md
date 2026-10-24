# Stage 41 — Seasonal Analysis

All metrics per cropping season, on the shared records.

| Season | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2016-17 | 131 | 1.1350 | 0.8853 | 0.1336 | -0.4486 | 1.0010 | 1.2362 | -0.7185 |
| 2017-18 | 216 | 1.5722 | 1.2312 | -1.0689 | -1.5098 | 1.0256 | 1.8936 | -2.6405 |
| 2018-19 | 19 | 4.0542 | 3.9302 | -3.9302 | -42.3748 | 0.8779 | 4.2252 | -46.1094 |

## Observed yields by season

| Season | n | Mean | Median | SD |
|---|---:|---:|---:|---:|
| 2016-17 | 131 | mean=4.9031 median=5.2500 sd=0.9466 |
| 2017-18 | 216 | mean=4.3086 median=4.1950 sd=0.9947 |
| 2018-19 | 19 | mean=5.1932 median=5.1100 sd=0.6325 |

## Reading

* Performance is **not stable across seasons**. The seasons differ in
  both the observed yield level and the model's error, and the bias
  changes sign between them. A single pooled metric hides that.
* The seasons with the largest |bias| are the ones where the observed
  yield level moved furthest from what the model produces. That is
  consistent with a model whose scale is set by a season-level integral
  that does not track the inter-annual variability of the region.
* Seasons with very small n are flagged in `stage41_analysis.json`
  (`sample_size_warning`); their metrics should not be read on their
  own.
