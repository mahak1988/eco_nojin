# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — DEPENDENCY FORENSICS REPORT

**Document ID:** ECO-00-DEPENDENCY-FORENSICS  
**Date:** 2026-10-08  
**Status:** COMPLETE
**Auditor:** Kilo autonomous agent

---

## 1. Dependency Graph Summary

The HyDroMA codebase has a three-layer architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                        services/                                 │
│    (FastAPI API gateway, business logic, auth, wallet, etc.)    │
├─────────────────────────────────────────────────────────────────┤
│                        engine/                                   │
│    (Scientific computation core, C++ kernels, data models)      │
├─────────────────────────────────────────────────────────────────┤
│                        database/                               │
│    (Shared ORM models, session management, connection hub)      │
│                           (external)                            │
└─────────────────────────────────────────────────────────────────┘
```

### Key External Dependency
The `database/` package is referenced extensively but is **not present** in the `engine/` or `services/` directories. It appears to be an external/shared package that must be installed alongside this codebase or lives outside the repository.

## 2. Engine → Engine Dependencies (Internal)

### Core Engine Modules
```
engine/__init__.py
  └─ engine.data_connector.connector
  └─ engine.safe_math (safe_sqrt, safe_log, nan_guard)
  └─ engine.resilience (circuit_breaker, with_timeout)

engine.data_connector.py
  └─ database.hub (deferred import)

engine.resource_manager.py
  └─ database.hub (deferred import)

engine.resilience.py
  └─ engine.resilience (self-reference, test)

engine.safe_math.py
  └─ engine.safe_math (self-reference, test)
```

### Land Engine
```
engine/land/
  ├─ models.py
  │   └─ engine.hydroma.provenance.ResultProvenance → models
  │
  ├─ terrain_analysis.py
  │
  ├─ hydrology.py (D8 flow routing)
  │
  ├─ slope_aspect.py
  │
  ├─ drainage.py
  │
  ├─ capability.py
  │
  ├─ erosion_risk.py
  │
  ├─ surface_water_analysis.py
  │
  ├─ dem_processor.py
  │
  ├─ integration/
  │   └─ water_adapter.py
  │       └─ services.map_engine.pipelines.runoff → FORBIDDEN (engine→services)
  │   └─ models.py
  │   └─ soil_integrator.py
  │
  └─ tests/ (test_terrain, test_slope, test_models, test_land_improved, test_land_comprehensive)

engine/land/slope_aspect.py
  └─ engine.land.models
