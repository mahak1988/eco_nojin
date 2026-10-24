# ECO-04.1: Final Model Validation Matrix — Report 23

## Model implementation status and scientific validation traceability

**Report Date**: 2026-10-08T17:00:00Z  
**Method**: File system inspection + AST scan + ECO-03.1 carry-forward

---

## CANON Model Inventory

### Models referenced in design documents

| Model ID | Name | Category | ECO-04 Status | Scientific Validation | Evidence Source |
|----------|------|----------|---------------|----------------------|-----------------|
| CANON-001 | Penman-Monteith ET0 | Evapotranspiration | ⚠️ IMPLEMENTATION_VERIFIED | ECO-03.1 (REQUIRES_SCIENTIFIC_REVIEW) | `engine/hydroma/et.py:14-88` |
| CANON-002 | Hargreaves ET0 | Evapotranspiration | ⚠️ IMPLEMENTATION_VERIFIED | ECO-03.1 (REQUIRES_SCIENTIFIC_REVIEW) | `engine/hydroma/et.py:92-126` |
| CANON-005 | SCS-CN Runoff | Hydrology | ✅ VERIFIED (ECO-03.1) | ECO-03.1 (REQUIRES_SCIENTIFIC_REVIEW) | `engine/hydroma/runoff.py` |
| CANON-007 | RUSLE LS Factor | Erosion | ⚠️ IMPLEMENTATION_VERIFIED | ECO-03.1 (REQUIRES_SCIENTIFIC_REVIEW) | `engine/hydroma/soil.py` |
| CANON-011 | Solar Radiation | Meteorology | ⚠️ IMPLEMENTATION_VERIFIED | ECO-03.1 (REQUIRES_SCIENTIFIC_REVIEW) | `engine/hydroma/solar.py` |
| CANON-016 | Climate Kernels (C++) | Numerical | ✅ VERIFIED (ECO-03.1) | C++ kernels load (61 symbols from .pyd) | `engine/cpp_core/climate.cpp` |
| CANON-017 | Soil Kernels (C++) | Numerical | ✅ VERIFIED (ECO-03.1) | C++ kernels load (61 symbols from .pyd) | `engine/cpp_core/soil.cpp` |
| CANON-004 | Theis Solution | Groundwater | ⚠️ IMPLEMENTATION_VERIFIED | ECO-03.1 (REQUIRES_SCIENTIFIC_REVIEW — convergence undocumented) | `engine/hydroma/theis.py` |

### Models claimed to be registered but registry does not exist

Report 19 and Report 20 claim "22 CANON models listed in `engine/models/registry.py`". This file **does not exist**.

| Claimed Models | Status |
|---------------|--------|
| CANON-001 through CANON-022 (22 total) | **NOT REGISTERED** — no registry file exists |

**Source of truth**: Report 19 lines 59–63; Report 20 lines 111–116. Both reference `engine/models/registry.py` — which `Test-Path` confirms is absent and `python -c "from engine.models.registry import ModelRegistry"` confirms fails with ModuleNotFoundError.

---

## Model Registry Traceability

| Model | Implementation File | Test File | Strict Test Reference | Registry Entry |
|-------|-------------------|-----------|----------------------|----------------|
| CANON-001 | engine/hydroma/et.py | strict_tests/test_et.py | FAO56 reference in conftest.py | ❌ None |
| CANON-002 | engine/hydroma/et.py | strict_tests/test_hargreaves.py | FAO56 alternative | ❌ None |
| CANON-005 | engine/hydroma/runoff.py | strict_tests/test_runoff.py | NRCS_SCS_CN_WORKED_EXAMPLE | ❌ None |
| CANON-007 | engine/hydroma/soil.py | strict_tests/test_soil.py | SAXTON_RAWLS_2006_AWC | ❌ None |
| CANON-011 | engine/hydroma/solar.py | strict_tests/test_solar.py | Haurwitz equation | ❌ None |
| CANON-016 | engine/cpp_core/climate.cpp | strict_tests/test_climate_cpp.py | N/A (kernels) | ❌ None |
| CANON-017 | engine/cpp_core/soil.cpp | strict_tests/test_soil_cpp.py | N/A (kernels) | ❌ None |
| CANON-004 | engine/hydroma/theis.py | strict_tests/test_theis.py | THEIS_REFERENCE | ❌ None |

**Finding**: All 8 implementation files exist with strict tests, but 0 models are registered in any registry (because the registry file does not exist).

---

## Strict Test Reference Data (conftest.py)

The following reference data is present in `engine/strict_tests/conftest.py` but cannot be executed (pytest + hypothesis + numpy not installed):

| Reference | Parameters | Expected Output | Testable? |
|-----------|------------|-----------------|-----------|
| FAO56_REFERENCE_DAY | 6 (lat, doy, albedo, etc.) | ET0 values | ❌ No (numpy missing) |
| NRCS_SCS_CN_WORKED_EXAMPLE | 6 (P, CN, Ia_factor, etc.) | Runoff depth | ❌ No (requires test run) |
| THEIS_REFERENCE | 5 (S, T, r, t, Q) | Drawdown values | ❌ No |
| SAXTON_RAWLS_2006_AWC | 12 soil types | Available water | ❌ No |

---

## Scientific Validation Status

| Component | Status | Reason |
|-----------|--------|--------|
| Scientific test suite | ✅ EXISTS | 16 test files + conftest.py in strict_tests/ |
| Reference data | ✅ EXISTS | 4 reference datasets in conftest.py |
| Test execution | ❌ BLOCKED | pytest + hypothesis + numpy not installed; no network |
| C++ kernel verification | ⚠️ PARTIAL | .pyd loads (61 symbols); no compiler for rebuild |
| Model output comparison | ❌ NOT_DONE | Tests cannot execute |

---

## Model Validation Summary

| Category | Count | Status |
|----------|-------|--------|
| Total CANON models claimed (Report 20) | 22 | ❌ NOT REGISTERED |
| Total CANON models with implementation | 8 | ✅ IMPLEMENTATION_VERIFIED (per ECO-03.1) |
| Total CANON models with strict tests | 8 | ✅ Tests exist |
| Total CANON models registered | 0 | ❌ Registry file does not exist |
| Models requiring scientific review | 7 | ECO-03.1 marked (not runtime-verified) |
| Models requiring ECO-03.1 carry-forward | 2 | CANON-016, CANON-017 (C++ kernels verified) |

---

## Conclusion

- **8 of 22 claimed models have implementation and tests** (ECO-03.1 carry-forward confirms implementation verified).
- **0 of 22 models are registered** — the Model Registry file does not exist.
- **0 of 8 models have been runtime-validated** — environment blocks test execution.
- Scientific validation status: **NOT EXECUTED** (deferred to ECO-04.10 / requires environment fix).

---

*This matrix is based on file system inspection, ECO-03.1 carry-forward, and conftest.py content analysis. Runtime verification was not possible due to environment constraints.*
