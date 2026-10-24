# Stage 31: Agricultural Dataset Acquisition, Provenance Audit & HYRUE Validation Readiness

## Objective

Identify, acquire, and assess real-world agricultural yield data to enable the first
empirical evaluation of HYRUE. This audit distinguishes three categories of data status:

1. **Identified potential source** — a dataset known to exist that may be relevant.
2. **Data actually retrieved** — files successfully downloaded and verified.
3. **Data qualified for validation** — retrieval confirmed, structure verified,
   and inputs compatible with the HYRUE prediction pipeline.

## Key Principle: Scale Mismatch Awareness

The HYRUE model operates at **field-level** resolution. Aggregated statistics
(county, state, or regional) are suitable for *regional aggregate validation* but
do **not** constitute independent field-level validation data. Any benchmark
execution using aggregated data must be labeled as such and cannot claim
field-level accuracy.

---

## Two Independent Validation Paths

### Path 1: Field-Level Validation (Primary)

Uses field-level yield observations (individual fields with GPS coordinates,
planting/harvest dates, measured yield). This is the target for true
external validation of HYRUE predictions.

### Path 2: Regional Validation (Secondary/Alternative)

Uses county/state-level yield statistics. Suitable for evaluating model
performance at regional aggregate scale, but with different uncertainty
characteristics and cannot be extrapolated to field-level claims.

---

## Source 1: USDA BARC Gridded Yield Data Archive (Priority 1)

### URLs

- **Dataset DOI:** https://doi.org/10.15482/USDA.ADC/28950746
- **Ag Data Commons landing page:** https://doi.org/10.15482/USDA.ADC/28950746
  (redirects to `https://agdatacommons.nal.usda.gov/articles/dataset/.../28950746`)
- **Data.gov catalog entry:** https://catalog.data.gov/dataset/USDA-Beltsville-Agricultural-Research-Center-BARC-Gridded-Yield-Data-Archive-version-1
- **Scientific paper:** https://doi.org/10.1002/agg2.20474 (Dulaney et al., 2024,
  *Agrosystems, Geosciences & Environment*)

### License & Access

- **License:** Public Domain (US Government work) per Ag Data Commons listing.
- **Access:** Free registration on Ag Data Commons may be required for large-file
  downloads. No API key needed.

### Publication Details (from scientific paper)

- **Authors:** Dulaney, W.P., Anderson, M.C., Gao, F., Stern, A., Moglen, G.,
  Meyers, G., Daughtry, C.S.T., White, W., Akumaga, U., Showalter, J.
- **Year:** 2024
- **Journal:** Agrosystems, Geosciences & Environment (AGSE)
- **DOI:** 10.1002/agg2.20474

### Dataset Description (from Data.gov and paper abstract)

- **Coverage:** Beltsville Agricultural Research Center (BARC), Beltsville, MD, USA
- **Coordinates:** Approximately 38.995°N, 76.937°W
- **Growing seasons:** Multi-year archive (paper reports 2015–2021;
  Ag Data Commons catalog lists files for 2014, 2016–2021)
- **Fields:** 43+ production fields with recorded boundaries
- **Spatial resolution:** 5-meter grid cells within each field
- **Crops:** Corn (grain), Soybean, Wheat, Sorghum (grain), Barley
- **Yield unit:** Typically Mg/ha or bu/ac (bushels per acre) — needs confirmation
  from actual files
- **Data types:**
  - Raw combine harvester yield monitor data (georeferenced)
  - Quality-controlled/cleaned yield data
  - Gridded yield maps (spatially interpolated)
  - Field boundary shapefiles
  - Metadata files

### Critical Caveats

1. **Gridded data are interpolated:** The 5m grid cells represent spatial
   interpolation (kriging or similar) of combine harvester point observations.
   Each grid cell must **not** be treated as an independent observation — this
   would inflate statistical degrees of freedom and produce artificially low
   uncertainty. The raw combine data contains the true independent observations.

2. **Yield units vary:** USDA/NASS commonly reports in bushels per acre (bu/ac).
   The BARC archive paper references both Mg/ha and bu/ac. Unit conversion
   traceability is required.

3. **Crop calendar dates:** Planting and harvest dates must be extracted from
   metadata or field records. The seasonal prediction pipeline requires exact
   planting and harvest dates.

4. **Single location:** All fields are within BARC, Maryland. This limits
   spatial generalization claims to the mid-Atlantic region.

### Status

| Criterion | Status |
|---|---|
| Dataset exists | **Confirmed** (DOI resolves) |
| License identified | Public Domain (US Gov) |
| Access method | Ag Data Commons download (registration may be required) |
| Yield type | Combine harvester point measurements (raw) + gridded maps |
| Spatial resolution | Field-level → 5m grid cells |
| Temporal coverage | ~2014–2021 (7 growing seasons) |
| Crops | Corn, Soybean, Wheat, Sorghum, Barley |
| Coordinates | 38.995°N, 76.937°W (Beltsville, MD) |
| **Retrieval attempted** | **Pending** |
| **Files verified** | **Pending** |

---

