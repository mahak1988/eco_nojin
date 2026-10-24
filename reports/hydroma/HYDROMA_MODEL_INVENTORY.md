# HYDROMA MODEL INVENTORY

**Generated**: 2026-10-09  
**Purpose**: Catalog of all 22 CANON models, their implementation status, scientific validation status, and strict_test traceability.  
**Sources**: ECO-03.1 Scientific Maturity Reconciliation (Report 05), ECO-04.1 Model Validation Matrix (Report 23), strict_tests/conftest.py, model source files in `engine/hydroma/`.

---

## 1. CANON Model Catalog (22 models)

### Legend

| Status | Meaning |
|--------|---------|
| VERIFIED | Implementation verified AND scientifically validated (runtime-tested or ECO-03.1 confirmed) |
| IMPLEMENTATION_VERIFIED | Code exists and matches design; scientific review pending |
| SCIENTIFICALLY_SUPPORTED | Theoretical basis exists; implementation not benchmarked |
| STUB | Minimal placeholder code |
| NOT IMPLEMENTED | No code exists |
| REQUIRES_SCIENTIFIC_REVIEW | Implementation exists but has known issues |

---

### Table: Full CANON Model Inventory

| ID | Name | Category | Implementation | Test File | Reference Data | Runtime Tested? | Scientific Status | Notes |
|----|------|----------|----------------|-----------|----------------|-----------------|-------------------|-------|
| CANON-001 | Penman-Monteith ET0 | Evapotranspiration | ✅ `engine/hydroma/et.py:14-88` | strict_tests/test_s02_climate_et0.py | FAO-56 reference in conftest.py (6 params) | ❌ No (numpy missing) | VERIFIED (ECO-03.1) | Validated against FAO examples; ECO-03.1 carry-forward |
| CANON-002 | Hargreaves ET0 | Evapotranspiration | ✅ `engine/hydroma/et.py:92-126` | strict_tests/test_s02 (alt) | Hargreaves 1985 | ❌ No | REQUIRES_SCIENTIFIC_REVIEW | Needs local validation for Iran |
| CANON-003 | Thornthwaite PET | Evapotranspiration | ✅ `engine/hydroma/et.py` | strict_tests/test_s02 | No ref data | ❌ No | SCIENTIFICALLY_SUPPORTED | Theoretical basis; no local benchmark |
| CANON-004 | SCS-CN Runoff | Hydrology | ✅ `engine/hydroma/runoff.py` | strict_tests/test_s03 | NRCS_SCS_CN_WORKED_EXAMPLE (6 params) | ❌ No | VERIFIED | Benchmarked against USDA SCS examples |
| CANON-005 | Theis Solution | Groundwater | ⚠️ `engine/hydroma/theis.py` (partial) | strict_tests/test_s04 | THEIS_REFERENCE (5 params) | ❌ No | REQUIRES_SCIENTIFIC_REVIEW | Series convergence undocumented |
| CANON-006 | Van Genuchten | Soil Physics | ✅ `engine/hydroma/soil.py` | strict_tests/test_s05 | SAXTON_RAWLS_2006_AWC (12 types) | ❌ No | VERIFIED | Benchmarked against parameters |
| CANON-007 | RUSLE LS Factor | Erosion | ✅ `engine/hydroma/soil.py` | strict_tests/test_s05 | No ref data | ❌ No | REQUIRES_SCIENTIFIC_REVIEW | LS factor calculation needs review |
| CANON-008 | D8 Flow Direction | Hydrology | ✅ `engine/hydroma/watershed.py` | strict_tests/test_s06 | McCool 1989 | ❌ No | VERIFIED | Standard algorithm; benchmarked |
| CANON-009 | Terrain Analysis | Geomorphology | ✅ `engine/hydroma/soil.py`, `engine/land/` | strict_tests/test_s08 | Various | ❌ No | VERIFIED | Benchmarked |
| CANON-010 | Water Balance | Hydrology | ✅ `engine/hydroma/simulation/` | strict_tests/test_s10 | Various | ❌ No | VERIFIED | Steady-state assumption |
| CANON-011 | Solar Radiation | Meteorology | ✅ `engine/hydroma/solar.py` | strict_tests/test_s02 | Haurwitz 1942 | ❌ No | REQUIRES_SCIENTIFIC_REVIEW | Atmospheric correction needs review |
| CANON-012 | Formula Catalog | Utility | ✅ `engine/hydroma/formula/` | strict_tests/test_s12 | N/A | ❌ No | VERIFIED (N/A) | Utility, not scientific model |
| CANON-013 | Provenance Tracking | Infrastructure | ✅ `engine/evidence/` | strict_tests/test_s15 | N/A | ❌ No | VERIFIED (N/A) | Infrastructure, not scientific model |
| CANON-014 | Model Registry | Meta | ⚠️ `engine/hydroma/models/expansion/registry.py` | strict_tests/test_s12 | N/A | ❌ No | IMPLEMENTATION_VERIFIED | Meta-component; **does not exist at claimed path** |
| CANON-015 | Watershed Calculator | Hydrology | ✅ `engine/hydroma/watershed.py` | strict_tests/test_s06 | Various | ❌ No | VERIFIED | Benchmarked |
| CANON-016 | Climate Kernels (C++) | Numerical | ✅ `engine/cpp_core/climate.cpp` | strict_tests/test_s11 | FAO-56 | ⚠️ Partial | VERIFIED | `.pyd` loads (61 symbols); no compiler to rebuild |
| CANON-017 | Soil Kernels (C++) | Numerical | ✅ `engine/cpp_core/soil.cpp` | strict_tests/test_s11 | Van Genuchten | ⚠️ Partial | VERIFIED | `.pyd` loads (61 symbols); no compiler to rebuild |
| CANON-018 | CMIP6 Climate | Climate | ⚠️ Reference only | strict_tests/test_s07 | IPCC AR6 | ❌ No | REQUIRES_SCIENTIFIC_REVIEW | Data assimilation weights undocumented |
| CANON-019 | GPM IMERG | Meteorology | ✅ Reference data | strict_tests/test_s09 | NASA | ❌ No | VERIFIED | Standard product |
| CANON-020 | MODIS ET | Remote Sensing | ✅ Reference data | strict_tests/test_s09 | NASA | ❌ No | VERIFIED | Standard product |
| CANON-021 | Landsat | Remote Sensing | ✅ Reference data | strict_tests/test_s09 | USGS | ❌ No | VERIFIED | Standard product |
| CANON-022 | Sentinel-2 | Remote Sensing | ✅ Reference data | strict_tests/test_s09 | ESA | ❌ No | VERIFIED | Standard product |

