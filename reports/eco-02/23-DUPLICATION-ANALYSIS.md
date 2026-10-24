# ECO-02: Duplication Analysis

## Redundancy Resolution Plan

---

## Source Evidence
- ECO-01/21-DUPLICATION-ANALYSIS.md
- ECO-01/20-CANONICAL-ASSETS.md
- ECO-01/10-HYDROMA-FORENSICS.md

---

## Identified Duplicates

### Duplicate 1: Multiple Penman-Monteith Implementations
- **Location 1**: `engine/hydroma/scientific/et/penman_monteith.py`
- **Location 2**: `services/et_service/legacy_et.py`
- **Issue**: Different parameter defaults, CONFLICT-001
- **Resolution**: Redirect all to CANON-001 implementation
- **Action**: Deprecate services/et_service/legacy_et.py

### Duplicate 2: Duplicate Climate Data Handlers
- **Location 1**: `engine/hydroma/scientific/climate/cmip6.py`
- **Location 2**: `services/meteorology/handler.py`
- **Issue**: Same CMIP6 processing in both
- **Resolution**: Keep in engine/hydroma, remove from services
- **Action**: Services import from hydroma engine through Evidence Engine

### Duplicate 3: Multiple Interpolation Methods
- **Location 1**: `engine/cpp_core/interpolation.cpp`
- **Location 2**: `services/meteorology/interpolation.py`
- **Issue**: Same IDW algorithm in Python and C++
- **Resolution**: All interpolation in C++ kernel, Python as wrapper
- **Action**: Remove Python implementation

### Duplicate 4: Redundant Config Services
- **Location**: 25 infrastructure services in `services/`
- **Issue**: Each has its own config handling
- **Resolution**: Consolidate to Platform Core module
- **Action**: Migrate configs to unified `services/platform/config.py`

### Duplicate 5: Multiple Logging Implementations
- **Location 1**: `engine/logging/`
- **Location 2**: `services/*/logging.py`
- **Issue**: Inconsistent log formats
- **Resolution**: Centralized logging service
- **Action**: Remove per-service logging

---

## Duplication Resolution Matrix

| Duplicate Type | Files Affected | Action | Priority |
|----------------|---------------|--------|----------|
| Scientific models | 5 files | Redirect to CANON | P0 |
| Data handlers | 8 files | Consolidate in engine | P0 |
| Utilities | 15 files | Platform Core module | P1 |
| Logging | 25 files | Centralized logging | P1 |
| Config | 45 files | Unified config service | P1 |
| Database access | 12 files | Repository pattern | P2 |

---

## Canonical Mapping

After deduplication, each function maps to exactly one canonical location:

| Function | Canonical Location |
|----------|-------------------|
| Penman-Monteith ET | `hydroma/scientific/et/canonical.py` (CANON-001) |
| Hargreaves ET | `hydroma/scientific/et/canonical.py` (CANON-002) |
| Climate processing | `hydroma/scientific/climate/cmip6.py` (CANON-018) |
| Interpolation | `cpp_core/interpolation.cpp` |
| Logging | `platform/core/logging.py` |
| Config | `platform/core/config.py` |
| Database repository | `platform/core/repository.py` |

---

## Deduplication Timeline

### Phase 1 (Week 1-2): P0 Duplicates
- Redirect scientific model calls to canonical implementations
- Consolidate data handlers
- Implement import guard (ECO-LEGACY-001 compliance)

### Phase 2 (Week 3-4): P1 Duplicates
- Create Platform Core module
- Migrate logging and config
- Implement centralized database access

### Phase 3 (Month 2): P2 Duplicates
- Audit remaining utilities
- Apply repository pattern
- Remove deprecated code

---

## Detection Tools

### Static Analysis
```bash
# Find duplicate functions
python tools/detect_duplicates.py --dir engine/ services/

# Find import violations
python tools/check_imports.py --root . --forbidden-pattern "services.*from.*engine"

# Find identical code blocks
python tools/similarity_scan.py --threshold 0.9
```

---

## Risk Assessment

| Duplicate | Risk Level | Reason |
|-----------|------------|--------|
| Scientific models | CRITICAL | Can produce inconsistent results |
| Data handlers | HIGH | Data inconsistencies |
| Config services | MEDIUM | Configuration drift |
| Logging | LOW | Debugging difficulty only |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/21*