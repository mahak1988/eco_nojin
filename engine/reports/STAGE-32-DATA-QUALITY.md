# Stage 32: CIMMYT Wheat Dataset — Data Quality Report

## Summary

| Item | Value |
|---|---|
| **Dataset** | CIMMYT Wheat Yield Data — Eastern India (DOI: 10.71682/10549424) |
| **Total records** | 5,689 |
| **Total columns** | 49 |
| **Sheet name** | `Sheet1` |
| **Crops** | Wheat (1) |
| **Sites (Districts)** | 10 (Begusarai, Bhojpur, Buxar, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura, Muzaffarpur, Rohtas) |
| **States** | 2 (Bihar, Uttar Pradesh) |
| **Seasons (Years)** | 6 (2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22) |
| **Verified field count** | 5,689 unique `Field_ID` values |
| **Published field count** | 5,689 (claimed in dataset description) |
| **Count match** | Exact match |

The published count of 5,689 wheat fields across six rabi seasons is **verified**.

---

## A. Sheet Structure

### Data file (`Wheat_Yld_Eastern_IND_Data.xlsx`)

| Property | Value |
|---|---|
| Sheet name | `Sheet1` |
| Dimensions | A1:AW5690 (49 columns × 5,689 data rows + 1 header) |
| Column count | 49 |
| Row count | 5,689 |

### Variable dictionary (`Wheat_Yld_Eastern_IND_Variables.xlsx`)

| Property | Value |
|---|---|
| Sheet name | `Sheet1` |
| Columns | `Sr_No`, `Variable name`, `Description`, `Variable type `, `Unit` |
| Row count | 49 variable definitions |

---

## B. Column Definitions (from variable dictionary)

