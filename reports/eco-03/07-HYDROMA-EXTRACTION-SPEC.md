# ECO-03: Hydroma Extraction Specification — Report 07
## Hydroma Canonicalization Plan

---

## Executive Summary

Hydroma is the scientific computation engine. ECO-03 verifies its boundaries against the CANONICAL architecture and identifies what must be extracted, replaced, inverted, or removed.

**Status**: PARTIALLY VERIFIED — Hydroma exists but has significant legacy coupling.

---

## 1. Hydroma Current Structure (Verified)

```
engine/hydroma/
├── __init__.py              # Public API
├── wrapper.py               # High-level Python wrapper
├── cpp_bridge/              # C++/Python bridge (56 functions)
├── provenance.py            # Result provenance tracking (minimal)
├── quantity.py              # Unit/quantity handling
├── formulas/                # Formula registry and catalog
├── climate/                 # Climate calculations (ET0)
├── soil/                    # Soil physics, chemistry, health
├── carbon/                  # Carbon sequestration
├── economics/               # Economic analysis
├── water/                   # Water quality analysis
├── groundwater/             # Groundwater modeling
├── simulation/              # Simulation orchestration
├── irrigation/              # Irrigation scheduling
├── models/                  # Scientific models (epia, hpheno, etc.)
├── utils/                   # Utility functions
├── visualization/           # Visualization tools
├── data_pipeline/           # Data ingestion pipeline
├── distributed_ml/          # Distributed ML training
├── generative_ai/           # Generative AI (VIOLATES boundary)
├── decision_support/        # Decision support
├── scenarios/              # Climate/crop scenarios
├── mrv/                    # MRV (Measurement-Reporting-Verification)
├── satellite/              # Satellite data processing
├── infrastructure/          # Infrastructure utilities
├── data/                    # Data models
├── analyses/                # Analysis modules
├── api/                     # API definitions
├── calibration/             # Calibration tools
├── biofertilizer/           # Biofertilizer models
├── crop/                    # Crop modeling
├── data_assimilation/       # Data assimilation
├── hybrid_ml/              # Hybrid ML
├── materials/              # Materials
├── optimization/            # Optimization
├── performance/             # Performance tools
├── plant_neuro/            # Plant neuroscience (experimental)
├── production/              # Production utilities
├── scenario/               # Scenario tools
├── water/                   # Water quality
```

### Target Hydroma Structure (Canonical)

```
engine/hydroma/                          # CANONICAL: Scientific Engine
├── __init__.py                          # Public API (versioned)
├── scientific/                          # CANONICAL: Pure scientific computation
│   ├── climate/
│   │   ├── et0.py                       # CANON-001, CANON-002, CANON-003
│   │   ├── radiation.py                 # CANON-011
│   │   └── scenarios.py                 # CANON-018
│   ├── soil/
│   │   ├── physics.py                   # CANON-006, CANON-017
│   │   ├── erosion.py                   # CANON-007
│   │   └── chemistry.py
│   ├── hydrology/
│   │   ├── runoff.py                    # CANON-004
│   │   ├── groundwater/                 # CANON-004, CANON-005
│   │   └── watershed/                   # CANON-015
│   ├── carbon/
│   │   ├── calculator.py                # CANON-0XX
│   │   └── models.py
│   ├── models/
│   │   ├── epia.py
│   │   └── hpheno.py
│   ├── economics/
│   │   └── analysis.py
│   └── water/
│       └── quality.py
├── numerical/                           # CANONICAL: C++ kernels interface
│   ├── cpp_bridge/                      # Zero-copy buffer protocol
│   └── kernels/                         # Compiled extensions
├── provenance/                          # CANONICAL: Provenance tracking
│   ├── __init__.py
│   └── types.py
├── uncertainty/                        # CANONICAL: Uncertainty propagation
│   ├── __init__.py
│   └── propagation.py
├── validation/                         # CANONICAL: Scientific validation
│   ├── __init__.py
│   └── cross_validation.py
└── gateway/                            # CANONICAL: Engine Gateway boundary
    ├── __init__.py
    ├── request.py
    ├── model_selector.py
    ├── units.py
    ├── validator.py
    ├── uncertainty.py
    ├── normalizer.py
    └── error_handler.py
```

