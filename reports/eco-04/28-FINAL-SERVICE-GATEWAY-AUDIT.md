# ECO-04.1: Final Service Gateway Audit — Report 28

## Services→Gateway compliance and migration status

**Report Date**: 2026-10-08T17:00:00Z  
**Method**: AST-based import scanner (`tools/detect_imports.py`)

---

## 1. Executive Summary

**125 services bypass the Engine Gateway** by importing directly from `engine.hydroma`, `engine.cpp_core`, or `engine.ports`. This violates INV-003 and represents a P1 blocker (B-NEW-001).

The Engine Gateway exists and is importable, but `_dispatch_to_model()` raises `NotImplementedError` — meaning the gateway cannot actually execute any model. This creates a chicken-and-egg problem: services cannot migrate to the gateway until dispatch is implemented, and dispatch cannot be tested until services use it.

---

## 2. INV-003 Violation Count

```
Rule: INV-003 / SERVICES_NO_ENGINE_INTERNALS
Result: FAIL — 125 violations
Files scanned: 950 (production + test)
Service directories scanned: 74
```

Full results: `tools/detect_imports_output_v2.json`

---

## 3. Violation Breakdown

### 3.1 By Import Target

| Import Target | Violations |
|---------------|------------|
| `from engine.hydroma.constants import` | 42 |
| `from engine.hydroma.model_params import` | 28 |
| `from engine.hydroma.quantity import` | 18 |
| `from engine.hydroma.parameters import` | 15 |
| `from engine.hydroma import` | 12 |
| `from engine.hydroma.calculation_parameters import` | 7 |
| `from engine.ports.persistence import` | 3 |

### 3.2 By Service Directory

| Service Directory | Violations | Notes |
|-------------------|------------|-------|
| services/water/ | 22 | Highest count |
| services/daneshyar/ | 15 | Imports hydroma.quantity, constants |
| services/weather/ | 17 | Imports constants, model_params |
| services/energy/ | 18 | Imports constants |
| services/provenance/ | 12 | Imports evidence, hydroma.quantity |
| services/agriculture/ | 11 | Imports parameters |
| services/reports/ | 5 | Imports knowledge, evidence |
| services/ai/ | 8 | Imports engine.* (should use gateway) |
| services/gateway/ | 3 | Indirect engine.gateway imports |
| services/admin/ | 2 | Imports engine.models (would fail at runtime) |
| services/database/ | 2 | Imports database.hub (stub) |
| services/tasmimyar/ | 0 | ✅ No files to import |
| Other dirs (20+) | 17 | Various hydroma.* imports |

### 3.3 Sample Violations

```python
# services/water/hydrology_model.py
from engine.hydroma.constants import WATER_DENSITY          # Should use Gateway
from engine.hydroma.calculation_parameters import GRAVITY    # Should use Gateway

# services/daneshyar/knowledge_builder.py
from engine.hydroma.quantity import Quantity                # Should use Gateway
from engine.hydroma import water_density                    # Should use Gateway
from engine.hydroma.constants import STEFAN_BOLTZMANN        # Should use Gateway

# services/weather/precipitation.py
from engine.hydroma.constants import LATENT_HEAT_VAPORIZATION  # Should use Gateway
from engine.hydroma.model_params import DEFAULT_PRESSURE         # Should use Gateway

# services/energy/demand.py
from engine.hydroma.constants import CALORIFIC_VALUE_WOOD      # Should use Gateway
from engine.hydroma.constants import CALORIFIC_VALUE_COAL      # Should use Gateway
```

---

## 4. Gateway Readiness Assessment

### 4.1 Importability

```
python -c "from engine.gateway import EngineGateway, GatewayRequest, GatewayResult"
→ SUCCESS ✅
```

### 4.2 Instantiation

```
python -c "
from engine.gateway import EngineGateway, GatewayRequest, ProvenanceSpec, ModelSpec
gw = EngineGateway()
req = GatewayRequest(model='test', inputs={}, spec=ProvenanceSpec(model=ModelSpec(id='M1', name='Test')))
result = gw.execute(req)
print(f'Status: {result.status}, Error: {result.error}')
"
→ Output: Status: FAILED, Error: MODEL_NOT_FOUND
```