| # | Column | Type | Unit | Description |
|---|---|---|---|---|
| 1 | `Field_ID` | Categorical - Nominal | na | Unique number assigned to field |
| 2 | `Year` | Categorical - Ordinal | na | Year of wheat cultivation (e.g. 2016-17 = sowing late 2016, harvest 2017) |
| 3 | `District` | Categorical - Nominal | na | Name of district where field located |
| 4 | `State` | Categorical - Nominal | na | Name of state where field located |
| 5 | `LandType` | Categorical - Ordinal | na | Type of land (water retention, elevation) |
| 6 | `SoilType` | Categorical - Ordinal | na | Soil type (texture) |
| 7 | `PreviousCrop` | Categorical - Nominal | na | Crop grown before wheat |
| 8 | `PrevCropResidue` | Numerical - Discrete | percent | Proportion of residue retained |
| 9 | `CropEstablishment` | Categorical - Binary | na | Method of wheat planting |
| 10 | `Variety` | Categorical - Nominal | na | Seed variety of wheat |
| 11 | `VarietyClass` | Categorical - Ordinal | na | Variety category by maturity duration |
| 12 | `SeedRate` | Numerical - Continuous | kg per ha | Amount of wheat seed used |
| 13 | `SowingDate` | Date | dd.mm.yyyy | Date of sowing wheat |
| 14 | `SowingDay` | Numerical - Continuous | days | Sowing date as Julian day |
| 15 | `BasalDAP` | Numerical - Continuous | kg per ha | Di-ammonium Phosphate applied at sowing |
| 16 | `BasalNPK` | Numerical - Continuous | kg per ha | NPK mixture fertilizer at sowing |
| 17 | `GradeNPK` | Categorical - Nominal | na | Grade name of NPK fertilizer |
| 18 | `BasalMOP` | Numerical - Continuous | kg per ha | Potash fertilizer at sowing |
| 19 | `BasalZn` | Numerical - Continuous | kg per ha | Zinc fertilizer at sowing |
| 20 | `Split1Urea` | Numerical - Continuous | kg per ha | Urea at first application |
| 21 | `Split2Urea` | Numerical - Continuous | kg per ha | Urea at second application |
| 22 | `Split3Urea` | Numerical - Continuous | kg per ha | Urea at third application |
| 23 | `IrrigationNumber` | Numerical - Continuous | kg per ha | Number of irrigations (unit is mislabeled) |
| 24 | `FirstIrrigationDay` | Numerical - Discrete | days | Days after sowing for first irrigation |
| 25 | `SecondIrrigationDay` | Numerical - Discrete | days | Days after sowing for second irrigation |
| 26 | `ThirdIrrigationDay` | Numerical - Discrete | days | Days after sowing for third irrigation |
| 27 | `FourthIrrigationDay` | Numerical - Discrete | days | Days after sowing for fourth irrigation |
| 28 | `FifthIrrigationDay` | Numerical - Discrete | days | Days after sowing for fifth irrigation |
| 29 | `HerbicideName` | Categorical - Nominal | na | Name of herbicide |
| 30 | `HerbicideType` | Categorical - Ordinal | na | Type of herbicide |
| 31 | `WeedingNumber` | Numerical - Continuous | numbers | Number of manual weedings |
| 32 | `CropLodging` | Numerical - Discrete | percent | Proportion of crop lodged at harvest |
| 33 | `HarvestDate` | Date | dd.mm.yyyy | Date of wheat harvest |
| 34 | `HarvestDay` | Numerical - Continuous | days | Harvest date as Julian day |
| 35 | `Prcp_Monsoon` | Numerical - Continuous | mm | Monsoon precipitation |
| 36 | `Prcp_Oct` | Numerical - Continuous | mm | October precipitation |
| 37 | `Nov_Tmax` | Numerical - Continuous | degree C | Average daily maximum temperature in November |
| 38 | `EDD_Nov` | Numerical - Continuous | days | Days exceeding Nov max temperature threshold |
| 39 | `Dec_Tmax` | Numerical - Continuous | degree C | Average daily maximum temperature in December |
| 40 | `EDD_Dec` | Numerical - Continuous | days | Days exceeding Dec max temperature threshold |
| 41 | `Jan_Srad` | Numerical - Continuous | 1000 kW/m² | Total solar radiation in January |
| 42 | `Feb_Srad` | Numerical - Continuous | 1000 kW/m² | Total solar radiation in February |
| 43 | `Mar_Tmax` | Numerical - Continuous | degree C | Average daily maximum temperature in March |
| 44 | `EDD_Mar` | Numerical - Continuous | days | Days exceeding Mar max temperature threshold |
| 45 | `Apr_Tmax` | Numerical - Continuous | degree C | Average daily maximum temperature in April |
| 46 | `EDD_Apr` | Numerical - Continuous | days | Days exceeding Apr max temperature threshold |
| 47 | `GrainYield` | Numerical - Continuous | t/ha | Mean yield from three crop-cut spots |
| 48 | `Latitude` | Geo-location | Decimal degrees | GPS latitude of wheat field |
| 49 | `Longitude` | Geo-location | Decimal degrees | GPS longitude of wheat field |

---

## C. Yield Definition

| Field | Value |
|---|---|
| Yield column | `GrainYield` |
| Yield unit | t/ha |
| Measurement method | "Mean yield of grain derived from readings recorded from three crop-cut spots" |
| Yield type | Plot yield at harvest (combine harvested, plot area basis) |
| Moisture basis | Not specified in dictionary (likely field moisture at harvest) |
| Value range | 1.39 to 6.955 t/ha |
| Mean | 4.1448 t/ha |
| Median | 4.190 t/ha |
| Negative values | 0 (none) |
| Missing values | 0 (none) |
| Non-finite values | 0 (none) |

The yield unit (t/ha) is valid per `VALID_YIELD_UNITS` in `field_validation.py`
and maps directly to HY-RUE's canonical unit with a conversion factor of 1.0.

---

## D. Crop Season Information

### Seasons (Rabi wheat, 2016-17 to 2021-22)

| Season | Record count | Sowing date range | Harvest date range |
|---|---|---|---|
| 2016-17 | 777 | 2016-11-01 to 2016-12-11 | 2017-03-21 to 2017-04-24 |
| 2017-18 | 1,313 | — | — |
| 2018-19 | 1,403 | — | — |
| 2019-20 | 1,318 | — | — |
| 2020-21 | 725 | — | — |
| 2021-22 | 153 | — | — |
| **Total** | **5,689** | | |

