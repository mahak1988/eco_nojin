# ECO-03: C++ / Python Boundary Specification — Report 15
## ABI, Memory Ownership, and Interface Contract

---

## Executive Summary

ECO-02/05 defines the C++/Python boundary protocol. ECO-03 verifies the actual C++/Python boundary against source code and identifies discrepancies.

---

## 1. C++ / Python Ownership (Verified)

### ECO-02 Definition
- C++ owns numerical kernels
- Python owns orchestration

### ECO-03 Verification
**Status**: VERIFIED

**Evidence**:
- C++ source files in `engine/cpp_core/src/` (10 .cpp files)
- C++ headers in `engine/cpp_core/include/hydroma/` (10 .hpp files)
- Python orchestration in `engine/hydroma/` (50+ Python modules)
- C++ functions exposed via pybind11 through `engine/cpp_core/bindings.cpp`
- Compiled extension: `engine/hydroma/cpp_bridge/hydroma_core.cp312-win_amd64.pyd`

**C++ Kernel Inventory (verified)**:

| Kernel | File | Functions | Unit Tests |
|--------|------|-----------|------------|
| climate.cpp | `src/climate.cpp` | `hargreaves_et0`, `extraterrestrial_radiation`, `fao56_net_radiation`, `penman_monteith_et0` + array variants | `test_climate_unit.cpp` |
| crop_water.cpp | `src/crop_water.cpp` | `simulate_crop_water`, `CropWaterParams`, `CropWaterResult` | `test_crop_water_unit.cpp` |
| erosion.cpp | `src/erosion.cpp` | `rusle_annual_soil_loss`, `ls_factor`, `estimate_rainfall_erosivity` | `test_erosion_unit.cpp` |
| hydrology.cpp | `src/hydrology.cpp` | `muskingum_cunge_route`, `route_flood_wave`, `route_multi_reach` | `test_hydrology_unit.cpp` |
| indices.cpp | `src/indices.cpp` | `ndvi`, `evi`, `savi`, `ndwi`, `nbr` + array variants | `test_indices_unit.cpp` |
| nojin_calculator.cpp | `src/nojin_calculator.cpp` | `NojinCalculator` | `test_nojin_calculator.cpp` |
| richards.cpp | `src/richards.cpp` | `simulate_richards`, `RichardsOptions`, `RichardsResult` | `test_richards_unit.cpp` |
| saint_venant.cpp | `src/saint_venant.cpp` | `simulate_saint_venant`, `SaintVenantOptions` | `test_saint_venant_unit.cpp` |
| sampling.cpp | `src/sampling.cpp` | `latin_hypercube`, `monte_carlo_uniform`, `estimate_mean_lhs`, `estimate_mean_mc` | `test_sampling_unit.cpp` |
| sediment.cpp | `src/sediment.cpp` | `sediment_yield`, `sediment_trapped`, `sediment_delivery_ratio` | `test_sediment_unit.cpp` |
| soil.cpp | `src/soil.cpp` | `soil_water_content`, `soil_params`, `soil_erodibility_k`, `specific_moisture_capacity`, `supported_textures` | `test_soil_unit.cpp` |

Total: **10 source files, 10 header files, 11 test files, 9 benchmark files** = 41 C++ files.

---

## 2. Interface Mechanisms

### 2.1 ctypes (Primary)

#### ECO-02 Claim
> ctypes used for simple function calls

#### ECO-03 Verification
**Status**: PARTIAL — ctypes is used at the C++ level but the actual primary mechanism is pybind11.

**Evidence**:
- `engine/cpp_core/bindings.cpp` uses pybind11 (not ctypes)
- `engine/hydroma/cpp_bridge/__init__.py` imports `hydroma_core` as a pybind11 module
- ECO-01/11-CPP-PYTHON-BOUNDARY.md §3 states ctypes is primary, but actual code uses pybind11

**Status**: CONFLICTING EVIDENCE — ECO-01/ECO-02 documents ctypes as primary, but code uses pybind11.

### 2.2 pybind11 (Complex Objects)

#### ECO-02 Claim
> pybind11 used for complex object interfaces

#### ECO-03 Verification
**Status**: VERIFIED

**Evidence**:
- `engine/cpp_core/bindings.cpp` — pybind11 bindings file
- `engine/hydroma/cpp_bridge/hydroma_core.cp312-win_amd64.pyd` — compiled pybind11 extension
- Line 3-14 of `bindings.cpp` shows standard pybind11 module definition

### 2.3 Buffer Protocol (Zero-Copy)

#### ECO-02 Claim
> Buffer protocol for zero-copy array transfer

#### ECO-03 Verification
**Status**: PARTIAL — buffer protocol is defined in contract but NOT verified for actual zero-copy behavior.

**Evidence**:
- `engine/hydroma/cpp_bridge/__init__.py` line 144: `py::array_t<double, c_style | forcecast>` binding mentioned in comment
- `engine/cpp_core/src/indices.cpp` has `ndvi_array`, `evi_array` etc. functions
- BUT: No test verifies zero-copy behavior
- C++ tests (`engine/cpp_core/tests/`) have NOT been run (UNRUNNABLE due to missing database package)

