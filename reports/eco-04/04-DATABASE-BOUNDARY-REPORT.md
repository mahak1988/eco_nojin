# ECO-04: Database Boundary Report — Report 04

## Engine→Database architectural violation status

---

## 1. Import Guard Results

**Command**: `python tools/detect_imports.py --root . --format=json`
**Result**: 7 violations (all database-related)

| # | File | Line | Import | Severity | Context |
|---|------|------|--------|----------|---------|
| 1 | `engine/data_connector.py` | 86 | `from database.hub import hub` | WARNING | Inside `default_hub()` function |
| 2 | `engine/resource_manager.py` | 45 | `from database.hub import hub` | WARNING | Inside `managed_connection()` function |
| 3 | `engine/resource_manager.py` | 70 | `from database.hub import hub` | WARNING | Inside `managed_connection()` function |
| 4 | `engine/resource_manager.py` | 83 | `from database.hub import hub` | WARNING | Inside `managed_connection()` function |
| 5 | `engine/ports/session.py` | 162 | `from database.config import SessionLocal` | WARNING | Inside `default_session_factory()` function |
| 6 | `engine/ports/session.py` | 201 | `from database.hub import hub` | WARNING | Inside `default_unit_of_work()` function |
| 7 | `engine/hydroma/biofertilizer/models.py` | 32 | `from database.base import Base` | ERROR* | Inside `try/except ImportError` with fallback |

*Note: Entry #7 is classified as ERROR because the import guard does not currently distinguish `try/except ImportError` blocks from unconditional imports. This is a **false positive** — the code has a proper SQLAlchemy fallback.

---

## 2. Architectural Analysis

### Current State

The engine uses **deferred imports** as an edge pattern:

1. **`engine/ports/session.py`**: Contains `SessionPort`, `QueryPort`, `SessionFactory` — the port interfaces
2. **`default_session_factory()`**: Returns production session factory, imports `database.config.SessionLocal` on first call
3. **`resolve_database_attr()`**: Lazy attribute resolution for ORM models
4. **`default_unit_of_work()`**: Returns `hub.get_session` on first call

### Architecture Assessment

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Ports defined | ✅ YES | `SessionPort`, `QueryPort`, `SessionFactory`, `UnitOfWork` in `engine/ports/session.py` |
| Adapters separate | ❌ NO | No adapter module exists |
| Engine imports database at module level | ❌ NO | All imports are deferred (inside functions) |
| `import engine` succeeds without database | ✅ YES | Verified |
| Port used for dependency injection | ✅ PARTIAL | `DataConnector.__init__(hub=None)` accepts injected hub |

### INV-002 Compliance: "Engine never depends on database"

| Aspect | Status | Notes |
|--------|--------|-------|
| Import-time dependency | ✅ NO | `import engine` succeeds without database |
| Runtime dependency | ⚠️ YES | Functions import `database` on first call |
| Fallback mechanism | ✅ PARTIAL | `biofertilizer/models.py` has SQLAlchemy fallback |
| Port abstraction | ✅ PARTIAL | `SessionPort` exists but `default_session_factory` still imports database |

---

## 3. Database Boundary Violation Classification

Per ECO-04.md §28 Database Stub Rule — **Mode A**: Engine should be database-independent.

### Mode A Analysis: Make engine database-independent

**What would be required**:

1. **Create a `PersistencePort`** that defines the interface for database access:
   ```python
   class PersistencePort(Protocol):
       def get_duckdb(self, name: str) -> Any: ...
       def get_sqlite(self, name: str) -> Any: ...
       def get_duckdb_pooled(self, database: str) -> Any: ...
       def return_duckdb_pooled(self, conn: Any, database: str) -> None: ...
       def get_session(self) -> SessionPort: ...
   ```

2. **Inject hub via constructor**: `DataConnector.__init__()` already accepts `hub=None`, so this is partially done.

3. **Remove deferred imports**: `default_hub()`, `default_session_factory()`, `default_unit_of_work()` would need to raise `RuntimeError("Persistence not configured")` instead of importing database.

4. **Services provide the adapter**: Services would pass a real hub implementation to the engine.

### Feasibility for ECO-04