```

### Hydroma Engine
```
engine/hydroma/
  ├─ __init__.py
  │   └─ engine.hydroma.models.results
  │   └─ engine.hydroma.cpp_bridge (delegated backend)
  │
  ├─ wrapper.py (high-level facade)
  │   └─ engine.hydroma.cpp_bridge
  │   └─ engine.hydroma.cpp_bindings (legacy loader, now delegates to cpp_bridge)
  │
  ├─ cpp_bindings.py
  │   └─ engine.hydroma.cpp_bridge (delegation pattern)
  │
  ├─ cpp_bridge/ (package directory)
  │   ├─ __init__.py        # Main bridge with telemetry, fallback logic
  │   ├─ indices_fast.py    # Numba-accelerated indices
  │   ├─ indices_fallback.py # NumPy fallback for indices
  │   ├─ soil_physics_fast.py # Numba-accelerated soil physics
  │   ├─ soil_physics_fallback.py # NumPy fallback for soil physics
  │   ├─ hydrology_fast.py   # Numba-accelerated hydrology
  │   ├─ hydrology_fallback.py # NumPy fallback for hydrology
  │   ├─ hydroma_core.*.pyd # Compiled C++ extension (Python 3.11, 3.12)
  │   ├─ hydroma_core.lib/.exp # Linker artifacts
  │   ├─ tests/
  │   │   ├─ test_parity.py  # C++/Python parity tests
  │   │   └─ test_benchmarks.py
  │   └─ README_STATUS_FA.md
  │
  ├─ formulas/
  │   ├─ catalog.py    # 34+ FormulaRecord entries
  │   ├─ registry.py
  │   ├─ records.py
  │   └─ research/
  │
  ├─ watershed/
  │   ├─ calculator.py → engine.hydroma.cpp_bridge
  │   ├─ models.py
  │   ├─ tests/
  │   └─ schemas.py
  │
  ├─ climate/
  │   └─ et_calculator.py → engine.hydroma.cpp_bridge._py_penman_monteith_et0
  │
  ├─ soil/
  │   ├─ physics.py → engine.hydroma.cpp_bridge
  │   ├─ chemistry.py
  │   ├─ health.py
  │   ├─ pedotransfer.py
  │   ├── salinity.py
  │   ├── taxonomy.py
  │   ├── texture.py
  │   ├── water_retention.py
  │   └─ ... (multiple modules)
  │
  ├─ carbon/
  │   └─ calculator.py
  │
  ├─ economics/
  │   ├─ analysis.py (NPV, payback)
  │   ├─ costing.py
  │   ├─ employment.py
  │   ├─ revenue.py
  │   ├─ risk.py
  │   └─ roi.py
  │
  ├─ water/
  │   └─ quality.py
  │
  ├─ groundwater/
  │   ├─ models.py
  │   └─ service.py
  │
  ├─ simulation/
  │   ├─ orchestrator.py
  │   ├─ weather_source.py
  │   ├─ calibration.py
  │   ├── scenarios.py
  │   ├── contracts.py
  │   ├── runners/
  │   │   └─ rothc_runner.py
  │   └─ ...
  │
  ├─ irrigation/
  │   └─ scheduler.py
  │
  ├─ models/
  │   ├─ base.py (ScientificModel)
  │   ├── results.py
  │   ├── expansion/
  │   │   └─ registry.py
  │   ├── epia.py
  │   ├── hpheno.py
  │   ├── runoff_model.py
  │   └── groundwater_model.py
  │
  ├─ mrv/
  │   ├─ metrics.py → engine.hydroma.wrapper
  │   ├──── iot_ingest.py → engine.hydroma.mrv.qa/schema
  │   ├──── qa.py
  │   └──── schemas.py
  │
  ├─ crop/
  │   └─ ndvi_analysis.py → engine.hydroma.wrapper
  │
  ├─ satellite/
  │   └─ processors/indices.py
  │
  ├─ calculations/
  │   └─ crop_water_req_calc.py
  │
  ├─ simulation_env/
  │   └─ weather.py
  │
  ├─ data_assimilation/
  │   └─ assimilation.py
  │
  ├─ hybrid_ml/
  │   ├─ pinn.py
  │   └─ gp_surrogate.py
  │
  ├─ distributed_ml/
  │   └─ trainer.py (torch optional import)
  │
  ├─ materials/
  │   └─ compost_formulator.py
  │
  ├─ generative_ai/
  │   └─ __init__.py → FORBIDDEN (engine→services.ai)
  │
  ├─ tests/
  │
  └─ core/
      └─ database.py (documents database.config dependency)
```

### Ports (Hexagonal Architecture)
```
engine/ports/
  ├─ __init__.py
  ├─ clock.py (Clock abstraction)
  └─ session.py → database.config, database.hub (deferred)
  └─ sinks.py (NullReadingSink, ReadingSink)
```

### Baseline
```
engine/baseline/
  ├─ cases.py → engine.hydroma.* multiple modules
  ├─ capture.py → engine.baseline.cases
  └─ R18.json (reference data)
```

### Strict Tests
```
engine/strict_tests/
  ├─ conftest.py → engine.hydroma.cpp_bridge, engine.hydroma.soil.physics
  ├─ test_s00 through test_s15
  └─ thresholds.py
```

### Data
```
engine/data/
  ├─ soil_table.py → engine.data.physics_guard
  ├─ physics_guard.py
  └─ generate_cpp_table.py
