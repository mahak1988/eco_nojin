# Stage 35 — Weather Ingestion

## Pipeline

`engine/hydroma/simulation/weather_source.py::fetch_daily_weather()`

### Request Parameters

```
latitude: float          Site latitude (WGS84)
longitude: float         Site longitude (WGS84)
start_date: str          ISO YYYY-MM-DD
end_date: str            ISO YYYY-MM-DD
daily: str               Comma-separated daily variables
hourly: str              Comma-separated hourly variables (VPD)
timezone: str            UTC
```

### Daily Variables (Open-Meteo archive)

`temperature_2m_min, temperature_2m_max, precipitation_sum, shortwave_radiation_sum, dew_point_2m_mean, relative_humidity_2m_mean, soil_moisture_0_to_7cm_mean, soil_moisture_7_to_28cm_mean, soil_moisture_28_to_100cm_mean`

### Hourly Variables (Open-Meteo archive)

`vapour_pressure_deficit` — aggregated to daily mean per date

### Reliability Features

| Feature | Implementation |
|---|---|
| Timeout | `REQUEST_TIMEOUT = (10.0, 60.0)` (connect, read) |
| Retry with backoff | `RetryConfig` — max 3 retries, exponential backoff, base 1s, max 30s |
| Rate limiting | `RateLimiter` — 60 requests/minute token bucket |
| Cache | `WeatherCache` — in-memory, 1-hour TTL, keyed by URL+params |
| HTTP validation | `WeatherUnavailable` on non-200 status |
| Fallback chain | Open-Meteo → NASA POWER → CHIRPS/NCEP |

### Output Columns (DataFrame)

MinTemp, MaxTemp, Precipitation, ReferenceET, Date, ShortwaveRadiation, PAR, DewPoint, RelativeHumidity, VapourPressureDeficit, SoilMoisture_0_7cm, SoilMoisture_7_28cm, SoilMoisture_28_100cm

### DataFrame Attributes (Provenance)

shortwave_unit, shortwave_source, par_unit, par_source, dewpoint_unit, dewpoint_source, relative_humidity_unit, relative_humidity_source, vpd_unit, vpd_source, soil_moisture_*_unit, soil_moisture_*_source

### Verified Output (Buxar, 2016-11-01 to 2017-04-21)

- 172 days of data
- VPD: 172/172 non-null, kPa, source: "Open-Meteo ERA5 (hourly aggregated)"
- Soil moisture 0-7cm: 172/172 non-null, m³/m³, source: "Open-Meteo ERA5"
- Dew point: 172/172 non-null, °C
- Relative humidity: 172/172 non-null, %

## Files

- `engine/hydroma/simulation/weather_source.py`
