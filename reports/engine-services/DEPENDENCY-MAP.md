# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — DEPENDENCY MAP

**Document ID:** ECO-00-DEPENDENCY-MAP  
**Date:** 2026-10-08  
**Status:** COMPLETE
**Auditor:** Kilo autonomous agent

---

## 1. Dependency Graph (Visual)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              LAYER 3                                    │
│                              services/                                  │
│   (FastAPI API gateway, business logic, auth, wallet, commerce, carbon, │
│    satellite, MRV, notification, workflow, marketplace, tourism, ...)  │
├─────────────────────────────────────────────────────────────────────────┤
│                              LAYER 2                                    │
│                              engine/                                    │
│   (Scientific computation core: land analysis, hydroma climate/soil/    │
│    carbon/watershed/simulation, C++ kernels with Python fallbacks)      │
├─────────────────────────────────────────────────────────────────────────┤
│                              LAYER 1                                    │
│                              database/                                  │
│   (Shared ORM models, session management, connection hub — NOT in repo)  │
├─────────────────────────────────────────────────────────────────────────┤
│                              LAYER 0                                    │
│                         Third-party packages                           │
│   (numpy, pandas, pydantic, sqlalchemy, fastapi, structlog, pytest, ...) │
└─────────────────────────────────────────────────────────────────────────┘
```

**External Package:** `database/` (must be provisioned externally)
**External Package:** `adapters/` (MISSING — referenced but not present)

---

## 2. Engine → Engine Dependency Graph

### Core Modules
```
engine/__init__.py
├── engine.data_connector
├── engine.safe_math
└── engine.resilience

engine.data_connector.py ──> database.hub (deferred)
engine.resource_manager.py ──> database.hub (deferred, 3x)
engine.ports/session.py ──> database.config, database.hub (deferred)
engine.ports/session.py ──> database.base (deferred)