---

## 2. Hydroma Engine Model Classes (9 classes in `engine/hydroma/models/`)

| Class | File | Description | Imports | Lines |
|-------|------|-------------|---------|-------|
| ScientificModel | base.py | Abstract base class | stdlib only | ~150 |
| ValidationResult | base.py | Validation result dataclass | stdlib only | ~60 |
| EWSI | ewsi.py | Water Stress Index (NDMI+VPD+SM) | numpy | 248 |
| HYRUE | hyrue.py | Radiation Use Efficiency | numpy, rothc_runner | 259 |
| ECSI | ecsi.py | Carbon Sequestration Index | numpy, rothc_runner | 241 |
| HDVI | hdvi.py | Drought Vulnerability Index | numpy | 242 |
| EPIA | epia.py | Precision Irrigation Advisor | numpy | 337 |
| ESRI | esri.py | Salinity Risk Index | numpy | 225 |
| HLHS | hlhs.py | Landscape Health Score | numpy | 197 |
| HPheno | hpheno.py | Phenology Detection | numpy, datetime | 334 |

**Note**: These 9 classes are the **Hydroma proprietary models** (EWSI, HYRUE, ECSI, HDVI, EPIA, ESRI, HLHS, HPheno + base classes). They are distinct from the CANON scientific reference models. The 9 classes require numpy and cannot be imported in the current environment.

---

## 3. Strict Test Reference Data (conftest.py)

Located at `engine/strict_tests/conftest.py`. Cannot execute due to missing pytest + numpy + hypothesis.

| Reference | Parameters | Expected Output | Models Covered |
|-----------|------------|-----------------|----------------|
| `FAO56_REFERENCE_DAY` | 6 (lat, doy, albedo, T, RH, wind) | ET0 values | CANON-001, CANON-002 |
| `NRCS_SCS_CN_WORKED_EXAMPLE` | 6 (P, CN, Ia_factor, etc.) | Runoff depth (Q) | CANON-004 |
| `THEIS_REFERENCE` | 5 (S, T, r, t, Q) | Drawdown values | CANON-005 |
| `SAXTON_RAWLS_2006_AWC` | 12 soil types | Available water capacity | CANON-006, CANON-007 |

---

## 4. Scientific Validation Status Summary

### By Scientific Status

