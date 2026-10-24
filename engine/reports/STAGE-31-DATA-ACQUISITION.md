# Stage 31: Data Acquisition Attempt — USDA BARC Gridded Yield Data Archive

## Summary

**Status:** Identified potential source · **Retrieval blocked** by WAF · **Files not acquired**

The USDA BARC Gridded Yield Data Archive (DOI `10.15482/USDA.ADC/28950746`) is
the highest-priority dataset for field-level HYRUE validation. Acquisition attempts
on 2026-10-18 were unable to retrieve dataset files due to an AWS WAF JavaScript
challenge on the Ag Data Commons website, and the Data.gov CKAN API returned
404 responses for both search and direct package lookup.

## A. Target Dataset

| Field | Value |
|---|---|
| Title | USDA Beltsville Agricultural Research Center BARC Gridded Yield Data Archive version 1 |
| DOI | https://doi.org/10.15482/USDA.ADC/28950746 |
| Landing page | https://agdatacommons.nal.usda.gov/datasets/USDA_Beltsville_Agricultural_Research_Center_BARC_Gridded_Yield_Data_Archive_version_1/28950746 |
| Paper DOI | 10.1002/agg2.20474 (Dulaney et al., 2024, AGSE) |
| License | Public Domain (US Government work) per Ag Data Commons listing |
| Location | Beltsville, MD (≈ 38.995°N, 76.937°W) |
| Years | ~2014–2021 (5 growing seasons) |
| Fields | 43+ production fields |
| Spatial resolution | 5m grid cells (interpolated from combine harvester points) |
| Crops | Corn (grain), Soybean, Wheat, Sorghum, Barley |

## B. Retrieval Attempts

### Attempt 1: Ag Data Commons Landing Page (HTTPS)

- **URL:** `https://agdatacommons.nal.usda.gov/datasets/USDA_Beltsville_Agricultural_Research_Center_BARC_Gridded_Yield_Data_Archive_version_1/28950746`
- **Method:** `curl` with browser User-Agent header
- **Result:** HTTP 200 with a JavaScript challenge page (AWS WAF Bot Control)
- **Page content:** Contains `AwsWafIntegration.getToken()` invocation and a
  challenge script from `https://64b6c62dfbe5.5fbc94a4.eu-west-1.token.awswaf.com/.../challenge.js`
- **Impact:** Programmatic download is blocked. A browser session executing
  JavaScript is required to obtain the WAF cookie before the dataset page
  (and any download links within it) can be accessed.

### Attempt 2: Ag Data Commons API

- **URL:** `https://agdatacommons.nal.usda.gov/api/v1/datasets/28950746`
- **Method:** `curl` with browser User-Agent header
- **Result:** HTTP 202 (Accepted) with the same AWS WAF challenge response
- **Impact:** The API endpoint is also behind the WAF challenge. No structured
  metadata or download links returned.

### Attempt 3: Data.gov CKAN API — Package Search

- **URL:** `https://catalog.data.gov/api/3/action/package_search?q=beltsville+yield+gridded&rows=3`
- **Method:** `curl` with browser User-Agent header
- **Result:** HTTP 404 — `{"detail":{},"message":"Not Found"}`
- **Impact:** The CKAN API endpoint does not respond at the expected path.

### Attempt 4: Data.gov CKAN API — Direct Package Lookup

- **URL:** `https://catalog.data.gov/api/3/action/package_show?identifier=USDA-Beltsville-Agricultural-Research-Center-BARC-Gridded-Yield-Data-Archive-version-1`
- **Method:** `curl` with browser User-Agent header
- **Result:** HTTP 404 — `{"detail":{},"message":"Not Found"}`
- **Impact:** No alternative identifier-based lookup available.

### Attempt 5: www.data.gov Domain

- **URL:** `https://www.data.gov/api/3/action/package_search?q=beltsville+yield&rows=5`
- **Method:** `curl` with browser User-Agent header
- **Result:** HTTPS 200 returning an HTML page (not JSON API response)
- **Impact:** The www.data.gov domain serves HTML, not CKAN API JSON. No
  structured dataset metadata or download links were obtainable.