engine.ports/
├── clock.py
├── session.py ──> database.* (deferred)
└── sinks.py
```

### Land Engine
```
engine/land/
├── __init__.py
├── models.py ──> engine.hydroma.provenance.ResultProvenance
├── dem_processor.py
├── hydrology.py (D8 flow routing — self-contained)
├── terrain_analysis.py
├── slope_aspect.py
├── drainage.py
├── capability.py
├── erosion_risk.py
├── surface_water_analysis.py
├── integration/
│   ├── __init__.py
│   ├── models.py
│   ├── soil_integrator.py
│   └── water_adapter.py ──> services.map_engine.pipelines.runoff (FORBIDDEN)
└── tests/ (self-contained, imports engine.land.*)
```

### Hydroma Engine
```
engine/hydroma/
├── __init__.py ──> engine.hydroma.models.results
├── wrapper.py
│   ├── engine.hydroma.cpp_bridge
│   └── engine.hydroma.cpp_bindings (delegates to cpp_bridge)
├── cpp_bindings.py ──> engine.hydroma.cpp_bridge (delegation)
├── cpp_bridge/
│   ├── __init__.py ← hydroma_core.pyd (C++ extension)
│   │   ├── hydroma_core (C++ .pyd)
│   │   └── numpy/numba (Python fallbacks)
│   ├── indices_fast.py ──> numba (optional)
│   ├── indices_fallback.py ──> numpy
│   ├── soil_physics_fast.py ──> numba (optional)
│   ├── soil_physics_fallback.py ──> numpy
│   ├── hydrology_fast.py
│   ├── hydrology_fallback.py
│   └── tests/
│       ├── test_parity.py
│       └── test_benchmarks.py
├── formulas/
│   ├── catalog.py (34+ FormulaRecord entries)
│   ├── records.py
│   └── research/__init__.py
├── climate/et_calculator.py ──> engine.hydroma.cpp_bridge
├── soil/physics.py ──> engine.data.soil_table, engine.hydroma.cpp_bridge
├── carbon/calculator.py
├── economics/ (analysis, costing, employment, revenue, risk, roi)
├── water/quality.py
├── groundwater/service.py
├── simulation/
│   ├── orchestrator.py ──> engine.hydroma.cpp_bridge
│   ├── weather_source.py
│   ├── calibration.py
│   ├── scenarios.py
│   ├── contracts.py
│   └── runners/rothc_runner.py
├── irrigation/scheduler.py
├── models/ (base, results, epia, hpheno, runoff_model, groundwater_model)
├── mrv/ (metrics, iot_ingest, qa, schemas)
├── crop/ndvi_analysis.py ──> engine.hydroma.wrapper
├── satellite/processors/indices.py
├── calculations/crop_water_req_calc.py
├── simulation_env/ (weather, climate)
├── data_assimilation/
├── hybrid_ml/ (pinn, gp_surrogate) ──> torch (optional)
├── distributed_ml/trainer.py ──> torch (optional)
├── materials/compost_formulator.py
├── generative_ai/__init__.py ──> services.ai.* (FORBIDDEN - mitigated via lazy)
├── tests/
└── core/database.py (documentation only)
```

### Baseline
```
engine/baseline/
├── cases.py ──> engine.hydroma.* (imports from ~20 module paths)
├── capture.py ──> engine.baseline.cases
└── R18.json
```

### Strict Tests
```
engine/strict_tests/
├── conftest.py ──> engine.hydroma.cpp_bridge, engine.hydroma.soil.physics
├── test_s00 through test_s15
└── thresholds.py
```

### Data
```
engine/data/
├── soil_table.py ──> engine.data.physics_guard
├── physics_guard.py
└── generate_cpp_table.py
```

---

## 3. Services → Engine Dependency Graph

```
services/
├── land/
│   ├── service.py ──> engine.land.models (5 classes)
│   └── tests/test_integration.py ──> engine.land.models
│
├── api_gateway/
│   ├── main.py ──> engine.hydroma.config.settings
│   ├── auth.py ──> engine.hydroma.config.settings
│   ├── errors.py (standalone)
│   ├── security.py ──> services.api_gateway.observability
│   ├── tracing.py ──> engine.hydroma.config.settings
│   ├── settings_repository.py ──> engine.hydroma.config.settings, database.hub
│   ├── eventbus/
│   │   └── nats_client.py ──> engine.hydroma.config.settings
│   └── routers/
│       ├── watershed.py ──> engine.hydroma.watershed.calculator
│       ├── soil.py ──> engine.hydroma.wrapper
│       ├── simulation.py ──> engine.hydroma.simulation.*
│       ├── scenarios.py ──> engine.hydroma.wrapper
│       ├── hydroma_mrv.py ──> engine.hydroma.mrv.*, engine.hydroma.wrapper
│       ├── hydroma_indices.py ──> engine.hydroma.models.*, engine.hydroma.wrapper
│       ├── carbon_engine.py ──> engine.hydroma.cpp_bindings
│       ├── platform.py ──> engine.hydroma.cpp_bindings
│       ├── analyses.py ──> engine.hydroma.analyses.*, engine.hydroma.models.*
│       ├── hydroma_climate.py ──> engine.hydroma.climate.*, irrigation.*, simulation.*
│       ├── hydroma_economics.py ──> engine.hydroma.economics.*
│       ├── hydroma_soil.py ──> engine.hydroma.soil.*
│       ├── hydroma_water.py ──> engine.hydroma.groundwater, engine.hydroma.models.*, watershed
│       ├── hydroma_simulation.py ──> engine.hydroma.simulation.*
│       ├── hydroma_carbon.py ──> engine.hydroma.carbon.calculator
│       ├── nojin.py ──> engine.hydroma.biofertilizer.*
│       ├── land.py ──> engine.land.models
│       ├── satellite.py ──> engine.hydroma.config.settings
│       ├── realtime.py ──> engine.hydroma.config.settings
│       ├── auth.py ──> engine.hydroma.config.settings
│       ├── auth_supabase.py ──> engine.hydroma.config.settings
│       ├── dashboard.py ──> engine.hydroma.config.settings
│       ├── analytics.py ──> engine.hydroma.config.settings
│       ├── automation.py ──> engine.hydroma.config.settings
│       ├── compliance.py ──> engine.hydroma.config.settings
│       ├── community.py ──> engine.hydroma.config.settings
│       ├── content_public.py ──> engine.hydroma.config.settings
│       ├── admin_content.py ──> engine.hydroma.config.settings
│       ├── admin_users.py ──> engine.hydroma.config.settings
│       ├── admin_security.py ──> engine.hydroma.config.settings
│       ├── blockchain.py ──> engine.hydroma.config.settings
│       ├── culture.py ──> engine.hydroma.config.settings
│       ├── contact.py ──> engine.hydroma.config.settings
│       ├── models.py ──> engine.hydroma.cpp_bridge (conditional)
│       ├── ai_chat.py ──> engine.hydroma.config.settings
│       └── sync.py ──> engine.hydroma.config.settings
│
├── models/
│   ├── registry.py ──> engine.hydroma.carbon.calculator (22 model imports)
│   └── pinn_surrogate.py ──> torch (optional)
│
├── validation/formula_checks.py ──> engine.hydroma.* (14 imports)
│
├── field_monitoring/service.py ──> engine.hydroma.soil.health, engine.hydroma.water.quality
│
├── workflow/
│   ├── service.py ──> engine.hydroma.simulation.*, engine.hydroma.decision_support.*
│   └── main.py ──> engine.hydroma.simulation.*, engine.hydroma.decision_support.*
│
├── nojin/repository.py ──> engine.hydroma.biofertilizer.models
│
├── admin/
│   ├── service.py ──> services.api_gateway.errors (conditional: marketplace, tourism, landscape)
│   └── overview_service.py ──> services.admin.repository_overview, services.api_gateway.eventbus
│
├── auth/
│   ├── compat.py ──> services.api_gateway.auth
│   └── permissions.py ──> services.landscape.models (conditional)
│
├── auth_legacy/
│   ├── service.py ──> services.api_gateway.auth, services.api_gateway.eventbus
│   └── repository.py ──> services.api_gateway.logging (conditional)
│
├── commerce/
│   ├── service.py ──> services.finance.*, services.inventory, services.api_gateway.exceptions
│   └── tests/
│
├── business_modules/
│   ├── voice/
│   │   ├── voice_assistant.py ──> services.ai.llm_router, services.ai.unified_rag
│   │   ├── whisper_stt.py ──> services.business_modules.voice.stt_provider
│   │   └── tts_provider.py ──> services.business_modules.voice.tts_provider (conditional)
│   └── iot/
│       └── device_connector.py ──> engine.hydroma.mrv.iot_ingest
│
├── contracts/ ├── models.py ──> database.base
│   ├── router.py ──> services.contracts.service, services.contracts.schemas
│   └── service.py ──> services.contracts.models, schemas