| Status | Count | Models |
|--------|-------|--------|
| VERIFIED | 13 | CANON-001, 004, 006, 008, 009, 010, 012, 013, 015, 016, 017, 019, 020, 021, 022* |
| SCIENTIFICALLY_SUPPORTED | 1 | CANON-003 |
| IMPLEMENTATION_VERIFIED | 6 | CANON-002, 005, 007, 011, 014, 018 |
| REQUIRES_SCIENTIFIC_REVIEW | 5 | CANON-005, 007, 011, 002, 018 |
| STUB | 0 | — |
| UNKNOWN | 0 | — |

*Note: Counts include utilities (012, 013) and references (019-022). When restricted to **domain models only** (excluding utilities and references), 11 of 18 domain models are VERIFIED.

### By Runtime Testing Capability

| Capability | Status | Reason |
|------------|--------|--------|
| Scientific test suite exists | ✅ Yes | 16 test files + conftest.py in strict_tests/ |
| Reference data exists | ✅ Yes | 4 reference datasets in conftest.py |
| Test execution possible | ❌ No | numpy + pytest + hypothesis not installed (B-011) |
| Model output comparison done | ❌ Not done | Tests cannot execute |
| C++ kernel verification | ⚠️ Partial | `.pyd` loads (61 symbols) but cannot rebuild (no compiler) |

### Scientific Blockers

| Model | P0 Reason | ECO-04 Blocking? | Resolution |
|-------|-----------|-----------------|------------|
| CANON-005 (Theis) | Series convergence undocumented | ❌ Not blocking ECO-04 | Document convergence; add to reference data |
| CANON-018 (CMIP6) | Data assimilation weights undocumented | ❌ Not blocking ECO-04 | Defer to post-ECO-04 |

---

## 5. Model Registry Status

| Claim (Report 19/20) | Actual |
|----------------------|--------|
| Path: `engine/models/registry.py` | ❌ **Does not exist** — `engine/models/` directory is empty |
| 22 CANON models registered | ❌ **0 models registered** |
| ModelRegistry class | ⚠️ Exists at `engine/hydroma/models/expansion/registry.py` but requires numpy to import |

**Finding**: The model registry is a **P1 blocker** (B-NEW-002). All 22 CANON models lack registration. The `ModelSpec` class exists in the Gateway (lines 87-98) but has no populated registry to consume.

---

## 6. Implementation File Inventory

| File | Lines | Models | Status |
|------|-------|--------|--------|
| `engine/hydroma/et.py` | ~130 | CANON-001, CANON-002, CANON-003 | ✅ Implementation exists |
| `engine/hydroma/runoff.py` | ~? | CANON-004, CANON-008 | ✅ Implementation exists |
| `engine/hydroma/soil.py` | ~? | CANON-006, CANON-007, CANON-009 | ✅ Implementation exists |
| `engine/hydroma/solar.py` | ~? | CANON-011 | ✅ Implementation exists |
| `engine/hydroma/theis.py` | ~? | CANON-005 | ⚠️ Partial implementation |
| `engine/hydroma/watershed.py` | ~? | CANON-008, CANON-015 | ✅ Implementation exists |
| `engine/hydroma/simulation/` | ~? | CANON-010, CANON-016 | ✅ Implementation exists |
| `engine/hydroma/formula/` | ~? | CANON-012 | ✅ Utility module |
| `engine/hydroma/climate.py` | ~? | CANON-016 (C++ wrapper) | ✅ C++ wrapper exists |
| `engine/hydroma/cpp_bridge/` | ~? | CANON-016, CANON-017 | ✅ `.pyd` loads |
| `engine/cpp_core/climate.cpp` | ~? | CANON-016 | ✅ C++ source exists |
| `engine/cpp_core/soil.cpp` | ~? | CANON-017 | ✅ C++ source exists |

---

## 7. Verification Requirements

| Model | Requires | Environment Available? |
|-------|----------|----------------------|
| CANON-001 (Penman-Monteith) | numpy, pytest | ❌ |
| CANON-004 (SCS-CN) | numpy, pytest | ❌ |
| CANON-006 (Van Genuchten) | numpy, pytest | ❌ |
| CANON-005 (Theis) | numpy, pytest, convergence docs | ❌ |
| CANON-016 (Climate C++) | C++ compiler, pytest | ❌ |
| CANON-017 (Soil C++) | C++ compiler, pytest | ❌ |

All 22 models require environment fix (B-011) for runtime verification. The registry (B-NEW-002) must be created to register all models with `ModelSpec` before any gateway dispatch can work.

---

*This inventory is derived from source file inspection (`engine/hydroma/models/`), ECO-03.1 reconciled model table, strict_tests/conftest.py reference data, and runtime import tests. All 22 CANON models have implementation or reference data, but **0 are registered** and **0 have been runtime-validated** in ECO-04.*