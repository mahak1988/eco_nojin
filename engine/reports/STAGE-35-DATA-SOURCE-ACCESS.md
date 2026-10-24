# Stage 35 — Data Source Access

## Summary

Real data access verified for EWSI computation. Two sources are operational:

### 1. Open-Meteo Historical Weather API (PRIMARY — WORKING)

Endpoint: `https://archive-api.open-meteo.com/v1/archive`

**Verified variables (hourly + daily, all returning real data for CIMMYT coordinates):**

| Variable | Unit | Source | Status |
|---|---|---|---|
| temperature_2m_max/min | °C | ERA5-Land | ✅ Working |
| precipitation_sum | mm/day | ERA5-Land | ✅ Working |
| shortwave_radiation_sum | MJ/m²/day | ERA5-Land | ✅ Working |
| dew_point_2m_mean | °C | ERA5-Land | ✅ Working (daily) |
| relative_humidity_2m_mean | % | ERA5-Land | ✅ Working (daily) |
| vapour_pressure_deficit | kPa | ERA5-Land | ✅ Working (hourly, aggregated to daily) |
| soil_moisture_0_to_7cm_mean | m³/m³ | ERA5-Land | ✅ Working |
| soil_moisture_7_to_28cm_mean | m³/m³ | ERA5-Land | ✅ Working |
| soil_moisture_28_to_100cm_mean | m³/m³ | ERA5-Land | ✅ Working |

**Implementation:** `engine/hydroma/simulation/weather_source.py::_fetch_open_meteo()`
- Daily variables fetched in one request
- Hourly VPD fetched separately and aggregated to daily mean
- Retry with exponential backoff, rate limiting, in-memory cache
- Full provenance metadata per variable

### 2. Microsoft Planetary Computer STAC (PRIMARY — WORKING)

Endpoint: `https://planetarycomputer.microsoft.com/api/stac/v1`

**Verified collections:**

| Collection | Bands | Resolution | Status |
|---|---|---|---|
| sentinel-2-l2a | B8A (NIR), B11 (SWIR), SCL (cloud mask) | 20 m | ✅ Working |
| landsat-c2-l2 | B5 (NIR), B6 (SWIR) | 30 m | ⚠️ Collection exists, assets need verification |

**Implementation:** `engine/hydroma/simulation/remote_sensing/satellite_source.py`
- `Sentinel2Source.fetch_reflectance()` — queries STAC, signs URLs via planetary-computer package, samples NIR/SWIR at point using rasterio
- `LandsatC2L2Source.fetch_reflectance()` — same pattern for Landsat
- Cloud masking via SCL band values {3, 8, 9, 10, 11}
- CRS transformation (WGS84 → UTM) for correct point sampling
- Disk cache via `SatelliteCache`

### Access Summary

| Source | API Key Required | Credentials Configured | Real Data Verified |
|---|---|---|---|
| Open-Meteo | No | N/A | ✅ Yes |
| Planetary Computer | No | N/A | ✅ Yes |

No API keys or tokens stored in code, reports, or git.
