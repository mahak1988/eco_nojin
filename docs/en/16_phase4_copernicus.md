# 16 — Phase 4 Groundwork: Real Copernicus Satellite Data

> Status: **scaffold complete** — real-data client shipped, labelled fallback kept.
> Remaining before live data: CDSE credentials (free registration) + band sampling.

## 1. Goal (why this matters)

Phase 4 replaces **W-001 (simulated satellite data)** with real Earth
observation data from the **Copernicus Data Space Ecosystem (CDSE)** —
the free, open data source behind Sentinel-1/2/3.

Every current `/api/v1/satellite/analyze` call fabricates NDVI/EVI/SAVI with
`random.seed(lat, lon)`. That is acceptable for **UI/UX development only** and
was always labelled as such in the weakness register. Phase 4 makes the
pipeline real, reproducible and scientific — which is the platform's core
promise (science-grounded, no fabricated claims).

## 2. What shipped in this groundwork

### `services/satellite/copernicus.py` — CDSE client (offline-safe)

| Piece | Behaviour |
|---|---|
| `CopernicusClient.configured` | True only when `CDSE_CLIENT_ID` + `CDSE_CLIENT_SECRET` are set |
| `get_token()` | OAuth2 client-credentials token from CDSE identity realm, cached with expiry |
| `query_catalog(lat, lon, ...)` | Sentinel-2 L2A OData catalogue search with bbox intersection, date window, cloud-cover filter, newest-first |
| `analyze_location(lat, lon, date)` | Returns scene metadata when found; **`ndvi=None`** until band sampling lands — never fabricates |
| `ndvi_from_bands / evi_from_bands / savi_from_bands` | Pure, unit-tested spectral math |
| `health_from_ndvi` | FAO-style health labels (poor/moderate/good) |

**Honesty contract:** with no credentials every network method raises
`CopernicusNotConfigured`. Callers (the API router) catch it and fall back to
the clearly-labelled `data_source="simulated"` path. No silent fake data can
ever be presented as real.

### `services/api_gateway/routers/satellite.py` — router upgrades

- `POST /api/v1/satellite/analyze` now returns `data_source`:
  - `"copernicus"` when a real scene with sampled bands is used,
  - `"simulated"` otherwise (explicit, machine-readable honesty flag).
- `farm_id` optional field → analysis rows persisted to the real
  `satellite_analyses` table.
- `GET /api/v1/satellite/history/{farm_id}` — real stored rows (newest first).
- `GET /api/v1/satellite/health` reports the active `data_source`.

### Tests — `tests/test_copernicus.py` (17, offline)

Spectral math (incl. degenerate denominators, out-of-range rejection),
credential gating, token request shape + caching, catalogue URL/bbox filter
building, scene parsing + cloud filtering, honest no-scene result. **Full
backend suite: 253 passing.**

## 3. How to go live (Phase 4 remainder, next working session)

1. **Register free CDSE account** → https://dataspace.copernicus.eu (OAuth).
2. Create client credentials in the CDSE dashboard; put them in `.env`:
   ```env
   CDSE_CLIENT_ID=...
   CDSE_CLIENT_SECRET=...
   ```
3. Implement **band sampling** in `analyze_location`: for the chosen scene,
   fetch `B04` (red) and `B08` (NIR) cloud-optimised GeoTIFFs via the CDSE
   S3/processing endpoint and sample the pixel around (lat, lon) → real NDVI.
4. Swap the labelled fallback to an **explicit error surface** once real data
   is flowing (no silent simulation in production).
5. Extend the alert engine (`services/bots/core/alerts.py`) to fire on real
   NDVI thresholds instead of missing-metric suppression.

## 4. References

- CDSE OData API: https://documentation.dataspace.copernicus.eu/APIs/OData.html
- Sentinel-2 MSI resolutions: https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/resolutions/spatial
- Weakness register: `docs/en/11_weaknesses_and_fixes.md` (W-001 → in progress)

## 5. Live now (no credentials required)

**NASA POWER weather** — `GET /api/v1/satellite/weather?lat=&lon=&days=`
returns REAL temperature, precipitation and Hargreaves ET0 for any
location. Free, no auth, backed by NASA's public API. The farm detail
dashboard shows a 7-day real weather card sourced from NASA POWER.

## 6. Real band sampling shipped (needs CDSE credentials to go live)

- `CopernicusClient.search_stac` — STAC v1 search over `sentinel-2-l2a`
  with bbox/datetime/cloud filters.
- `CopernicusClient.sample_bands` — downloads B04/B08/B02 COGs and samples
  the pixel around (lat, lon) with **rasterio** to compute REAL NDVI/EVI/SAVI.
