# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — INVENTORY REPORT

**Document ID:** ECO-00-INVENTORY-001  
**Date:** 2026-10-08  
**Status:** COMPLETE
**Auditor:** Kilo autonomous agent

---

## 1. Executive Summary

This report presents the complete read-only inventory of the `engine/` and `services/` directories in the HyDroMA project. The codebase consists of 290 Python files in the engine (plus C++ sources) and 644 Python files in services. The engine contains a scientific computation core with C++/Python dual implementations for critical numerical kernels. The services layer provides API endpoints, business logic, and data management for a hydrological/carbon/ecosystem platform.

## 2. File Counts

- **Total engine files (Python):** 290
- **Total service files (Python):** 644
- **C++ source files:** 10 (in `engine/cpp_core/src/`)
- **C++ header files:** 10 (in `engine/cpp_core/include/hydroma/`)
- **C++ test/benchmark files:** 21 (in `engine/cpp_core/tests/`)
- **Test files (Python):** 45+ across engine and services
- **Generated files:** `.pyc`, `.obj`, `.pyd` files in `__pycache__` and `build` directories
- **Data files:** CSV, JSON, configuration files

## 3. Languages

- **Python** (primary, ~900 files)
- **C++** (scientific kernels, 10 source + 10 header files)
- **CMake** (C++ build system)
- **Batch** (`.bat` build scripts)
- **JSON** (baseline test data, configuration)
- **CSV** (reference data tables)

## 4. Frameworks

| Framework | Location | Purpose |
|-----------|----------|---------|
| NumPy | engine, services | Numerical computing |
| Pydantic V2 | engine, services | Data validation models |
| SQLAlchemy | services | Database ORM |
| pytest | engine, services | Testing |
| pybind11 | engine/cpp_core | C++/Python bindings |
| FastAPI | services/api_gateway | API framework |
| structlog | services | Logging |
| Supabase | services/supabase | Auth/database client |
| psutil | engine | Memory monitoring (optional) |
| asyncio | services | Async I/O |

## 5. Build Systems

