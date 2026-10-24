# Stage 41 — Frozen Model Audit

## Verdict

| Question | Answer |
|---|---|
| Is the Stage 40 frozen model unchanged? | **NO** - 2 of 8 model code files changed since the freeze, reviewed below and shown to be non-scientific |
| Can the crop preset override the frozen parameters? | **YES** - explicit parameters win |
| Do the calibration and benchmark paths share one input basis? | YES - both resolve LAI, EWSI, VPD, soil moisture and PAR through the same pipeline code |
| Was the model changed in Stage 41? | **NO** - no parameter, weight, HI or model selection was performed on the test set |

## Frozen model identity

| Field | Value |
|---|---|
| Model id | 2.0.1 |
| Frozen config | `D:\HyDroMA\engine\reports\data\stage40_frozen_model_config.json` |
| Frozen config sha256 | `9e7ec63a633793aff22c117a2c0b0a4e33dd14361bc2a778bb4c5a48d0b009a0` |
| Model code hash | `1ae6ddbd5a8c17ca2eafcf6909956dda7e0744633f70744e19a65069c2c1e3f6` |
| Benchmark run id | stage41_1792473123 |
| Started | 2026-10-20T05:12:03.031610+00:00 |

## Model code hashes

| File | Recorded sha256 | Status |
|---|---|---|
| engine/hydroma/eval/identifiability_calibration.py | 999465b119477c23… | CHANGED |
| engine/hydroma/eval/seasonal_predictor.py | 68c7da0e490b0da7… | CHANGED |
| engine/hydroma/models/hyrue.py | cc437a5026edf41c… | MATCH |
| engine/hydroma/simulation/ewsi_pipeline.py | f79f485316ebbc77… | MATCH |
| engine/hydroma/simulation/lai_model.py | c6f04342040ebfab… | MATCH |
| engine/hydroma/simulation/par_pipeline.py | 61a1fd00166528b1… | MATCH |
| engine/hydroma/simulation/radiation_units.py | 9ef67c2489bd28bf… | MATCH |
| engine/hydroma/simulation/weather_source.py | 7454e2b14b34b73b… | MATCH |

### Code change review

| Question | Answer |
|---|---|
| Files changed since the Stage 40 freeze | engine/hydroma/eval/identifiability_calibration.py, engine/hydroma/eval/seasonal_predictor.py |
| Is the change scientific? | **NO** |
| Does it require a new model version? | **NO** |

Additive metadata only: a ``data_source`` provenance field was declared on the Stage 40/41 result dataclasses (SeasonProfile, FoldResult, RecordResult, OperationalReport) to satisfy the repository's provenance contract (engine/strict_tests/test_s15_provenance.py). No computation, no parameter, no default in the numerical path was changed.

**Evidence of inertness.** Records recomputed with the current code reproduce the Stage 40 predictions bit-identically whenever the upstream inputs are identical (see stage41_reproducibility.json), and the Stage 40 regression tests - including the check that the analytical calibration formula equals HYRUE.compute to rel 1e-12 - still pass.

## Parameters carried into Stage 41

| Parameter | Value | Origin |
|---|---|---|
| ε (g/MJ IPAR) | 2.6300 | **calibrated** on development districts |
| HI | 0.45 | fixed (ε/HI perfectly collinear) |
| k | 0.65 | wheat preset |
| t_opt | 20.0 | wheat preset |
| t_min | 5.0 | wheat preset |
| t_max | 35.0 | wheat preset |
| lai_max | 6.0 | wheat preset |

The baseline version uses the identical parameter set with
ε = 2.2. Nothing else differs.

## Unit contract

| Quantity | Unit |
|---|---|
| PAR | MJ/m²/day |
| LAI | m²/m² |
| EWSI | dimensionless fraction |
| T_mean | °C |
| Yield | t/ha |
| ε | g/MJ IPAR |
| HI | dimensionless |
| Radiation conversion | shortwave -> PAR via the weather source's own PARConversionSpec (DEFAULT_PAR_SPEC) |

## Input policy

| Input | Policy |
|---|---|
| LAI | observed > empirical (NDVI) > model-generated (GDD) via LAIModel |
| EWSI | NIR/SWIR + VPD + soil moisture, with per-component fallbacks |
| Weather | Open-Meteo ERA5 archive, NASA POWER fallback on timeout |
| Satellite | Sentinel-2 L2A COG, per-field 20 m pixel |

## Versions

| Component | Version |
|---|---|
| LAI model | engine.hydroma.simulation.lai_model.LAIModel (GDD sigmoid) |
| EWSI | engine.hydroma.simulation.ewsi_pipeline |
| VPD | engine.hydroma.simulation.vpd_model |
| Soil moisture | engine.hydroma.simulation.soil_moisture_model |
| PAR | engine.hydroma.simulation.radiation_units |
| Predictor | engine.hydroma.eval.seasonal_predictor |

## Test-set manifest

| Field | Value |
|---|---|
| Path | `D:\HyDroMA\engine\reports\data\stage40_test_sample.json` |
| sha256 | `dfc57da5adfa21b135d49213fa6867e76506857ccf2ecb38746d7ad9b0777320` |
| Frame records | 1722 |
| Frame record-id hash | `5136319fcba6ef6b32469e2fc0513e68d6fc5259f2eafa9e21ffbd24887cfbe1` |
| Districts | Buxar, Muzaffarpur, Rohtas |

## A finding about the frozen config's metadata

The Stage 40 frozen config records the **generic** HYRUE default
`t_opt = 25 °C` in one place while the wheat preset (and therefore the
model actually evaluated) uses `t_opt = 20 °C`. The *values actually
used* are the ones in the table above, taken from the frozen config's
`parameter_values` and confirmed by the model contract check: the
non-calibrated parameters match the wheat preset exactly. The frozen
config's own `parameter_values.t_opt` is 20 °C; the discrepancy was in
this audit's first attempt, which built a partial parameter object from
dataclass defaults instead of the full frozen set. It is recorded here
because it is exactly the kind of silent parameter substitution Stage 41
is meant to catch.
