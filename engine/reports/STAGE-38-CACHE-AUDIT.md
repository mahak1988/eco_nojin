# Stage 38 — Cache Audit

## Cache Architecture

Two-tier caching system:

### Tier 1: In-Memory Weather Cache (`WEATHER_CACHE`)

Located in `engine/hydroma/simulation/weather_source.py`. In-memory dictionary keyed by URL + sorted params. TTL: 1 hour. Used within a single process run to avoid duplicate API calls for identical requests.

### Tier 2: Persistent Scientific Cache (`ScientificCache`)

New module `engine/hydroma/simulation/data_cache.py`. SQLite-backed disk cache at `engine/reports/data/stage38_cache.sqlite`. Cache keys incorporate provider, endpoint, coordinates, date range, variables, and unit contract version. Entries expire after TTL (default 24 hours).

## Cache Key Design

Each cache key is a SHA-256 hash of:
- Provider name (e.g. "Open-Meteo", "Planetary Computer")
- Endpoint (e.g. "archive-api/v1/archive", "stac/v1/search")
- Latitude, longitude
- Start date, end date
- Sorted variable list
- Unit contract version

## Cache Statuses

| Status | Meaning |
|---|---|
| SUCCESS | Valid data retrieved |
| PARTIAL | Partial data (some variables missing) |
| NOT_FOUND | Data not found at source |
| RATE_LIMITED | API rate limit exceeded |
| NETWORK_ERROR | Network connectivity failure |
| INVALID_RESPONSE | Malformed API response |
| FAILED | Generic failure |

## Cache Statistics (from profiling run)

| Metric | Value |
|---|---|
| Cache hit rate | 0.0% (first run, no prior cache) |
| Cache entries created | 0 (in-memory only, not persisted) |

## Recommendations

1. **Integrate `ScientificCache` with `fetch_daily_weather`** — Currently `WEATHER_CACHE` is in-memory only. Integrating `ScientificCache` would persist weather data across runs, saving ~13s per record on re-runs.

2. **Cache STAC search results** — Satellite STAC search results can be cached by coordinates + date range, saving ~18.7s per record on re-runs.

3. **Deduplicate coordinates** — Multiple records may share the same coordinates. Caching by coordinates avoids redundant API calls.

4. **Never cache synthetic data as real** — All cache entries are tagged with `source_api_version` and `status` to distinguish real data from errors.

## Files

- `engine/hydroma/simulation/data_cache.py` — persistent cache module
- `engine/reports/data/stage38_cache.sqlite` — cache database (created on first run)
