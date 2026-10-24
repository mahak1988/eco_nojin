# Stage 35 — EWSI Pilot

## Pilot Design

Single representative record from CIMMYT dataset:
- **Field:** field_1, District: Buxar, Year: 2016-17
- **Coordinates:** 26.33°N, 83.54°E
- **Season:** 2016-11-01 to 2017-04-21 (172 days)
- **Observed yield:** 6.68 t/ha

## Pipeline Results

### Step 1: Weather (Open-Meteo ERA5)
✅ 172 days of real data
- VPD: 172/172 non-null (kPa, hourly aggregated)
- Dew point: 172/172 non-null (°C)
- Soil moisture 0-7cm: 172/172 non-null (m³/m³)
- Soil moisture 7-28cm: 172/172 non-null (m³/m³)
- Soil moisture 28-100cm: 172/172 non-null (m³/m³)

### Step 2: Satellite (Planetary Computer Sentinel-2 L2A)
✅ 7 cloud-free acquisitions
- B8A (NIR) and B11 (SWIR) sampled at point
- SCL cloud masking applied
- CRS transform WGS84 → EPSG:32644

### Step 3: EWSI Computation (STRICT policy)
✅ All 3 components present
- NDMI stress: from real Sentinel-2 reflectance
- VPD stress: from real Open-Meteo vapour pressure deficit
- Soil stress: from real Open-Meteo soil moisture (0-7cm layer)
- EWSI mean: **0.4592**
- Missing fields: **none**
- Weights: ndmi=0.4, vpd=0.3, soil=0.3 (project defaults, uncalibrated)

### Step 4: HYRUE Seasonal Computation
✅ HYRUE v2.0.0 with real EWSI
- PAR: from Open-Meteo shortwave radiation
- LAI: default 3.0 m²/m² (wheat typical, not calibrated)
- T_mean: from Open-Meteo temperature
- EWSI: real computed value
- **Predicted yield: 10.899 t/ha**
- **Observed yield: 6.680 t/ha**
- **Error: +4.219 t/ha (+63%)**

### Error Analysis (Expected)

The high prediction error is expected because:
1. LAI fixed at 3.0 (not calibrated to crop stage)
2. EWSI weights (0.4/0.3/0.3) are uncalibrated project defaults
3. No model parameters tuned on test data (per Stage 35 rule #6)
4. Single point sample vs. field-average yield

This is NOT a model failure — it demonstrates the pipeline works with real data. Calibration would require development-set data (not test data).

## Acceptance Gates

| Gate | Criterion | Status |
|---|---|---|
| A | Real weather data received | ✅ PASS |
| B | VPD from real source or computed from real inputs | ✅ PASS |
| C | Soil moisture with valid provenance | ✅ PASS |
| D | At least one satellite source returned NIR/SWIR | ✅ PASS |
| E | NDMI from valid reflectance | ✅ PASS |
| F | Date and coordinates recorded | ✅ PASS |
| G | EWSI from real or documented estimated inputs | ✅ PASS |
| H | No synthetic inputs in results | ✅ PASS |
| I | API errors and failed records reported | ✅ PASS |
| J | Data quality and spatial limitations documented | ✅ PASS |

**Pilot result: PASSED**

## Files

- `engine/reports/data/stage35_pilot_single.json` — pilot result JSON