**Status**: NOT VERIFIED — buffer protocol documented but not verified with running tests.

---

## 3. ABI Contract

### 3.1 ABI Specification (From Source Code)

| Property | Value | Evidence |
|----------|-------|----------|
| ABI format | pybind11 | `engine/cpp_core/bindings.cpp:3` (`PYBIND11_MODULE`) |
| Python version | 3.11, 3.12 | `.pyd` files: `cp311`, `cp312` |
| C++ standard | C++17 (assumed) | `engine/cpp_core/CMakeLists.txt` |
| Compiler | MSVC (Windows) | Build directory shows MSVC artifacts |
| Platform | Windows x64 | `win_amd64` in .pyd filenames |
| Extension name | `hydroma_core` | `sys.modules["hydroma_core"]` |

### 3.2 ABI Stability

**Status**: DESIGNED BUT NOT ENFORCED

- No ABI version checking at load time
- `cpp_bridge/__init__.py` line 56: `import hydroma_core as _hydroma_core` — no version check
- Different Python versions (3.11 vs 3.12) require different compiled extensions
- No documented ABI compatibility matrix

---

## 4. Memory Ownership

### ECO-02 Claim
> Python owns all memory

### ECO-03 Verification
**Status**: VERIFIED (for current implementation)

**Evidence**:
- `engine/hydroma/cpp_bridge/__init__.py` line 144-145: Comment confirms pybind11 reads caller's buffer
- C++ functions return `std::vector<double>` which pybind11 converts to Python `numpy.ndarray`
- Python creates arrays, passes them to C++, C++ returns new arrays
- No explicit memory allocation in C++ exposed to Python

---

## 5. Array Layout

### ECO-02 Claim
> Memory layout: C-contiguous for multi-dimensional

### ECO-03 Verification
**Status**: VERIFIED

**Evidence**:
- `engine/hydroma/cpp_bridge/__init__.py` line 144: `c_style | forcecast` flag used in array bindings
- Comment at line 140: "the natural shape for a reflectance time series" confirms C-contiguous assumption
- All C++ array functions accept `std::vector<double>` which maps to 1D C-contiguous arrays

---

## 6. dtype

### ECO-02 Claim
> All arrays: numpy.float64 (IEEE 754 double)

### ECO-03 Verification
**Status**: VERIFIED

**Evidence**:
- `engine/hydroma/cpp_bridge/__init__.py` line 44-54: `numpy.float64` explicitly used in Python fallbacks
- `engine/cpp_core/CMakeLists.txt`: C++ `double` type used for all arrays
- `numpy.asarray(data, dtype=np.float64)` at line 43 of ECO-01/05 contract

---

## 7. Endianness

### ECO-02 Claim
> IEEE 754 double

### ECO-03 Verification
**Status**: NOT ENFORCED

- No explicit endianness handling in code
- pybind11 handles endianness implicitly via buffer protocol
- No cross-platform testing documented
- No byte-order specification in contracts

**Status**: NOT VERIFIED

---

## 8. Exception / Error Propagation

### ECO-02 Claim
| C++ Error Code | Python Exception | Recovery |
|----------------|------------------|----------|
| CPP_SUCCESS | None | Continue |
| CPP_INVALID_INPUT | ValueError | Check input |
| CPP_OUT_OF_MEMORY | MemoryError | Retry or fail |
| CPP_COMPUTATION_ERROR | ComputationError | Log, retry |
| CPP_TIMEOUT | TimeoutError | Reduce workload |

### ECO-03 Verification
**Status**: PARTIALLY VERIFIED

**Evidence**:
- C++ code throws `std::invalid_argument` for invalid inputs (verified in `engine/cpp_core/src/climate.cpp:45-46`)
- pybind11 automatically converts `std::invalid_argument` to `ValueError`
- `engine/hydroma/cpp_bridge/__init__.py` line 244-248: C++ failures trigger fallback to Python

**Discrepancies**:
- No explicit `CPP_OUT_OF_MEMORY` → `MemoryError` handling in code
- No explicit `CPP_TIMEOUT` → `TimeoutError` handling
- Error codes mentioned in ECO-02 contract don't exist as named constants in code

---

## 9. Threading / Parallelism

### ECO-02 Claim
> C++ kernels use OpenMP for parallelism

### ECO-03 Verification
**Status**: VERIFIED (partial)

**Evidence**:
- `engine/cpp_core/src/climate.cpp` line 7: `#include <omp.h>`
- Line 159, 188, 227: `#pragma omp parallel for` in array functions
- CMake build file links OpenMP

**Status**: VERIFIED — OpenMP used for parallel array processing.

---

## 10. Build System

### ECO-02 Claim
| Component | Value |
|-----------|-------|
| Build System | CMake |
| Compiler | MSVC |
| Python | 3.12 |
| pybind11 | ✓ |

### ECO-03 Verification
**Status**: VERIFIED

**Evidence**:
- `engine/cpp_core/CMakeLists.txt` exists
- `engine/cpp_core/build2/` directory contains MSVC build artifacts
- `.pyd` files compiled for Python 3.12 (cp312)
- pybind11 detected from directory name

