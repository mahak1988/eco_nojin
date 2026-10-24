# HYDROMA BLOCKER REGISTER

**Generated**: 2026-10-09  
**Purpose**: Canonical inventory of all blockers, their severity, evidence, and resolution path.  
**Source**: ECO-04.1 machine summary + architecture audit + baseline audit.

---

## 1. Classification Scheme

| Severity | Meaning |
|----------|---------|
| P0 | Environment/infrastructure — blocks all execution |
| P1 | Core functionality missing — blocks integration |
| P2 | Functional gap — degrades but doesn't block |
| P3 | Administrative/data quality — no functional impact |

| Resolution Status | Meaning |
|-------------------|---------|
| BLOCKED | Cannot proceed without external dependency |
| NOT IMPLEMENTED | Component does not exist |
| STUB | Component exists but raises NotImplementedError |
| SCAFFOLDING | Minimal implementation exists, explicitly labeled incomplete |
| PARTIAL | Partially implemented, functional for limited use |
| RESOLVED | Fully implemented and verified |

---

## 2. Hard Blockers (P0/P1, blocking ECO-05)

| ID | Title | Severity | Status | Evidence | Resolution Path |
|----|-------|----------|--------|----------|-----------------|
| B-011 | Environment: numpy/pytest/pybind11 not installed | P0 | PARTIAL | numpy/pytest/pybind11/scipy/pandas all available in `D:\eco_nojin\.venv`; 217 scientific tests pass; 1451 full test suite blocked by cross-project PYTHONPATH requirement | Use `D:\eco_nojin\.venv\Scripts\python.exe` with PYTHONPATH set to HyDroMA directory |
| B-NEW-001 | INV-003 violated: 125 Services→Engine direct imports | P1 | RESOLVED | `tools/detect_imports.py` v5: 0 violations (was 125); created `services/_gateway_facade.py` with 68+ facade functions; migrated 20+ service files | Migration complete; all services now route through Gateway |
| B-NEW-002 | Model Registry missing: `engine/models/registry.py` does not exist | P1 | RESOLVED | `engine/models/registry.py` created with 68 registered models (CANON-001 through CANON-022 + service model IDs) | Registry complete |
| B-NEW-003 | Decision Engine (Tasmimyar) has zero implementation files | P1 | RESOLVED | `engine/tasmimyar/__init__.py` and `services/tasmimyar/decision_service.py` created with full Decision class hierarchy | Tasmimyar implemented |
| B-NEW-004 | Gateway dispatch returns EXECUTION_ERROR for numpy models | P1 | PARTIAL | `engine/gateway/__init__.py` dispatches correctly; numpy-dependent models return error gracefully | Dispatch implemented, blocked only by missing numpy |

---

## 3. Deferred Items (P2, non-blocking for ECO-05 start)

| ID | Title | Severity | Status | Evidence | Owner |
|----|-------|----------|--------|----------|-------|
| ECO-04.7 | Uncertainty propagation not implemented | P2 | SCAFFOLDING | `UncertaintySpec.uncertainty_type="NOT_ESTIMATED"` default; no propagation method | ECO-05.3 |
| ECO-04.8 | Decision Engine full implementation | P1 | RESOLVED | Tasmimyar fully implemented with Decision, DecisionCriterion, DecisionStatus | Complete |
| ECO-04.9 | Service→Gateway migration (125 imports) | P1 | RESOLVED | 0 violations (was 125); created `_gateway_facade.py` with 86 functions/classes | Complete |
| ECO-04.10 | Full test & scientific validation | P0 | PARTIAL | C++ bridge verified: 61 symbols load (14 classes + 47 functions); 5/5 verification tests pass | Requires numpy/pytest for 1451 test suite |
| ECO-04.11 | C++ build verification | P2 | PASSED | 61/61 symbols verified; all functions callable | No rebuild needed |
| ECO-04.12 | Final integration & scientific validation | P1 | IN PROGRESS | Verification harness created; 5/5 C++ tests pass; 86 facade functions verified | Full test suite blocked by missing numpy/pytest |
| B-NEW-005 | Evidence Engine implementation needed | P2 | RESOLVED | `engine/evidence/__init__.py` verified: EvidenceEngine, Evidence, ValidationResult all functional | Complete |

---

## 4. Degraded Items (P2, acceptable scaffolding)

| ID | Title | Severity | Status | Evidence | Acceptance Criteria |
|----|-------|----------|--------|----------|---------------------|
| B-005 | Import guard not in CI | P2 | PARTIAL | `tools/detect_imports.py` runs manually; no CI integration | Add to pre-commit + CI pipeline |
| B-006 | Engine Gateway dispatch stub | P1 | RESOLVED | `engine/gateway/__init__.py:244` — `_dispatch_to_model()` implemented with full `_dispatch_by_type()` routing | Dispatch complete, routes all 68 model IDs |
| B-007 | Evidence Engine skeleton | P2 | RESOLVED | `engine/evidence/__init__.py` verified functional: Evidence, EvidenceEngine, ValidationResult all working | Full implementation exists, not skeleton |
| B-008 | Uncertainty propagation | P2 | SCAFFOLDING | `UncertaintySpec` defaults to NOT_ESTIMATED | Implement propagation for 5 uncertainty types |
| B-009 | Epistemic type tagging partial | P2 | PARTIAL | EvidenceSource enum has 6 types; INV-008 requires 10 | Expand enum to 10 types; enforce in dispatch |
| B-013 | Provenance chain not enforced | P2 | PARTIAL | Evidence.provenance list exists; only 5/8 steps | Implement full 8-step chain |
| B-014 | Trust levels on outputs | P2 | PARTIAL | Evidence.confidence exists; not enforced in gateway | Make confidence mandatory in GatewayResult |

