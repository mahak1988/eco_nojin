# ECO-03: Repository Structure Specification — Report 18
## Canonical Repository / Package Map

---

## Executive Summary

This report specifies the canonical repository structure required for ECO-04 implementation. The current directory structure is based on historical microservice decomposition and does NOT reflect the canonical architecture.

**Status**: DESIGNED (conceptual proposal, NOT implemented)

---

## 1. Canonical Repository Structure (Proposed)

### 1.1 Engine Layer (Scientific Core)

```
engine/                              # ECO-04: Scientific Engine Core
├── __init__.py                      # Public API (versioned)
├── gateway/                         # Engine Gateway boundary (NEW - ECO-04)
│   ├── __init__.py
│   ├── request_validator.py         # Input validation
│   ├── model_selector.py            # CANON-XXX resolution
│   ├── unit_converter.py            # UNIFORMAT unit normalization
│   ├── parameter_validator.py       # Parameter constraint checking
│   ├── error_handler.py             # Error normalization
│   ├── result_normalizer.py         # Output normalization
│   └── telemetry.py                 # Performance monitoring
├── scientific/                      # Pure scientific computation (RENAMED from hydroma/scientific)
│   ├── climate/                     # CANON-001, CANON-002, CANON-011
│   │   ├── __init__.py
│   │   ├── et0.py                   # Penman-Monteith, Hargreaves, Thornthwaite
│   │   ├── radiation.py             # Solar radiation
│   │   └── scenarios.py             # CMIP6 scenarios (CANON-018)
│   ├── soil/                        # CANON-006, CANON-017
│   │   ├── __init__.py
│   │   ├── physics.py               # Van Genuchten
│   │   ├── erosion.py               # RUSLE
│   │   └── chemistry.py             # Soil chemistry
│   ├── hydrology/                   # CANON-004, CANON-005, CANON-015
│   │   ├── __init__.py
│   │   ├── runoff.py                # SCS-CN
│   │   ├── groundwater/             # Darcy, Theis
│   │   └── watershed/               # Watershed calculator
│   ├── carbon/                      # Carbon sequestration
│   ├── economics/                   # Economic analysis
│   ├── water/                       # Water quality
│   ├── models/                      # EPIA, H-Pheno
│   └── formulas/                    # Formula catalog
├── numerical/                       # C++ kernels interface (RENAMED from hydroma/cpp_bridge)
│   ├── __init__.py
│   ├── cpp_bridge/                  # Bridge module
│   └── kernels/                     # Compiled extensions
├── provenance/                      # Provenance tracking (EXTRACTED)
│   ├── __init__.py
│   ├── types.py                     # ResultProvenance enhanced
│   └── chain.py                     # Provenance chain
├── uncertainty/                     # Uncertainty propagation (NEW - ECO-04)
│   ├── __init__.py
│   └── propagation.py
├── validation/                      # Scientific validation (NEW - ECO-04)
│   ├── __init__.py
│   └── cross_validation.py
├── land/                            # Land intelligence (KEEP)
│   ├── __init__.py
│   ├── terrain_analysis.py
│   ├── hydrology.py
│   └── models.py
├── strict_tests/                    # Architectural guard tests (KEEP)
│   ├── conftest.py
│   ├── thresholds.py
│   ├── test_s00_*.py
│   └── test_s15_*.py
└── ports/                           # Hexagonal ports (KEEP)
    ├── clock.py
    ├── session.py
    └── sinks.py
```

### 1.2 C++ Core (KEEP, minor restructure)

```
engine/cpp_core/
├── src/                             # 10 C++ source files (KEEP)
├── include/hydroma/                 # 10 C++ headers (KEEP)
├── bindings.cpp                     # pybind11 bindings (KEEP)
├── tests/                           # 21 C++ test/benchmark files (KEEP)
├── CMakeLists.txt                   # Build configuration (KEEP, fix dual-build issue)
└── build/                           # Single build directory (remove build2/)
```

### 1.3 Knowledge Layer (NEW - ECO-04)

```
knowledge/                           # ECO-04: Knowledge Engine (Daneshyar)
├── __init__.py
├── daneshyar/                       # Knowledge Engine implementation
│   ├── __init__.py
│   ├── registry.py                  # 9 knowledge types
│   ├── epistemic_types.py           # Epistemic type definitions
│   ├── trust_propagation.py         # Trust matrix implementation
│   ├── iranian_knowledge.py         # KT-003 Iranian domain knowledge
│   └── versioning.py                # Knowledge item versioning
├── evidence/                        # Evidence Engine implementation
│   ├── __init__.py
│   ├── engine.py                    # Evidence collection/validation
│   ├── trust_levels.py              # Trust level assignment
│   ├── validation_pipeline.py       # Evidence validation
│   └── store.py                     # Immutable evidence store
└── contracts/                       # Shared domain contracts
    ├── __init__.py
    ├── formula.py                   # EXTRACTED from services/_contracts
    └── status.py
```

### 1.4 Decision Layer (NEW - ECO-04)

```
decision/                            # ECO-04: Decision Engine (Tasmimyar)
├── __init__.py
├── tasmimyar/                       # Decision Engine implementation
│   ├── __init__.py
│   ├── elements.py                  # 11 decision elements
│   ├── evaluation.py                # Evaluation process
│   ├── scenarios.py                 # Scenario evaluation protocol
│   ├── risk_assessment.py           # DE-002 Risk Assessment
│   ├── tradeoff_analysis.py         # DE-004 Trade-off Analysis
│   └── output.py                    # Decision output format
└── optimization/                    # Multi-objective optimization
```

### 1.5 Domain Services Layer

