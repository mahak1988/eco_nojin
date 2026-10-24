# Stage 34 — Benchmark Readiness

## Current Benchmark Status: PARTIALLY_EVALUATED

The HYRUE benchmark cannot transition to COMPLETED or VALIDATED_EXTERNAL
because real EWSI inputs (NIR/SWIR reflectance, VPD, soil moisture) are
not available from any configured data source.

## What Works

| Component | Status | Data Source |
|---|---|---|
| Weather (Tmin/Tmax/precip/shortwave) | Available | Open-Meteo ERA5-Land, NASA POWER |
| PAR (direct or converted) | Available | NASA POWER ALLSKY_SFC_PAR_TOT or shortwave × 0.5 |
| LAI (observed/NDVI/GDD) | Available | User-provided, NDVI empirical, GDD model |
| EWSI (NDMI+VPD+soil) | **NOT AVAILABLE** | Requires Sentinel-2/Copernicus + ERA5-Land |
| CIMMYT yield observations | Available | 5,689 records, 10 districts, 6 seasons |
| Spatial split protocol | Available | 3 test / 7 dev districts |
| Leakage audit | CLEAN | No site/field/season overlap |

## What's Blocked

**EWSI input pipeline** — HYRUE seasonal mode requires daily EWSI inputs.
The following are not available:

1. **Sentinel-2 L2A NIR/SWIR** — Requires Copernicus Data Space Ecosystem
   API access (no credentials configured). `Sentinel2Source.fetch_reflectance()`
   raises `NotImplementedError`.

2. **Landsat C2L2 NIR/SWIR** — Requires USGS EarthExplorer or AWS Open Data
   access. `LandsatC2L2Source.fetch_reflectance()` raises `NotImplementedError`.

3. **VPD from dewpoint/RH** — Open-Meteo and NASA POWER provide Tmin/Tmax
   but not dewpoint or RH. VPD cannot be computed without moisture data.

4. **Soil moisture** — ERA5-Land soil water layers require Copernicus CDS
   account (not configured).

## Path to COMPLETED

To transition from PARTIALLY_EVALUATED to COMPLETED:

1. Configure Copernicus Data Space Ecosystem API credentials
2. Implement `Sentinel2Source.fetch_reflectance()` or
   `LandsatC2L2Source.fetch_reflectance()`
3. Add VPD computation (requires dewpoint or RH data source)
4. Add soil moisture from ERA5-Land (requires Copernicus CDS)
5. Run CIMMYT integration with real EWSI inputs on all 5,689 records
6. Compute validation metrics (RMSE, MAE, bias, R², MAPE)
7. Transition benchmark status to COMPLETED, then VALIDATED_EXTERNAL
   only with independent scientific evidence

## Files

- `engine/reports/STAGE-34-CODE-AUDIT.md`
- `engine/reports/STAGE-34-EWSI-SCIENTIFIC-METHOD.md`
- `engine/reports/STAGE-34-REMOTE-SENSING-QUALITY.md`
- `engine/reports/STAGE-34-VPD-SOIL-MOISTURE.md`
- `engine/reports/STAGE-34-HYRUE-INTEGRATION.md`
- `engine/reports/STAGE-34-TEST-RESULTS.md`
- `engine/reports/STAGE-34-LIMITATIONS.md`
- `tools/stage34_cimmyt_integration.py`
