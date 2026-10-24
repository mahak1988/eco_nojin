# ECO-03.1: Engine→Database Dependency — Report 06

## Complete audit of all database imports in engine/

---

## Methodology

Full repository scan for:
- `from database`
- `import database`
- `database.` (module attribute access)

All occurrences in `engine/` code examined and classified.

---

## Classification Definitions

| Type | Definition | Architecture Violation? |
|------|------------|------------------------|
| direct_dependency | Import at module level (import-time) | YES |
| optional_dependency | Import inside `try/except ImportError` with fallback | NO (if fallback is safe) |
| test_only | Import inside test files only | NO |
| legacy_dependency | Import in deprecated/commented code | NO |
| adapter_dependency | Import behind port/adapter interface | NO |
| architecture_violation | Import in production code without fallback port | YES |

---

## Production Code: Database Imports

| File | Line | Import | Type | Classification | Notes |
|------|------|--------|------|----------------|-------|
| `engine/data_connector.py` | 86 | `from database.hub import hub` | Deferred (runtime) | architecture_violation | Inside method body, called at runtime |
| `engine/resource_manager.py` | 45 | `from database.hub import hub` | Deferred (runtime) | architecture_violation | Inside `managed_connection()` function |
| `engine/resource_manager.py` | 70 | `from database.hub import hub` | Deferred (runtime) | architecture_violation | Inside `managed_connection()` function |
| `engine/resource_manager.py` | 83 | `from database.hub import hub` | Deferred (runtime) | architecture_violation | Inside `managed_connection()` function |
| `engine/ports/session.py` | 162 | `from database.config import SessionLocal` | Deferred (runtime) | architecture_violation | Inside `default_session_factory()` |
| `engine/ports/session.py` | 201 | `from database.hub import hub` | Deferred (runtime) | architecture_violation | Inside `_default_session_port()` |
| `engine/hydroma/biofertilizer/models.py` | 32 | `from database.base import Base` | Optional (try/except) | architecture_violation | Has SQLAlchemy fallback, but still references database |
| `engine/hydroma/core/database.py` | 46-50 | `_SOURCES` dict referencing `database.config`, `database.models` | Lazy (PEP 562) | architecture_violation | Compatibility shim to database layer |

---

## Test Code: Database Imports

| File | Line | Import | Type | Classification | Notes |
|------|------|--------|------|----------------|-------|
| `engine/strict_tests/test_s12_table_registration.py` | 154 | `from database.base import Base` | Test-only | NOT_APPLICABLE | Test file |
| `engine/strict_tests/test_s12_table_registration.py` | 155 | `from database.config import Base` | Test-only | NOT_APPLICABLE | Test file |
| `engine/strict_tests/test_s12_table_registration.py` | 187, 201, 231, 249, 327 | `import database.models` | Test-only | NOT_APPLICABLE | Test file |
| `engine/hydroma/biofertilizer/tests/conftest.py` | 10 | `from database.base import Base` | Test-only | NOT_APPLICABLE | Test fixture |
| `engine/hydroma/biofertilizer/tests/conftest.py` | 11 | `from database.hub import hub` | Test-only | NOT_APPLICABLE | Test fixture |
| `engine/hydroma/biofertilizer/tests/test_calibration_session.py` | 27 | `from database.config import SessionLocal` | Test-only | NOT_APPLICABLE | Test file |
| `engine/hydroma/biofertilizer/tests/test_calibration_session.py` | 80 | `from database.models import ...` | Test-only | NOT_APPLICABLE | Test file |
| `engine/hydroma/biofertilizer/tests/test_nojin_comprehensive.py` | 197, 207, 220, 234, 245 | `from database import SessionLocal` | Test-only | NOT_APPLICABLE | Test file |

---

## Summary

| Classification | Count |
|----------------|-------|
| architecture_violation (production code, deferred) | 8 occurrences in 4 files |
| test_only | 15 occurrences in 4 files |
| optional_dependency | 1 (biofertilizer/models.py, has fallback) |
| legacy_dependency | 1 (comment in calibration.py:16-17) |

**Total production database references**: 9 (8 deferred + 1 with fallback)

---

## Architectural Assessment

### Current State

The engine uses **deferred imports** (lazy loading inside function bodies) as a workaround for the database dependency. This means:

1. `import engine` succeeds (no database import at module load time)
2. But database is still a runtime dependency
3. The architectural invariant INV-002 ("Engine never depends on database") is **technically violated at runtime**

### The Stub Fix

A `database/` stub package was created during ECO-03 to make `import engine` work. This is a **WORKAROUND**, not a **FIX**.

### Proper Resolution (ECO-04)

Per ECO-03.1 §28 Database Stub Rule — **Mode A**: Engine should be database-independent. The stub should be removed and replaced with:
1. A `PersistencePort` interface in `engine/ports/`
2. Database injection via dependency injection
3. Services provide the database implementation to the engine

However, this is a **refactoring task** that violates the "no refactor" rule of ECO-03.1 §89. It must be **DEFERRED_TO_ECO_04**.

---

## Blocker Classification

| Question | Answer | Implication |
|----------|--------|------------|
| Does `import engine` succeed? | YES | BOOTP-002 (import failure) = FIXED_BUT_UNVERIFIED |
| Does engine architecturally violate INV-002? | YES | ARCH-VIOLATION = CONFIRMED_BLOCKER |

**B-002 is now TWO separate findings**:
- B-002-imp (import failure): RESOLVED
- B-002-arch (architectural violation): REMAINS AS HARD BLOCKER for ECO-04

---

## Recommendation for ECO-04

| Action | Priority | Required By |
|--------|----------|-------------|
| Create `PersistencePort` in `engine/ports/` | HIGH | ECO-04.1 |
| Inject hub via constructor (DataConnector.__init__ already accepts `hub=None`) | HIGH | ECO-04.1 |
| Remove all deferred `from database.hub` imports | HIGH | ECO-04.1 |
| Remove stub `database/` package after refactoring | LOW | ECO-04.2 |

---

*Report generated: 2026-10-08*
*Status: 8 production database references remain as architectural violations*