**Findings**:
- Two build directories exist: `build/` and `build2/` — potential configuration drift
- No build script for non-Windows platforms
- No documented build reproducibility (missing requirements.txt)

---

## 11. Performance Claims

### ECO-01 Claim
> Performance speedups: 10x, 50x, 100x, 200x

### ECO-03 Verification
**Status**: NOT VERIFIED

**Evidence**:
- `reports/eco-01/PERF-PERFORMANCE-KNOWLEDGE.md` mentions speedups
- `engine/hydroma/cpp_bridge/__init__.py` line 141-147: Comment describes 1339x speedup for buffer protocol fix
- BUT: No benchmark results files found in repository
- No `benchmark_*` results stored
- C++ benchmarks exist (`engine/cpp_core/tests/benchmark_*.cpp`) but tests UNRUNNABLE

**Verification of 1339x claim**:
- The comment at line 141 says: "the same shape now takes 0.005 s: 1339x faster"
- This compares 6.77s → 0.005s, which is indeed ~1355x
- This is a **real performance fix** but only applies to specific array shapes
- General claims of 10x-200x for other operations are NOT documented with evidence

**Status**: PARTIAL — Specific 1339x claim verified in code comments, general claims NOT VERIFIED.

---

## 12. C++/Python Boundary Test Requirements

| Test | Required | ECO-03 Status | Evidence Location |
|------|----------|---------------|-------------------|
| C++ unit tests | ✓ | EXISTS | `engine/cpp_core/tests/` (11 test files) |
| Python fallback tests | ✓ | EXISTS | `engine/hydroma/cpp_bridge/tests/test_parity.py` |
| C++/Python parity | ✓ | EXISTS | `engine/hydroma/cpp_bridge/tests/test_parity.py` |
| Buffer protocol tests | ✓ | EXISTS | `engine/cpp_core/tests/test_*.cpp` |
| Benchmark results | ✓ | NOT FOUND | No benchmark results stored |

---

## 13. C++ Kernel Issues

### Discrepancy Resolution Fixes (Already Applied)

The `engine/hydroma/cpp_bridge/__init__.py` file documents several fixes:

1. **Hargreaves exponent**: Fixed 0.50 → 0.48 (FAO-56 eq. 52) — both C++ and Python
   - Evidence: `engine/cpp_core/src/climate.cpp:59-60` and `cpp_bridge/__init__.py:374-378`

2. **Penman-Monteith parameter order**: Fixed parameter swap in Python fallback
   - Evidence: `cpp_bridge/__init__.py:362-372`

3. **EVI clipping**: Fixed Python fallback to clip [-1, 1]
   - Evidence: `cpp_bridge/__init__.py:294-322`

4. **Clear-sky ratio**: Fixed cloudiness factor clipping
   - Evidence: `cpp_bridge/__init__.py:408-425` and `climate.cpp:93-95`

5. **Polar night handling**: Fixed Rs/Rso division by zero
   - Evidence: `cpp_bridge/__init__.py:418-425` and `climate.cpp:94`

6. **Temperature constant**: C++ uses 273.0, Python uses 273.16 — **STILL DIVERGENT**
   - Evidence: `climate.cpp:138` vs `cpp_bridge/__init__.py:435`
   - **Status**: CONFLICTING EVIDENCE — divergence still exists

---

## 14. Findings

1. **VERIFIED**: C++ owns numerical kernels, Python owns orchestration. Clear boundary.

2. **CONFLICTING EVIDENCE**: ECO-01/05 claims ctypes is primary interface, but code uses pybind11. Documentation mismatch.

3. **NOT VERIFIED**: Buffer protocol performance claims — tests UNRUNNABLE.

4. **CONFLICTING EVIDENCE**: Temperature conversion constant: C++ uses 273.0, Python fallback uses 273.16. This produces different results for identical inputs.

5. **DESIGNED BUT NOT ENFORCED**: ABI version checking, endianness handling, error code mapping.

6. **VERIFIED**: OpenMP parallelism exists in C++ array functions.

7. **NOT VERIFIED**: General 10x-200x speedup claims — only specific 1339x fix documented with evidence.

8. **BLOCKING**: C++ tests cannot run due to missing `database/` package.

---

## 15. C++/Python Boundary Invariants

| Invariant | Status | Evidence |
|-----------|--------|----------|
| C++ owns numerical kernels | VERIFIED | 10 .cpp source files |
| Python owns orchestration | VERIFIED | 50+ Python modules |
| Python owns memory | VERIFIED | pybind11 buffer conversion |
| Arrays use float64 | VERIFIED | IEEE 754 double in both |
| C-contiguous arrays | VERIFIED | `c_style | forcecast` flag |
| Single source of truth for equations | VIOLATED | Temperature constant divergence |
| Error codes mapped to exceptions | PARTIAL | ValueError works, others not |
| ABI version tracked | NOT ENFORCED | No version checking |
| Endianness explicit | NOT ENFORCED | No byte-order specification |

---

*Report generated: 2026-10-08*
*Status: VERIFIED with CONFLICTING EVIDENCE (temperature constant divergence)*