---

## 2. Dependency Analysis

### Dependencies Hydroma SHOULD have (Canonical)

| Dependency | Keep/Replace/Invert/Remove/Adapter/Defer | Evidence | Notes |
|-----------|------------------------------------------|----------|-------|
| `numpy` | KEEP | All numerical code uses numpy | Core dependency |
| `pybind11` | KEEP | C++ bindings | C++/Python bridge |
| `scipy` | KEEP | Some numerical routines | Scientific computing |
| `pint` (or custom units) | DEFER | UNIFORMAT defined but not enforced | Will implement in ECO-04 |
| `pydantic` | KEEP | Data models | Type validation |

### Dependencies Hydroma MUST NOT have (Legacy)

| Dependency | Current Status | Evidence | Disposition |
|-----------|----------------|----------|-------------|
| `database` | **VIOLATED** | `engine/data_connector.py:86`, `engine/resource_manager.py:45` | Remove |
| `services.*` | **VIOLATED** | `engine/hydroma/generative_ai/__init__.py:20-22` | Remove |
| `services.api_gateway` | **VIOLATED** | `engine/hydroma/generative_ai/__init__.py:46-48` (via services.ai) | Remove |
| `services.security` | Referenced in comment | `engine/data_connector.py:51` (comment only) | Remove comment |

### Dependencies Hydroma SHOULD NOT have directly

| Dependency | Current Status | Evidence | Disposition |
|-----------|----------------|----------|-------------|
| `FastAPI` | **VIOLATED** | `engine/hydroma/api/` directory exists | Move to services |
| `SQLAlchemy` | **VIOLATED** | `database.hub`, `database.config` | Remove |
| `requests` | **PARTIAL** | Some modules may use for data fetching | Move to services |
| Auth logic | **NOT FOUND** | - | N/A |
| Payment logic | **NOT FOUND** | - | N/A |
| Wallet logic | **NOT FOUND** | - | N/A |
| Blockchain | **NOT FOUND** | - | N/A |
| HTTP framework | **VIOLATED** | `engine/hydroma/api/` | Move to services |
| Application workflow | **VIOLATED** | `engine/hydroma/simulation/orchestrator.py` has workflow logic | Move to Decision layer |
| UI | **NOT FOUND** | - | N/A |

---

## 3. Legacy Components in Hydroma

| Module | Path | Classification | Reason | Disposition |
|--------|------|----------------|--------|-------------|
| `generative_ai/` | `engine/hydroma/generative_ai/` | **ECO-LEGACY-001 VIOLATION** | Imports from services.ai | REMOVE from engine, move to services/ai |
| `api/` | `engine/hydroma/api/` | HTTP Framework | Should be in services | MOVE to services |
| `data_pipeline/` | `engine/hydroma/data_pipeline/` | Data ingestion | Partial service coupling | REVIEW, may need extraction |
| `infrastructure/` | `engine/hydroma/infrastructure/` | Infrastructure utils | May contain service coupling | REVIEW |
| `visualization/` | `engine/hydroma/visualization/` | UI-related | Engine should not have visualization | REMOVE, move to reporting layer |
| `plant_neuro/` | `engine/hydroma/plant_neuro/` | Experimental | Research only | RESEARCH_ONLY |
| `hybrid_ml/` | `engine/hydroma/hybrid_ml/` | Experimental | ML in engine boundary violation | RESEARCH_ONLY |
| `distributed_ml/` | `engine/hydroma/distributed_ml/` | Experimental | ML in engine boundary violation | RESEARCH_ONLY |

---

## 4. Scientific Models in Hydroma (Verified)

