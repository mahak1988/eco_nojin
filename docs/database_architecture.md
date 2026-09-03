# Database Architecture - Eco Nojin

Last updated: 2026-09-03 05:29

## Overview

The Eco Nojin project uses a consolidated, multi-database architecture
with a centralized data access layer (DataHub).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Services                       │
│  (Auth, Marketplace, Tourism, Analytics, Reporting, ...)    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Processing Engine (engine.data_connector)       │
│              Scientific Motors, Simulations, MRV            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              DataHub (database.hub.DataHub)                  │
│              Unified Data Access Layer                       │
└──┬──────────────┬──────────────┬──────────────┬─────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│DuckDB  │  │SQLAlchemy│  │SQLite │  │Redis   │
│(Master)│  │(SQLite) │  │(Manual)│  │(Cache) │
│132 tbls│  │62 tbls  │  │18 tbls │  │        │
│467K rows│  │36 rows │  │175K rows│  │        │
└────────┘  └────────┘  └────────┘  └────────┘
```

## Databases

### 1. Master Database (DuckDB)

- **Path**: `data/eco_nojin_master.duckdb`
- **Tables**: 132
- **Rows**: 466,925+
- **Purpose**: Analytics, climate data, scientific reference

**Key tables:**
- `weather_daily` (58,464 rows) - Daily weather observations
- `weather_history_annual` (10,200 rows) - Annual aggregates
- `climate_normals_monthly` (3,600 rows) - Climate normals
- `climate_disasters` (1,020 rows) - Disaster records
- `crop_water_parameters` (52 rows) - Crop coefficients

### 2. Transactional Database (SQLAlchemy/SQLite)

- **Path**: `data/econojin.db`
- **Tables**: 62
- **Purpose**: User data, business transactions, CRUD

**Key tables:**
- `users` - User accounts
- `land_profiles` - Farm/land profiles
- `auditlog` - Audit trail
- `ecowallet` - Wallet balances

### 3. Reference Database (SQLite)

- **Path**: `data/manual/eco_manual_v1.sqlite`
- **Tables**: 18
- **Rows**: 175,067
- **Purpose**: Scientific reference, curated datasets

## Access Patterns

### For Application Services

```python
from database.hub import hub
from database.models import User

with hub.get_session() as session:
    user = session.query(User).first()
```

### For Processing Engines

```python
from engine.data_connector import connector

# Analytics query
df = connector.get_climate_data(station_id=123, year=2020)

# Reference data
params = connector.get_crop_parameters("wheat")

# Transactional
with connector.get_session() as session:
    # ...
```

## Migration History

| Phase | Date | Action |
|-------|------|--------|
| 1 | 2026-09 | Unified Base class, created DataHub |
| 2 | 2026-09 | Migrated 59 files to use DataHub |
| 3 | 2026-09 | Consolidated 3 DuckDB into master |
| Final | 2026-09 | Connected processing engine |

## Backup Strategy

All databases have `.phase3.bak` backups:

```
data/
├── eco_nojin_master.duckdb
├── eco_nojin_master.duckdb.phase3.bak
├── econojin.db
├── econojin.db.phase3.bak
└── manual/
    ├── eco_manual_v1.sqlite
    └── eco_manual_v1.sqlite.phase3.bak
```
