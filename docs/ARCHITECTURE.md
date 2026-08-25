# Architecture

## System Overview

Eco Nojin follows a **modular, service-oriented architecture** with clear separation
of concerns between the scientific engine (backend) and presentation layer (frontend).

## High-Level Architecture

```
+---------------------------------------------------------------+
|                    ACCESS CHANNELS                            |
+-------------+-------------+-------------+-------------+-------+
|  Web App    |     PWA     |    USSD     |     SMS     | Voice |
| Next.js 15  |  Offline+   |  *384*73#   |  Commands   |  IVR  |
+------+------+------+------+------+------+------+------+------+
                              |
                    +---------+---------+
                    |    API GATEWAY    |
                    |     (FastAPI)     |
                    +---------+---------+
                              |
+-----------------------------+-----------------------------+
|              HyDroMa SCIENTIFIC ENGINE                    |
+-----------------------------------------------------------+
| Soil | AI/RAG | Satellite | Scenarios | Marketplace       |
| Carbon | Watershed | Sync | USSD/SMS | Voice | Blockchain |
| Climate | Hydrology | Erosion | Biofertilizer | Materials |
| Irrigation | Groundwater | Economics | Finance | Risk      |
| Ecotourism | Land | Infrastructure | Decision Support    |
| Simulation | Calibration | MRV | Standards               |
+-----------------------------------------------------------+
                              |
                    +---------+---------+
                    |    DATA LAYER     |
                    | SQLite/PostgreSQL |
                    |   File Storage    |
                    +-------------------+
```

## Backend Structure

```
eco_nojin/
+-- engine/hydroma/
|   +-- core/            # Database, configuration
|   +-- models/          # SQLAlchemy models
|   +-- calculations/    # Scientific computations
|   +-- cpp_bridge/      # Numba-accelerated functions
|   +-- scenarios/       # Climate + crop scenarios
|   +-- scenario/        # Single scenario module
|   +-- marketplace/     # Products, orders, traceability
|   +-- carbon/          # Carbon credit calculator
|   +-- watershed/       # Watershed structure design
|   +-- satellite/       # Satellite data providers
|   +-- ai_assistant/    # RAG engine
|   +-- performance/     # Benchmark utilities
|   +-- ussd/            # USSD/SMS gateway
|   +-- voice/           # IVR + TTS/STT providers
|   +-- blockchain/      # Carbon registry + supply chain
|   +-- analyses/        # Data analysis modules
|   +-- biofertilizer/   # Biofertilizer calculations
|   +-- calibration/     # Model calibration tools
|   +-- climate/         # Climate data processing
|   +-- crop/            # Crop-specific models
|   +-- data_ingestion/  # Raw data input handlers
|   +-- decision_support/ # Decision support systems
|   +-- economics/       # Economic modeling
|   +-- ecotourism/      # Ecotourism platform logic
|   +-- erosion/         # Erosion modeling
|   +-- finance/         # Financial calculations
|   +-- geospatial/      # Geospatial utilities
|   +-- groundwater/     # Groundwater flow models
|   +-- hydrology/       # Hydrological models
|   +-- infrastructure/  # Infrastructure planning
|   +-- irrigation/      # Irrigation system design
|   +-- materials/       # Material properties and costs
|   +-- ml/              # Machine learning models
|   +-- mrv/             # Monitoring, Reporting, Verification
|   +-- optimization/    # Optimization algorithms
|   +-- plants/          # Plant-specific data and models
|   +-- risk/            # Risk assessment models
|   +-- simulation/      # General simulation engine
|   +-- soil/            # Soil property models
|   +-- standards/       # Compliance and standard checks
|   +-- utils/           # General utility functions
|   +-- visualization/   # Data visualization tools
|   +-- web_search/      # Web search integration for RAG
+-- engine/cpp_core/     # C++20 numerical core
|   +-- src/             # C++ source files (Richards, Saint-Venant, FAO-56, RUSLE)
|   +-- include/         # C++ headers
|   +-- bindings/        # pybind11 bindings for Python
+-- services/
|   +-- api_gateway/     # Main FastAPI application, routing to all services
|   |   +-- main.py      # FastAPI app entry
|   |   +-- routers/     # API endpoints per module (admin, ai, land, soil, blockchain, etc.)
|   +-- admin/           # Administrative panel logic
|   +-- analytics/       # Analytics and reporting services
|   +-- auth/            # Authentication and authorization
|   +-- bots/            # Chatbot integrations
|   +-- business_modules/ # Business logic modules
|   +-- carbon/          # Carbon-specific service logic
|   +-- content/         # Content management
|   +-- data_sources/    # External data source connectors
|   +-- design_engine/   # Design and planning engine
|   +-- ecowallet/       # Wallet and payment logic
|   +-- field_monitoring/ # Field monitoring services
|   +-- land/            # Land management services
|   +-- ledger/          # Transaction ledger
|   +-- map_engine/      # Mapping and GIS engine
|   +-- mobile_monitoring/ # Mobile-specific monitoring
|   +-- models/          # Shared data models
|   +-- notification/    # Notification services
|   +-- reporting/       # Reporting services
|   +-- satellite/       # Satellite data processing services
|   +-- science/         # Core science service facade
|   +-- scientific_motors/ # Reusable scientific computation units
|   +-- supabase/        # Supabase integration services
|   +-- telegram_bot/    # Telegram bot logic
|   +-- workflow/        # Workflow management
+-- frontend/
|   +-- app/             # Next.js app router
|   +-- components/      # React components (10 panels)
|   +-- lib/             # Hooks (offline, geo, camera)
|   +-- locales/         # 14 language JSON files
+-- tests/
|   +-- unit/            # Module-level tests
|   +-- integration/     # API integration tests
|   +-- benchmarks/      # Performance tests
+-- docs/                # Documentation
```