## Source 2: USDA NASS Quick Stats (Regional Fallback)

### URLs

- **API docs:** https://quickstats.nass.usda.gov/api/
- **Data access:** https://quickstats.nass.usda.gov/
- **General info:** https://www.nass.usda.gov/

### Dataset Description

- **Scope:** State and county-level crop statistics across the entire United States
- **Parameters available:** Yield (bushels/acre), area planted, area harvested,
  production, price
- **API key required:** Yes (free registration)
- **Crops:** Corn, Soybeans, Wheat, Cotton, Sorghum, and many others
- **Temporal coverage:** 1990s–present (varies by parameter)
- **Spatial resolution:** State, county, or national aggregate — **NOT field-level**

### Status for Field-Level Validation

| Criterion | Status |
|---|---|
| Field-level data | **No** — aggregated to state/county level |
| Coordinates | County-level, no field GPS |
| Suitable for regional validation | **Yes** — if weather data matched |
| Suitable for field-level HYRUE validation | **No** — scale mismatch |
| **Retrieval attempted** | **Pending** |

---

## Source 3: Open-Meteo Historical Weather API (Weather Inputs)

### URLs

- **Archive API:** https://open-meteo.com/en/docs/historical-weather-api
- **Base URL:** https://archive-api.open-meteo.com/v1/archive

### Dataset Description

- **Source model:** ERA5-Land (reanalysis, 0.1° × 0.1° ≈ 9km resolution)
- **Parameters available:**
  - `temperature_2m_min`, `temperature_2m_max` (°C)
  - `precipitation_sum` (mm)
  - `shortwave_radiation_sum` (MJ/m²/day)
  - ET₀ computed via Hargreaves (in pipeline)
- **Temporal coverage:** 1940–present (ERA5-Land starts ~1950)
- **API key:** None required
- **Rate limit:** No documented limit for archive API (generous)

### Status

| Criterion | Status |
|---|---|
| **Retrieval attempted** | **Yes** — tested by `weather_source.py` tests |
| Integration status | Fully implemented in `fetch_daily_weather()` |
| PAR data | Not directly available (derived via 0.5 × shortwave conversion) |
| LAI data | Not available from Open-Meteo |
| VPD | Available via hourly API (not daily) |
| Soil moisture | Available from ERA5-Land |

### Limitation for BARC Validation

Open-Meteo provides at point locations, but the spatial resolution (~9km)
may not perfectly match BARC field coordinates. NASA POWER provides
a 0.5° × 0.5° grid. Both are reanalysis products, not ground-station data.

---

## Source 4: NASA POWER (Weather Inputs / Fallback)

### URLs

- **API docs:** https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- **Base URL:** https://power.larc.nasa.gov/api/temporal/daily/point

### Dataset Description

- **Source model:** MERRA-2 reanalysis (0.5° × 0.625° ≈ 50–60km resolution)
- **Parameters available:**
  - `T2M_MIN`, `T2M_MAX` (°C)
  - `PRECTOTCORR` (mm)
  - `ALLSKY_SFC_SW_DWN` (kW-h/m² → converted to MJ/m²)
  - `ALLSKY_SFC_PAR_TOT` (MJ/m²/day) — satellite-retrieved PAR from CERES
- **Temporal coverage:** 1981–present (near real-time)
- **API key:** None required
- **Spatial resolution:** ~50km grid

### Status

| Criterion | Status |
|---|---|
| **Retrieval attempted** | **Yes** — tested by `weather_source.py` tests |
| Integration status | Fully implemented as fallback in `fetch_daily_weather()` |
| PAR data | **Yes** — `ALLSKY_SFX_PAR_TOT` (satellite-retrieved from CERES) |
| LAI data | Not available |
| VPD | Available via `RVPD` or `RH2M` (can compute VPD from RH+T) |

---

## Source 5: NASA POWER Ag (Application API — Ag-specific Reports)

### URLs

- **Ag API:** https://power.larc.nasa.gov/docs/services/api/application/

### Description

NASA POWER provides crop-specific application APIs that return ag-relevant
summaries (growing degree days, frost dates, etc.) derived from the same
MERRA-2 reanalysis data. Not a primary data source but useful for
cross-checks.

### Status

| Criterion | Status |
|---|---|
| Integration needed | Not needed — core daily parameters sufficient |

---

## Source 6: Copernicus CDS (ERA5-Land, Sentinel-2, Soil Moisture)

### URLs

- **CDS:** https://cds.climate.copernicus.eu/
- **API:** https://cds.climate.copernicus.eu/api-how-to/

### Description

- **ERA5-Land:** High-resolution (0.1°) reanalysis with soil moisture,
  2m temperature, etc.
- **Sentinel-2 LAI:** 10m resolution LAI from Copernicus Sentinel-2
  (requires ESA account and data download).
- **Soil Moisture:** ESA Climate Change Initiative soil moisture products.
- **API key:** ESA/Copernicus account required (free).

### Status

| Criterion | Status |
|---|---|
| LAI data | Available via Sentinel-2 (10m, Level-2A products) |
| Soil moisture | Available via ESA CCI or ERA5-Land |
| **Retrieval attempted** | **Not yet** |

