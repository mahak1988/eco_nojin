# ECO-04.1: Final Blocker Register — Report 33

## Complete inventory of all blockers, P0/P1 issues, and deferred items

**Report Date**: 2026-10-08T17:00:00Z  
**Method**: Repository scan + runtime testing + report reconciliation

---

## 1. Initial Blocker Accounting (from ECO-03.1)

```
Initial blockers: 15

FIXED_AND_VERIFIED:          3 (B-001, B-002-imp, B-003)
FIXED_BUT_UNVERIFIED:        0
FALSE_POSITIVE:              1 (B-004)
DUPLICATE:                    2 (B-010, B-012)
CONFIRMED_BLOCKER:            3 (B-005, B-006, B-011)
DEFERRED_TO_ECO_04:           6 (B-002-arch, B-007, B-008, B-009, B-013, B-014)
REQUIRES_SCIENTIFIC_REVIEW:   1 (B-015/Theis)
                              1 (B-015/Theis)
NON_BLOCKING:                 0
Total:                        15 ✅
```

---

## 2. Re-verification of Initial Blockers

| ID | Original Description | ECO-03.1 Status | ECO-04.1 Re-verification | Current Status |
|---|---|---|---|---|
| B-001 | Engine → Services import | FIXED_AND_VERIFIED | Confirmed: 0 violations (import guard) | **RESOLVED** ✅ |
| B-002-imp | Missing database package (import) | FIXED_AND_VERIFIED | `import engine` succeeds | **RESOLVED** ✅ |
| B-002-arch | Engine→Database architectural fix | DEFERRED_TO_ECO_04 | Confirmed: 0 violations (PersistencePort) | **RESOLVED** ✅ |
| B-003 | Missing dependency manifest | FIXED_AND_VERIFIED | `pyproject.toml` exists, valid TOML | **RESOLVED** ✅ |
| B-004 | Temperature constant divergence | FALSE_POSITIVE | — | **CLOSED** ✅ |
| B-005 | Import guard not in CI | CONFIRMED_BLOCKER | Tool exists and runs; CI not available | **DEGRADED** ⚠️ |
| B-006 | No Engine Gateway | CONFIRMED_BLOCKER → IMPLEMENTED IN ECO-04 | Gateway exists but dispatch is stub | **PARTIAL** ⚠️ |
| B-007 | No Evidence Engine | DEFERRED_TO_ECO_04 | Skeleton created but not fully implemented | **SCAFFOLDING** ⚠️ |
| B-008 | No uncertainty propagation | DEFERRED_TO_ECO_04 | UncertaintySpec exists but NOT_ESTIMATED only | **SCAFFOLDING** ⚠️ |
| B-009 | No epistemic type tagging | DEFERRED_TO_ECO_04 | Enums exist but not enforced | **PARTIAL** ⚠️ |
| B-010 | (duplicate of B-005) | DUPLICATE | — | **CLOSED** ✅ |
| B-011 | Tests UNRUNNABLE | CONFIRMED_BLOCKER | Confirmed: pytest/numpy missing, no network | **BLOCKED** ❌ |
| B-012 | (duplicate of B-005) | DUPLICATE | — | **CLOSED** ✅ |
| B-013 | No provenance on outputs | DEFERRED_TO_ECO_04 | ProvenanceSpec exists; chain not enforced | **PARTIAL** ⚠️ |
| B-014 | No trust levels on outputs | DEFERRED_TO_ECO_04 | Evidence.confidence exists but not enforced | **PARTIAL** ⚠️ |
| B-015 | Theis convergence undocumented | REQUIRES_SCIENTIFIC_REVIEW | Not in sprint scope | **DEFERRED** ⏳ |

---

## 3. New Blockers Identified by ECO-04.1

| ID | Description | Severity | Evidence | Blocking ECO-05? |
|---|---|---|---|---|
| B-NEW-001 | **INV-003 VIOLATED**: 125 Services→Engine direct imports | P1 | Import guard v2: SERVICES_NO_ENGINE_INTERNALS rule, 125 violations | **YES** |
| B-NEW-002 | **Model Registry does not exist**: `engine/models/registry.py` claimed in Report 19/20 but file absent | P1 | Test-Path → False; `python -c "from engine.models.registry import ModelRegistry"` → ModuleNotFoundError | **YES** |
| B-NEW-003 | **Decision Engine has zero implementation**: `services/tasmimyar/` is empty | P1 | Get-ChildItem -File -Recurse → no files | **YES** |
| B-NEW-004 | **Gateway dispatch is stub**: `_dispatch_to_model()` raises NotImplementedError | P1 | `engine/gateway/__init__.py:354` — always raises; gateway.execute() cannot compute | **YES** |
| B-NEW-005 | **Import guard missing SERVICE rule**: SERVICES_NO_ENGINE_INTERNALS rule was missing from detect_imports.py | P1 | Added in ECO-04.1; 125 violations found | **YES** (now detected) |
| B-NEW-006 | **Saved import guard JSON stale**: `03-IMPORT-GUARD-REPORT.json` shows FAIL/7 violations | P2 | File not updated after PersistencePort fix | NO (corrected by this report) |
| B-NEW-007 | **Report 19 self-contradiction**: Gate table says "Services use Gateway ✅ PASS" but Section 9 says "❌ NO" | P2 | Report 19 internal inconsistency | NO (documented here) |
| B-NEW-008 | **Report 19 claims Model Registry implemented**: 22 CANON models registered | P1 | Contradicts B-NEW-002 | YES (same as B-NEW-002) |

