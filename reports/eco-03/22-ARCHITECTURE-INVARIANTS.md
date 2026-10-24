# ECO-03: Architecture Invariants — Report 22
## Formally Registered Invariants

---

## Executive Summary

This report formally registers all architecture invariants, with verification status against actual source code. 15 invariants are defined; verification shows 4 VIOLATED, 11 DESIGNED BUT NOT ENFORCED.

---

## Invariant Registry

### INV-001
**Statement**: Engine never depends on UI.

| Field | Value |
|-------|-------|
| verification_status | VERIFIED |
| evidence | `engine/hydroma/visualization/` exists but contains NO UI framework imports; only generates plots for internal use |
| enforcement | N/A (no UI in engine) |
| owner | engine team |

---

### INV-002
**Statement**: Engine never depends directly on database.

| Field | Value |
|-------|-------|
| verification_status | **VIOLATED** |
| evidence | `engine/data_connector.py:86`: `from database.hub import hub`; `engine/resource_manager.py:45,70,83`: `from database.hub import hub`; `engine/ports/session.py:162`: `from database.config import SessionLocal`; `engine/hydroma/biofertilizer/models.py:32`: `from database.base import Base` |
| enforcement | NOT ENFORCED |
| owner | engine team |
| blocking | YES |

---

### INV-003
**Statement**: Scientific models cannot be silently modified by AI.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | No AI code imports scientific model definitions; but no import guard exists to prevent it |
| enforcement | NOT ENFORCED |
| owner | ai team |
| blocking | YES |

---

### INV-004
**Statement**: AI cannot change scientific equations.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | AI services do not currently modify equations, but no import guard prevents it |
| enforcement | NOT ENFORCED |
| owner | ai team |
| blocking | Yes |

---

### INV-005
**Statement**: AI cannot change provenance.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | No provenance mutation guard exists; `engine/hydroma/provenance.py` has no write protection |
| enforcement | NOT ENFORCED |
| owner | provenance team |
| blocking | Yes |

---

### INV-006
**Statement**: AI cannot change epistemic status.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | No epistemic status system exists in code; if it did, no guard would prevent AI mutation |
| enforcement | NOT ENFORCED |
| owner | knowledge team |
| blocking | Yes |

---

### INV-007
**Statement**: Model output is not observation.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | `engine/hydroma/provenance.py:ResultProvenance` has `MODEL_OUTPUT` and `OBSERVATION` constants, but no runtime enforcement prevents treating them as equivalent |
| enforcement | NOT ENFORCED |
| owner | provenance team |
| blocking | Yes |

---

### INV-008
**Statement**: Local knowledge is not automatically scientific fact.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | `services/daneshyar/` exists but Local Knowledge (KT-008) is NOT distinguished from SCIENTIFIC_FACT in any code path |
| enforcement | NOT ENFORCED |
| owner | knowledge team |
| blocking | Yes |

---

### INV-009
**Statement**: Software test success is not scientific validation.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | Test passes are conflated with validation in comments and report language; ECO-01/07-MODEL-QUALITY-MATRIX.md uses "VERIFIED" for both software tests and scientific validation |
| enforcement | NOT ENFORCED |
| owner | engine team |
| blocking | No |

---

### INV-010
**Statement**: Recommendation requires traceable evidence.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | `engine/hydroma/decision_support/recommender.py` exists but does not trace recommendations to evidence |
| enforcement | NOT ENFORCED |
| owner | decision team |
| blocking | Yes |

---

### INV-011
**Statement**: Uncertainty absence is not certainty.

| Field | Value |
|-------|-------|
| verification_status | VIOLATED |
| evidence | All model outputs return point estimates without any uncertainty metadata; C++ kernels return `double` or `std::vector<double>` with no uncertainty fields |
| enforcement | NOT ENFORCED |
| owner | uncertainty team |
| blocking | Yes |

---

### INV-012
**Statement**: Units must be explicit.

| Field | Value |
|-------|-------|
| verification_status | PARTIAL |
| evidence | UNIFORMAT defined in ADR-005 but not enforced; C++ kernels use mixed conventions (celsius for temperature input); no unit annotations in function signatures |
| enforcement | NOT ENFORCED |
| owner | engine team |
| blocking | Yes |

---

### INV-013
**Statement**: Scientific model identity must be versioned.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | ECO-01/20-CANONICAL-ASSETS.md defines models but NO version field; services/models/registry.py has model entries but no version tracking |
| enforcement | NOT ENFORCED |
| owner | knowledge team |
| blocking | No |

---

### INV-014
**Statement**: Legacy directory structure is not canonical architecture.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED |
| evidence | ECO-01 §1.2 correctly identifies inconsistent paths (`hydra/`, `hydorama/`); actual code uses `hydroma/` consistently |
| enforcement | NOT ENFORCED |
| owner | architecture team |
| blocking | No |

---

### INV-015
**Statement**: Smart contracts from old project are not production contracts.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED |
| evidence | `services/blockchain/` exists but is empty/stub; no actual smart contracts found in repository |
| enforcement | NOT ENFORCED |
| owner | blockchain team |
| blocking | No |

---

## New Invariants Identified by ECO-03

### INV-016
**Statement**: Engine may not import from services.

| Field | Value |
|-------|-------|
| verification_status | VIOLATED |
| evidence | `engine/hydroma/generative_ai/__init__.py:20-22,46-48` imports from `services.ai.*` |
| enforcement | NOT ENFORCED |
| owner | engine team |
| blocking | YES |

---

### INV-017
**Statement**: Engine may not import from database (external package).

| Field | Value |
|-------|-------|
| verification_status | VIOLATED |
| evidence | `engine/data_connector.py:86`, `engine/resource_manager.py:45,70,83`, `engine/ports/session.py:162` import from `database.*` — an external package not present in repository |
| enforcement | NOT ENFORCED |
| owner | engine team |
| blocking | YES |

---

### INV-018
**Statement**: Service count must match registry.

| Field | Value |
|-------|-------|
| verification_status | DESIGNED BUT NOT ENFORCED |
| evidence | ECO-01 reports 73 services; actual count is 75. Discrepancy never reconciled. |
| enforcement | NOT ENFORCED |
| owner | services team |
| blocking | No |

---

## Invariant Compliance Summary

| Status | Count | Invariants |
|--------|-------|------------|
| VERIFIED | 1 | INV-001 |
| PARTIAL | 1 | INV-012 |
| DESIGNED | 1 | INV-014 |
| DESIGNED BUT NOT ENFORCED | 9 | INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-013 |
| VIOLATED | 3 | INV-002, INV-011, INV-016, INV-017 |
| **Total** | **18** | |

---

## Invariant Enforcement Strategy (For ECO-04)

### Phase 1: Immediate Fixes
1. Fix INV-016: Remove `engine/hydroma/generative_ai/` → move to `services/ai/`
2. Fix INV-017: Remove or provision `database/` dependency
3. Fix INV-002: Remove all `database` imports from engine
4. Fix INV-011: Add uncertainty fields to all model outputs

### Phase 2: Runtime Enforcement
1. Add import guard decorator for AI isolation
2. Add provenance immutability enforcement
3. Add epistemic type tagging to knowledge items

### Phase 3: CI/CD Integration
1. AST-based import scanning in CI pipeline
2. Architecture invariant tests in test suite
3. Block merges on invariant violations

---

*Report generated: 2026-10-08*
*Status: 3 invariants VIOLATED, 10 DESIGNED BUT NOT ENFORCED, 5 verified/partial*