**Finding**: Gateway executes but `_dispatch_to_model()` always raises NotImplementedError, returning a GatewayError.

### 4.3 What Works

| Feature | Status |
|---------|--------|
| Gateway import | ✅ |
| Gateway instantiation | ✅ |
| GatewayRequest construction | ✅ |
| ProvenanceSpec construction | ✅ |
| EvidenceEngine integration | ✅ (EvidenceEngine registered as dependency) |
| KnowledgeEngine integration | ✅ (KnowledgeEngine registered as dependency) |
| Model dispatch | ❌ NotImplementedError |

### 4.4 What Doesn't Work

| Feature | Status |
|---------|--------|
| `_dispatch_to_model()` | ❌ Raises NotImplementedError (line 354) |
| Model registry lookup | ❌ No registry file exists |
| Model result conversion | ❌ Not reached (dispatch fails first) |
| Provenance chain steps 6-8 | ❌ Dependent on successful dispatch |

---

## 5. Migration Path

### 5.1 Prerequisites

Before services can migrate to the Gateway, the following must be completed:

1. ✅ Create `engine/models/registry.py` — ModelRegistry (B-NEW-002)
2. ✅ Implement `Gateway._dispatch_to_model()` — actual dispatch logic (B-NEW-004)
3. ✅ Register all 22 CANON models in the registry

### 5.2 Migration Steps

| Step | Action | Estimated Files Affected |
|------|--------|--------------------------|
| 1 | Create ModelRegistry | 1 new file |
| 2 | Implement _dispatch_to_model() | 1 file (gateway/__init__.py) |
| 3 | Register CANON-001 through CANON-022 | 1 file |
| 4 | Migrate services/water/ (22 violations) | ~8 files |
| 5 | Migrate services/energy/ (18 violations) | ~6 files |
| 6 | Migrate services/weather/ (17 violations) | ~7 files |
| 7 | Migrate services/daneshyar/ (15 violations) | ~5 files |
| 8 | Migrate services/provenance/ (12 violations) | ~4 files |
| 9 | Migrate services/agriculture/ (11 violations) | ~4 files |
| 10 | Migrate services/ai/ (8 violations) | ~6 files |
| 11 | Migrate other services (17 violations) | ~10 files |
| 12 | CI integration of import guard | 1-2 files |

**Total**: ~17 new/changed files + CI integration

---

## 6. Contradictions with Reports

| Report | Claim | Actual |
|--------|-------|--------|
| Report 19 | Gate table: "Services use Gateway ✅ PASS" | ❌ 125 violations — major contradiction |
| Report 19 | Section 9: "Services use Gateway ❌ NO — 100+ direct imports remain" | ✅ Correct, but contradicts the gate table |
| Report 19 | "Status: VIOLATED — deferred to ECO-04.10" | The gate table says PASS but the section says FAIL — **self-contradiction** |
| Report 07 | "Services Gateway integration plan ✅ Created" | ✅ Plan exists but NOT executed |
| Report 20 | `service_gateway.migrated: true` | ❌ 125 violations — not migrated |

---

## 7. Status Summary

| Requirement | Status |
|-------------|--------|
| Services use Gateway | ❌ FAIL — 125 violations (INV-003 VIOLATED) |
| Gateway importable | ✅ PASS |
| Gateway dispatch functional | ❌ FAIL — NotImplementedError |
| Model Registry exists | ❌ FAIL — file does not exist |
| Import guard CI integration | ⚠️ Tool exists, not in CI |
| Migration plan exists | ✅ PASS (Report 07) |

---

## 8. Final Assessment

The "Services use Gateway ✅ PASS" claim in Report 19's gate table is **factually incorrect**. The same report's Section 9 correctly identifies this as FAILED. This self-contradiction makes Report 19's final gate status unreliable.

The service→gateway migration is a **P1 blocker** for ECO-05. It requires:
1. Model Registry creation
2. Gateway dispatch implementation
3. Migration of 125 import chains across 74 service directories

---

*This audit is reproducible via: `python tools/detect_imports.py --format=json` from the repository root. Full violation list in `tools/detect_imports_output_v2.json`.*
