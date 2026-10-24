# Stage 39 — Uncertainty Analysis

## Method

District-level cluster bootstrap, implemented in
`engine/hydroma/eval/stage39_benchmark.py::cluster_bootstrap_uncertainty()`.

Records within a district are spatially correlated (same fields, same
weather regime, same management). Resampling individual records would
treat them as independent and understate the uncertainty. The bootstrap
therefore resamples **districts**, carrying every record of a sampled
district with it.

```
for b in 1..B:
    sampled = choice(districts, size=n_districts, replace=True)
    records_b = concat(all records of each sampled district)
    rmse_b, mae_b, bias_b = metrics(records_b)
```

`B = 1000`, seed = 42, 95% percentile interval.

## Critical Limitation — Three Districts

The test set contains **three** districts: Buxar, Muzaffarpur, Rohtas.

`cluster_bootstrap_uncertainty()` therefore reports:

```json
{"status": "BLOCKED",
 "reason": "Only 3 independent district(s) available; at least 3 are required...",
 "n_districts": 3}
```

With three clusters, the bootstrap distribution is the distribution of
*three* draws. The 2.5th and 97.5th percentiles are essentially the
extreme resamples (the same district drawn three times, or a single
district drawn twice), so the interval is driven by a handful of
outcomes and is not a stable estimate of the sampling distribution.

**The interval is reported as a limited uncertainty estimate, not as a
confidence statement about generalisation to other regions.** No claim of
broad generalisability is made from three districts.

## What the Uncertainty Does and Does Not Cover

| Source of uncertainty | Covered? |
|---|---|
| Spatial variation between the three test districts | Yes (with the caveat above) |
| Sampling of records within a district | No — deliberately not resampled |
| Calibration uncertainty | **No** — no calibration was performed |
| Remote-sensing input uncertainty | **No** — not propagated |
| Weather reanalysis uncertainty | **No** — not propagated |

The bootstrap quantifies only the first row. The parameter and input
components are unquantified, and the total uncertainty is therefore
**larger** than the reported interval.

## Separation of Calibration and Input Uncertainty

Because no calibration was performed, the "calibration uncertainty"
component is not merely unquantified — it is undefined. The frozen model
has a single parameter set with no fitted distribution, so there is
nothing to propagate.

Once calibration is executed with the recommended design (see
`STAGE-39-PARAMETER-IDENTIFIABILITY.md`), the calibration uncertainty
can be estimated from the leave-one-district-out folds and reported
separately from the bootstrap interval.

## Recommendation for Stage 40

1. Execute the development calibration (3 free parameters, leave-one-
   district-out).
2. Report the fold-to-fold spread of each calibrated parameter as the
   calibration-uncertainty component.
3. Re-run the bootstrap on the test set and report both components
   separately.
4. State plainly that the total uncertainty exceeds the spatial
   component, and that three districts cannot support a generalisation
   claim beyond the eastern-India wheat domain.