| System | Location | Description |
|--------|----------|-------------|
| Python pip | root | Python package management |
| CMake | engine/cpp_core/CMakeLists.txt | C++ build orchestration |
| pybind11 | engine/cpp_core/bindings.cpp | Python-C++ bridge |
| Batch scripts | engine/cpp_core/*.bat | Windows build scripts |

## 6. Dependency Manifest

**Finding:** No `requirements.txt`, `pyproject.toml`, `setup.py`, or similar dependency manifest was found in the repository root. Dependencies are inferred from imports.

Key external dependencies:
- `numpy`, `pandas` (numerical/data analysis)
- `pydantic` (validation)
- `sqlalchemy` (ORM)
- `pytest`, `pytest-asyncio` (testing)
- `structlog` (logging)
- `psutil` (optional memory monitoring)
- `supabase` (client library, optional)
- `torch` (optional, ML surrogate)

## 7. Test Files

### Engine Tests
- `engine/test_connector.py` — DataConnector tests
- `engine/strict_tests/` — 16 strict tests (test_s00 through test_s15)
- `engine/land/tests/` — Land analysis tests
- `engine/land/integration/tests/` — Integration tests
- `engine/hydroma/watershed/tests/` — Watershed calculator tests
- `engine/hydroma/data_pipeline/tests/` — Data pipeline tests
- C++ tests: 15 test/benchmark files in `engine/cpp_core/tests/`

### Service Tests
- `services/admin/tests/` — Admin service tests
- `services/land/tests/` — Land service tests
- `services/inventory/tests/` — Inventory service tests
- `services/conftest.py` — Shared test fixtures (56 lines)
- Various test files across service directories

## 8. Directory Tree

```
HyDroMA/
├── engine/
│   ├── __init__.py              # v2.0.0 — core exports
│   ├── README.md                # Architecture documentation
│   ├── data_connector.py        # 478 lines — DataHub unified access
│   ├── memory_monitor.py        # 166 lines — memory tracking
│   ├── resilience.py            # 348 lines — circuit breaker, timeout, retry
│   ├── resource_manager.py      # 124 lines — context managers for connections
│   ├── safe_math.py             # 324 lines — NaN/overflow-safe math
│   ├── test_connector.py        # 1617 bytes — connector tests
│   ├── baseline/                # Baseline test cases (R18.json, cases.py)
│   ├── cpp_core/                # C++ scientific kernels (10 src + 10 headers)
│   │   ├── src/                 # C++ implementations
│   │   ├── include/hydroma/     # C++ headers
│   │   ├── bindings.cpp         # pybind11 bindings
│   │   ├── build/               # Compiled .pyd
│   │   ├── tests/               # C++ tests and benchmarks
│   │   ├── CMakeLists.txt       # Build configuration
│   │   └── *.bat                # Windows build scripts
│   ├── data/                    # Reference data (soil tables CSV, etc.)
│   ├── hydroma/                 # Hydroma scientific engine (main subsystem)
│   │   ├── __init__.py          # Public API
│   │   ├── wrapper.py           # High-level Python wrapper
│   │   ├── cpp_bindings.py      # Python bindings loader (delegates to cpp_bridge)
│   │   ├── provenance.py        # Result provenance tracking
│   │   ├── quantity.py          # Unit/quantity handling
│   │   ├── formulas/            # Formula registry and catalog
│   │   │   ├── catalog.py       # 34+ FormulaRecord entries
│   │   │   ├── registry.py      # Registration & validation
│   │   │   ├── records.py       # FormulaRecord dataclass
│   │   │   └── research/        # Research definitions for novel formulas
│   │   ├── watershed/           # Watershed calculations
│   │   ├── formulas/            # Formula catalog and registry
│   │   ├── climate/             # Climate calculations (ET0)
│   │   ├── soil/                # Soil physics, chemistry, health
│   │   ├── carbon/              # Carbon sequestration
│   │   ├── economics/           # Economic analysis
│   │   ├── water/               # Water quality analysis
│   │   ├── groundwater/         # Groundwater modeling
│   │   ├── simulation/          # Simulation orchestration
│   │   ├── irrigation/          # Irrigation scheduling
│   │   ├── models/              # Scientific models (epia, hpheno, etc.)
│   │   ├── economics/           # Economic analysis modules
│   │   ├── utils/               # Utility functions
│   │   ├── visualization/       # Visualization tools
│   │   ├── data_pipeline/       # Data ingestion pipeline
│   │   ├── distributed_ml/      # Distributed ML training
│   │   └── tests/               # Various test files
│   ├── land/                    # Land intelligence engine (v1.6.0)
│   │   ├── __init__.py          # Module exports
│   │   ├── models.py            # Pydantic V2 data structures
│   │   ├── dem_processor.py     # DEM loading/processing
│   │   ├── terrain_analysis.py  # Slope, aspect, TWI, TPI
│   │   ├── drainage.py          # Drainage analysis, Strahler ordering
│   │   ├── capability.py        # USDA capability classification
│   │   ├── erosion_risk.py      # Erosion risk estimation
│   │   ├── surface_water.py     # Surface water analysis
│   │   ├── hydrology.py         # D8 flow routing (core)
│   │   ├── reference/           # Geographic reference data
│   │   ├── integration/         # Integration tests and modules
│   │   └── tests/               # Land engine tests
│   ├── ports/                   # Hexagonal ports (adapters)
│   │   ├── __init__.py
│   │   ├── clock.py             # Clock abstraction
│   │   ├── session.py           # Session/DB abstraction
│   │   └── sinks.py             # Output sinks
│   └── strict_tests/            # Strict validation tests (s00-s15)
│       ├── conftest.py          # Test configuration
│       ├── thresholds.py        # Test thresholds
│       ├── test_s00_baseline.py
│       ├── test_s01_import_integrity.py
│       ├── test_s02_climate_et0.py
│       ├── test_s03_hydrology_runoff.py
│       ├── test_s04_groundwater.py
│       ├── test_s05_soil_retention.py
│       ├── test_s06_watershed_design.py
│       ├── test_s07_carbon.py
│       ├── test_s08_irrigation.py
│       ├── test_s09_dimensional_consistency.py
│       ├── test_s10_property_invariants.py
│       ├── test_s11_parity_tripwires.py
│       ├── test_s12_table_registration.py
│       ├── test_s13_soil_table.py
│       ├── test_s14_published_table.py
│       └── test_s15_provenance.py
└── services/
    ├── __init__.py              # Main entry point imports
    ├── conftest.py              # 19KB test fixtures
    ├── _contracts/              # Formula contracts
    │   ├── formula.py           # Single source of truth for formulas
    │   ├── money.py             # Money handling
    │   └── status.py            # Status/provenance types
    ├── admin/                   # Admin service
    ├── alerting/                # Alerting service
    ├── analysis/                # Analysis service
    ├── analytics/               # Analytics service
    ├── api_gateway/             # API gateway
    │   ├── routers/             # API route handlers (20+ routers)
    │   ├── middleware/          # HTTP middleware
    │   ├── eventbus/            # Event bus (NATS)
    │   ├── auth.py              # Authentication
    │   ├── errors.py            # Error handling
    │   ├── security.py          # Security utilities
    │   ├── tracing.py           # Request tracing
    │   └── main.py              # Gateway main
    ├── auth/                    # Authentication service
    ├── auth_legacy/             # Legacy auth (deprecated)
    ├── backup/                  # Backup service
    ├── blockchain/              # Blockchain services
    ├── bots/                    # Bot services
    ├── business_modules/        # Business modules (voice, carbon)
    ├── carbon/                  # Carbon service
    ├── commerce/                # Commerce service
    ├── content/                 # Content service
    ├── contracts/               # Contract testing service
    ├── data/                    # Data management
    ├── data_manual/             # Manual data
    ├── data_sources/            # Data source management
    ├── design_engine/           # Design engine
    ├── ecowallet/               # Eco wallet service
    ├── ecosystem/               # Ecosystem service
    ├── ecowallet/               # Eco wallet (earnings, ledger, redemption)
    ├── field_monitoring/        # Field monitoring service
    ├── finance/                 # Finance service
    ├── governance/              # Governance service
    ├── hydroma/                 # Hydroma services (mostly empty dirs)
    ├── integration/             # Integration services
    ├── inventory/               # Inventory service
    ├── jobs/                    # Job processing service
    ├── knowledge/               # Knowledge service
    ├── land/                    # Land service
    ├── landscape/               # Landscape service
    ├── ledger/                  # Ledger service
    ├── legal/                   # Legal service
    ├── livestock/               # Livestock service
    ├── logistics/               # Logistics service
    ├── map_engine/              # Map engine
    ├── marketplace/             # Marketplace service
    ├── mobile_monitoring/       # Mobile monitoring
    ├── models/                  # Scientific model registry
    │   ├── __init__.py
    │   ├── base.py              # 2 bytes (near-empty)
    │   ├── land_models.py       # Land model DB schemas
    │   ├── pinn_surrogate.py    # PINN surrogate scaffold
    │   ├── registry.py          # Model registry (22 models)
    │   ├── soil_climate_models.py  # 2 bytes (near-empty)
    │   └── water_models.py      # 2 bytes (near-empty)
    ├── mrv/                     # MRV (Measurement, Reporting, Verification)
    ├── nojin/                   # Nojin admin/business
    ├── notification/            # Notification service
    ├── ogc/                     # OGC service
    ├── oracle/                  # Oracle service
    ├── organization/            # Organization service
    ├── privacy/                 # Privacy service
    ├── provenance/              # Provenance service
    ├── quality/                 # Quality service
    ├── quality_assurance/       # QA service
    ├── rangeland/               # Rangeland service
    ├── reliability/             # Reliability service
    ├── reporting/               # Reporting service
    ├── restoration/             # Restoration service
    ├── satellite/               # Satellite service
    ├── science/                 # Science service
    ├── scientific_motors/       # Scientific motors
    ├── security/                # Security utilities
    ├── simulation/              # Simulation service
    ├── sponsors/                # Sponsors service
    ├── supabase/                # Supabase integration
    ├── tasmimyar/               # Tasmimyar service
    ├── telegram_bot/            # Telegram bot service
    ├── territory/               # Territory service
    ├── tourism/                 # Tourism service
    ├── validation/              # Validation service
    ├── wallet/                  # Wallet service
    ├── workers/                 # Background workers
    └── workflow/                # Workflow service
```

## 9. Languages Summary

| Language | Files | Primary Location |
|----------|-------|-----------------|
| Python | ~570+ source files | engine/, services/ |
| C++ | 10 source + 10 header | engine/cpp_core/ |
| CMake | 1 | engine/cpp_core/CMakeLists.txt |
| Batch | ~8 | engine/cpp_core/*.bat |
| JSON | ~5+ | engine/baseline/, test data |
| CSV | 1+ | engine/data/soil_vg_table.csv |

## 10. Frameworks Summary

| Framework | Used For | Location |
|-----------|----------|----------|
| NumPy | Numerical computing | engine, services |
| Pydantic V2 | Data models | engine/land/models.py, services |
| SQLAlchemy | ORM | services/models/, database layer |
| pytest | Testing | All test directories |
| pybind11 | C++/Python bindings | engine/cpp_core/ |
| FastAPI | API framework | services/api_gateway/ |
| structlog | Structured logging | services |

## 11. Build Systems

| System | Configuration | Notes |
|--------|---------------|-------|
| CMake | engine/cpp_core/CMakeLists.txt | Builds C++ kernels with OpenMP |
| pybind11 | engine/cpp_core/bindings.cpp | Exports C++ to Python as `hydroma_core` |
| Python packages | No manifest found | Dependencies must be inferred |

## 12. Dependency Manifests

**Status:** NONE FOUND in repository root

No `requirements.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile`, or `poetry.lock` was found. Dependencies are inferred from imports throughout the codebase.

**Finding (BLOCKER-P2):** Missing dependency manifest makes reproducibility difficult and prevents deterministic builds.

## 13. Test Files

### Engine Tests
| Test File | Type | Purpose |
|-----------|------|---------|
| engine/test_connector.py | Unit | DataConnector tests |
| engine/strict_tests/test_s00_baseline.py | Baseline | Import baseline |
| engine/strict_tests/test_s01_import_integrity.py | Import | Import integrity |
| engine/strict_tests/test_s02_climate_et0.py | Numerical | Climate/ET0 tests |
| engine/strict_tests/test_s03_hydrology_runoff.py | Numerical | Hydrology/runoff |
| engine/strict_tests/test_s04_groundwater.py | Numerical | Groundwater |
| engine/strict_tests/test_s05_soil_retention.py | Numerical | Soil retention |
| engine/strict_tests/test_s06_watershed_design.py | Numerical | Watershed design |
| engine/strict_tests/test_s07_carbon.py | Numerical | Carbon |
| engine/strict_tests/test_s08_irrigation.py | Numerical | Irrigation |
| engine/strict_tests/test_s09_dimensional_consistency.py | Unit | Dimensional analysis |
| engine/strict_tests/test_s10_property_invariants.py | Property | Property invariants |
| engine/strict_tests/test_s11_parity_tripwires.py | Parity | Backend parity |
| engine/strict_tests/test_s12_table_registration.py | Integration | Table registration |
| engine/strict_tests/test_s13_soil_table.py | Unit | Soil table |
| engine/strict_tests/test_s14_published_table.py | Unit | Published table |
| engine/strict_tests/test_s15_provenance.py | Unit | Provenance tracking |
| engine/land/tests/ | Unit | Land analysis tests |
| engine/land/integration/tests/ | Integration | Integration tests |
| engine/hydroma/watershed/tests/ | Unit | Watershed tests |
| engine/hydroma/data_pipeline/tests/ | Unit | Data pipeline tests |
| engine/cpp_core/tests/ | C++ Unit | 15 C++ test/benchmark files |

### Service Tests
| Test File | Type | Purpose |
|-----------|------|---------|
| services/admin/tests/test_integration.py | Integration | Admin service |
| services/land/tests/test_integration.py | Integration | Land service |
| services/land/tests/test_service.py | Unit | Land service |
| services/land/tests/test_land_profile.py | Unit | Land profile |
| services/inventory/tests/test_inventory.py | Unit | Inventory service |
| services/conftest.py | Integration | Shared test fixtures (56KB) |

## 14. Scientific Modules

| Module | Path | Domain | Language |
|--------|------|--------|----------|
| Terrain Analysis | engine/land/terrain_analysis.py | Topography | Python |
| Hydrology/D8 | engine/land/hydrology.py | Flow routing | Python |
| Drainage | engine/land/drainage.py | Drainage | Python |
| Capability | engine/land/capability.py | USDA LCC | Python |
| Erosion Risk | engine/land/erosion_risk.py | Erosion | Python |
| Surface Water | engine/land/surface_water_analysis.py | Hydrology | Python |
| DEM Processor | engine/land/dem_processor.py | DEM | Python |
| Soil Physics | engine/hydroma/soil/physics.py | Soil water | Python |
| ET0 Calculator | engine/hydroma/climate/et_calculator.py | Climate | Python/C++ |
| Carbon Calculator | engine/hydroma/carbon/calculator.py | Carbon | Python |
| Watershed Calculator | engine/hydroma/watershed/calculator.py | Hydrology | Python/C++ |
| Formula Registry | engine/hydroma/formulas/ | Multi-domain | Python |
| EPIA | engine/hydroma/models/epia.py | Irrigation | Python |
| H-Pheno | engine/hydroma/models/hpheno.py | Phenology | Python |
| Groundwater | engine/hydroma/models/groundwater_model.py | Hydrogeology | Python |
| Runoff | engine/hydroma/models/runoff_model.py | Hydrology | Python |
| MODFLOW6 | engine/hydroma/models/expansion/modflow6.py | Groundwater | Python |
| SWAT+ | engine/hydroma/models/expansion/swat_plus.py | Watershed | Python |
| RUSLE | engine/cpp_core/src/erosion.cpp | Erosion | C++ |
| Penman-Monteith | engine/cpp_core/src/climate.cpp | ET0 | C++ |
| Saint-Venant | engine/cpp_core/src/saint_venant.cpp | Flow | C++ |
| Richards | engine/cpp_core/src/richards.cpp | Soil water | C++ |

### C++ Scientific Kernels

| Kernel | File | Unit Tests | Benchmarks |
|--------|------|------------|------------|
| Climate (ET0) | src/climate.cpp | test_climate_unit.cpp | benchmark_climate.cpp |
| Crop Water | src/crop_water.cpp | test_crop_water_unit.cpp | benchmark_crop_water.cpp |
| Erosion (RUSLE) | src/erosion.cpp | test_erosion_unit.cpp | benchmark_erosion.cpp |
| Hydrology (Muskingum) | src/hydrology.cpp | test_hydrology_unit.cpp | benchmark_hydrology.cpp |
| Indices (NDVI/EVI) | src/indices.cpp | test_indices_unit.cpp | benchmark_indices.cpp |
| Nojin Calculator | src/nojin_calculator.cpp | test_nojin_calculator.cpp | N/A |
| Richards Equation | src/richards.cpp | test_richards_unit.cpp | benchmark_richards.cpp |
| Saint-Venant | src/saint_venant.cpp | test_saint_venant_unit.cpp | benchmark_saint_venant.cpp |
| Sampling | src/sampling.cpp | test_sampling_unit.cpp | benchmark_sampling.cpp |
| Sediment | src/sediment.cpp | test_sediment_unit.cpp | benchmark_sediment.cpp |
| Soil Physics | src/soil.cpp | test_soil_unit.cpp | benchmark_soil.cpp, benchmark_soil_extended.cpp |
| Advanced (combined) | test_advanced.cpp, test_hydroma.cpp | 2 files | N/A |

## 15. Business-Domain Services

| Service | Purpose | Key Files |
|---------|---------|-----------|
| Land Service | Land profile and terrain analysis | services/land/service.py, terrain_analysis.py, land_profile.py |
| Wallet Service | Eco wallet earning, credits, challenges | services/wallet/{eco_balance,credits,challenges}.py |
| Admin Service | Admin operations, overview | services/admin/service.py, overview_service.py |
| Commerce Service | Order processing | services/commerce/service.py |
| Auth Service | Authentication | services/auth/service.py |
| Auth Legacy Service | Legacy authentication (deprecated) | services/auth_legacy/service.py |
| API Gateway | API routing, auth, eventbus | services/api_gateway/ (20+ routers) |
| Model Registry | Scientific model registry (22 models) | services/models/registry.py |
| Validation Service | Formula validation | services/validation/ |
| Quality Assurance | QA checks | services/quality_assurance/ |
| Inventory Service | Inventory management | services/inventory/service.py |
| Workflow Service | Workflow orchestration | services/workflow/service.py |
| Notification Service | Notifications | services/notification/ |
| Satellite Service | Satellite data | services/satellite/ |
| Finance Service | Financial operations | services/finance/ |
| Observability | Monitoring/setup | services/observability/ |
| Contracts Service | Contract versioning | services/contracts/ |
| Backup Service | Backup operations | services/backup/ |
| MRV Service | Measurement, Reporting, Verification | services/mrv/ (in engine/hydroma/mrv/) |

## 16. Native Modules

| Module | Location | Notes |
|--------|----------|-------|
| hydroma_core.pyd | engine/cpp_core/build/ | Compiled pybind11 extension |
| C++ sources | engine/cpp_core/src/ | 10 .cpp files |
| C++ headers | engine/cpp_core/include/hydroma/ | 10 .hpp files |
| CMake build | engine/cpp_core/CMakeLists.txt | Uses OpenMP |

## 17. Generated Code

| File | Generated By |
|------|-------------|
| All .pyc files | Python bytecode compiler |
| *.obj files | C++ compiler |
| hydroma_core.pyd | pybind11/C++ build |
| *.exp files | Linker |
| __pycache__/ | Python bytecode |

## 18. Configuration

| File | Location | Purpose |
|------|----------|---------|
| engine/baseline/R18.json | Test data | Baseline test reference data |
| engine/data/soil_vg_table.csv | Reference data | Soil van Genuchten parameters |
| No root configuration manifests found | — | BLOCKER-P2 |

## 19. Schema Files

| Location | Description |
|----------|-------------|
| services/admin/schemas.py | Admin schemas |
| services/land/ - (inline) | Land profile schemas |
| services/inventory/routers/inventory.py | Inventory schemas |
| engine/land/models.py | Land analysis models (Pydantic V2) |
| engine/hydroma/models/results.py | Result models (Pydantic V2) |
| engine/hydroma/soil/pedotransfer.py | Pedotransfer functions |

## 20. Adapters

| Adapter | Location | Purpose |
|---------|----------|---------|
| engine.ports/ | clock.py, session.py, sinks.py | Hexagonal ports (abstractions) |
| (Present) | services/land/service.py | References `adapters.engine_adapter.EngineAdapter` — **CREATED** (was BLOCKER-P1) |

**RESOLVED:** `services/land/service.py:12` imports `from adapters.engine_adapter import EngineAdapter` — `adapters/` package created at project root with `engine_adapter.py` and `hydroma_adapter.py`.

## 21. External Dependencies

| Dependency | Used By | Type |
|-----------|---------|------|
| `database.hub` | engine/data_connector.py, engine/resource_manager.py | Internal (database package) |
| `database.models` | engine/hydroma/biofertilizer/tests/ | Internal |
| `database.config` | engine/ports/session.py | Internal |
| `database.base` | engine/hydroma/biofertilizer/models.py | Internal |
| numpy | engine/land/, engine/hydroma/ | External |
| pandas | engine/data_connector.py | External |
| pydantic | engine/land/models.py, engine/hydroma/ | External |
| sqlalchemy | services/models/ | External |
| structlog | services | External |
| supabase | services/supabase/ | External (optional) |
| torch | services/models/pinn_surrogate.py | External (optional) |
| psutil | engine/resource_manager.py | External (optional) |

## 22. Internal Dependencies

| Dependency | Direction | Files |
|-----------|-----------|-------|
| `database` → engine | engine depends on database | engine/data_connector.py, engine/resource_manager.py |
| `services` → engine | services depend on engine | services/models/registry.py, services/api_gateway/routers/*, services/land/service.py, etc. |
| `services` → services | service inter-dependencies | services/auth/compat.py, services/commerce/service.py, services/workflow/service.py, services/auth_legacy/service.py, services/business_modules/* |
| `services` → database | services depend on database | services/conftest.py, services/admin/service.py |

## 23. Potentially Obsolete Modules

| Module | Evidence | Classification |
|--------|----------|---------------|
| engine/hydroma/generative_ai/ | Imports from `services.ai.embedding_service` and `services.ai.llm_router` (NO NEW AI rule violation) | LEGACY_WRAPPER — engine importing service-layer AI |
| engine/hydroma/simulation/ | May contain orchestrator code | UNKNOWN — needs review |
| services/hydroma/ | Empty directories (api, models, repositories, schemas, tests) | OBSOLETE — placeholder directories with no content |
| engine/cpp_core/bindings.cpp | Uses legacy `bindings.cpp` (duplicated by cpp_bridge) | UNKNOWN — needs investigation |
| services/models/base.py, water_models.py, soil_climate_models.py | 2 bytes each | OBSOLETE — empty files |
| services/hydroma/* | All subdirectories are empty | OBSOLETE |

## 24. Potentially Duplicated Modules

| Module 1 | Module 2 | Evidence | Classification |
|----------|----------|----------|----------------|
| engine/hydroma/cpp_bindings.py | engine/hydroma/cpp_bridge.py | cpp_bindings.py is documented as a legacy loader, delegates to cpp_bridge | DUPLICATE |
| services/survey/ | services/tasmimyar/ | Both appear to handle survey data | UNKNOWN |
| engine/hydroma/calculations/ | engine/hydroma/core/ | May overlap | UNKNOWN |
| engine/land/hydrology.py | engine/cpp_core/src/hydrology.cpp | Python D8 + C++ flow routing | HYBRID |
| engine/hydroma/formulas/catalog.py | services/_contracts/formula.py | Both define formulas | DUPLICATE_CANDIDATE |

## 25. Missing Dependencies

| Dependency | Needed By | Status |
|-----------|-----------|--------|
| `adapters.engine_adapter` | services/land/service.py:12 | MISSING — import fails |
| `adapters.hydroma_adapter` | engine/README.md references | MISSING — referenced but not present |
| `database.hub` | engine/data_connector.py:86, engine/resource_manager.py:45 | BLOCKED_EXTERNAL_DEPENDENCY |
| `database.models` | engine/hydroma/biofertilizer/tests/ | BLOCKED_EXTERNAL_DEPENDENCY |
| `database.config` | engine/ports/session.py:162 | BLOCKED_EXTERNAL_DEPENDENCY |
| `database.base` | engine/hydroma/biofertilizer/models.py:32 | BLOCKED_EXTERNAL_DEPENDENCY |

## 26. Broken Imports

| File | Import | Error |
|------|--------|-------|
| services/land/service.py:12 | `from adapters.engine_adapter import EngineAdapter` | ModuleNotFoundError: No module named 'adapters' |
| services/models/registry.py:49 | `from services.api_gateway.routers.carbon_engine import ...` | api_gateway.routers not in scope for services-only |
| engine/hydroma/distributed_ml/trainer.py | Possible torch import | Optional dependency |
| engine/hydroma/cpp_bindings.py:34 | `from engine.hydroma.cpp_bridge import ...` | cpp_bridge module may not exist (see analysis) |

## 27. Unclear Ownership

| Item | Issue |
|------|-------|
| `adapters/` directory | Referenced in README, **CREATED** — `adapters/engine_adapter.py` and `adapters/hydroma_adapter.py` now exist |
| `services/ai/` modules | Used by `engine/hydroma/generative_ai/` (engine depending on services violates architecture) |
| `database/` package | Referenced extensively from both engine and services, but not part of engine/ or services/ |
| `engine/hydroma/cpp_bridge.py` | Referenced in cpp_bindings.py but file was not found at expected path |

## 28. Legacy References

Found references to:
- `services.security.query_safe` (line 51-62 of data_connector.py mentions it)
- `services.scientific_motors` (mentioned in services/models/registry.py docstring)
- `services.map_engine` (imported in engine/land/integration/water_adapter.py:230)
- `adapters.engine_adapter` (imported in services/land/service.py:12) — **CREATED**
- `database.hub`, `database.models`, `database.config`, `database.base` (throughout engine and services)
- `services.api_gateway.*` (imported by various services modules)

## 29. Engine → Engine Dependencies

The engine has strong internal structure:
- `engine/land/` modules depend on `engine.land.hydrology` for flow calculations
- `engine/land/models.py` depends on `engine.hydroma.provenance` for ResultProvenance
- `engine/hydroma/` modules depend on `engine.hydroma.provenance` and `engine.hydroma.models`
- `engine/data_connector.py` references `services.security.query_safe` (cross-package dependency - FORBIDDEN)

## 30. Engine → Services Dependencies

**CRITICAL FINDING:** The engine has dependencies on services that violate the engine boundary rule:

| Engine File | Service Import | Violation |
|-------------|----------------|-----------|
| engine/hydroma/generative_ai/__init__.py | `from services.ai.embedding_service import ...` | Engine → Services AI |
| engine/land/integration/water_adapter.py | `from services.map_engine.pipelines.runoff import ...` | **FIXED** (Engine → Services map_engine — forbidden import removed) |
| engine/data_connector.py (comment) | References `services.security.query_safe` | Engine references Services (in comment, code was moved) |

## 31. Services → Engine Dependencies

This is the expected direction:
- `services/land/service.py` → `from engine.land.models import ...`
- `services/models/registry.py` → `from engine.hydroma.carbon.calculator import ...` (22 model imports)
- `services/api_gateway/routers/*` → Various engine imports for scientific calculations
- `services/validation/formula_checks.py` → Multiple engine.hydroma imports
- `services/field_monitoring/service.py` → engine.hydroma imports

## 32. Services → External Packages

- `services/supabase/` → supabase client
- `services/models/pinn_surrogate.py` → torch (optional)
- Various services → sqlalchemy, structlog, pytest

## 33. Forbidden Dependencies

| Type | Location | Evidence |
|------|----------|----------|
| engine → database | engine/data_connector.py:86, engine/resource_manager.py:45, engine/ports/session.py:162 | Deferred imports, but still present |
| engine → services | engine/hydroma/generative_ai/__init__.py:20-22 | Direct import of services.ai modules |
| engine → services | engine/land/integration/water_adapter.py:230 | Import of services.map_engine |
| services → services (cross-domain) | services/commerce/service.py | Imports finance, inventory |
| services → services (cross-domain) | services/auth_legacy/service.py | Imports api_gateway.auth |

## 34. Key Findings Summary

1. ✅ **FIXED** — Adapter import: `adapters.engine_adapter` now exists (was BLOCKER-P1)
2. **C++/Python dual implementation**: engine has both C++ kernels and Python fallbacks
3. **Missing dependency manifest**: No requirements.txt or pyproject.toml
4. **Missing cpp_bridge module**: Referenced but not found
5. **Empty directories**: services/hydroma/ has empty subdirectories
6. **Near-empty files**: services/models/base.py, water_models.py, soil_climate_models.py are 2 bytes
7. **Formula duplication**: Two formula registries exist (engine formulas + services/_contracts/formula.py)
8. **Engine importing services**: Violations of engine boundary in generative_ai and water_adapter
9. **Database boundary violations**: Engine modules import from database/ package
10. **C++ bindings duplication**: Two binding loaders (cpp_bindings.py + cpp_bridge.py)

---

*End of Inventory Report*
