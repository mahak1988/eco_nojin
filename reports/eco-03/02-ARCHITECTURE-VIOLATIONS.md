# ECO-03: Architecture Violations — Report 02
## Boundary Violation Matrix

---

## Executive Summary

ECO-02/00 claims "Boundary violations: ✅ Identified and resolved". ECO-03 forensic verification finds **multiple unresolved violations**. The architecture exists on paper but is NOT enforced in source code.

---

## 1. Dependency Direction Matrix

Verified against source code using AST import analysis:

| Boundary | Expected | Actual | Status | Evidence |
|----------|----------|--------|--------|----------|
| Product → Application | ALLOWED (downward) | NOT IMPLEMENTED | DESIGN_ONLY | No Product layer exists in codebase |
| Application → Decision | ALLOWED | Partial | PARTIAL | `services/api_gateway/` exists, Tasmimyar in `services/tasmimyar/` |
| Application → Engine | VIOLATION | VIOLATED | BLOCKING | `services/api_gateway/routers/*.py` imports directly from `engine.hydroma.*` |
| Decision → Knowledge | ALLOWED | NOT ENFORCED | DESIGN_ONLY | Tasmimyar → Daneshyar coupling not enforced |
| Knowledge → Evidence | ALLOWED | NOT ENFORCED | DESIGN_ONLY | No Evidence Engine implementation exists |
| Evidence → Domain Services | ALLOWED | NOT ENFORCED | DESIGN_ONLY | Evidence Engine is a concept, not implemented |
| Domain Services → Engine | VIOLATION (no direct) | VIOLATED | PARTIAL | Services import engine via Engine Gateway concept, but some bypass it |
| Domain Services → Evidence | VIOLATION (must go through Evidence) | VIOLATED | PARTIAL | `services/models/registry.py` imports engine directly, bypassing Evidence |
| Engine → Database | VIOLATION | VIOLATED | BLOCKING | `engine/data_connector.py:86` imports `database.hub` |
| Engine → Services | VIOLATION (ECO-LEGACY-001) | VIOLATED | BLOCKING | `engine/hydroma/generative_ai/__init__.py:20-22` imports `services.ai.*` |
| Engine → Frontend | VIOLATION | VIOLATED | DESIGN_ONLY | No frontend implementation, but engine has `visualization` module |
| Engine → Application | VIOLATION | NOT VIOLATED | PASS | engine does not import services/application |
| Engine → Auth | VIOLATION | NOT VIOLATED | PASS | engine does not import auth |
| Engine → Payment | VIOLATION | NOT VIOLATED | PASS | No payment in engine scope |
| Engine → Blockchain | VIOLATION | NOT VIOLATED | PASS | No blockchain in engine scope |
| AI → Engine internals | VIOLATION | VIOLATED | BLOCKING | `engine/hydroma/generative_ai/__init__.py:20-22` imports from services.ai, which imports from engine |
| AI → Evidence Engine | ALLOWED (only) | VIOLATED | PARTIAL | AI imports from engine directly via generative_ai layer |
| service → engine internals | VIOLATION (should use Gateway) | VIOLATED | PARTIAL | 30+ services import engine.* directly, bypassing Engine Gateway |

---

## 2. ECO-LEGACY-001 Violation Details

### Violation 1: engine → services (CRITICAL)

**File**: `engine/hydroma/generative_ai/__init__.py:20-22, 46-48`

```python
# Lines 20-22 (lazy imports):
from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
from services.ai.llm_router import LLMProvider, LLMRouter
from services.ai.unified_rag import RAGConfig as RAGConfig, UnifiedRAG as RAGEngine

# Lines 46-48 (eager imports):
from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
from services.ai.llm_router import LLMProvider, LLMRouter
from services.ai.unified_rag import RAGConfig as RAGConfig, UnifiedRAG as RAGEngine
```

**Impact**: Engine depends on services layer — violates dependency inversion principle. Prevents engine from being used as standalone library.

**Evidence**: Verified via `grep -rn "from services\." "D:\HyDroMA\engine"` — 6 matches in `generative_ai/__init__.py`

**Status**: **NOT FIXED** — contradicted ECO-02/00 claim "[x] No imports from engine/ in services/"

### Violation 2: engine → database (BLOCKED_EXTERNAL_DEPENDENCY)

**Files**:
- `engine/data_connector.py:86`: `from database.hub import hub` (deferred import)
- `engine/resource_manager.py:45,70,83`: `from database.hub import hub` (deferred)
- `engine/ports/session.py:162`: `from database.config import SessionLocal`
- `engine/hydroma/biofertilizer/models.py:32`: `from database.base import Base`
- `engine/hydroma/biofertilizer/tests/conftest.py:10-11`: `from database.base import Base`, `from database.hub import hub`

**Impact**: `database/` package not present in repository → all tests UNRUNNABLE, all imports fail at runtime.

