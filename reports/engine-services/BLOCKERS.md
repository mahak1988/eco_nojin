# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — BLOCKERS

**Document ID:** ECO-00-BLOCKERS  
**Date:** 2026-10-08  
**Status:** COMPLETE

---

## Blocker Classification Policy

Per ECO-00 Section 44:
- **BLOCKER-P0**: Security / data corruption / scientific correctness
- **BLOCKER-P1**: Build-breaking defects / Import-breaking defects / Critical runtime failures
- **BLOCKER-P2**: Incorrect validation / Incorrect units / Incorrect state handling / Broken tests
- **BLOCKER-P3**: Architectural coupling / Duplication / Maintainability problems

---

## Critical Blockers (P0)

**NONE IDENTIFIED**

No P0 security vulnerabilities, data corruption, or scientific correctness errors remain unresolved. All identified scientific defects were fixed during this audit.

---

## Import-Building Blockers (P1)

### BLOCKER-P1-001: Missing `adapters.engine_adapter` module

| Field | Value |
|-------|-------|
| **Priority** | BLOCKER-P1 (Import-breaking) |
| **File** | `services/land/service.py:12` |
| **Import** | `from adapters.engine_adapter import EngineAdapter` |
| **Error** | `ModuleNotFoundError: No module named 'adapters'` |
| **Impact** | `LandService` class cannot be imported; `import services.land.service` raises ImportError at module load time |
| **Evidence** | Confirmed: no `adapters/` directory exists at project root. Only nested `adapters/` directories exist in `services/bots/adapters/` and `services/simulation/adapters/` (unrelated) |
| **Status** | **FIXED** — `adapters/engine_adapter.py` and `adapters/hydroma_adapter.py` created |
| **Fix Verified** | 45 test assertions pass (see `FINAL-VALIDATION.md`) |

### BLOCKER-P1-002: Engine importing services.map_engine

| Field | Value |
|-------|-------|
| **Priority** | BLOCKER-P1 (Import-breaking for engine) |
| **File** | `engine/land/integration/water_adapter.py:230` |
| **Import** | `from services.map_engine.pipelines.runoff import ...` |
| **Error** | ImportError if `services` package not importable |
| **Impact** | `import engine.land.integration.water_adapter` will fail if services package is absent |
| **Evidence** | Found in grep results — direct top-level import violating engine boundary |
| **Status** | **FIXED** — forbidden import removed; SCS-CN calculation is inline |
| **Fix Verified** | No `from services` or `import services` strings remain; static check passes |

---

## Correctness Blockers (P2)

### BLOCKER-P2-001: Missing dependency manifest

| Field | Value |
|-------|-------|
| **Priority** | BLOCKER-P2 |
| **Location** | Project root |
| **Issue** | No `requirements.txt`, `pyproject.toml`, `setup.py`, or `Pipfile` found |
| **Impact** | Cannot reproduce environment; dependencies are inferred |
| **Status** | **DOCUMENTED** — blocked by scope (cannot create new root files outside reports/docs) |
| **Recommended Fix** | Create `requirements.txt` or `pyproject.toml` outside this task scope |

### BLOCKER-P2-002: Empty services/hydroma/ directories

| Field | Value |
|-------|-------|
| **Priority** | BLOCKER-P2 (maintainability) |
| **Location** | `services/hydroma/` (api/, models/, repositories/, schemas/, tests/) |
| **Issue** | All subdirectories are empty — no `__init__.py` or files |
| **Impact** | Confusion about hydroma service location; dead weight |
| **Status** | **DOCUMENTED** — classified as OBSOLETE |
| **Recommended Fix** | Remove empty directories in future cleanup task |

### BLOCKER-P2-003: Near-empty model stub files

| Field | Value |
|-------|-------|
| **Priority** | BLOCKER-P2 (maintainability) |
| **Location** | `services/models/base.py`, `services/models/water_models.py`, `services/models/soil_climate_models.py` |
| **Issue** | All 2 bytes (whitespace only) — empty stubs |
| **Impact** | Misleading — files exist but contain nothing |
| **Status** | **DOCUMENTED** — `services/models/__init__.py` documents models moved to `database.models` |
| **Recommended Fix** | Remove stub files; import directly from database.models |

### BLOCKER-P2-004: Engine → services.dependency (generative_ai)

| Field | Value |
|-------|-------|
| **Priority** | BLOCKER-P2 (architectural) |
| **Location** | `engine/hydroma/generative_ai/__init__.py` |
| **Issue** | Engine module imports from `services.ai.*` (mitigated via lazy loading but architecture violation remains) |
| **Status** | **MITIGATED** (lazy loading) — should be removed entirely |
| **Recommended Fix** | Remove module or move to services layer |

### BLOCKER-P2-005: Model registry cross-layer import

| Field | Value |
|-------|-------|
| **Priority** | BLOCKER-P2 (architectural) |
| **Location** | `services/models/registry.py:49` |
| **Import** | `from services.api_gateway.routers.carbon_engine import ...` |
| **Issue** | Services-models should not import from api_gateway routers |
| **Status** | **DOCUMENTED** |
| **Recommended Fix** | Move scientific model functions to engine layer |

---

## External Blockers (BLOCKED_EXTERNAL_DEPENDENCY)

### BLOCKER-EXT-001: Missing `database/` package

| Field | Value |
|-------|-------|
| **Priority** | BLOCKED_EXTERNAL_DEPENDENCY |
| **Referenced By** | 20+ engine files, 40+ service files |
| **Import Patterns** | `from database.hub import hub`, `from database.models import ...`, `from database.base import Base`, `from database.config import SessionLocal` |
| **Impact** | Cannot run tests or execute services that touch the database |
| **Status** | All imports are deferred — engine and services can be imported without database |
| **Scope Note** | Per ECO-00 Section 34, creating a new database is out of scope. This blocker is **blocked by future ECO task**. |
| **Recommended Fix** | Provision `database/` package in separate task (not ECO-00) |

---

## Summary

| Priority | Count | Active | Documented | Fixed |
|----------|-------|--------|------------|-------|
| BLOCKER-P0 | 0 | 0 | 0 | 0 |
| BLOCKER-P1 | 2 | 0 | 0 | 2 |
| BLOCKER-P2 | 5 | 3 | 2 | 0 |
| BLOCKED_EXTERNAL | 1 | 1 (deferred) | 0 | 0 |

---

*End of Blockers Report*