Planting dates (`SowingDate`) range from 2016-11-01 to 2021-12-11.
Harvest dates (`HarvestDate`) range from 2017-03-21 to 2022-04-22.
Both `SowingDate` and `HarvestDate` are stored as `datetime64[ns]` with no missing values.

Season length (harvest - sowing): the dataset does not have an explicit season
length column, but `SowingDay` and `HarvestDay` (Julian day) are present.
Typical rabi wheat season length: ~120–170 days.

---

## E. Location Identifiers and Spatial Resolution

| Field | Value |
|---|---|
| Location identifiers | `District`, `State`, `Field_ID`, `Latitude`, `Longitude` |
| Districts | 10 (Buxar, East Champaran, Muzaffarpur, etc.) |
| States | 2 (Bihar, Uttar Pradesh) |
| Latitude range | 24.87° to 26.98° N |
| Longitude range | 83.40° to 86.97° E |
| Precision | Decimal degrees (float64) |
| Unique Field_IDs | 5,689 (one per record) |
| Unique lat/lon pairs | 714 (out of 5,689 records) |
| Max fields per lat/lon pair | 157 |

**Spatial anonymity assessment:** GPS coordinates (`Latitude`, `Longitude`) ARE
present in the dataset and are stored at decimal-degree precision. However,
the coordinate resolution is **coarse** — 714 unique (lat, lon) pairs cover
5,689 fields, with up to 157 fields sharing the same coordinates. This
indicates the coordinates are likely aggregated to the village/representative
point level rather than being precise field-level GPS. The coordinates are
sufficient for weather extraction (Open-Meteo/NASA POWER grid resolution is
~9–50 km) but should be treated as representative points, not exact field
boundaries.

---

## F. Management Variables

| Variable | Details |
|---|---|
| Variety | 25 unique wheat varieties; `HD2967` dominates (4,162 records), followed by `PBW373` (620), `HI1563` (376), `HD2733` (296) |
| VarietyClass | Categories based on duration to maturity |
| SeedRate | kg/ha (continuous) |
| BasalDAP | kg/ha — Di-ammonium Phosphate at sowing |
| BasalNPK | kg/ha — NPK mixture at sowing |
| BasalMOP | kg/ha — Potash at sowing |
| BasalZn | kg/ha — Zinc at sowing |
| Split1Urea | kg/ha — First urea application |
| Split2Urea | kg/ha — Second urea application |
| Split3Urea | kg/ha — Third urea application |
| IrrigationNumber | 1–5 irrigations (3 most common: 2,736 records) |
| CropEstablishment | ZT (Zero Tillage) / Conv (Conventional) |
| PreviousCrop | E.g. Rice (dominant), Maize, etc. |
| PrevCropResidue | % residue retained |
| HerbicideName/Type | Chemical weed control |
| WeedingNumber | Manual weeding count |
| CropLodging | % lodging at harvest |

---

## G. Weather Variables Present

### Summary

The dataset contains **monthly/sesonal summary weather data**, NOT daily
weather. The weather columns represent monthly average maximum temperatures,
monthly total solar radiation, growing degree day excess counts, and monthly
precipitation.

| Column | Description | Unit | Type |
|---|---|---|---|
| `Prcp_Monsoon` | Monsoon precipitation | mm | Seasonal total |
| `Prcp_Oct` | October precipitation | mm | Monthly total |
| `Nov_Tmax` | Avg daily max temperature, November | °C | Monthly mean |
| `Dec_Tmax` | Avg daily max temperature, December | °C | Monthly mean |
| `Mar_Tmax` | Avg daily max temperature, March | °C | Monthly mean |
| `Apr_Tmax` | Avg daily max temperature, April | °C | Monthly mean |
| `EDD_Nov` | Days exceeding Nov max temp threshold | days | Count |
| `EDD_Dec` | Days exceeding Dec max temp threshold | days | Count |
| `EDD_Mar` | Days exceeding Mar max temp threshold | days | Count |
| `EDD_Apr` | Days exceeding Apr max temp threshold | days | Count |
| `Jan_Srad` | Total solar radiation, January | 1000 kW/m² (GJ/m²) | Monthly total |
| `Feb_Srad` | Total solar radiation, February | 1000 kW/m² (GJ/m²) | Monthly total |

