# Stage 34 — Codebase Audit Report

## A. EWSI Contract — What It Is

The EWSI (EcoNojin Water Stress Index) contract is defined in:

- `engine/hydroma/models/ewsi.py:40` — `EWSI(ScientificModel)` class
- `engine/hydroma/simulation/ewsi_pipeline.py:66` — `compute_daily_ewsi()` orchestrator
- `engine/hydroma/models/hyrue.py:267` — HYRUE consumption: `f_water = 1 - EWSI`

### Current EWSI formula

```
EWSI = w_ndmi * S_NDMI + w_vpd * S_VPD + w_soil * S_SOIL
```

Default weights: `w_ndmi=0.4, w_vpd=0.3, w_soil=0.3` (`EWSIWeights`, ewsi.py:28)

Component stress indices (ewsi.py:179-219):

- **S_NDMI** = clip(1 - NDMI, 0, 1), where NDMI = (NIR - SWIR) / (NIR + SWIR)
- **S_VPD** = clip((VPD - 0.5) / 3.5, 0, 1) — anchors 0.5 kPa (low) and 4.0 kPa (high)
- **S_SOIL** = clip(1 - soil_moisture / field_capacity, 0, 1)

### EWSI semantics (confirmed in code)

- Range [0, 1]: 0 = no water stress, 1 = severe water stress (ewsi.py:175-177, hyrue.py:337-342)
- HYRUE uses `f_water = 1 - EWSI` (hyrue.py:267, confirmed)
- HYRUE validate_inputs rejects EWSI outside [0, 1] (hyrue.py:172-173)

### All three inputs are REQUIRED

`ewsi_pipeline.py:compute_daily_ewsi()` requires NIR/SWIR, VPD, and soil_moisture for every day. Missing any component raises `ValueError`. There is no partial-computation or weight-redistribution path.

---

## B. Required Inputs

From `engine/hydroma/simulation/ewsi_pipeline.py:29-41` (`EWSIInputSeries`):

| Input | Type | Required | Default | Unit |
|---|---|---|---|---|
| NIR | np.ndarray | Yes | None | surface reflectance |
| SWIR | np.ndarray | Yes | None | surface reflectance |
| VPD | np.ndarray | Yes | None | kPa |
| soil_moisture | np.ndarray | Yes | None | m³/m³ |
| soil_field_capacity | float | Yes | 0.35 | m³/m³ |
| dates | list[str] | Yes | None | ISO date strings |

All arrays must have the same length (`len(dates)`).

---

## C. Optional Inputs

`soil_field_capacity` defaults to 0.35 m³/m³ but is still required for the soil stress division (ewsi.py:201-211). There are no truly optional inputs — all three components must be present.

---

## D. Units of Each Variable

| Variable | Unit | Valid Range | Source |
|---|---|---|---|
| NIR | dimensionless reflectance | [0, 1] typical | ewsi.py:75 |
| SWIR | dimensionless reflectance | [0, 1] typical | ewsi.py:75 |
| NDMI | dimensionless | [-1, 1] | ewsi.py:75, clipped |
| VPD | kPa | [0, 10] | ewsi.py:76 |
| soil_moisture | m³/m³ | [0, 0.6] | ewsi.py:77 |
| EWSI | dimensionless | [0, 1] | ewsi.py:175 |
| f_water | dimensionless | [0, 1] | hyrue.py:267 |
| PAR | MJ/m²/day | [0, 50] | hyrue.py:166 |
| LAI | m²/m² | [0, 10] | hyrue.py:169 |
| t_mean | °C | [-10, 50] | hyrue.py:175 |

---

## E. How HYRUE Consumes EWSI

`engine/hydroma/models/hyrue.py:237-281` (`compute_daily`):

```python
f_water = 1 - ewsi_arr
biomass = apár * self.params.epsilon * f_water * f_temp
```

Where `apár = par_arr * f_ipar`, `f_ipar = 1 - exp(-k * min(LAI, lai_max))`, `f_temp = exp(-((T - t_opt) / 8)^2)`.

Seasonal mode (`hyrue.py:352-364`): sums daily biomass over the season array.

---

## F. EWSI = 0 Means No Stress

**Confirmed.** HYRUE docstring (hyrue.py:337-342): "EWSI is a STRESS index in [0, 1] where 0 = no water stress and 1 = severe water stress. f_water is its complement 1 - EWSI, so f_water = 1 means the crop was fully water-supplied (EWSI = 0)."

---

## G. Model Uses f_water = 1 - EWSI

