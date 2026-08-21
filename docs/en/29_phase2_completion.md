# 29. Phase 2 Completion — Real MRV Data Channels

**Date:** 2026-08-17 | **Status:** Active | **Class:** Technical
**Basis:** Doc 27 Phase 2 (weeks 3–4); EM-01 requirement in PDF section 41.

> This document describes the Phase-2 completion additions: live Sentinel-2
> NDVI from CDSE, IoT/LoRaWAN ingestion, offline citizen sync, and a
> PII-free public dashboard. (The core three-level slice landed in d697a21.)

## 1) Phase-2 Components (commits d697a21 → 984a399 → this commit)

| Component | Path | Role |
|---|---|---|
| Real Sentinel-2 NDVI | `engine/hydroma/mrv/satellite_cdse.py` | CDSE STAC client + rasterio NDVI |
| Live satellite refresh | `POST /api/v1/mrv/satellite-refresh` | per-site NDVI stored as `data_source="real"`; gated by `ENABLE_SATELLITE_REAL` |
| Shared IoT ingest | `engine/hydroma/mrv/iot_ingest.py` | single QA/QC path + TTN v3 parser + MQTT consumer |
| LoRaWAN webhook | `POST /api/v1/mrv/lorawan-webhook` | TTN v3 / ChirpStack uplinks with `X-Webhook-Key` |
| Offline sync | `POST /api/v1/mrv/citizen-reports/batch` | citizen offline queue upload (level 3) |
| Public dashboard | `GET /api/v1/mrv/public/dashboard-summary` | PII-free aggregates |
| Dependencies | `paho-mqtt`, `psycopg2-binary` | MQTT client; Postgres driver |

## 2) Real NDVI Pipeline (CDSE)

```
POST /satellite-refresh {site_id, lat, lon, start, end, half_side_km}
  → 1) OAuth2 client_credentials token (identity.dataspace.copernicus.eu)
  → 2) STAC search: SENTINEL-2 L2A, site bbox, time window, cloud < 20%
  → 3) download B04 (red) + B08 (NIR) 10 m bands
  → 4) NDVI = (NIR−R)/(NIR+R) with statistics + valid-pixel share
  → 5) store as level 1 with data_source="real" and full provenance
```

- Band files live in `tempfile.TemporaryDirectory` (stdlib cleanup — no
  manual file-removal APIs).
- Any failure (credentials/search/download/no valid pixels) → explicit 502;
  simulated data is **never stored silently** — the frontend chooses a
  labeled fallback.
- `ENABLE_SATELLITE_REAL != true` → 503 with a clear message.

## 3) Contracts & Security
- Webhook: `X-Webhook-Key` compared in constant time; empty key → 401.
- TTN v3 parser: direct or `uplink_message.decoded_payload` shape with a
  built-in unit map; unknown fields skipped.
- MQTT: connects only on `start()`; default topic `hydroma/+/reading`;
  malformed messages are logged and dropped (loop never dies).
- Honesty: all rows (even rejected) are archived; `data_source="real"` only
  for real data; the public summary is PII-free (test-enforced).

## 4) Environment Keys
```
CDSE_BASE_URL / CDSE_IDENTITY_URL / CDSE_CLIENT_ID / CDSE_CLIENT_SECRET
ENABLE_SATELLITE_REAL=true
TELCO_WEBHOOK_KEY=***
MQTT_BROKER_HOST/PORT/USERNAME/PASSWORD   # optional MQTT consumer
POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB   # local Postgres connection
```

## 5) Test Status
- 28 new tests this phase (14 completion + 14 CDSE); full suite: **431+ passed**.
- Alembic `upgrade head` on local PostgreSQL: success — 20 tables
  (PostGIS available on this install; docker-compose path removed).