```
services/                            # ECO-04: Domain Services (consolidated)
├── __init__.py
├── domain/                          # Bounded Contexts
│   ├── __init__.py
│   ├── hydroma_engine/              # Context: Hydroma Engine
│   │   ├── __init__.py
│   │   ├── model_registry.py        # 22 models registry
│   │   └── scientific_analysis.py   # Science analysis
│   ├── agriwater/                   # Context: AgriWater
│   │   ├── __init__.py
│   │   ├── climate.py
│   │   ├── soil.py
│   │   └── irrigation.py
│   ├── hydrology/                   # Context: Hydrology
│   │   ├── __init__.py
│   │   ├── watershed.py
│   │   └── groundwater.py
│   ├── ecosystem/                   # Context: Ecosystem Science
│   │   ├── __init__.py
│   │   ├── carbon.py
│   │   └── biodiversity.py
│   ├── land_intelligence/           # Context: Land Intelligence
│   │   ├── __init__.py
│   │   └── terrain.py
│   ├── remote_sensing/              # Context: Remote Sensing
│   │   ├── __init__.py
│   │   ├── satellite.py
│   │   └── indices.py
│   └── platform_core/               # Context: Platform Core
│       ├── __init__.py
│       ├── auth.py
│       ├── config.py
│       ├── logging.py
│       └── monitoring.py
├── reporting/                       # Context: Reporting / Product
│   ├── __init__.py
│   └── report_generator.py
├── ai/                              # Context: AI (ISOLATED)
│   ├── __init__.py
│   ├── interpretation/              # ONLY: read Evidence, interpret
│   ├── research/                    # Experimental, no engine imports
│   └── prompts/                     # Prompt templates
└── contracts/                       # Service contracts (shared)
    ├── __init__.py
    └── api_models.py
```

### 1.6 Tests Directory

```
tests/                               # ECO-04: Unified Test Suite
├── __init__.py
├── conftest.py                      # Shared fixtures
├── unit/                            # Unit tests
│   ├── engine/
│   ├── knowledge/
│   ├── decision/
│   └── services/
├── integration/                     # Integration tests
│   ├── cpp_python_boundary/         # Engine Gateway tests
│   ├── evidence_chain/              # Evidence chain tests
│   ├── ai_isolation/                # AI boundary tests
│   └── decision_engine/             # Decision flow tests
├── property/                        # Property-based tests
│   └── numerical_parity/            # C++/Python parity
├── benchmarks/                      # Performance benchmarks
│   ├── cpp/
│   └── python/
└── architecture/                    # Architecture enforcement tests
    ├── boundary_tests/              # Import boundary tests
    ├── invariant_tests/             # Architecture invariant tests
    └── service_ownership_tests/     # Service ownership tests
```

### 1.7 Root Configuration (NEW - ECO-04)

```
kilo.json                            # Kilo configuration
AGENTS.md                            # Agent instructions
requirements.txt                     # Python dependencies (MISSING - BLOCKER)
pyproject.toml                       # Project metadata (MISSING)
CMakeLists.txt                       # Root C++ build (optional)
docker-compose.yml                   # Development environment
.mypy.ini                            # Type checking config
pytest.ini                           # Test configuration
ruff.toml                            # Linting configuration
```

---

## 2. Architecture Principles Applied

| Principle | How Applied |
|-----------|-------------|
| Architecture follows responsibility | Directory names reflect bounded contexts, not historical microservice names |
| Single source of truth | Each scientific model has ONE implementation in `engine/scientific/` |
| Separation of concerns | Engine (computation), Knowledge (classification), Decision (evaluation), Services (orchestration) |
| Hexagonal architecture | `ports/` in engine provides abstractions; adapters in services |
| Dependency inversion | Domain services depend on abstractions, not concrete implementations |

---

## 3. Migration Path (ECO-04)

### ECO-04.1: Canonical Repository Skeleton
- Create new directory structure
- Establish dependency rules

### ECO-04.2: Scientific Contracts
- Implement model contracts with CANON-XXX IDs
- Define parameter schemas
- Define unit schemas

### ECO-04.3: Engine Gateway
- Implement Engine Gateway module
- Create request validation
- Create model selection
- Create unit normalization

### ECO-04.4: Hydroma Extraction
- Remove `generative_ai` from engine
- Extract `api/`, `visualization/` from engine
- Remove `database` dependency

### ECO-04.5: Evidence Infrastructure
- Implement Evidence Engine
- Implement epistemic type tagging
- Implement trust level assignment

### ECO-04.6: Daneshyar Core
- Implement Knowledge Engine
- Implement 9 knowledge types
- Implement trust propagation

### ECO-04.7: Tasmimyar Core
- Implement Decision Engine
- Implement 11 decision elements
- Implement recommendation generation

### ECO-04.8: Canonical Services
- Consolidate services into bounded contexts
- Remove legacy infrastructure services
- Isolate AI layer

### ECO-04.9: Application Layer
- API gateway
- Workflow orchestration

### ECO-04.10: Product/API/UI Phases
- Reporting layer
- Product experience (out of scope)

---

## 4. Findings

1. **DESIGNED**: Repository structure is well-specified conceptually but NOT implemented. Current structure is historical.

2. **BLOCKING**: Missing `requirements.txt` and `pyproject.toml` prevents reproducible builds.

3. **DESIGNED BUT NOT ENFORCED**: No architectural enforcement of the directory structure or import rules.

4. **DUAL BUILD**: `engine/cpp_core/` has both `build/` and `build2/` directories — potential configuration drift.

5. **CONFLICTING EVIDENCE**: `services/hydroma/` exists with empty subdirectories — should be deleted per legacy extraction plan but still present.

---

*Report generated: 2026-10-08*
*Status: DESIGNED BUT NOT ENFORCED*