**Confirmed.** `hyrue.py:267`: `f_water = 1 - ewsi_arr`. This is the only water stress path in HYRUE.

---

## H. Status Vocabulary — Missing / Estimated / Invalid / Observed

Existing quality status strings across the codebase:

| Module | Statuses Used |
|---|---|
| `weather_source.py:151-155` | field_measured, satellite_retrieved, analysis_product, estimated, missing, not_converted, observed |
| `field_data.py:58-69` (ObservationSource) | field_measured, satellite_retrieved, analysis_product, model_generated |
| `field_data.py:198-208` (quality_flag) | good, suspect, bad, missing, estimated |
| `seasonal_predictor.py:49-58` (InputQuality) | complete, partial, unavailable |
| `prediction.py:68-73` | COMPLETE, PARTIAL, UNAVAILABLE |
| `ewsi_pipeline.py:54` | model_generated |
| `dataset_manifest.py:28-33` (DataProvenance) | real_field_observations, synthetic_test_fixtures, unknown |

**Gap:** No unified `QualityStatus` enum exists that covers all four states (OBSERVED, SATELLITE_RETRIEVED, REANALYSIS_ESTIMATE, MODEL_ESTIMATE, INTERPOLATED, MISSING, INVALID) as specified in Stage 34 Part B. Each module uses its own string vocabulary.

---

## I. Historical Weather Fetch Capability

**Confirmed.** `fetch_daily_weather()` (`weather_source.py:201`) accepts `start` and `end` ISO date strings. Fallback chain:
1. Open-Meteo ERA5 archive (primary, no API key)
2. NASA POWER + Hargreaves ET0 (fallback, no API key)
3. CHIRPS/NCEP (not implemented, raises WeatherUnavailable)

Timeout: `REQUEST_TIMEOUT = (10.0, 60.0)` (connect, read).

---

## J. Cache, Retry, Timeout, Rate Limit, QC — What Exists

| Feature | Status |
|---|---|
| Timeout | Yes — `REQUEST_TIMEOUT = (10.0, 60.0)` in weather_source.py |
| Retry with backoff | **No** — not implemented anywhere in the simulation pipeline |
| Rate limiting | **No** — not implemented |
| Cache | **No** — no cache module exists in `engine/hydroma/simulation/` |
| HTTP response validation | Yes — `WeatherUnavailable` on non-200 status |
| Schema validation | Partial — numpy/pandas structural checks only |
| Date validation | Yes — start <= end, window <= 366 days |
| Unit validation | Partial — PAR shortwave unit normalization in par_pipeline.py |
| Error logging | Yes — `logger.warning()` on fallback |
| Synthetic data guard | Yes — `generate_synthetic_weather()` explicitly labeled |

**Missing:** retry/backoff, rate limiting, disk cache, schema validation of API responses, provenance tracking per API call.

---

## Discrepancies vs Stage 34 Specification

| Stage 34 Requirement | Current State | Action |
|---|---|---|
| Unified QualityStatus enum (OBSERVED, SATELLITE_RETRIEVED, REANALYSIS_ESTIMATE, MODEL_ESTIMATE, INTERPOLATED, MISSING, INVALID) | Each module uses its own string vocabulary | Create unified quality status module |
| remote_sensing package (satellite_source, reflectance_quality, spectral_indices, temporal_composite, satellite_cache) | Does not exist | Build new package |
| VPD model module (vpd_model.py) | Does not exist | Build new module |
| Soil moisture model module (soil_moisture_model.py) | Does not exist | Build new module |
| EWSI missing component policy (strict vs allow_estimated) | `compute_daily_ewsi()` requires all three; no policy | Enhance ewsi_pipeline.py |
| API retry/backoff, rate limit, cache | Not implemented | Add reliability layer |
| Temporal alignment (interpolation flagged, not labeled as observed) | Not implemented in satellite pipeline | Add temporal_composite.py |

---

## Next Steps

1. Create `engine/hydroma/simulation/quality_status.py` — unified quality status vocabulary
2. Create `engine/hydroma/simulation/remote_sensing/` package — satellite data pipeline
3. Create `engine/hydroma/simulation/vpd_model.py` — VPD computation
4. Create `engine/hydroma/simulation/soil_moisture_model.py` — soil moisture stress
5. Enhance `engine/hydroma/simulation/ewsi_pipeline.py` — missing component policy
6. Update `engine/hydroma/simulation/seasonal_predictor.py` — integrate new pipelines
7. Add reliability layer (retry, timeout, cache) to weather_source.py
8. Write tests (30+ unit tests + integration tests)
9. Run on CIMMYT data and determine benchmark status
