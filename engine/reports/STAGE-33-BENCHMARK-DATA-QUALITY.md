# Stage 33: Data Quality Report

## A. GrainYield Audit

| Property | Value |
|---|---|
| Column | GrainYield |
| Unit | t/ha |
| Measurement method | Mean yield from three crop-cut spots (plot basis, harvest) |
| Total records | 5689 |
| Valid count | 5689 |
| Missing count | 0 |
| Negative count | 0 |
| Zero count | 0 |
| Non-finite count | 0 |
| Min | 1.39 |
| Max | 6.955 |
| Mean | 4.144759580246569 |
| Median | 4.19 |
| Std | 1.0369771146637283 |

### Yield Groups

| Group | Count | Description |
|---|---|---|
| Valid (usable) | 5600 | Values within expected wheat yield range [2.0, 6.5] t/ha |
| Requires review | 0 | IQR outliers (fences: [0.97, 7.26]); includes low-yield (<2.0) and high-yield (>6.5) records |
| Unusable | 0 | Negative, missing, or zero values |

**Records removed:** 0 (None — all records have valid GrainYield in t/ha, non-negative and finite)

All 5,689 records have valid GrainYield values (non-negative, finite, t/ha).
No records were removed. The IQR outlier range is [0.975, 7.255]
t/ha, flagged as "requires review" but retained for analysis.

## B. Spatial Independence Audit

| Property | Value |
|---|---|
| Unique Field_IDs | 5689 |
| Field_ID duplicates | 0 |
| Unique lat/lon pairs | 714 |
| Max fields per coordinate | 157 |
| Coordinate precision | 2 decimal places (coarse, ~1km resolution) |
| Spatial independence groups (districts) | 10 |
| Temporal independence groups (seasons) | 6 |

**Spatial anonymity:** 714 unique (lat, lon) pairs cover 5689 fields; up to 157 fields share the same coordinates. Coordinates are aggregated to village/representative points, not exact field boundaries. Sufficient for weather API extraction.

### Districts

| District | Records |
|---|---|
| Begusarai | 380 |
| Bhojpur | 632 |
| Buxar | 709 |
| Deoria | 669 |
| EastChamparan | 825 |
| Kushinagar | 556 |
| Lakhisarai | 347 |
| Madhepura | 558 |
| Muzaffarpur | 427 |
| Rohtas | 586 |

### Seasons

| Season | Records |
|---|---|
| 2016-17 | 777 |
| 2017-18 | 1313 |
| 2018-19 | 1403 |
| 2019-20 | 1318 |
| 2020-21 | 725 |
| 2021-22 | 153 |

### Data Leakage: District-Season Pairs

- Duplicate (District, Year) pairs: 5630
- Note: This is expected — multiple fields exist per district per season.
  The correct site-level identifier is `Field_ID` (5,689 unique), not `District`.

## C. Weather Data Audit

| Property | Value |
|---|---|
| Weather resolution in file | monthly_summary — NOT daily |
| Usable for HYRUE | False |
| Reason | HYRUE requires daily Tmin/Tmax, daily shortwave/PAR, daily LAI, daily EWSI. Monthly averages lack intra-month variability needed for thermal stress and PAR integration. |
| PAR derivable | True |
| PAR method | PAR = 0.5 * shortwave (Monteith & Unsworth 2013), status: estimated; OR direct from NASA POWER ALLSKY_SFX_PAR_TOT (CERES SYN1deg), status: satellite_retrieved |
| Daily weather source | Open-Meteo ERA5-Land archive (primary) or NASA POWER MERRA-2 (fallback) |
| Daily weather requires | Coordinates + growing season dates (both available in CIMMYT dataset) |

### Missing Weather Values in File

| Column | Missing Count |
|---|---|
| Prcp_Monsoon | 19 |
| Prcp_Oct | 0 |
| Nov_Tmax | 0 |
| Dec_Tmax | 0 |
| Mar_Tmax | 0 |
| Apr_Tmax | 0 |
| Jan_Srad | 19 |
| Feb_Srad | 19 |
| EDD_Nov | 0 |
| EDD_Dec | 0 |
| EDD_Mar | 0 |
| EDD_Apr | 0 |

## D. Weather Data Missing in CIMMYT File (19 records)

19 records have missing values in `Prcp_Monsoon`, `Jan_Srad`, and `Feb_Srad`.
These are correlated (likely the same 19 records from a specific district/season).
These records are still retained — weather data will be fetched from the API
during prediction execution.

## E. Quality Gate Results

All 5,689 records pass structural validation (pydantic constraints):
- GrainYield is non-negative, finite, in t/ha ✓
- SowingDate and HarvestDate are valid, harvest >= sowing ✓
- Latitude in [-90, 90], Longitude in [-180, 90] ✓
- data_label = "real_field_data" (not synthetic) ✓

All records are flagged `REQUIRES_REVIEW` due to missing optional metadata
(`area_ha`, `harvest_sample_size`), not structural data quality issues.
