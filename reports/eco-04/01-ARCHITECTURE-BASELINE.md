# ECO-04: Architecture Baseline — Report 01

## Architecture baseline state at ECO-04 start

---

## 1. Architecture Invariant Status (Pre-ECO-04.1)

| Invariant | Description | Status | Evidence |
|-----------|-------------|--------|----------|
| INV-001 | Engine MUST NOT import services | **PASS** | Import guard: 0 violations |
| INV-002 | Engine MUST NOT import database | **FAIL** | Import guard: 7 violations (WARNING/ERROR) |
| INV-003 | Services MUST NOT import engine internals directly | **FAIL** | 100+ violations (all go through direct imports) |
| INV-004 | Circular dependency forbidden | **PASS** | No circular imports detected |
| INV-005 | Frontend cannot call kernel directly | **PASS** | No frontend imports in engine |
| INV-006 | Scientific output must have provenance | **FAIL** | No provenance on outputs |
| INV-007 | Model output not stored as observation | **FAIL** | No epistemic types |
| INV-008 | Epistemic status not implicit | **FAIL** | No type tagging |
| INV-009 | AI has no scientific authority | **PASS** | No AI in engine computation |
| INV-010 | AI cannot change equations/parameters | **PASS** | No AI→engine imports |
| INV-011 | Absence of uncertainty ≠ certainty | **FAIL** | All outputs are point estimates |
| INV-012 | Decision must be traceable | **FAIL** | No decision tracking |
| INV-013 | Test success ≠ scientific validity | PASS | (by design) |
| INV-014 | Scientific validity needs separate evidence | PASS | (by design) |
| INV-015 | Research code vs production code separated | PARTIAL | Mixed in some modules |

---

## 2. Architecture Violations Summary

| Violation Type | Count | Severity | Action Required |
|----------------|-------|----------|-----------------|
| Engine→Database (deferred) | 6 | WARNING | ECO-04.3: Replace with port/adapter |
| Engine→Database (immediate) | 1 | ERROR | ECO-04.3: Replace with port/adapter |
| Services→Engine (direct) | 100+ | HIGH | ECO-04.9: Route through Gateway |
| No provenance on outputs | All | HIGH | ECO-04.5 |
| No uncertainty | All | MEDIUM | ECO-04.7 |
| No epistemic types | All | MEDIUM | ECO-04.6 |
| No trust levels | All | MEDIUM | ECO-04.5 |

---

## 3. Import Guard Baseline

**Command**: `python tools/detect_imports.py --root .`
**Result**: FAIL (7 violations)

**Violation Detail**:
| # | Rule | File | Line | Severity |
|---|------|------|------|----------|
| 1 | ENGINE_NO_DATABASE | `engine/data_connector.py` | 86 | WARNING |
| 2 | ENGINE_NO_DATABASE | `engine/resource_manager.py` | 45 | WARNING |
| 3 | ENGINE_NO_DATABASE | `engine/resource_manager.py` | 70 | WARNING |
| 4 | ENGINE_NO_DATABASE | `engine/resource_manager.py` | 83 | WARNING |
| 5 | ENGINE_NO_DATABASE | `engine/ports/session.py` | 162 | WARNING |
| 6 | ENGINE_NO_DATABASE | `engine/ports/session.py` | 201 | WARNING |
| 7 | ENGINE_NO_DATABASE (ERROR) | `engine/hydroma/biofertilizer/models.py` | 32 | ERROR |

**No ENGINE_NO_SERVICES violations** — B-001 is verified FIXED.

---

## 4. Bounded Context Status

| Context | Services | Violations | Status |
|---------|----------|------------|--------|
| CTX-001 Platform Core | 9 | 0 | PASS |
| CTX-002 Hydroma Engine | 1 | 0 | PASS |
| CTX-003 Hydrology | 6 | 0 | PASS |
| CTX-004 AgriWater | 6 | 0 | PASS |
| CTX-005 Evidence Provenance | 5 | 0 | PASS |
| CTX-006 Decision Engine | 3 | 0 | PASS |
| CTX-007 Remote Sensing | 2 | 0 | PASS |
| CTX-008 Reporting/AI | 3 | 1 (services.ai→scientific_motors, potential) | WATCH |

---

## 5. Architecture Baseline Conclusion

**Status**: 2 invariants violated (INV-002, INV-003), 6 invariants not implemented (INV-006 through INV-012, INV-015 partial).

The architecture baseline shows:
1. **Engine→Services**: ✅ FIXED (0 violations)
2. **Engine→Database**: ❌ 7 violations (deferred imports, architecture violation remains)
3. **Services→Engine via Gateway**: ❌ No gateway enforced
4. **Provenance/Evidence**: Not implemented (deferred to ECO-04.5)
5. **Uncertainty/Epistemic types**: Not implemented (deferred to ECO-04.6/04.7)

---

*Report generated: 2026-10-08*
*Status: Architecture baseline captured. 7 violations detected (all database-related).*