| Model | File | C++ Acceleration | Status |
|-------|------|-----------------|--------|
| Penman-Monteith ET0 | `climate/et_calculator.py` | ✅ C++ in `cpp_core/src/climate.cpp` | VERIFIED |
| Hargreaves ET0 | `climate/et_calculator.py` | ✅ C++ in `cpp_core/src/climate.cpp` | VERIFIED |
| Van Genuchten | `soil/physics.py` | ✅ C++ in `cpp_core/src/soil.cpp` | VERIFIED |
| RUSLE Erosion | `soil/erosion.py` | ✅ C++ in `cpp_core/src/erosion.cpp` | VERIFIED |
| D8 Flow Direction | `land/hydrology.py` | Python | VERIFIED |
| Terrain Analysis | `land/terrain_analysis.py` | Python | VERIFIED |
| Muskingum | `hydrology.cpp` | ✅ C++ | VERIFIED |
| Saint-Venant | `saint_venant.cpp` | ✅ C++ | VERIFIED |
| Richards | `richards.cpp` | ✅ C++ | VERIFIED |
| EPIA | `models/epia.py` | Python | IMPLEMENTATION_VERIFIED |
| H-Pheno | `models/hpheno.py` | Python | IMPLEMENTATION_VERIFIED |

---

## 5. Engine Gateway Boundary (Verified)

### What Hydroma Has
- `engine/hydroma/cpp_bridge/__init__.py` — Python-C++ bridge with 56 functions, telemetry, fallbacks
- `engine/hydroma/cpp_bridge/` directory with `.pyd` files and test suite
- No formal "Engine Gateway" module — the term appears only in ECO-02 contracts

### What's Missing
- No `engine/gateway/` module exists
- No request validation layer
- No model selection router (services must use `services/models/registry.py` which bypasses any gateway)
- No unit normalization layer (UNIFORMAT defined but not implemented)
- No provenance enforcement at boundary

**Status**: Engine Gateway contract DESIGNED, NOT IMPLEMENTED

---

## 6. Extraction Plan

### Phase 1: Remove Violations (Pre-ECO-04 requirement)
1. **REMOVE** `engine/hydroma/generative_ai/` from engine
2. **MOVE** `engine/hydroma/generative_ai/` to `services/ai/generative_ai/`
3. **REMOVE** `engine/data_connector.py:86` database import
4. **REMOVE** `engine/resource_manager.py:45,70,83` database import

### Phase 2: Extract Legacy Components (ECO-04)
1. **MOVE** `engine/hydroma/api/` → `services/api_gateway/`
2. **MOVE** `engine/hydroma/visualization/` → `services/reporting/`
3. **REVIEW** `engine/hydroma/data_pipeline/` for service coupling
4. **RESEARCH_ONLY** `engine/hydroma/hybrid_ml/`, `distributed_ml/`, `plant_neuro/`

### Phase 3: Build Engine Gateway (ECO-04)
1. Create `engine/gateway/` module
2. Implement request validation
3. Implement model selection
4. Implement unit normalization
5. Implement provenance capture
6. Implement result normalization

---

## 7. Findings

1. **BLOCKING**: `engine/hydroma/generative_ai/__init__.py` imports from `services.ai.*` — direct ECO-LEGACY-001 violation.
2. **BLOCKING**: `engine/data_connector.py` imports from `database/` — missing package blocks all execution.
3. **DESIGNED BUT NOT ENFORCED**: Engine Gateway exists as contract, no implementation in code.
4. **DESIGNED BUT NOT ENFORCED**: Scientific models exist but no canonical model contract enforcement at runtime.
5. **NOT VERIFIED**: Performance claims (10x-200x speedup) — no benchmark results found.
6. **PARTIAL**: Hydroma scientific core is well-structured, but legacy coupling violations prevent isolation.

---

*Report generated: 2026-10-08*
*Status: BLOCKED (requires ECO-LEGACY-001 fix before ECO-04)*