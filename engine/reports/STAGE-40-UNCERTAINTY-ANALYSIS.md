# Stage 40 — Uncertainty Analysis

## Test-set uncertainty (district-level cluster bootstrap)

| Quantity | Value |
|---|---|
| Status | OK |
| Independent districts | 3 |
| Records | 450 |
| Bootstrap samples | 1000 |
| RMSE mean | 1.2806 t/ha |
| RMSE 95 % CI | [1.1991, 1.3507] |
| MAE mean | 1.0049 t/ha |
| MAE 95 % CI | [0.9577, 1.0861] |
| Bias mean | -0.3996 t/ha |
| Bias 95 % CI | [-0.6135, -0.1420] |

## The three-district limitation

The test set contains **three** districts. A cluster bootstrap over
three clusters has a bootstrap distribution that is the distribution of
three draws: the 2.5th and 97.5th percentiles are close to the
extreme resamples (the same district drawn three times, or one drawn
twice). The interval is therefore driven by a handful of outcomes and
is **not** a stable estimate of the sampling distribution of spatial
generalisation.

The interval is reported as a limited uncertainty estimate, not as a
confidence statement about generalisation beyond these districts.

## What the interval does and does not cover

| Source of uncertainty | Covered? |
|---|---|
| Spatial variation between the three test districts | Yes, with the caveat above |
| Sampling of records within a district | No — deliberately not resampled |
| **Calibration uncertainty** | **No** — the bootstrap uses the frozen model, not the calibration |
| Remote-sensing input uncertainty | No |
| Weather reanalysis uncertainty | No |
| Observation uncertainty | No |

The reported interval therefore **understates** the total uncertainty.
With a single fitted parameter and a nearly flat objective, the
calibration component is not negligible: the fold-to-fold spread of ε
(0.0210 g/MJ IPAR, relative range
0.0266) is the available estimate of
that component, and it is reported separately.

## Development-set parameter stability as the calibration component

| Quantity | Value |
|---|---|
| Folds | 7 |
| ε values | 2.660, 2.620, 2.590, 2.650, 2.640, 2.630, 2.630 |
| Standard deviation | 0.0210 |
| Relative range | 0.0266 |
| Assessed stable | True |

## Combining the components

A defensible total interval would need the three components added in
quadrature (or a bootstrap that resamples the calibration as well).
That requires running the calibration inside the bootstrap loop, which
multiplies the cost by the number of bootstrap samples. It is recorded
as Stage 41 work.

## Conclusion

The spatial component is reported with an explicit warning about the
cluster count. The calibration and input components are **not** covered
and are stated as such. No claim of broad generalisability is made.