├── backup/
│   ├── service.py ──> services.backup.models, schemas, services.api_gateway.errors
│   └── router.py ──> services.backup.schemas, service

├── carbon/
│   └── service.py ──> database.models

├── ecowallet/
│   └── service.py ──> database.models

├── wallet/
│   ├── eco_balance.py ──> database.models
│   └── credits.py ──> database.models

├── satellite/ (standalone package)
├── oracle/ (standalone package)
├── privacy/ (standalone package)
├── ecosystem/ (standalone package)
├── analytics/ (standalone package)
├── field_monitoring/
├── inventory/ (standalone package)
├── finance/ (standalone package)
├── governance/ (standalone package)
└── tests/
```

---

## 4. Services → Services Dependency Matrix

| Service → Depends On | admin | auth | auth_legacy | backup | commerce | contracts | ecowallet | finance | inventory | workflow | business_modules | api_gateway | models |
|----------------------|------|------|-------------|--------|----------|-----------|-----------|---------|-----------|----------|-----------------|-------------|--------|
| admin                | -    | -    | -           | -      | -        | -         | -         | -       | -         | -        | -               | ✓           | -      |
| auth                 | -    | -    | -           | -      | -        | -         | -         | -       | -         | -        | -               | ✓           | -      |
| auth_legacy          | -    | ✓    | -           | -      | -        | -         | -         | -       | -         | -        | -               | ✓           | -      |
| backup               | -    | -    | -           | -      | -        | -         | -         | -       | -         | -        | -               | ✓           | -      |
| commerce             | -    | -    | -           | -      | -        | ✓         | -         | ✓✓✓     | ✓         | -        | -               | ✓           | -      |
| contracts            | -    | -    | -           | -      | -        | -         | -         | -       | -         | -        | -               | ✓           | -      |
| workflow             | -    | -    | -           | -      | -        | -         | -         | -       | -         | -        | -               | ✓           | -      |
| business_modules     | -    | -    | -           | -      | -        | -         | -         | -       | -         | -        | -               | ✓           | ✓      |
| models               | -    | -    | -           | -      | -        | -         | -         | -       | -         | -        | -               | -           | -      |

**Legend:**
- ✓ = dependency exists
- ✓✓✓ = heavy dependency (multiple modules)

---

## 5. Engine → Services Forbidden Dependencies

### Violation 1: Engine Generative AI → Services AI

| Attribute | Value |
|-----------|-------|
| **File** | `engine/hydroma/generative_ai/__init__.py` |
| **Import Pattern** | `from services.ai.embedding_service import EmbeddingService as EmbeddingProvider` |
| **Import Pattern** | `from services.ai.llm_router import LLMProvider, LLMRouter` |
| **Import Pattern** | `from services.ai.unified_rag import RAGConfig, UnifiedRAG as RAGEngine` |
| **Status** | **MITIGATED** — all three imports moved to lazy `PEP 562 __getattr__` |
| **Remaining Risk** | Lazy imports still create a runtime dependency on `services` being importable when these names are accessed |
| **Recommendation** | Remove this module entirely — engine should not depend on services at all |

### Violation 2: Engine Land Integration → Services Map Engine

| Attribute | Value |
|-----------|-------|
| **File** | `engine/land/integration/water_adapter.py` |
| **Line** | 230 |
| **Import** | `from services.map_engine.pipelines.runoff import ...` |
| **Status** | **FIXED** — forbidden import removed |
| **Impact** | `import engine.land.integration.water_adapter` will fail if `services` is not importable |
| **Recommendation** | Remove the import or convert to lazy loading |

### Violation 3: Engine Data Connector → Services Security (Comment Reference)

| Attribute | Value |
|-----------|-------|
| **File** | `engine/data_connector.py` |
| **Lines** | 51-62 |
| **Reference** | Comment mentions `services.security.query_safe` |
| **Status** | Resolved — the allowlist was moved to engine's own code |
| **Note** | The comment documents that the allowlist was DELETED from services and reimplemented in engine |

---

## 6. Engine → database Dependencies (External Package)

| Engine File | Line | Import | Pattern | Status |
|-------------|------|--------|---------|--------|
| `engine/data_connector.py` | 86 | `from database.hub import hub` | Deferred | Acceptable fallback |
| `engine/resource_manager.py` | 45 | `from database.hub import hub` | Deferred | Acceptable fallback |
| `engine/resource_manager.py` | 70 | `from database.hub import hub` | Deferred | Acceptable fallback |
| `engine/resource_manager.py` | 83 | `from database.hub import hub` | Deferred | Acceptable fallback |
| `engine/ports/session.py` | 162 | `from database.config import SessionLocal` | Deferred | Acceptable fallback |
| `engine/ports/session.py` | 201 | `from database.hub import hub` | Deferred | Acceptable fallback |
| `engine/hydroma/biofertilizer/models.py` | 32 | `from database.base import Base` | Deferred | Acceptable fallback |
| `engine/hydroma/biofertilizer/tests/conftest.py` | 10-11 | `from database.base import Base`, `from database.hub import hub` | Top-level | Test-only |
| `engine/hydroma/biofertilizer/tests/test_calibration_session.py` | 27 | `from database.config import SessionLocal` | Deferred | Test-only |
| `engine/hydroma/biofertilizer/tests/test_calibration_session.py` | 80 | `from database.models import NojinCalibrationRecordDB` | Deferred | Test-only |
| `engine/strict_tests/test_s12_table_registration.py` | 154-155 | `from database.base import Base`, `from database.config import Base` | Deferred | Test-only |
| `engine/strict_tests/test_s12_table_registration.py` | 198-201 | `from database.base import Base`, `from database.models` | Deferred | Test-only |
| `engine/strict_tests/test_s12_table_registration.py` | 249 | `from database.base import Base` | Deferred | Test-only |
| `engine/hydroma/core/database.py` | — | Documents `database.config` | Documentation | Documentation only |

**Classification:** BLOCKED_EXTERNAL_DEPENDENCY — The `database/` package is not present in the repository. All imports are deferred, meaning the engine can be imported without `database/` installed. The `database` package must be provisioned separately.

---

## 7. Services → database Dependencies (External Package)

Services depend on `database/` for ORM models and session management. Over 100 import statements across 40+ files. The main patterns are:

1. `from database.hub import hub` — Session/database hub (primary)
2. `from database.hub.hub import hub` — Same, different path
3. `from database.models import <ModelClass>` — ORM model classes
4. `from database.base import Base` — SQLAlchemy base class
5. `from database.config import SessionLocal, Base` — Session factory

All service files that use `database` use deferred/lazy imports inside functions or methods.

**Classification:** BLOCKED_EXTERNAL_DEPENDENCY — Same as engine.

---

## 8. Services → engine Dependency Count

Total services → engine import statements: **~100+** across **30+ service files**

Most common engine imports from services:
1. `engine.hydroma.config.settings` (get_settings) — ~25 files
2. `engine.hydroma.cpp_bridge` — 4 files
3. `engine.hydroma.cpp_bindings` — 2 files
4. `engine.land.models` — 3 files
5. `engine.hydroma.watershed.calculator` — 2 files
6. `engine.hydroma.soil.*` — 2 files
7. `engine.hydroma.economics.*` — 1 file
8. `engine.hydroma.climate.*` — 2 files
9. `engine.hydroma.models.*` — 3 files

---

## 9. Circular Dependency Analysis

### Circular Dependency 1: engine.generative_ai ↔ services.ai

```
engine/hydroma/generative_ai/__init__.py
    → imports services.ai.embedding_service (lazy)
    → imports services.ai.llm_router (lazy)
    → imports services.ai.unified_rag (lazy)