### Attempt 6: Scientific Paper (DOI 10.1002/agg2.20474)

- **URL:** `https://agupubs.onlinelibrary.wiley.com/doi/10.1002/agg2.20474`
- **Method:** `webfetch`
- **Result:** HTTP 403 (blocked by Wiley licensing/institutional access wall)
- **Impact:** Paper abstract not retrievable without institutional access.
  Dataset file inventory and field-level yield unit details from the paper
  could not be confirmed.

## C. Directory Created

The following directory was created to receive BARC data files if/when
access is resolved:

```
data/external/usda_barc_yield/    (empty — no files retrieved)
```

No files were downloaded. No file hashes can be computed.

## D. Blockers

| Blocker | Technical Detail | Resolution Path |
|---|---|---|
| Ag Data Commons WAF | AWS WAF Bot Control requires JavaScript execution to obtain access cookie | Manual browser download, or contact USDA ARS data steward |
| Data.gov CKAN API | Returns 404 at `catalog.data.gov/api/3/action/` endpoints | Try alternate `catalog.data.gov` API versioning or direct DOI resolution |
| Wiley institutional wall | Paper DOI behind access control | Access via institutional subscription or request author manuscript |
| Registration requirement | Ag Data Commons states "free registration may be required for large-file downloads" | Register for Ag Data Commons account (still blocked by WAF until then) |

## E. Required Fields for HYRUE Integration (from `RealFieldRecord` contract)

The BARC dataset must provide the following to enable field-level validation.
These requirements are derived from `engine/hydroma/eval/field_validation.py`:

**RealFieldRecord required fields:**
- `site_id` — stable unique identifier
- `field_id` — field parcel identifier
- `season_id` — season identifier (e.g. "corn_2016")
- `crop` — crop name
- `planting_date` — ISO date string
- `harvest_date` — ISO date string
- `latitude` — WGS84 decimal degrees
- `longitude` — WGS84 decimal degrees
- `area_ha` — field area in hectares
- `observed_yield` — numeric yield value
- `observed_yield_unit` — one of `t/ha`, `kg/ha`, `g/m²` (from `VALID_YIELD_UNITS`)
- `observation_source` — one of `field_measured`, `satellite_retrieved`, `analysis_product`, `published_literature`
- `quality_gate_decision` — `ACCEPTED`, `REJECTED`, or `REQUIRES_REVIEW`
- `data_label` — must not start with "synthetic"

**Unit conversion:** `convert_yield_to_t_ha()` maps `kg/ha` → 0.001×, `g/m²` → 0.01×, `t/ha` → 1.0×.

If BARC data is in bushels/acre (bu/ac), a conversion factor must be applied
before ingestion (e.g., corn: 1 bu/ac ≈ 0.0673 t/ha at 56 lb/bushel moisture-free).

## F. Integration Path (Once Data Is Retrieved)

1. Compute file hashes via `compute_hashes()` from `dataset_manifest.py`
2. Create `DatasetManifest` with `provenance=REAL_FIELD_OBSERVATIONS`,
   publisher="USDA ARS Beltsville", license_url="Public Domain"
3. Run `run_data_quality_checks()` on raw records
4. Verify data independence with `check_data_independence()`
5. Build `RealFieldRecord` instances with `observation_source="published_literature"`
6. Construct `ValidationProtocol` with `EvaluationTarget.SPATIAL_AND_TEMPORAL`
7. Execute `compute_seasonal_prediction()` for each field record
8. Produce validation report via `produce_validation_report()`
9. Generate benchmark report via `produce_benchmark_report()`

## G. Next Action

The BARC dataset is **identified but not accessible** through automated means.
Options for resolution:

1. **Manual download** — Access BARC via a browser session to complete the WAF
   challenge, manually download files, and place them in `data/external/usda_barc_yield/`
2. **Contact USDA ARS** — Request a direct data transfer or alternative access
   method from the data steward
3. **Regional fallback** — Attempt USDA NASS Quick Stats API as a regional
   validation path (lower spatial resolution, but accessible)