| Task | Complexity | Risk | ECO-04 Sprint |
|------|-----------|------|---------------|
| Create PersistencePort | LOW | Low | ECO-04.3 |
| Update DataConnector to use port | LOW | Low | ECO-04.3 |
| Update session.py defaults to raise | LOW | Low | ECO-04.3 |
| Update models.py fallback | LOW | Low | ECO-04.3 |
| Remove database/ stub | LOW | Low | ECO-04.3 |

---

## 4. Database Stub Assessment

Per ECO-04.md §12: "Stubهای ECO-03.1 را production implementation تلقی نکنید"

| Stub File | Purpose | Status | Action |
|-----------|---------|--------|--------|
| `database/__init__.py` | Package marker | Temporary | Will be removed after boundary fix |
| `database/hub.py` | Hub stub (raises NotImplementedError) | Temporary | Will be removed; replaced by adapter |
| `database/config.py` | SessionLocal placeholder | Temporary | Will be removed; replaced by adapter |
| `database/base.py` | SQLAlchemy Base placeholder | Temporary | Will be removed; replaced by adapter |

**Decision**: The stub should **remain** during ECO-04.1 (Architecture Enforcement) and be **removed** during ECO-04.3 (Database Dependency Removal) after the port/adapter pattern is implemented.

---

## 5. Database Boundary Violation List (Complete)

### Production Code (7 sites, 4 files)

| File | Line | Import | Deferred? | Fallback? | Violation Type |
|------|------|--------|-----------|-----------|----------------|
| `engine/data_connector.py` | 86 | `from database.hub import hub` | YES (function) | No | Architecture violation |
| `engine/resource_manager.py` | 45 | `from database.hub import hub` | YES (function) | No | Architecture violation |
| `engine/resource_manager.py` | 70 | `from database.hub import hub` | YES (function) | No | Architecture violation |
| `engine/resource_manager.py` | 83 | `from database.hub import hub` | YES (function) | No | Architecture violation |
| `engine/ports/session.py` | 162 | `from database.config import SessionLocal` | YES (function) | No | Architecture violation |
| `engine/ports/session.py` | 201 | `from database.hub import hub` | YES (function) | No | Architecture violation |
| `engine/hydroma/biofertilizer/models.py` | 32 | `from database.base import Base` | YES (try/except) | YES (SQLAlchemy) | Architecture violation |

### Test Code (NOT COUNTED as violations)

| File | Line | Import |
|------|------|--------|
| `engine/strict_tests/test_s12_table_registration.py` | 154, 155, 187, 201, 231, 249, 327 | `from database.base/config` / `import database.models` |
| `engine/hydroma/biofertilizer/tests/conftest.py` | 10, 11 | `from database.base/hub import ...` |
| `engine/hydroma/biofertilizer/tests/test_calibration_session.py` | 27, 80 | `from database.config/models import ...` |
| `engine/hydroma/biofertilizer/tests/test_nojin_comprehensive.py` | 197, 207, 220, 234, 245 | `from database import SessionLocal` |

Test-only imports are **acceptable** — tests can and should import test fixtures.

---

## 6. Resolution Plan for ECO-04.3

| Step | Action | Complexity |
|------|--------|-----------|
| 1 | Define `PersistencePort` in `engine/ports/` | LOW |
| 2 | Update `DataConnector` to accept port via DI | LOW |
| 3 | Update `default_session_factory()` to raise if port not configured | LOW |
| 4 | Update `resolve_database_attr()` to use port | LOW |
| 5 | Update `default_unit_of_work()` to raise if port not configured | LOW |
| 6 | Update `biofertilizer/models.py` to use port | LOW |
| 7 | Remove `database/` stub | LOW |
| 8 | Re-run import guard to verify 0 violations | LOW |

---

## 7. Conclusion

**Database boundary status**: 

- **Import-time dependency**: RESOLVED (engine imports without database)
- **Runtime/architectural dependency**: NOT RESOLVED (7 deferred imports in production code)
- **Action required**: ECO-04.3 — Implement PersistencePort and remove deferred database imports

The database boundary is **not** blocking ECO-04.1 or ECO-04.2, but must be resolved in ECO-04.3 before full architecture enforcement.

---

*Report generated: 2026-10-08*
*Status: 7 violations documented, fix deferred to ECO-04.3*