# Stage 39 — Limitations

## Scientific Limitations

1. **The uncalibrated model is currently worse than a mean-predictor.**
   On the 26 test records evaluated so far, R² = −1.099 with a
   systematic under-prediction (Bias = −0.686 t/ha). The dominant
   mechanism is the uncalibrated scale parameter ε·HI. Until the
   development calibration is executed, this is the honest
   characterisation of the model's predictive skill.

2. **No calibration was performed.** The frozen model carries the
   project-default parameters. Any benchmark metrics characterise the
   *default* model, not a calibrated one. See
   `STAGE-39-CALIBRATION-REPORT.md`.

2. **ε and HI are not separately identifiable** from yield data; only
   their product can be estimated. See
   `STAGE-39-PARAMETER-IDENTIFIABILITY.md`.

3. **EWSI weights and anchors have no published source** for wheat in
   eastern India. They are model assumptions, not measured coefficients.

4. **The LAI series is model-generated** (GDD model with default
   parameters). No observed LAI exists for the CIMMYT records, and the
   empirical NDVI→LAI coefficient (3.5) is not validated for this crop
   and region.

5. **Satellite NDMI is a single-pixel point sample**, not a field
   average. CIMMYT coordinates are approximate (~1 km resolution) while
   the Sentinel-2 pixel is 20 m.

6. **Satellite temporal coverage is sparse** — typically ~4% of season
   days have an observation, so the NDMI series is heavily
   forward-filled between acquisitions. The interpolation is labelled
   (`INTERPOLATED`), but the resulting NDMI series is weakly
   constrained.

7. **Weather inputs are reanalysis estimates** at ~9 km resolution
   (ERA5-Land), not field measurements. Soil moisture in particular is a
   grid-cell estimate.

8. **The 0.5 shortwave→PAR factor is an approximation**, not a measured
   quantity for these sites.

## Data Limitations

1. **Single dataset.** All results derive from the CIMMYT eastern-India
   wheat dataset (5,689 records, 10 districts, 2016-2022). No second
   dataset is available for external validation.

2. **Only three test districts** — Buxar, Muzaffarpur, Rohtas. This
   limits any generalisation claim and makes the district-level
   bootstrap statistically fragile.

3. **Coordinate-cell overlap between development and test** (374 of 445
   distinct test cells also appear in development). Not a record- or
   district-level leak, but it weakens the independence of the test set.

4. **CIMMYT coordinates are anonymised/approximate.** The dataset does
   not provide field boundaries, so neither satellite nor weather inputs
   can be matched to an actual field polygon.

## Execution Limitations

1. **Benchmark runtime.** At the measured ~30 s per record
   (≈52 s for a first-time satellite season fetch, ~2 s for a cached
   one), the full 1,722-record test set takes approximately **14 hours**
   of wall-clock time. The run is resumable and continues in the
   background.

2. **Development calibration was not executed.** The same cost applies
   to the 3,967 development records (~33 hours), before any parameter
   search.

3. **Parallel execution was not enabled.** The Stage 38 requirement is
   to measure and respect the API rate limit before raising the
   request rate. That measurement was not performed, so a parallel run
   would multiply the request rate against Planetary Computer and
   Open-Meteo without a measured basis.

4. **Runtime environment defect.** The sandbox filesystem exhibits
   path-cache poisoning and duplicated `.pth` entries. The fix
   (`engine/hydroma/eval/runtime_bootstrap.py`) works around this, but
   it is an environment property, not a property of the codebase. A
   clean environment would not need it.

## Generalisation Limits

Any result from this stage is valid, at most, for **winter wheat in
Bihar and eastern Uttar Pradesh, India, 2016-2022**. It does not
transfer to other crops, other Indian regions, other climates, or
outside that period without further validation.

## Claim Limits

The following statements are **not** supported by this stage:

* that HYRUE is a validated model;
* that the reported accuracy generalises beyond the test districts;
* that the EWSI index is physiologically correct;
* that the parameter values are empirically identified.

What *is* supported: the pipeline executes reproducibly on real data,
produces per-record outputs with complete provenance, and the residual
error on the pilot record was reduced from +63.2% to −28.0% by correcting
the PAR unit chain.