**Evidence**: `reports/engine-services/TEST-REPORT.md §2.1`: `python -c "import engine"` → `ModuleNotFoundError: No module named 'database'`

**Status**: **BLOCKED** — blocks all ECO-04 testing

### Violation 3: services → engine (DIRECT imports, no Gateway)

**Files** (30+ verified):
- `services/models/registry.py:22-48`: imports 8+ engine.hydroma modules directly
- `services/validation/formula_checks.py:22-33`: imports 12+ engine.hydroma modules
- `services/api_gateway/routers/*.py` (20+ files): imports directly from engine.hydroma
- `services/field_monitoring/service.py:22-23`: engine.hydroma imports
- `services/land/service.py:13`: `from engine.land.models import`
- `services/workflow/service.py:124,136`: engine.hydroma imports
- `services/satellite/*.py`: engine.hydroma imports

**Impact**: Services bypass the Engine Gateway entirely. Dependency direction is correct (services→engine) but the architectural pattern (through Gateway) is not enforced.

**Evidence**: 100+ grep matches for `from engine\.` in services/

**Status**: **DESIGNED BUT NOT ENFORCED** — Engine Gateway concept exists in ECO-02 contracts but no gateway implementation exists

---

## 3. AI → Engine Violation Analysis

### AI Boundary Contract Claims (ECO-03 §13 requirement)

**AI MAY INTERPRET.** — Verified: AI modules provide interpretation only
**AI MAY NOT SILENTLY AUTHORIZE SCIENCE.** — Verified in design, NOT enforced in code

| AI Boundary Question | ECO-02 Claim | ECO-03 Verdict | Evidence |
|---------------------|--------------|----------------|----------|
| Can AI read Evidence? | AI receives Evidence through Decision Engine | NOT VERIFIED in code | No Evidence Engine implementation |
| Can AI modify Evidence? | AI cannot directly access Evidence | NOT ENFORCED | No code-level enforcement |
| Can AI change equations? | AI cannot change scientific equations | NOT ENFORCED | `services/ai/*.py` has no equation access, but no import guard |
| Can AI change parameters? | AI cannot change parameters | NOT ENFORCED | No import guard |
| Can AI change provenance? | AI cannot change provenance | NOT ENFORCED | No import guard |
| Can AI change epistemic status? | AI cannot change epistemic status | NOT ENFORCED | No import guard |
| AI → recommendation must go through Tasmimyar? | Yes | NOT IMPLEMENTED | Tasmimyar exists as service but no enforcement |

**Finding**: The AI isolation is **DESIGNED BUT NOT ENFORCED**. While AI services (`services/ai/`) currently only import from engine for computation (not equation modification), there is **no code-level import guard** preventing it.

---

## 4. C++/Python Boundary Verification

### ECO-02 Claims vs ECO-03 Evidence

| Claim (ECO-02/05) | Status | Evidence |
|-------------------|--------|----------|
| ctypes for simple calls | PARTIALLY VERIFIED | C++ kernels exist in `engine/cpp_core/`, accessed via pybind11 (.pyd files) |
| pybind11 for complex objects | VERIFIED | `hydroma_core.cp312-win_amd64.pyd` exists in `engine/hydroma/cpp_bridge/` |
| Buffer protocol for zero-copy | DESIGNED BUT NOT ENFORCED | Buffer protocol documented but NOT verified in runtime tests |
| C++ owns numerical kernels | VERIFIED | 10 .cpp files in `engine/cpp_core/src/` confirmed |
| Python owns orchestration | VERIFIED | Python orchestration exists, C++ delegated via cpp_bridge |

### C++ Kernel Inventory (Verified)

| Kernel | File | Unit Tests | Bench |
|--------|------|------------|-------|
| Climate (ET0) | `src/climate.cpp` | `test_climate_unit.cpp` | `benchmark_climate.cpp` |
| Crop Water | `src/crop_water.cpp` | `test_crop_water_unit.cpp` | `benchmark_crop_water.cpp` |
| Erosion (RUSLE) | `src/erosion.cpp` | `test_erosion_unit.cpp` | `benchmark_erosion.cpp` |
| Hydrology (Muskingum) | `src/hydrology.cpp` | `test_hydrology_unit.cpp` | `benchmark_hydrology.cpp` |
| Indices (NDVI/EVI) | `src/indices.cpp` | `test_indices_unit.cpp` | `benchmark_indices.cpp` |
| Nojin Calculator | `src/nojin_calculator.cpp` | `test_nojin_calculator.cpp` | N/A |
| Richards Equation | `src/richards.cpp` | `test_richards_unit.cpp` | `benchmark_richards.cpp` |
| Saint-Venant | `src/saint_venant.cpp` | `test_saint_venant_unit.cpp` | `benchmark_saint_venant.cpp` |
| Sampling | `src/sampling.cpp` | `test_sampling_unit.cpp` | `benchmark_sampling.cpp` |
| Sediment | `src/sediment.cpp` | `test_sediment_unit.cpp` | `benchmark_sediment.cpp` |
| Soil Physics | `src/soil.cpp` | `test_soil_unit.cpp` | `benchmark_soil.cpp`, `benchmark_soil_extended.cpp` |

