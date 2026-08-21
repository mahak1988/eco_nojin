# 04. Data Model

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. Storage Strategy

- **Research mode:** SQLite (`hydroma_research.db`) via SQLAlchemy; DuckDB
  planned for analytical time-series queries.
- **Production (planned):** PostgreSQL + PostGIS (docker-compose already
  defines `postgis/postgis:16-3.4`); GeoPackage for field geometries.

## 2. Core Entities (SQLAlchemy, `engine/hydroma/core/models.py`)

### soil_profiles
| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| name | str(100) | indexed |
| texture | str(50) | e.g. Sandy Loam, Clay |
| ph | float | 0–14 |
| ec | float | dS/m |
| organic_matter | float | % |
| created_at | datetime | |

### plants
| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| scientific_name | str(150) | indexed |
| local_name | str(100) | |
| category | str(50) | crop / tree / medicinal |
| water_need | str(20) | low / medium / high |
| drought_tolerance | str(20) | |
| salinity_tolerance | str(20) | |
| created_at | datetime | |

### materials
| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| name | str(100) | indexed |
| category | str(50) | animal / plant / mineral / microbial |
| c_n_ratio | float | carbon:nitrogen |
| ph | float | |
| created_at | datetime | |

## 3. Marketplace Entities (in-memory, `engine/hydroma/marketplace/models.py`)

- **Product:** category, price/kg, quantity, minimum order, organic flag,
  carbon/water footprints, harvest date, batch number, traceability code.
- **Producer:** type (cooperative / nomadic / individual), verification
  status, rating, certifications (organic, GlobalG.A.P., nomadic product…).
- **Order:** lifecycle pending → confirmed → shipped → delivered (or
  cancelled, restoring reserved quantity); revenue statistics.

All marketplace state is in-memory for research mode; persistence is planned.

## 4. Carbon Projects (in-memory, `engine/hydroma/carbon/calculator.py`)

- **CarbonProject:** type (afforestation, reforestation, soil carbon, biochar,
  agroforestry, grassland), area, duration, location, status
  (draft → submitted → verified), verifier, estimated tonnes, methodology.

## 5. Sync Log (`services/api_gateway/routers/sync.py`)

In-memory list of `{device_id, client_id, endpoint, method, payload,
timestamp, server_id, synced_at}` — queued offline actions from mobile
clients. Persistence and conflict resolution planned.

## 6. Satellite & Climate Data

- **NASA POWER** meteorological time series (T2M_MIN/MAX, RH2M, WS2M,
  ALLSKY_SFC_SW_DWN, PRECTOTCORR) — fetched live.
- **Sentinel-2 L2A** metadata via the public Element 84 STAC API — metadata
  real, **band values currently simulated** (see `02_hydroma_engine.md` §7).
- Raw rasters (GeoTIFF/NetCDF) are staged under `data/raw/` (git-ignored).

## 7. Schema Migrations

Research mode uses `Base.metadata.create_all` on startup. Production requires
Alembic migrations; the Alembic setup is a planned task.

## 8. Future Entities

Groundwater wells, irrigation schedules, livestock/herd records, MRV
measurements, reward tokens, ecotourism listings, index-insurance contracts.