---

## Input Data Requirements for HYRUE

Based on the `SeasonalPredictionRequest` contract and `compute_seasonal_prediction()`
pipeline:

| Input | Source | Required? | Status |
|---|---|---|---|
| Daily min/max temperature | Weather API | Required | Available (Open-Meteo/Power) |
| Daily precipitation | Weather API | Required | Available (Open-Meteo/Power) |
| Daily shortwave radiation | Weather API | Required | Available (Open-Meteo/Power) |
| PAR (photosynthetically active radiation) | Weather API or derived | Required for HYRUE | **Partial** — NASA POWER provides satellite-retrieved PAR; Open-Meteo requires 0.5× shortwave conversion |
| LAI (leaf area index) | Observation or model | Required for EWSI | **Missing** — not in weather APIs; can be derived from NDVI (Sentinel-2) or GDD model |
| EWSI inputs (NIR, SWIR, VPD, Soil Moisture) | Observation or satellite | Required for EWSI | **Partial** — VPD from RH/T, Soil Moisture from ERA5-Land, NIR/SWIR from Sentinel-2 |
| Vapour Pressure Deficit (VPD) | Observation or derived | Required for EWSI | Available from NASA POWER (`RVPD`) or computable from T/RH |
| Soil moisture | Observation or reanalysis | Required for EWSI | Available from ERA5-Land |
| Growing season dates | Site metadata | Required | Must come from yield dataset metadata |
| Site coordinates (lat/lon) | Location data | Required | Yes — BARC provides field boundaries |

### Input Provenance Classification

Each input must be traced to one of these provenance levels:

| Provenance Level | Definition | Example Source |
|---|---|---|
| `field_measured` | Instrument deployed at the site | Ground PAR sensor, lysimeter |
| `satellite_retrieved` | Satellite product | Sentinel-2 LAI, CERES PAR |
| `analysis_product` | Reanalysis/gridded product | ERA5-Land, NASA POWER |
| `estimated` | Derived via documented coefficient | PAR = 0.5 × shortwave |
| `missing` | Not available for this day | — |

**Important distinction:** Reanalysis products (Analysis) are spatially interpolated
and temporally smoothed. They are not "field measurements" in the strict sense.
For strict input policy benchmarking, reanalysis weather inputs may be acceptable
as long as they are clearly labeled `analysis_product`.

---

## Data Integration Plan

If BARC data is successfully retrieved, the integration pipeline will:

1. **Create `DatasetManifest`** with `provenance=REAL_FIELD_OBSERVATIONS`,
   publisher="USDA ARS", license_url="Public Domain"
2. **Run `run_data_quality_checks()`** on the raw yield records
3. **Verify data independence** with `check_data_independence()`
4. **Compute file hashes** with `compute_hashes()`
5. **Convert yield units** to t/ha using `convert_yield_to_t_ha()`
6. **Build `RealFieldRecord`** instances for each field observation
7. **Construct `ValidationProtocol`** with BARC as validation dataset
   (calibration_dataset_id = different source)
8. **Execute `BenchmarkSpec.check_prerequisites()`** — should return READY
9. **Run `compute_seasonal_prediction()`** for each observation
10. **Evaluate via `produce_validation_report()` and `produce_benchmark_report()`**

### Coordinate Mapping

BARC fields are at ~38.995°N, 76.937°W. The nearest Open-Meteo/NASA POWER grid
points will be used for weather extraction. Spatial representativeness error
should be documented.

### Seasonal Alignment

Each field observation has a planting date and harvest date. The seasonal
prediction request will use these exact dates. Growing season length typically
80–120 days for the BARC crops.

---

## Assessment Summary

| Source | Type | Field-Level? | Access Attempted | Integration Path |
|---|---|---|---|---|
| USDA BARC Gridded Yield | Yield observations | **Yes** (combine data) | **Pending retrieval** | Primary field-level validation |
| USDA NASS Quick Stats | Yield aggregates | No | Not yet | Regional validation fallback |
| Open-Meteo | Weather reanalysis | N/A | Tested (in code) | Weather inputs (primary) |
| NASA POWER | Weather reanalysis | N/A | Tested (in code) | Weather inputs (fallback) + satellite PAR |
| Copernicus ERA5-Land | Weather reanalysis | N/A | Not yet | EWSI inputs (soil moisture, VPD) |
| Sentinel-2 (LAI) | Satellite product | N/A | Not yet | LAI retrieval |

## Decision Points (pending data retrieval)

1. **If BARC raw combine data is accessible and structurally compatible** →
   proceed to field-level validation benchmark
2. **If only BARC gridded/interpolated maps are available** → use with caution,
   applying spatial independence corrections (effective sample size < grid cell count)
3. **If BARC is inaccessible** → evaluate NASS for regional validation path
4. **If no yield data available** → retain BLOCKED status, document specific
   limitations

### Next Action

Attempt to retrieve the BARC dataset files from Ag Data Commons to verify
actual structure, format, and compatibility with the HYRUE evaluation pipeline.