### C++ Test Status

| Status | Count | Notes |
|--------|-------|-------|
| VERIFIED (Python can import) | 0 | No `database/` package → all tests UNRUNNABLE |
| C++ tests compiled but NOT RUN | 15 | `test_advanced.cpp`, `test_hydroma.cpp` exist but test execution NOT documented |
| Benchmarks exist | 9 | NOT RUN, no benchmark results recorded |

**Performance Claims from ECO-01/PERF-PERFORMANCE-KNOWLEDGE.md**: 10x-200x speedup claimed. **NOT VERIFIED** — no benchmark results in repository.

---

## 5. Import Guard Protocol Status

ECO-02/02 §"Import Guard Protocol (ADR-010)" claims:
- services/ → engine/ (BLOCKED)
- ai/ → engine/ (BLOCKED)
- engine/ → services/ (BLOCKED)

**ECO-03 Verification**: **DESIGNED BUT NOT ENFORCED**

- No import guard code exists in the codebase
- AST-based detection script referenced in ADR-010 is NOT found in repository
- `tools/detect_imports.py` and `tools/check_boundary.py` referenced in ECO-02/15 do NOT exist
- Only `engine/strict_tests/test_s01_import_integrity.py` provides any import checking — and it only checks internal engine imports, not cross-package boundaries

---

## 6. Architecture Invariants Enforcement

| Invariant | ECO-02/22 Claim | ECO-03 Status | Evidence |
|-----------|-----------------|---------------|----------|
| INV-001: Engine never depends on UI | ACCEPTED | VERIFIED | Engine has `visualization` module but no UI imports |
| INV-002: Engine never depends on database | ACCEPTED | **VIOLATED** | `engine/data_connector.py:86` imports `database.hub` |
| INV-003: Scientific models cannot be silently modified by AI | ACCEPTED | DESIGNED BUT NOT ENFORCED | No code-level guard |
| INV-004: AI cannot change scientific equations | ACCEPTED | DESIGNED BUT NOT ENFORCED | No code-level guard |
| INV-005: AI cannot change provenance | ACCEPTED | DESIGNED BUT NOT ENFORCED | No code-level guard |
| INV-006: AI cannot change epistemic status | ACCEPTED | DESIGNED BUT NOT ENFORCED | No code-level guard |
| INV-007: Model output is not observation | ACCEPTED | DESIGNED BUT NOT ENFORCED | No runtime distinction |
| INV-008: Local knowledge is not scientific fact | ACCEPTED | DESIGNED BUT NOT ENFORCED | No epistemic tagging |
| INV-009: Software test success ≠ scientific validation | ACCEPTED | DESIGNED BUT NOT ENFORCED | Tests pass but don't imply scientific validity |
| INV-010: Recommendation requires traceable evidence | ACCEPTED | DESIGNED BUT NOT ENFORCED | Tasmimyar exists but no evidence tracing |
| INV-011: Absence of uncertainty data ≠ certainty | ACCEPTED | DESIGNED BUT NOT ENFORCED | No uncertainty propagation |
| INV-012: Units must be explicit | ACCEPTED | PARTIAL | UNIFORMAT defined but not enforced at API boundaries |
| INV-013: Scientific model identity must be versioned | ACCEPTED | DESIGNED BUT NOT ENFORCED | No version enforcement |
| INV-014: Legacy directory structure ≠ canonical architecture | ACCEPTED | PARTIAL | Some cleanup done, some legacy paths remain |
| INV-015: Old smart contracts ≠ production contracts | ACCEPTED | N/A | No smart contracts in code |

---

## 7. Findings Summary

1. **BLOCKING**: ECO-LEGACY-001 violation (`engine→services`) exists at `engine/hydroma/generative_ai/__init__.py:20-22,46-48`. Must be fixed before ECO-04.

2. **BLOCKING**: `database/` package missing → all engine imports fail → 0 tests executable.

3. **DESIGNED BUT NOT ENFORCED**: Import Guard Protocol (ADR-010) exists as design document but no enforcement code exists.

4. **CONFLICTING EVIDENCE**: ECO-02/00 claims "[x] Boundary violations: Identified and resolved" but 3 critical violations remain.

5. **NOT VERIFIED**: AI isolation claims — AI imports services.ai, which imports engine, creating a circular dependency path.

6. **DESIGNED BUT NOT ENFORCED**: Engine Gateway exists as a contract but no implementation prevents services from importing engine directly.

---

*Report generated: 2026-10-08*
*Status: BLOCKED*