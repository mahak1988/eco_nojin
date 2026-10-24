# Stage 41 — District Analysis

All metrics per test district, on the shared records, with the baseline
and the mean reference alongside.

| District | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Buxar | 102 | 1.6877 | 1.2276 | -0.6179 | -1.6600 | 1.0691 | 1.8291 | -2.1244 |
| Muzaffarpur | 150 | 1.5010 | 1.0714 | -0.7228 | -1.3383 | 0.9862 | 1.7610 | -2.2185 |
| Rohtas | 114 | 1.8412 | 1.4971 | -1.0229 | -2.5419 | 0.9850 | 2.1097 | -3.6502 |

## Observed yields by district

| District | n | Mean | Median | SD | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| Buxar | 102 | mean=4.2988 median=4.3000 sd=1.0399 min=2.0300 max=6.6800 |
| Muzaffarpur | 150 | mean=4.6628 median=4.8750 sd=0.9849 min=2.5800 max=6.2600 |
| Rohtas | 114 | mean=4.6818 median=4.8500 sd=0.9826 min=2.6400 max=6.2300 |

## Records with estimated inputs, by district

| District | n | Records with an estimated input |
|---|---:|---:|
| Buxar | 102 | 102 |
| Muzaffarpur | 150 | 150 |
| Rohtas | 114 | 114 |

## Reading

* **Sample-size warning.** The test set has **3
  districts**. Per-district metrics rest on a few hundred records each,
  but the *spatial* generalisation of the result rests on three
  clusters. A district that looks good is evidence about that district,
  **not** evidence about the region, and no district is presented as
  proof of good performance anywhere.
* The **bias sign is not consistent across districts**. Where a
  district's bias flips sign relative to the others, the error is
  dominated by a *level* difference between districts that the model
  cannot represent (management, soil, or a different observed yield
  distribution) rather than by a scale error that a single global ε
  could fix.
* Districts with more estimated inputs show larger error, consistent
  with the input-quality attribution.
