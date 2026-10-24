# Stage 33: Limitations and Scientific Constraints Report

## A. Hard Limitations (Blocking Benchmark Completion)

### 1. EWSI Input Unavailability (PRIMARY BLOCKER)

**HYDROLOGICAL:** The EWSI (Evapotranspiration Water Stress Index) model requires
three inputs:
- **NIR/SWIR reflectance:** Satellite data (Sentinel-2, Landsat) — NOT available
  from Open-Meteo or NASA POWER
- **VPD (Vapor Pressure Deficit):** Can be computed from NASA POWER RH+T, but
  NIR/SWIR and soil moisture are still required
- **Soil moisture:** Available from ERA5-Land (Copernicus CDS API), but NOT
  implemented in the current pipeline

**Consequence:** `compute_hyrue_seasonal()` requires `input_quality == "complete"`,
which requires all four inputs (PAR, LAI, EWSI, T_mean). Without EWSI, the
model raises `WeatherUnavailable` for both STRICT and ALLOW_ESTIMATED policies.

### 2. STRICT Policy Cannot Produce Any Valid Predictions

| Input | Availability | STRICT Status |
|---|---|---|
| PAR | NASA POWER ALLSKY_SFC_PAR_TOT (satellite_retrieved) OR Open-Meteo shortwave → estimated | FAIL (Open-Meteo primary → estimated) |
| LAI | GDD model (model_generated) | FAIL |
| EWSI | Unavailable | FAIL |
| T_mean | Daily from weather API | OK |

Even if NASA POWER were configured as primary (providing satellite_retrieved PAR),
LAI is still model_generated and EWSI is still unavailable.

### 3. ALLOW_ESTIMATED Policy Cannot Produce Any Valid Predictions

| Input | Availability | ALLOW_ESTIMATED Status |
|---|---|---|
| PAR | Open-Meteo shortwave → 0.5 conversion (estimated) | OK (estimated allowed) |
| LAI | GDD model (model_generated) | OK (model_generated allowed) |
| EWSI | Unavailable | FAIL (WeatherUnavailable) |
| T_mean | Daily from weather API | OK |

The ALLOW_ESTIMATED policy permits estimated PAR and model-generated LAI, but
`compute_hyrue_seasonal()` does not enable `allow_legacy_fallback` for this
policy (only DIAGNOSTIC enables it). Without EWSI, the computation cannot proceed.

### 4. No Model Calibration Performed

HYRUE parameters were NOT calibrated on CIMMYT data. The model version is frozen
at 2.0.0 with wheat preset parameters:
- epsilon (RUE): 2.2 g/MJ IPAR
- hi (harvest index): 0.45
- t_opt (optimal temperature): 20°C
- k (extinction coefficient): 0.65
- t_min: 5°C, t_max: 35°C

No parameters were changed using test data. The benchmark evaluates the existing
model configuration without any parameter tuning.

## B. Data Limitations

### 1. Coarse Spatial Resolution

| Property | Value |
|---|---|
| Unique lat/lon pairs | 714 |
| Total records | 5689 |
| Max fields per coordinate | 157 |
| Coordinate precision | 2 decimal places (coarse, ~1km resolution) |

Coordinates are aggregated to ~2 decimal places (~1km resolution), indicating
village/representative points rather than precise field boundaries. This is
sufficient for weather API extraction but limits claims about field-level
spatial independence.

### 2. Missing Optional Metadata

All 5689 records are flagged REQUIRES_REVIEW due to missing:
- `area_ha` (field area) — not in dataset
- `harvest_sample_size` — not in dataset

These are optional metadata fields; their absence does not block execution
but limits scientific interpretability.

### 3. Monthly Weather Summary (Not Daily)

The CIMMYT file contains 12 monthly weather summary columns, NOT daily weather.
HYRUE requires daily inputs. Daily weather was fetched from Open-Meteo ERA5-Land
archive API, which was confirmed accessible.

### 4. Weather File Missing Values

19 records have missing values in
`Prcp_Monsoon`, `Jan_Srad`, and `Feb_Srad` (correlated, likely same 19 records).
These records are retained — weather data is fetched from the API.

## C. Scientific Limitations

### 1. LAI Model is a Placeholder

The GDD sigmoid LAI model (`LAIModel`) is documented as a "placeholder growth
curve, not a validated crop model." Its provenance is `model_generated`, not
`observed`. Using it in evaluation requires `allow_estimated` policy.

### 2. PAR Conversion is Estimated

When using Open-Meteo (primary), PAR is derived via the 0.5 shortwave-to-PAR
conversion (Monteith & Unsworth 2013). This is a "calibration-grade assumption"
(Status B), not a site-measured value. NASA POWER provides direct PAR via
`ALLSKY_SFX_PAR_TOT` (CERES SYN1deg Ed. 4.2), which would be satellite_retrieved,
but the primary weather source is Open-Meteo.

### 3. EWSI is a Novel Composite Index

The EWSI (Evapotranspiration Water Stress Index) is a novel composite index
(NDMI + VPD + soil moisture with weights 0.4/0.3/0.3). Only the NDMI sub-index
has a source (Gao 1996, corrected to note it is NDWI not NDMI). The index has
no external validation.

### 4. Legacy Constant Mode (Diagnostic Only)

When `allow_legacy_fallback=True` (DIAGNOSTIC policy only), HYRUE runs in
`legacy_constant` mode, which assumes identical conditions for all days and
overstates seasonal totals. This mode is explicitly documented as not
physiologically correct.

## D. Sensitivity Analysis Summary (Supplementary)

| Parameter | Baseline | Max Delta | Max Relative Sensitivity |
|---|---|---|---|
| par | 9.1584 | 0.9652 | 0.25 |
| lai | 1.9966 | 0.4514 | 0.1169 |
| t_mean | 20.5032 | 1.7998 | 0.2998 |
| ewsi | 0.1 | 0.5362 | 0.1111 |

Baseline yield (diagnostic, legacy mode): 4.8261 t/ha
Days analyzed: 126

**Notes:**
- Sensitivity was run on a single representative record's inputs
- EWSI was held constant at 0.1 (scalar) for this analysis only — actual EWSI
  was unavailable
- No HYRUE parameters were changed during sensitivity analysis
- Sensitivity results are INDEPENDENT of the main benchmark evaluation

## E. Evaluation Status

| Dimension | Status |
|---|---|
| Data file hash verified | PASS |
| Protocol defined | PASS |
| Data leakage check | PASS |
| STRICT execution | BLOCKED (EWSI unavailable) |
| ALLOW_ESTIMATED execution | BLOCKED (EWSI unavailable) |
| DIAGNOSTIC execution | COMPLETED (supplementary only) |
| Overall benchmark status | BLOCKED |

## F. What Would Be Needed to Unblock

1. **NIR/SWIR reflectance data:** Sentinel-2 Level-2A data or comparable satellite
   imagery for the CIMMYT site coordinates during the growing seasons.
2. **VPD:** Daily VPD from NASA POWER (`VPD` parameter) or computed from RH+T.
3. **Soil moisture:** Daily soil moisture from ERA5-Land (Copernicus CDS API).
4. With these three inputs, EWSI can be computed, and the ALLOW_ESTIMATED
   evaluation can proceed. The STRICT evaluation would still require observed
   LAI (available from satellite LAI products or field measurements).