```

## 3. Services → Engine Dependencies (Expected)

This is the primary and expected dependency direction. Services import from the engine for scientific computations.

### Service → Engine Import Summary

| Service | Engine Imports |
|---------|---------------|
| services/land/service.py | `engine.land.models` (5 classes) |
| services/land/tests/test_integration.py | `engine.land.models` |
| services/land/land_profile.py | (no engine imports — uses local models) |
| services/api_gateway/main.py | `engine.hydroma.config.settings`, `engine.hydroma.carbon.calculator`, `engine.hydroma.cpp_bridge` |
| services/api_gateway/routers/*.py | 20+ routers import from `engine.hydroma.*` and `engine.land.*` |
| services/api_gateway/routers/watershed.py | `engine.hydroma.watershed.calculator` |
| services/api_gateway/routers/soil.py | `engine.hydroma.wrapper` |
| services/api_gateway/routers/simulation.py | `engine.hydroma.simulation.*` |
| services/api_gateway/routers/scenarios.py | `engine.hydroma.wrapper` |
| services/api_gateway/routers/hydroma_mrv.py | `engine.hydroma.mrv.*`, `engine.hydroma.wrapper` |
| services/api_gateway/routers/hydroma_indices.py | `engine.hydroma.models.*`, `engine.hydroma.wrapper` |
| services/api_gateway/routers/carbon_engine.py | `engine.hydroma.cpp_bindings` |
| services/api_gateway/routers/platform.py | `engine.hydroma.cpp_bindings` |
| services/api_gateway/routers/analyses.py | `engine.hydroma.analyses.*`, `engine.hydroma.models.*` |
| services/api_gateway/routers/hydroma_climate.py | `engine.hydroma.climate.*`, `engine.hydroma.irrigation.*`, `engine.hydroma.simulation.*` |
| services/api_gateway/routers/hydroma_economics.py | `engine.hydroma.economics.*` |
| services/api_gateway/routers/hydroma_soil.py | `engine.hydroma.soil.*` |
| services/api_gateway/routers/hydroma_water.py | `engine.hydroma.groundwater.service`, `engine.hydroma.models.*`, `engine.hydroma.watershed.calculator` |
| services/api_gateway/routers/hydroma_simulation.py | `engine.hydroma.simulation.*` |
| services/api_gateway/routers/hydroma_carbon.py | `engine.hydroma.carbon.calculator` |
| services/api_gateway/routers/nojin.py | `engine.hydroma.biofertilizer.data` |
| services/api_gateway/routers/land.py | `engine.land.models` |
| services/api_gateway/routers/satellite.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/realtime.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/auth.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/auth_supabase.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/dashboard.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/analytics.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/automation.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/compliance.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/community.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/content_public.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/admin_content.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/admin_users.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/admin_security.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/blockchain.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/culture.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/contact.py | `engine.hydroma.config.settings` |
| services/api_gateway/routers/models.py | `engine.hydroma.cpp_bridge` |
| services/api_gateway/middleware/upload_size.py | `engine.hydroma.config.settings` |
| services/api_gateway/middleware/locale.py | `engine.hydroma.config.settings` |
| services/api_gateway/auth.py | `engine.hydroma.config.settings` |
| services/api_gateway/eventbus/nats_client.py | `engine.hydroma.config.settings` |
| services/api_gateway/settings_repository.py | `engine.hydroma.config.settings` |

### Service-to-Service Dependencies (services → services)

| Service | Depends On |
|--------|-----------|
| services/admin/service.py | services.api_gateway.errors |
| services/admin/service.py | services.marketplace.models (conditional) |
| services/admin/service.py | services.tourism.models (conditional) |
| services/admin/service.py | services.landscape.models (conditional) |
| services/admin/overview_service.py | services.admin.repository_overview |
| services/admin/overview_service.py | services.api_gateway.eventbus.nats_client |
| services/admin/__init__.py | services.admin.schemas, service |
| services/admin/api/__init__.py | services.admin.schemas, service |
| services/admin/tests/conftest.py | services.admin.service |
| services/auth/compat.py | services.api_gateway.auth |
| services/auth/service.py | services.auth.compat, models, repository, schemas |
| services/auth/repository.py | services.auth.models |
| services/auth/__init__.py | services.auth.schemas, service |
| services/auth/api/__init__.py | (database.hub) |
| services/auth/tests/ | services.auth.service |
| services/auth/permissions.py | services.landscape.models (conditional) |
| services/auth_legacy/service.py | services.api_gateway.auth |
| services/auth_legacy/service.py | services.api_gateway.eventbus |
| services/auth_legacy/repository.py | services.api_gateway.logging (conditional import) |
| services/auth_legacy/service.py | services.api_gateway.routers.auth (conditional) |
| services/auth_legacy/service.py | services.api_gateway.dependencies (conditional) |
| services/backup/service.py | services.backup.models |
| services/backup/service.py | services.backup.schemas |
| services/backup/service.py | services.api_gateway.errors |
| services/backup/router.py | services.backup.schemas, service |
| services/backup/service.py | database.hub.hub.normalize_database_url (conditional) |
| services/commerce/service.py | services.commerce.service (self) |
| services/commerce/service.py | services.finance.ledger_service |
| services/commerce/service.py | services.finance.payment_provider |
| services/commerce/service.py | services.finance.wallet_service |
| services/commerce/service.py | services.inventory.service |
| services/commerce/service.py | services.api_gateway.exceptions |
| services/commerce/routers/commerce.py | services.commerce.service |
| services/commerce/tests/ | services.commerce.service, services.api_gateway.exceptions |
| services/contracts/router.py | services.contracts.service |
| services/contracts/service.py | services.contracts.models |
| services/contracts/service.py | services.contracts.schemas |
| services/contracts/router.py | services.contracts.service (conditional) |
| services/contracts/models.py | database.base |
| services/workflow/service.py | services.api_gateway.errors |
| services/workflow/main.py | services.api_gateway.errors |
| services/workflow/service.py | database.hub, database.models |
| services/ecowallet/service.py | database.models |
| services/field_monitoring/service.py | engine.hydroma.soil.health |
| services/field_monitoring/service.py | engine.hydroma.water.quality |
| services/models/registry.py | engine.hydroma.carbon.calculator (22 imports) |
| services/validation/formula_checks.py | engine.hydroma.* (14 imports) |
| services/business_modules/voice/voice_assistant.py | services.ai.llm_router |
| services/business_modules/voice/voice_assistant.py | services.ai.unified_rag |
| services/business_modules/voice/whisper_stt.py | services.business_modules.voice.stt_provider |
| services/business_modules/voice/tts_provider.py | services.business_modules.voice.tts_provider (self-reference) |
| services/business_modules/iot/device_connector.py | engine.hydroma.mrv.iot_ingest |
| services/api_gateway/main.py | engine.hydroma.config.settings |
| services/api_gateway/main.py | engine.hydroma.carbon.calculator (conditional) |
| services/api_gateway/main.py | engine.hydroma.cpp_bridge.backend_status (conditional) |

## 4. Engine → Services Dependencies (ForBIDDEN)

**CRITICAL ARCHITECTURAL VIOLATION:** The engine layer imports from the services layer, violating the dependency inversion principle.

### Violation 1: Engine Generative AI → Services AI

**File:** `engine/hydroma/generative_ai/__init__.py`

**Status:** MITIGATED via lazy loading

This module re-exports services AI modules (`services.ai.embedding_service`, `services.ai.llm_router`, `services.ai.unified_rag`) through a PEP 562 `__getattr__` lazy loader. The original code had three unconditional imports at module level which were replaced with lazy loading. The module docstring documents this change:

```python
# Original (removed) - would fail if services not present:
# from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
# from services.ai.llm_router import LLMProvider, LLMRouter
# from services.ai.unified_rag import RAGConfig as RAGConfig, UnifiedRAG as RAGEngine