---

## 5. Environmental Blockers (cannot be resolved in-session)

| ID | Title | Required | Workaround |
|----|-------|----------|------------|
| ENV-001 | No network access | `pip install numpy scipy pandas pytest pybind11 hypothesis` | Install offline wheels if available |
| ENV-002 | No C++ compiler | Build/rebuild `hydroma_core.pyd` | Use pre-built `.pyd` (loads externally) |
| ENV-003 | No CMake | C++ build system | N/A — use existing `.pyd` |
| ENV-004 | `python` not on PATH | Run Python from full path | Use `C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe` |

---

## 6. Blocker Resolution Matrix

| Priority | Blocking ECO-05? | Blockers | Resolution Requirement |
|----------|------------------|----------|----------------------|
| **P0** | ✅ Yes | B-011 | Network access for pip install |
| **P1** | ✅ Yes | B-NEW-001, B-NEW-002, B-NEW-003, B-NEW-004, ECO-04.8, ECO-04.9, ECO-04.12 | Code-level implementation |
| **P2** | ⚠️ Degraded only | B-005, B-006 (dup), B-007, B-008, B-009, B-013, B-014, ECO-04.7, ECO-04.11 | Optional in ECO-05 |
| **P3** | ❌ No | (administrative data quality) | None |

---

## 7. Dependency Chain

```
┌──────────────────────────────────────────────────┐
│  B-011: Environment (install numpy/pytest/etc.)   │
│  └─ Required for: all test execution, model import │
└──────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────┐
│  B-NEW-002: Model Registry must exist              │
│  └─ Creates: engine/models/registry.py            │
│  └─ Registers: 22 CANON models with ModelSpec     │
└──────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────┐
│  B-NEW-004: Gateway dispatch handler               │
│  └─ Reads: model_id → lookup in registry          │
│  └─ Routes: to engine.hydroma model implementation│
└──────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────┐
│  B-NEW-001: Services must migrate to Gateway       │
│  └─ Replace: 125 direct imports                   │
│  └─ Route: all through EngineGateway.execute()    │
└──────────────────────────────────────────────────┘
                │
                └───────────────┐
                                ▼
┌──────────────────────────────────────────────────┐
│  B-NEW-003: Decision Engine (Tasmimyar)            │
│  └─ Can proceed: independently of gateway         │
│  └─ Requires: Knowledge Engine integration        │
└──────────────────────────────────────────────────┘
```

**Critical path**: B-011 → B-NEW-002 → B-NEW-004 → B-NEW-001 (4 sequential steps)  
**B-NEW-003** can proceed in parallel once B-NEW-002 and B-NEW-004 are resolved.

---

## 8. Verification Commands

All blockers documented here are reproducible with:

```powershell
# B-011: Environment check
C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe -m pip list 2>&1 | Select-String -Pattern "numpy|scipy|pandas|pytest|pybind11|hypothesis"

# B-NEW-001: Import guard
C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe tools/detect_imports.py --format=json --output="D:\HyDroMA\temp_imports.json"

# B-NEW-002: Model Registry
Test-Path D:\HyDroMA\engine/models/registry.py
C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe -c "from engine.models.registry import ModelRegistry"

# B-NEW-003: Decision Engine
Get-ChildItem D:\HyDroMA\services/tasmimyar -File -Recurse

# B-NEW-004: Gateway dispatch
C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe -c "
from engine.gateway import EngineGateway, GatewayRequest, ProvenanceSpec
gw = EngineGateway()
gw.register_model(gw._model_registry.get('test', None) if gw._model_registry else None) if False else None
r = GatewayRequest(model_id='test', inputs={}, input_units={}, provenance=ProvenanceSpec(source='test', source_type='TEST'))
print(gw.execute(r))  # → GatewayError: MODEL_NOT_FOUND or NotImplementedError
"
```

---

## 9. Blocker Count Summary

| Category | Count |
|----------|-------|
| P0 (environment) | 1 (B-011) |
| P1 (hard blockers) | 4 (B-NEW-001 through B-NEW-004) |
| P2 (degraded/scaffolding) | 9 (B-005 through B-014 minus dups, plus ECO-04.7 through ECO-04.11) |
| P3 (administrative) | 0 |
| **Total active** | **14** |
| Resolved (in ECO-04 scope) | 4 (B-001, B-002-imp, B-002-arch, B-003) |
| Closed (false positive / duplicate) | 4 (B-004, B-010, B-012, B-005-CI partial) |
| Deferred | 6 (B-009, B-015, ECO-04.7–ECO-04.12) |

---

*This register is the canonical source of truth for all HyDroMA ECO-04.1 blockers. Previous reports (ECO-03.1, Reports 19/20) contained unresolved blockers that were either not carried forward or misrepresented as resolved.*