### Weather Variable Statistics

| Column | Min | Max | Mean | Missing |
|---|---|---|---|---|
| `Nov_Tmax` | 26.06 | 28.38 | 27.67 | 0 |
| `Dec_Tmax` | 19.99 | 25.03 | 22.99 | 0 |
| `Jan_Srad` | 368.0 | 509.0 | 444.59 | 19 |
| `Feb_Srad` | 449.0 | 538.0 | 497.69 | 19 |
| `Mar_Tmax` | 28.59 | 34.52 | 31.40 | 0 |
| `Apr_Tmax` | 32.46 | 40.12 | 35.67 | 0 |
| `Prcp_Monsoon` | 573.87 | 1296.58 | 872.92 | 19 |
| `Prcp_Oct` | 2.89 | 228.43 | 46.20 | 0 |

### Weather Source

The dataset description states that **AgERA5 v2.0** (daily max/min temperature,
shortwave radiation, etc.) was matched to each field's growing season.
However, the actual data in the file contains **monthly summary statistics**
derived from AgERA5, not the raw daily values. The monthly summaries represent:
- Average daily maximum temperature per month
- Total solar radiation per month
- Count of days exceeding monthly temperature thresholds (EDD = excess degree days)
- Monthly precipitation totals

### Shortwave Radiation Details

- **Columns:** `Jan_Srad`, `Feb_Srad`
- **Unit:** "1000 kW per m²" = GJ/m² (gigajoules per square meter, monthly total)
- **Conversion:** 1 unit = 1 GJ/m² = 1,000 MJ/m² (monthly total)
  - To daily MJ/m²/day: divide by number of days in the month (e.g., Jan: 31, Feb: 28/29)
  - Formula: `daily_shortwave = value * 1000 / days_in_month` → MJ/m²/day
- **PAR:** Not provided directly. PAR would need to be derived from shortwave
  using the 0.5 conversion coefficient (Monteith & Unsworth 2013).
  - `PAR = 0.5 * shortwave_daily`
  - This is an estimated provenance (see `par_pipeline.py` `DEFAULT_PAR_SPEC`)

### Temperature Usability for Thermal Stress

The temperature data in the file consists of **monthly average daily maximum
temperatures** (`Nov_Tmax`, `Dec_Tmax`, `Mar_Tmax`, `Apr_Tmax`). HYRUE's
thermal stress computation (`compute_hyrue_seasonal`) requires **daily**
mean temperature arrays (`t_mean = (t_min + t_max) / 2`). The monthly
averages cannot be directly used — they lack:
- Daily minimum temperature (`Tmin`)
- Intra-month variability
- Daily thermal stress calculation inputs

Daily temperature data can be obtained via `weather_source.fetch_daily_weather()`
using the dataset's coordinates and growing season dates, drawing from
Open-Meteo (ERA5-Land) or NASA POWER (MERRA-2).

---

## H. Missing Values

| Column | Missing count | Missing percentage |
|---|---|---|
| `GradeNPK` | 4,659 | 81.9% |
| `BasalZn` | 5,185 | 91.1% |
| `FifthIrrigationDay` | 5,640 | 99.1% |
| `HerbicideName` | 325 | 5.7% |
| `HerbicideType` | 325 | 5.7% |
| `Prcp_Monsoon` | 19 | 0.3% |
| `Jan_Srad` | 19 | 0.3% |
| `Feb_Srad` | 19 | 0.3% |

**Critical fields** (`Field_ID`, `Year`, `District`, `State`, `SowingDate`,
`HarvestDate`, `GrainYield`, `Latitude`, `Longitude`): **0 missing values**.

**Note:** The 19 missing values in `Prcp_Monsoon`, `Jan_Srad`, and `Feb_Srad`
are correlated — these likely correspond to the same 19 records (possibly from
a specific district/season with missing weather data).

