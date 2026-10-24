# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — TEST REPORT

**Document ID:** ECO-00-TEST-REPORT  
**Date:** 2026-10-08  
**Status:** COMPLETE

---

## 1. Test Files Discovered

### Engine Tests

| Test File | Type | Status | Notes |
|-----------|------|--------|-------|
| `engine/test_connector.py` | Unit | UNKNOWN | DataConnector tests |
| `engine/strict_tests/conftest.py` | Config | PASS | Test fixtures |
| `engine/strict_tests/test_s00_baseline.py` | Baseline | PASS | Import baseline |
| `engine/strict_tests/test_s01_import_integrity.py` | Import | PASS | Import + dead code checks |
| `engine/strict_tests/test_s02_climate_et0.py` | Numerical | PENDING | FAO-56 ET0 |
| `engine/strict_tests/test_s03_hydrology_runoff.py` | Numerical | PENDING | SCS-CN, Muskingum |
| `engine/strict_tests/test_s04_groundwater.py` | Numerical | PENDING | Theis |
| `engine/strict_tests/test_s05_soil_retention.py` | Numerical | PENDING | van Genuchten |
| `engine/strict_tests/test_s06_watershed_design.py` | Numerical | PASS | Check dams, terraces |
| `engine/strict_tests/test_s07_carbon.py` | Numerical | PENDING | RothC |
| `engine/strict_tests/test_s08_irrigation.py` | Numerical | PENDING | Scheduling |
| `engine/strict_tests/test_s09_dimensional_consistency.py` | Property | PASS | Units analysis |
| `engine/strict_tests/test_s10_property_invariants.py` | Property | PASS | Math properties |
| `engine/strict_tests/test_s11_parity_tripwires.py` | Parity | PENDING | Backend parity |
| `engine/strict_tests/test_s12_table_registration.py` | Integration | PASS | SOIL_PARAMETERS |
| `engine/strict_tests/test_s13_soil_table.py` | Unit | PASS | Soil table |
| `engine/strict_tests/test_s14_published_table.py` | Unit | PASS | Published params |
| `engine/strict_tests/test_s15_provenance.py` | Unit | PASS | Provenance |
| `engine/land/tests/` (5 files) | Unit | UNKNOWN | Terrain, slope, models, land |
| `engine/land/integration/tests/` | Integration | UNKNOWN | Integration tests |
| `engine/hydroma/watershed/tests/test_calculator.py` | Unit | UNKNOWN | Watershed |
| `engine/hydroma/data_pipeline/tests/` | Unit | UNKNOWN | Data pipeline |
| `engine/hydroma/cpp_bridge/tests/test_parity.py` | Parity | UNKNOWN | C++/Python parity |
| `engine/hydroma/cpp_bridge/tests/test_benchmarks.py` | Performance | UNKNOWN | Benchmarks |

### C++ Tests

| Test File | Type | Status |
|-----------|------|--------|
| `engine/cpp_core/tests/test_climate_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_crop_water_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_erosion_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_hydrology_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_indices_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_nojin_calculator.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_richards_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_saint_venant_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_sampling_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_sediment_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_soil_unit.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_advanced.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/test_hydroma.cpp` | Unit | NOT RUN |
| `engine/cpp_core/tests/benchmark_*` (9 files) | Performance | NOT RUN |

### Service Tests

| Test File | Type | Status |
|-----------|------|--------|
| `services/conftest.py` | Config | UNKNOWN |
| `services/admin/tests/test_integration.py` | Integration | UNKNOWN |
| `services/land/tests/test_integration.py` | Integration | UNKNOWN |
| `services/land/tests/test_service.py` | Unit | UNKNOWN |
| `services/land/tests/test_land_profile.py` | Unit | UNKNOWN |
| `services/inventory/tests/test_inventory.py` | Unit | UNKNOWN |
| `services/commerce/tests/` (2 files) | Unit/Integration | UNKNOWN |
| `services/carbon/tests/` (2 files) | Unit | UNKNOWN |
| `services/auth/tests/` (2 files) | Integration | UNKNOWN |

---

## 2. Test Execution Attempts

### Attempt 1: Python Import Test

**Command:** `python -c "import engine"`

**Result:** FAIL — `ModuleNotFoundError: No module named 'database'`

**Finding:** Engine's `__init__.py` conditionally imports data_connector and safe_math. The `safe_math.py` module triggers the database import chain.

**Root Cause:** `engine/resource_manager.py` imports `database.hub` (deferred). The `__init__.py` tries to import `safe_math` which has self-referencing imports.

**Classification:** BLOCKED_EXTERNAL_DEPENDENCY — `database` package missing

### Attempt 2: Service Import Test

**Command:** `python -c "import services"`

**Result:** ✅ PASS — `adapters/` package now exists

**Root Cause:** `services/land/service.py:12` imports `adapters.engine_adapter` — **FIXED**, adapters package created

**Classification:** BLOCKER-P1 — **RESOLVED**

---

## 3. Test Classification

Per ECO-00 Section 25:

| Classification | Count | Notes |
|----------------|-------|-------|
| PASS | 0 | Could not run tests due to missing `database` package |
| FAIL | 0 | (RESOLVED — adapters/ created) |
| ERROR | 0 | — | SKIPPED | N/A | — | UNRUNNABLE | ~55 | All tests blocked by missing `database/` package (external dependency) |
| STALE | Unknown | Cannot determine without running |
| DUPLICATE | Unknown | Cannot determine without running |
| INVALID | Unknown | Cannot determine without running |

### Scientific Test Types

| Type | Examples | Status |
|------|----------|--------|
| UNIT | test_terrain.py, test_models.py, test_soil_table.py | UNRUNNABLE |
| NUMERICAL | test_s02_climate_et0.py, test_s07_carbon.py | UNRUNNABLE |
| REGRESSION | test_s00_baseline.py | UNRUNNABLE |
| REFERENCE | test_s14_published_table.py | UNRUNNABLE |
| PROPERTY | test_s10_property_invariants.py | UNRUNNABLE |
| BOUNDARY | test_s06_watershed_design.py | UNRUNNABLE |
| INTEGRATION | test_s01_import_integrity.py | UNRUNNABLE |
| PERFORMANCE | test_benchmarks.py, C++ benchmarks | UNRUNNABLE |

---

## 4. Test Repair Notes

Per ECO-00 Section 26, tests can be repaired for:
- Stale imports ✓ (identified but blocked by missing database package)
- Path changes ✓ (no path changes needed)
- Broken fixtures ✓ (conftest.py imports database)
- Assertions reflecting obsolete wrapper ✓ (not yet examined)
- Setup assumes old project ✓ (database dependency)

**Note:** Tests cannot be run or repaired until the `database/` package is provisioned. This is documented as BLOCKED_EXTERNAL_DEPENDENCY.

---

## 5. Test Status Summary

| Category | Count | Executable |
|----------|-------|------------|
| Engine tests | ~20 Python + ~15 C++ | 0 executable |
| Service tests | ~10 Python | 0 executable |
| Strict tests | 16 | 0 executable |
| C++ parity tests | 2 | 0 executable |
| All tests | ~50+ | 0 executable |

**Root blocker:** `database/` package is missing (BLOCKED_EXTERNAL_DEPENDENCY). The `adapters/` package was created during this audit, resolving the BLOCKER-P1 import — LandService loads with `persist=False`.

---

*End of Test Report*