---

## 4. Blocker Classification

| Classification | Count | Blocking ECO-05? |
|---|---|---|
| RESOLVED (fixed in ECO-04) | 4 (B-001, B-002-imp, B-002-arch, B-003) | — |
| CLOSED (false positive / duplicate) | 4 (B-004, B-010, B-012, B-005-CI partial) | — |
| SCAFFOLDING (exists but incomplete) | 5 (B-006-gateway, B-007-evidence, B-008-uncertainty, B-013-provenance, B-014-trust) | No (scaffolding is acceptable for these) |
| DEFERRED (out of sprint scope) | 2 (B-009-epistemic, B-015-Theis) | No |
| **HARD BLOCKER (P0/P1, unresolved)** | **5** (B-011, B-NEW-001, B-NEW-002, B-NEW-003, B-NEW-004) | **YES** |
| **PARTIAL (degraded)** | 1 (B-005 — tool exists, no CI) | No |

---

## 5. Detailed Blocker Descriptions

### B-011 — Environment (P0)
- **Status**: BLOCKED
- **Evidence**: `pip install -e ".[dev]"` fails — `HTTPSConnectionPool` — no network. `python -m pip list` confirms numpy, scipy, pandas, pytest, pybind11 not installed.
- **Verification command**: `python -m pip install -e ".[dev]"` → FAILED
- **Impact**: 119 test files cannot be collected; 0 tests executed; scientific validation blocked; C++ build blocked.

### B-NEW-001 — INV-003 Service Boundary Violation (P1)
- **Status**: VIOLATED
- **Evidence**: `python tools/detect_imports.py --json` → 125 violations of SERVICES_NO_ENGINE_INTERNALS rule
- **Verification command**: `python tools/detect_imports.py --format=json --output tools/detect_imports_output_v2.json`
- **Impact**: Services bypass Engine Gateway; provenance/unit validation/input validation not enforced.

### B-NEW-002 — Model Registry Missing (P1)
- **Status**: NOT IMPLEMENTED
- **Evidence**: `test-path engine/models/registry.py` → False; `python -c "from engine.models.registry import ModelRegistry"` → `ModuleNotFoundError: No module named 'engine.models'`
- **Impact**: No model registration; ModelSpec exists only in gateway but no registry to populate it.

### B-NEW-003 — Decision Engine Missing (P1)
- **Status**: NOT IMPLEMENTED
- **Evidence**: `Get-ChildItem services/tasmimyar -File -Recurse` → empty (no Python files in directory)
- **Impact**: No decision/recommendation capability; Tasmimyar contract unimplemented.

### B-NEW-004 — Gateway Dispatch Stub (P1)
- **Status**: IMPLEMENTED (stub)
- **Evidence**: `engine/gateway/__init__.py:346-357` — `_dispatch_to_model()` raises `NotImplementedError`
- **Verification command**: `python -c "from engine.gateway import EngineGateway, GatewayRequest, ProvenanceSpec; gw=EngineGateway(); gw.execute(GatewayRequest(...))"` → returns GatewayError
- **Impact**: Gateway exists but cannot execute any model.

---

## 6. Blocker Resolution Path

| Blocker | Requires | Environment Available? |
|---|---|---|
| B-011 (env) | Network access for pip install | ❌ No |
| B-NEW-001 (services) | Gateway dispatch + service migration | ✅ Can start (code changes) |
| B-NEW-002 (registry) | New file creation | ✅ Can start |
| B-NEW-003 (decision) | New implementation | ✅ Can start |
| B-NEW-004 (dispatch) | Implementation of model dispatch handler | ✅ Can start |

**Critical insight**: B-NEW-001 through B-NEW-004 require the gateway dispatch to be implemented first. But the gateway dispatch itself is blocked on the model registry (B-NEW-002), creating a dependency chain. The service migration (B-NEW-001) cannot complete without a working dispatch (B-NEW-004).

---

## 7. Final Blocker Count

| Type | Count |
|---|---|
| Resolved in ECO-04 | 4 |
| Closed (false positive / duplicate) | 4 |
| Scaffolding (acceptable for now) | 5 |
| Deferred (out of scope) | 2 |
| **Hard blockers (unresolved, P0/P1)** | **5** |

---

*This register is the canonical source of truth for all ECO-04 blockers. Previous reports (ECO-03.1, ECO-04 Reports 00–20) contained unresolved blockers that were either not carried forward or misrepresented as resolved.*