# Current (lazy via __getattr__):
def __getattr__(name: str) -> Any:
    target = _LAZY.get(name)
    ...
    value = getattr(import_module(module_path), attribute)
    ...
```

**Evidence of circular import risk:** The docstring notes `services.ai` imports engine modules, so eager re-exports created a circular dependency cycle.

### Violation 2: Engine Land Integration → Services Map Engine

**File:** `engine/land/integration/water_adapter.py`
**Line** 230

```python
from services.map_engine.pipelines.runoff import ...
```

This is a **direct top-level import**, not mitigated by lazy loading. The module docstring even acknowledges the violation:

> "Remove direct imports from engine.land as the service will handle this via its dependency injection"

But then proceeds to import from `services.map_engine`, contradicting its own intent.

## 5. Database → Engine/Services Dependencies

The `database/` package is used extensively but is NOT part of the repository. It must be externally provided.

### Engine → database

| Engine File | database Import | Context |
|-------------|-----------------|---------|
| engine/data_connector.py:86 | `from database.hub import hub` | Deferred (inside function) |
| engine/resource_manager.py:45,70,83 | `from database.hub import hub` | Deferred (inside functions) |
| engine/ports/session.py:162 | `from database.config import SessionLocal` | Deferred (inside function) |
| engine/ports/session.py:201 | `from database.hub import hub` | Deferred (inside function) |
| engine/hydroma/biofertilizer/models.py:32 | `from database.base import Base` | Deferred (inside try/except) |
| engine/hydroma/biofertilizer/tests/conftest.py:10-11 | `from database.base import Base`, `from database.hub import hub` | Top-level |
| engine/hydroma/biofertilizer/tests/test_calibration_session.py:27 | `from database.config import SessionLocal as ConfiguredSessionLocal` | Deferred |
| engine/hydroma/biofertilizer/tests/test_calibration_session.py:80 | `from database.models import NojinCalibrationRecordDB` | Deferred |
| engine/strict_tests/test_s12_table_registration.py:154-155 | `from database.base import Base`, `from database.config import Base` | Deferred |
| engine/strict_tests/test_s12_table_registration.py:198-201 | `from database.base import Base`, `from database.models` | Deferred |
| engine/strict_tests/test_s12_table_registration.py:249 | `from database.base import Base` | Deferred |
| engine/hydroma/core/database.py | Documents `database.config` dependency | Documentation only |

### Services → database

Services reference `database/` extensively (over 100 import statements across 30+ files):

| Import Pattern | Count | Primary Services |
|---------------|-------|-----------------|
| `from database.hub import hub` | ~50+ | Almost all services |
| `from database.hub.hub import hub` | ~10 | workflow, auth, backup |
| `from database.models import ...` | ~40+ | commerce, auth, api_gateway, carbon, ecowallet, analytics, user data |
| `from database.base import Base` | ~15 | admin, contracts, auth, disputes, backup, models |
| `from database.config import SessionLocal` | ~5 | auth_legacy, tests |

## 6. Third-Party Dependencies

### Direct Imports of Third-Party Libraries

| Library | Evidence | Used By |
|---------|----------|---------|
| `numpy` | `import numpy as np` or `import numpy as _np` | engine (core), services, cpp_bridge |
| `pandas` | `from pandas import ...` | engine/data_connector.py |
| `pydantic` | `from pydantic import ...` | engine/land/models.py, services |
| `sqlalchemy` | `from sqlalchemy import ...` | services (models, repositories) |
| `fastapi` | `from fastapi import ...` | services/api_gateway |
| `structlog` | `import structlog` | services |
| `pytest` | `from pytest import ...` | tests |
| `psutil` | `import psutil` / deferred | engine/memory_monitor.py, resource_manager.py |
| `torch` | `import torch` / deferred | services/models/pinn_surrogate.py, engine/hydroma/distributed_ml |
| `supabase` | `from supabase import ...` | services/supabase/, services/auth_legacy |
| `pybind11` | In C++ build | engine/cpp_core/bindings.cpp |

### Optional Dependencies (deferred or try/except)

| Library | File | Evidence |
|---------|------|----------|
| `pandas` | engine/data_connector.py | `try: import pandas... except` |
| `psutil` | engine/resource_manager.py | `try: import psutil... except` |
| `psutil` | engine/memory_monitor.py | `try: import psutil... except` |
| `structlog` | services/api_gateway/main.py | `try: import structlog... except` |
| `supabase` | services/supabase/ | try/except wrapping |
| `torch` | services/models/pinn_surrogate.py | `try: import torch... except` |
| `numba` | engine/hydroma/cpp_bridge/indices_fast.py | `try: import numba... except` |
| `hydroma_core` | engine/hydroma/cpp_bridge/__init__.py | `try: import hydroma_core... except ImportError` |

## 7. Circular Dependencies

### Identified Circular Dependency 1: engine.generative_ai ↔ services.ai

**Path:**
1. `engine/hydroma/generative_ai/__init__.py` imports `services.ai.embedding_service`, `services.ai.llm_router`, `services.ai.unified_rag`
2. `services.ai.*` modules import from `engine.hydroma.*`

**Status:** Mitigated via lazy loading (PEP 562 `__getattr__`) in `generative_ai/__init__.py`. The module docstring explicitly documents this as a circular import case that was made latent rather than resolved at the architectural level.

### Potential Circular Dependency 2: engine.hydroma.cpp_bridge ↔ engine.hydroma.cpp_bindings

**Path:**
1. `engine/hydroma/cpp_bindings.py` imports from `engine.hydroma.cpp_bridge`
2. `engine/hydroma/cpp_bridge/__init__.py` does NOT import cpp_bindings (no cycle)

**Status:** No actual cycle. The cpp_bindings module is a thin delegation layer over cpp_bridge.

### Potential Circular Dependency 3: services.commerce ↔ services.finance, services.inventory

**Path:**
1. `services/commerce/service.py` imports `services.finance.ledger_service`, `services.finance.payment_provider`, `services.finance.wallet_service`, `services.inventory.service`
2. `services/finance/wallet_service.py` may import `services.commerce` (unconfirmed)

**Status:** Requires investigation.

## 8. Broken/Invalid Imports

| File | Import | Error | Classification |
|------|--------|-------|----------------|
| services/land/service.py:12 | `from adapters.engine_adapter import EngineAdapter` | ModuleNotFoundError: No module named 'adapters' | **FIXED** (adapters package created) |
| services/land/service.py:40 | `self.engine = engine or EngineAdapter()` | Runtime failure — cannot instantiate LandService | **FIXED** |
| engine/hydroma/generative_ai/__init__.py:20-22 | `from services.ai.*` (original) | ImportError if services absent | **FIXED** (now lazy) |
| engine/land/integration/water_adapter.py:230 | `from services.map_engine.pipelines.runoff import ...` | ImportError if services absent | **FIXED** — import removed |
| services/api_gateway/routers/models.py:52 | `from engine.hydroma.cpp_bridge import ...` | Conditional (deferred) | OK |

## 9. Missing Adapters

### RESOLVED: `adapters.engine_adapter`

**Referenced by:** `services/land/service.py:12`

```python
from adapters.engine_adapter import EngineAdapter
```

**Status:** CREATED. `adapters/` directory now exists at project root with `engine_adapter.py` and `hydroma_adapter.py`.

### Previously Missing: `adapters.hydroma_adapter`

**Referenced by:** `services/land/tests/test_integration.py:7`

**Status:** CREATED. `HydromaAdapter` class now exists in `adapters/hydroma_adapter.py`.

## 10. Deps Missing (Empty Placeholder Directories)

### services/hydroma/

All subdirectories under `services/hydroma/` are **empty** (no `__init__.py` or any files):

- `services/hydroma/api/`
- `services/hydroma/models/`
- `services/hydroma/repositories/`
- `services/hydroma/schemas/`
- `services/hydroma/tests/`

This appears to be a leftover structure from a previous architecture where hydroma services were planned here, but functionality was moved to `engine/hydroma/` or `services/` directly.

## 11. Near-Empty Stub Files

| File | Size | Content | Classification |
|------|------|---------|----------------|
| services/models/base.py | 2 bytes | (whitespace only) | STUB |
| services/models/water_models.py | 2 bytes | (whitespace only) | STUB |
| services/models/soil_climate_models.py | 2 bytes | (whitespace only) | STUB |

**Note:** `services/models/__init__.py` documents that all DB models have been moved to `database/models.py`. The `services/models/` package is effectively deprecated.

## 12. Dependency Summary by Layer

### Engine Internal Dependencies
- `engine.hydroma.cpp_bridge` is the single trusted C++ bridge
- `engine.hydroma.cpp_bindings` delegates to `cpp_bridge` (legacy compatibility)
- `engine.land.*` depends on `engine.hydroma.*` for provenance, models
- `engine.hydroma.wrapper` is the high-level facade that most services import
- `engine.baseline.cases` imports from nearly every engine.hydroma.* module
- `engine.strict_tests.*` exercises all engine modules including cpp_bridge

### Services Internal Dependencies
- `services.api_gateway` is the central hub — all routers depend on it
- `services.contracts` is standalone
- `services.commerce` depends on `services.finance`, `services.inventory`
- `services.workflow` depends on `services.api_gateway.errors`
- `services.admin` depends on `services.api_gateway`
- `services.business_modules.voice` depends on `services.ai`

### Cross-Layer Dependencies
- **Services → Engine:** 100+ import statements across 30+ service files. This is the expected direction.
- **Engine → Services:** 2 violations:
  1. `engine/hydroma/generative_ai/__init__.py` (mitigated via lazy loading)
  2. `engine/land/integration/water_adapter.py` (unmitigated — top-level import)
- **Engine → database:** Multiple deferred imports (acceptable pattern but indicates incomplete refactoring)
- **Services → database:** 100+ import statements (database is shared external package)

## 13. Architectural Violations

| Violation | Severity | File(s) | Notes |
|-----------|----------|---------|-------|
| Engine importing services | CRITICAL | engine/hydroma/generative_ai/__init__.py | Mitigated but should be removed |
| Engine importing services | HIGH | engine/land/integration/water_adapter.py:230 | **FIXED** — import removed |
| Missing adapters package | HIGH | services/land/service.py:12 | **FIXED** — adapters/ created |
| Missing dependency manifest | HIGH | (no requirements.txt/pyproject.toml) | Reproducibility issue |
| Empty services/hydroma/ dirs | LOW | services/hydroma/* | Code organization debt |
| Engine importing database | MEDIUM | engine/data_connector.py, engine/resource_manager.py, engine/ports/session.py | Deferred but should be resolved |

---

*End of Dependency Forensics Report*
