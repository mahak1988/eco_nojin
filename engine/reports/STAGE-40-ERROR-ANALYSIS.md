# Stage 40 — Error Analysis

## The headline change

| Stage | Model | Development R² | Development RMSE |
|---|---|---:|---:|
| 39 | uncalibrated defaults | -0.1586 | 1.0579 t/ha |
| 40 | ε fitted on development data | 0.3284 | 0.8054 t/ha |

The negative R² of the uncalibrated model is the central diagnostic
finding of the last two stages. It is explained by the identifiability
structure: `ε` and `HI` multiply the seasonal biomass, and the
literature default for `ε` does not match the harvest index actually
realised by these fields, so every prediction was displaced in the same
direction.

Fitting `ε` on development data (with `HI` fixed) moves the scale to
where the development observations put it, and the R² crosses zero.

## Where the error now comes from

| Source | Evidence | Status |
|---|---|---|
| Yield scale (ε) | Fitted on development data; stable across 7 LODO folds (rel. range 0.0266) | **Addressed** - see the caveat below |
| EWSI amplitude | Weights and anchors are uncalibrated defaults; the fitted ε may have absorbed an EWSI scale error | **Open** |
| LAI | Every record uses the same GDD-model curve (`LAIModel`), so the seasonal LAI shape is assumed | **Open** |
| Thermal response | `t_opt` = 20 °C with a hard-coded 8 °C width; the width has no source | **Open** |
| Soil moisture | ERA5-Land reanalysis at ~9 km; field capacity 0.35 m³/m³ is a default | **Open** |
| Satellite NDMI | Single 20 m pixel; ~4-6 % of days observed, rest forward-filled | **Open** |
| Season length | Sowing/harvest dates from CIMMYT; the biomass window follows them | **Open** |
| Observation uncertainty | Not propagated | **Open** |

## A defect found and fixed during this stage

The first Stage 40 benchmark run was **aborted** because a review of the
code found that the frozen parameters were never reaching the model.
`HYRUE.__init__` applied the crop preset whenever a crop name was
supplied, silently overwriting any explicit `HYRUEParams` — so
`HYRUE(params=calibrated, crop="wheat")` evaluated the *uncalibrated*
default. The calibrated run would have been byte-for-byte the baseline
run.

Three things were done about it:

1. `HYRUE.__init__` now gives explicit parameters precedence over the
   crop preset.
2. The parameter set is threaded explicitly through
   `compute_hyrue_seasonal` → `SeasonalPredictionRequest` →
   `ResumableBenchmarkRunner`, and is recorded in the run manifest and
   in the per-record data hash.
3. Regression tests now assert that a supplied parameter set changes
   the prediction, and that the analytical calibration formula is
   numerically identical to `HYRUE.compute` (`rel = 1e-12`).

The Stage 39 baseline was re-checked against the current code on a
26-record sample: **26/26 predictions identical, max difference 0.0**
(`stage40_baseline_equivalence.json`), so the baseline numbers remain
valid.

A second defect was found at the same time: the first profile builder
used a **synthetic sigmoid LAI** and a hard-coded PAR factor of 0.5,
while the benchmark pipeline resolves LAI with the GDD model and
converts PAR with the weather source's own factor. The calibration was
therefore fitted against a different input basis from the one it was
evaluated on. The profiles are now built by the **same runner the
benchmark uses**, with the resolved daily arrays captured from the live
pipeline, so the skew is removed by construction. The fitted ε changed
from 2.570 to 2.630 when this
was corrected.

## Why only one parameter was freed

`ε` and `HI` are perfectly collinear; the EWSI weights are collinear
with each other and with the EWSI amplitude; `k`, `lai_max` and the
LAI series are mutually confounded; `t_opt` is confounded with the
hard-coded Gaussian width. Freeing several of these together would
produce a fit without identifying which change caused it, and would make
the fitted values uninterpretable.

The single free parameter is therefore a **modelling decision**, and the
fitted `ε` should be read as "the scale that the development set
implies", not as "the true radiation use efficiency of wheat in Bihar".

## An important caveat about the objective

The objective was nearly flat over the pre-registered ε grid
(relative spread 0.0330, i.e.
many ε values fit the development data almost equally well). The
leave-one-district-out estimate is nevertheless stable, which says the
grid minimum sits in the same place regardless of which district is
held out — but the *width* of the flat region means the data do not
determine ε precisely. The frozen value should be treated as one
defensible point on a plateau, not as a sharp measurement.

## Test-set error (frozen model)

| Group | n | Bias (t/ha) |
|---|---:|---:|
| Buxar | 189 | -0.3939 |
| Muzaffarpur | 110 | -0.1420 |
| Rohtas | 151 | -0.6135 |

## What would reduce the remaining error

1. **Observed LAI.** With a real LAI series, `k` and `lai_max` become
   separately informative and the LAI amplitude stops being assumed.
2. **A published EWSI weighting.** The EWSI amplitude currently has
   no independent constraint, so it can only be absorbed by `ε`.
3. **Field-level soil moisture.** Replacing the ERA5-Land reanalysis
   with in-situ measurements would remove a systematic spatial bias.
4. **A second dataset.** Every result here comes from one dataset in
   one region over six years.