- `CopernicusClient.analyze_location` — end-to-end: scene → bands → indices;
  returns explicit `status` ("ok" | "no_scene" | "band_error"), never fake data.
- Credential styles: `CDSE_CLIENT_ID/SECRET` (client-credentials) or
  `CDSE_USERNAME/CDSE_PASSWORD` (password grant, cdse-public).

## 7. Provenance + analytics + alerts

- Alembic migration `b7c9d2e4f1a3`: `satellite_analyses` gains
  `data_source`, `scene_id`, `cloud_cover` (data-provenance per the plan).
- DuckDB analytics: `services/analytics/duckdb_service.py` + endpoint
  `GET /api/v1/satellite/stats/{farm_id}` (mean/min/max/latest NDVI,
  real-data count).
- Real alert foundation: `ndvi_alert_rules()` + `satellite_row_to_metrics()`
  in `services/bots/core/alerts.py` — alerts fire ONLY on rows whose
  `data_source == "copernicus"` (simulated values can never trigger a farm alert).

## 8. Remaining Phase 4 work

- CDSE credentials in `.env` (registration is free) → live Sentinel-2 NDVI.
- STAC → processing → storage → API → dashboard flow is fully coded; the
  acceptance criterion (a real Sentinel-2 product with provenance in the
  dashboard) is one credential away.
- DVC/MLflow reproducibility tooling remains for the data-science layer.

## 9. Phase 4 completion status (2026-08-16)

- ✅ Real weather: NASA POWER + **Open-Meteo ERA5** (FAO-56 ET0, no creds)
  — `/api/v1/satellite/weather` returns both labelled sources.
- ✅ Real NDVI pipeline (STAC + COG band sampling) — coded and unit-tested;
  **live activation waits only for CDSE credentials in `.env`.**
- ✅ Provenance columns (migration `b7c9d2e4f1a3`), DuckDB stats, real NDVI
  alert rules + alert runner (`services/bots/core/alert_runner.py`).
- ✅ DVC pipeline scaffold (`dvc.yaml`: stac_fetch → band_sample → load_db).
- ⏳ Remaining: CDSE credentials (user action), DVC/MLflow activation, pixel
  cloud-mask (SCL) refinement.

## 5. Phase 4 completion (this session)

### Cloud masking (SCL) — acceptance criterion "with cloud mask" ✅
- `sample_bands` now also fetches the Sentinel-2 **SCL** band (best-effort)
  and samples a 5×5 window around the point → `scl_clear_ratio`.
- New status `"cloudy"`: when the SCL clear ratio is below 0.5 the analysis
  returns `ndvi/evi/savi = None` — a cloudy reading is never presented as a
  real vegetation index (honesty contract).
- Pure helpers `scl_is_clear` / `clear_ratio_from_scl` (clear classes
  4=vegetation, 5=non-vegetated, 6=water; 0=nodata). If SCL is missing the
  pipeline degrades to `scl_clear_ratio=None` (no masking applied, flagged).
- Tests: `tests/test_scl_masking.py` (7, offline, synthetic COGs via
  rasterio MemoryFile). Fix along the way: `blue` key may be present-but-None
  → `bands.get("blue") or 0.1`.

### Periodic real-data alert evaluation ✅
- `run_all_farm_alerts(db)` in `services/bots/core/alert_runner.py` — loops
  every farm, evaluates real (copernicus-only) NDVI rules, logs fired alerts.
- Wired into the API lifespan as a background asyncio task
  (`_alert_loop`), interval `ALERT_INTERVAL_SECONDS` (default 900),
  toggle `ALERTS_AUTORUN=0`; graceful cancellation on shutdown.
- Tests: `tests/test_alert_loop.py` (4).

### Admin bootstrap (Phase 5 readiness) ✅
- `python scripts/bootstrap_admin.py you@example.com` — idempotent CLI that
  sets role=admin for an existing user (no raw SQL needed).

## 6. Bonus data source: CDS (Climate Data Store, ERA5)

`services/satellite/cds.py` — real CDS REST client (submit → poll → download)
with plain httpx (no cdsapi dependency). Requires in `.env`:
```
CDS_API_URL=https://cds.climate.copernicus.eu/api
CDS_UID=<your uid>
CDS_API_KEY=<your key>
```
- `GET /api/v1/satellite/cds/status` — honest configured flag + note that
  NetCDF/GRIB parsing needs netcdf4/xarray (not bundled).
- Tests: `tests/test_cds.py` (5, offline with mocked httpx).
