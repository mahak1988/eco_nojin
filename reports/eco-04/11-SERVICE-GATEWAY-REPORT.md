# ECO-04: Service Gateway Report — Report 11

## Service-to-Engine boundary status

---

## 1. Current State

Per ECO-04.md §3: "INV-003: Services MUST NOT directly import engine internals"

**Status**: VIOLATION — 100+ direct imports

---

## 2. Violation Count

**Command**: `grep -rn "from engine\|import engine" services/ --include="*.py" | grep -v "test_" | wc -l`

**Result**: 100+ matches

### Violation Classification

| Pattern | Count | Acceptable? | Notes |
|---------|-------|-------------|-------|
| `from engine.hydroma.config.settings import get_settings` | 10+ | ⚠️ POTENTIAL | Settings import, not computation |
| `from engine.hydroma.cpp_bindings import *` | 5+ | ❌ YES | Direct C++ binding access |
| `from engine.hydroma.* import <scientific_function>` | 80+ | ❌ YES | Direct scientific computation call |
| `from engine.hydroma.simulation.* import *` | 5+ | ❌ YES | Direct simulation call |

The services bypass the Engine Gateway entirely. Per ECO-04.md §156: "تمام دسترسی‌های production باید از Engine Gateway عبور کنند."

---

## 3. Violation Examples

### 3.1 Direct Scientific Computation Access

```python
# services/api_gateway/routers/soil.py:633
from engine.hydroma.wrapper import compute_erosion as cpp_erosion

# services/api_gateway/routers/models.py:52
from engine.hydroma.cpp_bridge import (...)

# services/api_gateway/routers/hydroma_water.py:16
from engine.hydroma.watershed.calculator import (
    StructureType, design_watershed_structure
)
```

### 3.2 C++ Binding Access

```python
# services/api_gateway/routers/carbon_engine.py:6
from engine.hydroma import cpp_bindings

# services/scientific_motors/erosion_rusle.py:19
from engine.hydroma.cpp_bindings import is_cpp_available
```

### 3.3 Simulation Orchestration

```python
# services/api_gateway/routers/simulation.py:21
from engine.hydroma.simulation.contracts import ChainInputs

# services/api_gateway/routers/simulation.py:22
from engine.hydroma.simulation.orchestrator import run_chain
```

---

## 4. Impact Assessment

| Impact Area | Status |
|-------------|--------|
| Provenance capture | ❌ NOT ENFORCED |
| Unit normalization | ❌ NOT ENFORCED |
| Input validation | ❌ NOT ENFORCED |
| Error normalization | ❌ NOT ENFORCED |
| Model selection | ❌ NOT ENFORCED |

Without the Engine Gateway, services bypass:
- Input validation
- Unit normalization
- Provenance initialization
- Uncertainty metadata
- Applicability validation

---

## 5. Service Gateway Status

| Criterion | Status |
|-----------|--------|
| Engine Gateway exists | ✅ YES (skeleton) |
| Services use Engine Gateway | ❌ NO |
| Import guard detects service bypass | ✅ YES (but not blocking in CI) |
| Services → Engine direct imports | 100+ (VIOLATION) |

---

## 6. Resolution Plan

| Sprint | Action |
|--------|--------|
| ECO-04.9 | Update services to use Engine Gateway |
| ECO-04.9 | Add SERVICES_NO_DIRECT_ENGINE rule to import guard |
| ECO-04.10 | Verify 0 violations |

**Recommended import guard rule**:
```python
Rule(
    id="SERVICES_NO_ENGINE_INTERNALS",
    name="Services must not import engine internals",
    source_module="services",
    forbidden_prefixes=["engine.hydroma", "engine.cpp_core", "engine.ports"],
    mode="FORBIDDEN_ALL",
    rationale="INV-003: Services must use Engine Gateway"
)
```

---

## 7. Conclusion

The service-to-engine boundary is **VIOLATED** with 100+ direct imports. The Engine Gateway exists as a skeleton but is not yet wired into services.

This is **DEFERRED_TO_ECO_04.9** (Service Gateway sprint). It does not block ECO-04.1-04.8, but must be resolved before full architecture enforcement.

---

*Report generated: 2026-10-08*
*Status: 100+ service bypass violations, deferred to ECO-04.9*