## Data Flow Examples

### Satellite Analysis Flow
```
User -> SatellitePanel -> POST /api/v1/satellite/analyze
      -> EarthSearchProvider (STAC API)
      -> Numba-accelerated indices (NDVI, EVI, etc.)
      -> Interpretation + Recommendation
      -> JSON response
```

### USSD Menu Flow
```
User dials *384*73#
  -> Telco gateway -> POST /api/v1/ussd/ussd
  -> UssdHandler routes based on text
  -> Returns CON (continue) or END (terminate)
  -> Telco displays menu
```

### Blockchain Carbon Credit Flow
```
Developer -> POST /api/v1/blockchain/carbon/projects
  -> CarbonRegistry.register_project() [generates tx_hash]
  -> Verifier: POST /verify
  -> Issue credits: POST /issue
  -> Transfer: POST /transfer
  -> Retire: POST /retire (permanent offset)
```

## Scientific Foundation

### Vegetation Indices (Numba-accelerated)
- **NDVI** (Rouse et al. 1974): `(NIR - Red) / (NIR + Red)`
- **EVI** (Huete et al. 2002): Enhanced vegetation index
- **SAVI** (Huete 1988): Soil-adjusted for sparse vegetation
- **NDWI** (McFeeters 1996): Water detection
- **NBR** (Key & Benson 2006): Burn severity

### Hydrology
- **Muskingum-Cunge**: Flood routing (Cunge 1969)
- **van Genuchten**: Soil water retention curves
- **Hargreaves-Samani**: Reference evapotranspiration

### Climate Scenarios
- **CMIP6 SSP pathways**: SSP1-2.6, SSP2-4.5, SSP5-8.5
- **Time horizons**: 2030, 2050, 2100
- **Regional adjustments**: tropical, temperate, arid

## Design Principles

1. **Offline-first**: All mobile features work without internet
2. **Inclusive access**: Feature phones via USSD/SMS
3. **Scientific rigor**: Peer-reviewed methodologies
4. **Performance**: Numba JIT for heavy computation
5. **Multi-language**: 14 languages with RTL/LTR support
6. **Modularity**: Each module independently testable
7. **Open standards**: FAO, IPCC, OGC compliance

## Security Considerations

- **CVE-2025-66478**: Documented in `docs/security/CVE-2025-66478.md`
- Safe in development (localhost)
- Must upgrade before production deployment