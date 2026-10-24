# Stage 35 — Data Coverage

## CIMMYT Dataset Coverage

| Metric | Value |
|---|---|
| Total records | 5,689 |
| Districts | 10 (EastChamparan, Buxar, Deoria, Bhojpur, Rohtas, Madhepura, Kushinagar, Muzaffarpur, Begusarai, Lakhisarai) |
| Years/Seasons | 6 (2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22) |
| Crop | Wheat (Rabi) |
| Region | Bihar and Eastern Uttar Pradesh, India |
| Yield unit | t/ha |
| Yield range | Valid GrainYield for all records |

### District Record Counts

| District | Records |
|---|---|
| EastChamparan | 825 |
| Buxar | 709 |
| Deoria | 669 |
| Bhojpur | 632 |
| Rohtas | 586 |
| Madhepura | 558 |
| Kushinagar | 556 |
| Muzaffarpur | 427 |
| Begusarai | 380 |
| Lakhisarai | 347 |

## Weather Data Coverage (Open-Meteo ERA5)

Verified for Buxar coordinates (26.33, 83.54), 2016-11-01 to 2017-04-21:

| Variable | Days Available | Coverage |
|---|---|---|
| Tmin/Tmax | 172/172 | 100% |
| Precipitation | 172/172 | 100% |
| Shortwave radiation | 172/172 | 100% |
| Dew point | 172/172 | 100% |
| Relative humidity | 172/172 | 100% |
| VPD (hourly aggregated) | 172/172 | 100% |
| Soil moisture 0-7cm | 172/172 | 100% |
| Soil moisture 7-28cm | 172/172 | 100% |
| Soil moisture 28-100cm | 172/172 | 100% |

## Satellite Data Coverage (Sentinel-2 L2A)

Verified for Buxar coordinates, 2016-11-01 to 2017-04-21:

| Metric | Value |
|---|---|
| Cloud-free acquisitions | 7 |
| Date range covered | 2016-11 to 2017-04 |
| Cloud cover threshold | < 20% |
| Bands retrieved | B8A, B11, SCL |
| Spatial resolution | 20 m |
| Temporal gaps | Expected (5-day revisit + clouds) |

## Coverage Limitations

1. **Satellite temporal gaps** — Sentinel-2 5-day revisit with cloud cover creates gaps. Interpolation used to fill missing dates (flagged as INTERPOLATED).
2. **Point vs. field** — CIMMYT coordinates are approximate (~1 km resolution). Point sampling does not represent field-average reflectance.
3. **Weather spatial resolution** — ERA5-Land ~9 km grid, not field-specific.
4. **Season coverage** — Only verified for one season (2016-17, Buxar). Other seasons/districts not yet tested.

## Files

- `engine/reports/data/stage35_pilot_single.json`
