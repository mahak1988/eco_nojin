# Stage 34 — Data Source Audit

## Available Data Sources

### Weather

| Source | Parameters | Access | Cost | Status |
|---|---|---|---|---|
| Open-Meteo ERA5-Land | Tmin, Tmax, precip, shortwave | No API key | Free | Available (verified) |
| NASA POWER MERRA-2 | Tmin, Tmax, precip, shortwave, PAR | No API key | Free | Available (verified) |
| CHIRPS/NCEP | Precip, temperature | Via pipeline | Free | Not implemented |

### Satellite Reflectance (NOT AVAILABLE)

| Source | Parameters | Access | Cost | Status |
|---|---|---|---|---|
| Copernicus Data Space Ecosystem | Sentinel-2 L2A NIR/SWIR | API key required | Free | Not configured |
| USGS EarthExplorer | Landsat C2L2 NIR/SWIR | API key required | Free | Not configured |
| AWS Open Data | Landsat C2L2 NIR/SWIR | No key (requester pays) | Free tier | Not configured |

### Soil Moisture (NOT AVAILABLE)

| Source | Parameters | Access | Cost | Status |
|---|---|---|---|---|
| Copernicus CDS ERA5-Land | Soil water layers | Account required | Free | Not configured |
| Copernicus SWI | Soil Water Index | Account required | Free | Not configured |

## What's Missing for EWSI

1. NIR/SWIR reflectance — requires satellite API access
2. VPD — requires dewpoint or RH (not in Open-Meteo/NASA POWER)
3. Soil moisture — requires ERA5-Land or Copernicus SWI

## CIMMYT Dataset

- File: `data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx`
- SHA-256: `919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde`
- Records: 5,689
- Districts: 10 (Buxar, Muzaffarpur, Rohtas, Deoria, Lakhisarai, Begusarai, EastChamparan, +3 more)
- Seasons: 2016-17 to 2021-22 (6 seasons)
- Crop: Wheat (Rabi)
- Region: Bihar and Eastern Uttar Pradesh, India

## Recommendation

Configure Copernicus Data Space Ecosystem access and implement
Sentinel-2 L2A reflectance fetching to unblock real EWSI computation.