services/ai/*
    → imports engine.hydroma.* (various)
```

**Status:** Mitigated via lazy loading. The circular dependency exists at runtime when the lazy imports are triggered. If `services.ai` imports `engine.hydroma.generative_ai` at module level, a circular import would occur.

### Circular Dependency 2: engine.hydroma.cpp_bridge ↔ engine.hydroma.cpp_bindings

```
engine/hydroma/cpp_bindings.py
    → imports engine.hydroma.cpp_bridge
engine/hydroma/cpp_bridge/__init__.py
    → does NOT import cpp_bindings
```

**Status:** No cycle. `cpp_bindings` is a one-way delegation layer.

---

## 10. External Dependencies (Third-Party)

| Package | Required? | Used By | Notes |
|---------|-----------|---------|-------|
| `numpy` | **Yes** | engine, services | Core numerical computing |
| `pydantic` | **Yes** | engine, services | Data validation |
| `pydantic-settings` | **Yes** | engine/config/settings.py | Settings management |
| `pandas` | Optional | engine/data_connector.py | Deferred import |
| `pyyaml` | Optional | Various | Deferred import |
| `sqlalchemy` | **Yes** | services | ORM framework |
| `fastapi` | **Yes** | services/api_gateway | API framework |
| `structlog` | Optional | services | Structured logging |
| `pytest` | **Yes (test)** | All tests | Testing framework |
| `pytest-asyncio` | Optional (test) | tests | Async test support |
| `psutil` | Optional | engine | Memory monitoring |
| `torch` | Optional | services/models/pinn_surrogate, engine/hydroma/distributed_ml | ML surrogate |
| `supabase` | Optional | services/supabase | Cloud DB client |
| `numba` | Optional | engine/hydroma/cpp_bridge | JIT compiler for Python fallback |
| `pybind11` | **Yes** (C++ build) | engine/cpp_core | C++/Python bridge |

---

## 11. Missing Dependencies

### 11.1 RESOLVED: `adapters` package at root

| Attribute | Value |
|-----------|-------|
| **Referenced by** | `services/land/service.py:12` |
| **Import** | `from adapters.engine_adapter import EngineAdapter` |
| **Status** | **CREATED** — `adapters/engine_adapter.py` and `adapters/hydroma_adapter.py` now exist |
| **Classification** | FIXED (BLOCKER-P1 resolved) |

### 11.2 Missing: `database` package

| Attribute | Value |
|-----------|-------|
| **Referenced by** | 20+ engine files, 40+ service files |
| **Import patterns** | `from database.hub import hub`, `from database.models import ...`, `from database.base import Base` |
| **Status** | **MISSING** — external package not in repository |
| **Classification** | BLOCKED_EXTERNAL_DEPENDENCY |

### 11.3 RESOLVED: `services.map_engine` module (was BLOCKER-P1)

| Attribute | Value |
|-----------|-------|
| **Referenced by** | `engine/land/integration/water_adapter.py:230` (FORBIDDEN) |
| **Status** | **FIXED** — forbidden import removed from water_adapter.py |
| **Classification** | BLOCKER-P1 resolved |

---

## 12. Dependency Isolation Recommendations

### Phase 1: Immediate (P0/P1)
1. ✅ FIXED — `adapters/` package created with `engine_adapter.py` and `hydroma_adapter.py`
2. ✅ FIXED — removed `engine/land/integration/water_adapter.py:230` import of `services.map_engine`

### Phase 2: Architectural (P3)
1. Remove `engine/hydroma/generative_ai/__init__.py` or move its content to services layer
2. Create a `database` stub package or interface to decouple the dependency

### Phase 3: Long-term
1. Establish a clean `adapters/` package at project root for engine↔service adapters
2. Implement dependency inversion: services depend on engine abstractions (interfaces), not engine implementations

---

*End of Dependency Map*
