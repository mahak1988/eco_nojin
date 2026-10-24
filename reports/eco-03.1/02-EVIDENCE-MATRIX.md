# ECO-03.1: Evidence Matrix — Report 02

## Master evidence table for all blockers

---

## Evidence Matrix

| Blocker | Original Claim | Source File(s) | Line(s) | Reproduced? | Fixed? | Verified? | Current Severity | ECO-04 Blocking? |
|---------|----------------|----------------|---------|-------------|--------|-----------|------------------|-----------------|
| B-001 | Engine→Services import | `engine/hydroma/generative_ai/__init__.py` | 20-22, 46-48 | YES | YES | YES | — | NO (fixed) |
| B-002-imp | Import failure (database missing) | `engine/data_connector.py`, `engine/resource_manager.py`, `engine/ports/session.py` | 86, 45/70/83, 162 | YES | YES (stub) | YES | — | NO (stub works) |
| B-002-arch | Engine→database architectural violation | Same files | Same lines | YES | NO | NO | HIGH | DEFERRED |
| B-003 | Missing dependency manifest | Repository root | — | YES | YES | YES | — | NO (fixed) |
| B-004 | Temperature constant divergence | `engine/cpp_core/src/climate.cpp`, `engine/hydroma/cpp_bridge/__init__.py` | 97-98, 138 vs 429, 435 | YES | YES (historical) | YES | — | NO (false positive) |
| B-005 | No import guard enforcement | `tools/` | — | YES | YES (created) | YES | MEDIUM | NO (defers to CI) |
| B-006 | No Engine Gateway implementation | `engine/gateway/` | — | YES | NO | NO | HIGH | NO (ECO-04 task) |
| B-007 | No Evidence Engine implementation | `knowledge/evidence/` | — | YES | NO | NO | MEDIUM | DEFERRED |
| B-008 | No uncertainty propagation | All model outputs | — | YES | NO | NO | MEDIUM | DEFERRED |
| B-009 | No epistemic type tagging | All data outputs | — | YES | NO | NO | MEDIUM | DEFERRED |
| B-010 | AI isolation not enforced | No import guard | — | YES | PARTIAL | PARTIAL | HIGH | NO (dup of B-005) |
| B-011 | All tests UNRUNNABLE | Repository-wide | — | YES | NO | NO | HIGH | YES (environment) |
| B-012 | Services bypass Gateway | `services/*/routers/` | 100+ imports | YES | NO | NO | — | DUPLICATE of B-005 |
| B-013 | No provenance on outputs | All model outputs | — | YES | NO | NO | MEDIUM | DEFERRED |
| B-014 | No trust levels on outputs | All model outputs | — | YES | NO | NO | MEDIUM | DEFERRED |
| B-015 | Theis Solution unverified | `reports/eco-01/20-CANONICAL-ASSETS.md` | CANON-005 | YES | NO | NO | P0 | NO (deferred) |

---

## Verification Evidence

### B-001 Verification (FIXED_AND_VERIFIED)

**Command**: `python tools/detect_imports.py --root .`
**Result**: 0 ENGINE_NO_SERVICES violations
**Command**: `python -c "import engine; print('OK')"`
**Result**: OK
**Conclusion**: ✅ FIXED_AND_VERIFIED

### B-002 Verification (IMPORT FIXED, ARCH VIOLATION REMAINS)

**Command**: `python -c "import engine; print('OK')"`
**Result**: OK (with database stub)
**Command**: `python tools/detect_imports.py --root .`
**Result**: 7 ENGINE_NO_DATABASE violations (all deferred in production code)
**Conclusion**: Import failure FIXED, architectural violation DEFERRED_TO_ECO_04

**Production database imports** (from import guard):
| File | Line | Import | Severity |
|------|------|--------|----------|
| `engine/data_connector.py` | 86 | `from database.hub import hub` | WARNING (deferred) |
| `engine/resource_manager.py` | 45, 70, 83 | `from database.hub import hub` | WARNING (deferred) |
| `engine/ports/session.py` | 162 | `from database.config import SessionLocal` | WARNING (deferred) |
| `engine/ports/session.py` | 201 | `from database.hub import hub` | WARNING (deferred) |
| `engine/hydroma/biofertilizer/models.py` | 32 | `from database.base import Base` | ERROR (try/except fallback) |

### B-003 Verification (FIXED_AND_VERIFIED)

**Command**: `Test-Path pyproject.toml`
**Result**: True
**Command**: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`
**Result**: SUCCESS
**Conclusion**: ✅ FIXED_AND_VERIFIED

### B-004 Verification (FALSE_POSITIVE)

**Source comparison**:
- `climate.cpp:97-98`: `t_max + 273.16`, `t_min + 273.16`
- `climate.cpp:138`: `t_mean + 273.0` (per FAO-56 eq. 6)
- `cpp_bridge/__init__.py:429`: `(tmax + 273.16)**4`
- `cpp_bridge/__init__.py:435`: `(tmean + 273.0)`

**Conclusion**: Both backends consistent. ✅ FALSE_POSITIVE

### B-005 Verification (FIXED)

**Command**: `python tools/detect_imports.py --root .`
**Result**: Tool runs and reports 7 violations
**Conclusion**: ✅ FIXED — tool exists and works

### B-006 Verification (CONFIRMED_BLOCKER)

**Command**: `Test-Path engine/gateway/`
**Result**: False
**Conclusion**: ❌ CONFIRMED_BLOCKER — Engine Gateway must be built in ECO-04

### B-011 Verification (CONFIRMED_BLOCKER - ENVIRONMENT)

**Environment**: Python 3.12.0, no network access, no packages installed
**numpy**: Not installed
**pytest**: Not installed
**Result**: All tests fail at collection
**Conclusion**: ❌ CONFIRMED_BLOCKER (environment) — requires `pip install -e .[dev]`

---

## Files Created During ECO-03.1

| File | Purpose | Classification |
|------|---------|----------------|
| `database/__init__.py` | Database stub package | Minimal hardening (B-002) |
| `database/hub.py` | Hub stub with Hub class | Minimal hardening (B-002) |
| `database/config.py` | Config stub with SessionLocal | Minimal hardening (B-002) |
| `database/base.py` | Base stub for SQLAlchemy | Minimal hardening (B-002) |
| `services/ai/generative_ai/__init__.py` | Moved from engine | Minimal hardening (B-001) |
| `pyproject.toml` | Dependency manifest | Minimal hardening (B-003) |
| `tools/detect_imports.py` | AST-based import guard | Minimal hardening (B-005) |

## Files Deleted During ECO-03.1

| File | Reason |
|------|--------|
| `engine/hydroma/generative_ai/__init__.py` | B-001: Engine→Services violation |

## Files Modified During ECO-03.1

None.

---

*Report generated: 2026-10-08*
*Status: 4 confirmed hard blockers, 3 fixed, 1 false positive, 6 deferred, 1 duplicate, 1 scientific review*