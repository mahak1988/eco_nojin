# Stage 34 Code Audit — Stage 35 Input

## A. Source Classes Actually Implemented

| Class | File | fetch_reflectance / compute | Status |
|---|---|---|---|
| `Sentinel2Source` | satellite_source.py:159 | `fetch_reflectance()` | **NotImplementedError** |
| `LandsatC2L2Source` | satellite_source.py:198 | `fetch_reflectance()` | **NotImplementedError** |
| `SatelliteSource` | satellite_source.py:126 | abstract base | Abstract (not instantiable) |
| `VPD model` | vpd_model.py | `compute_daily_vpd()` | **Implemented** |
| `Soil moisture model` | soil_moisture_model.py | `compute_daily_soil_stress()` | **Implemented** |
| `Weather source` | weather_source.py | `fetch_daily_weather()` | **Implemented** |
| `EWSI pipeline` | ewsi_pipeline.py | `compute_daily_ewsi()` | **Implemented** |

## B. Methods With NotImplementedError

- `Sentinel2Source.fetch_reflectance()` (satellite_source.py:191)
- `LandsatC2L2Source.fetch_reflectance()` (satellite_source.py:230)

## C. Methods That Only Accept Test Data

- `generate_synthetic_weather()` (seasonal_predictor.py:984) — labeled `synthetic_test_data`, must never be used for scientific predictions
- `SatelliteCache.put()/get()` — stores/loads ReflectanceTimeSeries; accepts any serializable data (test fixtures included)

## D. APIs Actually Callable

| API | Endpoint | Key Required | Status |
|---|---|---|---|
| Open-Meteo ERA5 archive | archive-api.open-meteo.com/v1/archive | No | **Callable** |
| NASA POWER | power.larc.nasa.gov/api/temporal/daily/point | No | **Callable** |

## E. Variables from Actual Sources

| Variable | Source | Unit | Provenance |
|---|---|---|---|
| Tmin | Open-Meteo / NASA POWER | °C | reanalysis_estimate |
| Tmax | Open-Meteo / NASA POWER | °C | reanalysis_estimate |
| Precipitation | Open-Meteo / NASA POWER | mm/day | reanalysis_estimate |
| Shortwave radiation | Open-Meteo / NASA POWER | MJ/m²/day | reanalysis_estimate |
| PAR | NASA POWER ALLSKY_SFC_PAR_TOT or shortwave×0.5 | MJ/m²/day | satellite_retrieved / estimated |

## F. Variables Only From Synthetic Data

| Variable | Status |
|---|---|
| NIR reflectance | Not available — satellite fetch raises NotImplementedError |
| SWIR reflectance | Not available — satellite fetch raises NotImplementedError |
| VPD | Not available — Open-Meteo/NASA POWER don't provide dewpoint/RH in current fetch |
| Soil moisture | Not available — requires ERA5-Land / Copernicus SWI |
| EWSI composite | Only from user-provided arrays (no real source) |

## G. Tests That Are Mock-Only

Stage 34 tests (`test_stage34_ewsi_pipeline.py`) use synthetic EWSI inputs (numpy arrays) to verify pipeline structure. No tests call real satellite or weather APIs.

## H. Cache Distinguishes Real From Mock

**No.** `WeatherCache` stores JSON responses keyed by URL+params. No flag distinguishes real API responses from mock/synthetic data. `SatelliteCache` similarly stores any ReflectanceTimeSeries.

## I. Provenance Preserved to Final HYRUE Output

**Yes.** Through `SeasonalClimateInputs` → `compute_hyrue_seasonal()` → `PredictionResult` → `OperationalReport`. EWSI component provenance, weights, missing fields, and computation policy all flow through.

## J. Benchmark Can Mistake Synthetic for Real

**No.** `check_no_synthetic_label()` (dataset_manifest.py:502) and `RealFieldRecord.reject_synthetic_label()` (field_validation.py:186) reject records labeled "synthetic*". The `data_label` starting with "synthetic" is a hard rejection gate.

---

## Discrepancies vs Stage 34 Plan

The Stage 34 plan assumed Copernicus / USGS access would be configured. **No credentials exist.** Both satellite sources raise NotImplementedError. Open-Meteo was only verified for Tmin/Tmax/precip/shortwave — NOT for dewpoint, RH, VPD, or soil moisture.

## Immediate Next Step (Part 2)

Test Open-Meteo Historical API for the additional variables needed for EWSI:
- `dew_point_2m`, `relative_humidity_2m`, `vapour_pressure_deficit`
- `soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm`, `soil_moisture_28_to_100cm`

Verify which variables actually return data for CIMMYT coordinates before extending weather_source.py.