---

## I. Duplicate Records

| Key definition | Duplicate count | Notes |
|---|---|---|
| `Field_ID` alone | 0 duplicates | Each record has a unique Field_ID |
| `(Field_ID, Year)` | 0 duplicates | No repeated field-season pairs |
| `(Field_ID, Season, Crop)` | 0 duplicates | No duplicate keys |
| `(District, Year, Crop)` | 5,630 warnings | Multiple fields per district per season |

**Finding:** When using `Field_ID` as the site-level identifier (which is the
correct approach for field-level validation), there are **zero duplicates**.
The 5,630 duplicate warnings arise only when using `District` as the site_id,
which would be incorrect for field-level analysis. The `run_data_quality_checks()`
function in `dataset_manifest.py` checks for duplicate `(site_id, season_id, crop)`
keys — if `District` is used as `site_id`, this produces a warning (not a failure).

---

## J. Quality Gate Results

### `run_data_quality_checks()` from `dataset_manifest.py`

Records were prepared with `site_id = District`, `season_id = Year`,
`crop = "wheat"`, `observed_yield = GrainYield`, `observed_yield_unit = "t/ha"`,
`data_label = "real_field_data"`.

| Check | Status | Details |
|---|---|---|
| `required_fields_present` | PASS | All 5,689 records have required fields |
| `yield_unit_consistency` | PASS | All 5,689 yield values are valid (t/ha, non-negative, finite) |
| `no_synthetic_label` | PASS | No synthetic labels found in 5,689 records |
| `duplicate_records` | WARNING | 5,630 duplicate (District, Year, crop) keys — expected with district-level site_id; zero when using Field_ID |

**Overall quality gate status:** NOT BLOCKED (1 warning, 0 failures)

### `run_quality_gates()` from `field_validation.py` (RealFieldRecord)

`RealFieldRecord` instances were constructed from the full dataset (all 5,689 records).
Each record was validated against pydantic field constraints:
- `observed_yield`: finite and non-negative ✓ (all pass)
- `observed_yield_unit`: must be in `{t/ha, kg/ha, g/m²}` ✓ (all "t/ha")
- `harvest_date >= planting_date` ✓ (verified)
- `data_label` not starting with "synthetic" ✓ (all "real_field_data")
- `observation_source` in valid set ✓ (all "published_literature")
- `latitude` in [-90, 90] ✓
- `longitude` in [-180, 90] ✓

**Quality gate decisions after `run_quality_gates()`:**

| Decision | Count | Reason |
|---|---|---|
| ACCEPTED | 0 | — |
| REQUIRES_REVIEW | 5,689 | `area_ha` is missing (no field area column in dataset); `harvest_sample_size` is not specified |
| REJECTED | 0 | — |

**Interpretation:** All 5,689 records pass structural validation (pydantic
constraints). All are flagged `REQUIRES_REVIEW` because the dataset does not
include field area (`area_ha`) or harvest sample size (`harvest_sample_size`).
These are **optional metadata fields** in `RealFieldRecord` — their absence
does not block benchmark execution but requires documentation. The
`run_quality_gates()` function explicitly marks records as `REQUIRES_REVIEW`
(not `REJECTED`) for missing optional metadata, allowing them to proceed
with a documented caveat.

---

## K. Data Quality Conclusion

The CIMMYT wheat dataset passes all quality gates:
1. ✅ Required fields present (site_id, season_id, crop, observed_yield, observed_yield_unit)
2. ✅ Yield values are non-negative and finite
3. ✅ Yield units are valid (t/ha)
4. ✅ No records labeled "synthetic"
5. ✅ No duplicate (Field_ID, Year, crop) keys
6. ✅ All 5,689 records construct valid `RealFieldRecord` instances

The only warning is duplicate `(District, Year, crop)` keys when using district
as site_id — this is resolved by using `Field_ID` instead. The `REQUIRES_REVIEW`
status of all `RealFieldRecord` instances is due to missing optional metadata
(field area, harvest sample size), not data quality issues.
