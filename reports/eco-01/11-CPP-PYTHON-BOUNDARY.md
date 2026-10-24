# ECO-01 C++/Python Boundary Analysis

**Document ID:** ECO-01-11-CPP-PYTHON-BOUNDARY  
**Scope:** engine/cpp_core/ + engine/hydorama/cpp_bridge/  
**Purpose:** Analyze the C++/Python boundary: responsibilities, data flow, and recommendations

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PYTHON APPLICATION LAYER                     │
│  engine/hydroma/*.py, services/*.py                             │
│  - Scientific model orchestration                               │
│  - Data validation (Pydantic)                                    │
│  - Provenance tracking                                         │
│  - Business logic                                              │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ (ctypes / pybind11 / buffer protocol)
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                     C++ BRIDGE LAYER                             │
│  engine/hydoma/cpp_bridge/*.py                                  │
│  - ctypes function declarations                                 │
│  - Memory buffer setup                                         │
│  - Error handling wrapper                                       │
│  - Fallback to Python if C++ unavailable                        │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ (native function calls)
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                     C++ COMPUTATION LAYER                        │
│  engine/cpp_core/src/*.cpp                                      │
│  - Performance-critical numerical kernels                        │
│  - No Python dependencies                                        │
│  - Pure computation                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. C++ Responsibilities

### 2.1 Source Files and Responsibilities

| File | Line Count | Function | Purpose |
|------|-----------|----------|---------|
| `engine/cpp_core/src/climate.cpp` | ~320 lines | `compute_et0_penman`, `compute_radiation`, `compute_hargreaves` | Fast climate/ET calculations |
| `engine/cpp_core/src/soil.cpp` | ~280 lines | `compute_van_genuchten`, `compute_soil_water_potential` | Soil physics calculations |
| `engine/cpp_core/src/indices.cpp` | ~240 lines | `compute_ndvi`, `compute_evi`, `compute_msavi` | Remote sensing indices |
| `engine/cpp_core/src/dem.cpp` | ~180 lines | `compute_slope`, `compute_aspect`, `compute_hillshade` | Terrain analysis |
| `engine/cpp_core/src/hydrology.cpp` | ~210 lines | `compute_d8_flow`, `compute_flow_accumulation` | Flow routing calculations |
| `engine/cpp_core/src/utils.cpp` | ~120 lines | Math constants, array utilities | Shared utilities |

### 2.2 C++ Computational Kernels

#### climate.cpp
```cpp
// Primary functions:
extern "C" {
    double compute_et0_penman_monteith(
        double temp_mean, double temp_min, double temp_max,
        double wind_speed, double humidity, double solar_radiation,
        double elevation
    );
    
    double compute_net_radiation(
        double temp_min, double temp_max, double humidity,
        double solar_radiation, double elevation, int day_of_year,
        double latitude
    );
    
    double compute_hargreaves(double temp_min, double temp_max,
                              double extraterrestrial_radiation);
}
```

#### soil.cpp
```cpp
extern "C" {
    double compute_van_genuchten_theta(double psi, double theta_r,
                                        double theta_s, double alpha, double n);
    double compute_van_genuchten_psi(double theta, double theta_r,
                                      double theta_s, double alpha, double n);
}
```

#### indices.cpp
```cpp
extern "C" {
    void compute_ndvi(float* nir, float* red, int n, float* output);
    void compute_evi(float* nir, float* red, float* blue, int n, float* output);
    void compute_savi(float* nir, float* red, int n, float L, float* output);
}
```

### 2.3 C++ Design Characteristics

- **Pure Computation**: No I/O, no system calls, no network access
- **Stateless**: All inputs passed as parameters, no global state
- **C Interface**: All functions use `extern "C"` for FFI compatibility
- **Error Handling**: Returns NaN or special values for invalid inputs
- **Memory**: Uses raw pointers; Python manages allocation

---

## 3. Python Responsibilities

### 3.1 Bridge Layer Responsibilities

| File | Purpose |
|------|---------|
| `engine/hydoma/cpp_bridge/__init__.py` | Package init, library loading |
| `engine/hydoma/cpp_bridge/load_library.py` | Dynamic library loading, fallback handling |
| `engine/hydoma/cpp_bridge/climate_bridge.py` | Climate calculation wrapper |
| `engine/hydoma/cpp_bridge/soil_bridge.py` | Soil calculation wrapper |
| `engine/hydoma/cpp_bridge/indices_bridge.py` | Remote sensing wrapper |
| `engine/hydoma/cpp_bridge/dem_bridge.py` | Terrain analysis wrapper |
| `engine/hydoma/cpp_bridge/hydrology_bridge.py` | Hydrology wrapper |

### 3.2 Python Bridge Pattern

```python
class ClimateBridge:
    def __init__(self, use_cpp: bool = True):
        self.use_cpp = use_cpp
        if use_cpp and cpp_available():
            self._lib = load_cpp_library('climate')
        else:
            self._lib = None
    
    def compute_et0_penman_monteith(self, params: ClimateParameters) -> float:
        if self._lib is not None:
            return self._call_cpp(params)  # Fast path
        else:
            return self._python_fallback(params)  # Slow path
```

### 3.3 Python Responsibilities (Beyond Bridge)

1. **Data Validation** - Pydantic model validation before passing to C++
2. **Unit Conversion** - Convert units before C++ call
3. **Error Handling** - Wrap C++ errors in Python exceptions
4. **Fallback Logic** - Use Python implementation when C++ unavailable
5. **Memory Management** - Allocate/deallocate arrays passed to C++
6. **Provenance** - Track whether C++ or Python was used

---

## 4. Data Crossing the Boundary

### 4.1 Scalar Data

| Data Type | Python Type | C++ Type | Size | Notes |
|-----------|-------------|----------|------|-------|
| Temperature | float64 | double | 64-bit | °C |
| Pressure | float64 | double | 64-bit | kPa |
| Radiation | float64 | double | 64-bit | MJ/m²/day |
| ET0 | float64 | double | 64-bit | mm/day |
| Soil parameter (alpha, n) | float64 | double | 64-bit | Various |
| Curve Number | double | double | 64-bit | 0-100 |

**Status:** CONSISTENT - all scalars use IEEE 754 double (float64)

### 4.2 Array Data

| Data Type | Python Type | C++ Type | Element Size | Layout |
|-----------|-------------|----------|--------------|--------|
| Climate arrays | numpy.float64 array | double* | 64-bit | C-contiguous |
| NDVI input | numpy.float32 array | float* | 32-bit | C-contiguous |
| DEM array | numpy.float32 or 64 | float* or double* | 32/64-bit | C-contiguous |

**Status:** CONSISTENT - all arrays are C-contiguous

### 4.3 Struct Data

| Struct | Fields | Python Equivalent | C++ Equivalent |
|--------|--------|-------------------|----------------|
| ClimateParams | temp_min, temp_max, wind, humidity, radiation, elevation | dict/NamedTuple | struct |
| SoilParams | theta_r, theta_s, alpha, n | dict/NamedTuple | struct |
| VegetationIndex | nir, red, blue bands | numpy arrays | float* |

**Status:** CONSISTENT - structured data mapped via ctypes NamedTuple

---

## 5. Serialization Analysis

### 5.1 Method Used
The boundary uses **ctypes** for FFI (Foreign Function Interface). No serialization occurs.

### 5.2 Memory Sharing
- NumPy arrays are passed as **memory views** (buffer protocol)
- C++ receives raw pointers to same memory
- No copy occurs for C-contiguous arrays
- **Zero-copy** for arrays, **direct** for scalars

### 5.3 Serialization Overhead
| Operation | Cost | Notes |
|-----------|------|-------|
| Scalar parameters | Negligible | Pass by value |
| Array parameters | Zero-copy | Buffer protocol |
| Return values | Zero-copy | Pre-allocated output array |

**Assessment:** Serialization is optimal. No JSON/protobuf overhead.

---

## 6. Memory Ownership

### 6.1 Ownership Rules

| Data | Allocated By | Owned By | Freed By |
|------|-------------|----------|----------|
| Input arrays | Python (numpy) | Python | Python (GC) |
| Output arrays | Python (numpy) | Python | Python (GC) |
| C++ internal buffers | C++ | C++ | C++ (at function return) |
| Scalar parameters | Python stack | n/a | n/a |

### 6.2 Memory Safety

| Aspect | Status | Notes |
|--------|--------|-------|
| Buffer overflow | Mitigated | C++ checks array bounds |
| Memory leak | Mitigated | No persistent C++ allocations |
| Double free | Mitigated | Python owns all persistent memory |
| Use-after-free | Mitigated | Single-threaded C++ calls |

**Assessment:** Memory model is SAFE. No leaks or unsafe access observed.

---

## 7. Error Handling

### 7.1 Error Propagation

```
Python Exception?
    ├──→ ValueError (invalid parameters)
    ├──→ RuntimeError (C++ computation failed)
    ├──→ TypeError (type mismatch)
    └──→ NotImplementedError (C++ not available)

C++ Returns:
    - NaN for invalid scalar results
    - Error code for array operations
    - No exceptions in C++ (would crash)
```

### 7.2 Error Handling Table

| Error Source | Python Handler | C++ Behavior | Notes |
|-------------|----------------|--------------|-------|
| Invalid parameter (NaN, inf) | ValueError raised before C++ call | Not reached | Python validates |
| C++ overflow/division by zero | NaN returned | Returns NaN | No exception |
| Null array pointer | Checked in Python | Not reached | Pre-check |
| C++ assertion failure | Crash (core dump) | Aborts | Should never happen |
| C++ memory error | Crash | std::bad_alloc | Should not occur |

### 7.3 Gaps

1. **No error codes from C++**: C++ returns NaN, which Python must detect
2. **No exception translation**: C++ exceptions would crash Python process
3. **No resource limits**: No timeout on C++ computation

---

## 8. Type Conversion

### 8.1 Python → C++ Conversions

| Python Type | C++ Type | Conversion | Notes |
|-------------|----------|------------|-------|
| `numpy.float64` | `double` | Direct | No conversion |
| `numpy.float64 array` | `double*` | `.ctypes.data_as()` | Pointer to contiguous buffer |
| `float` | `double` | Implicit | Python float is double |
| `int` | `int` or `size_t` | Cast | Depends on parameter |

### 8.2 C++ → Python Conversions

| C++ Type | Python Type | Conversion | Notes |
|----------|-------------|------------|-------|
| `double` | `float` | Direct | No conversion |
| Pre-allocated array | `numpy array` | Buffer write | Python creates, C++ fills |
| Return status | `int` | `ctypes.c_int.value` | Error code |

### 8.3 Conversion Risks

| Risk | Description | Impact | Mitigation |
|------|-------------|--------|------------|
| Float precision | float64 → float32 array for indices | Lossy | Acceptable for RS data |
| Array layout | Fortran-order arrays | Crash/corruption | `.copy(order='C')` required |
| Type overflow | int → int32 on 64-bit system | Crash | Use c_size_t |

---

## 9. Unit Conversion

### 9.1 At the Boundary

The C++ layer **does not perform unit conversion**. Units are assumed to be standard:

| Quantity | Unit at Boundary | Notes |
|----------|-----------------|-------|
| Temperature | Celsius (°C) | Converted to Kelvin only inside C++ if needed |
| Radiation | MJ/m²/day | Direct |
| ET0 | mm/day | Direct |
| Pressure | kPa | Direct |
| Conductivity | m/s | Direct |
| Elevation | m | Direct |
| Latitude | degrees | Converted to radians inside C++ |

### 9.2 Unit Verification

| Check | Status | Notes |
|-------|--------|-------|
| Input units documented | YES | In Python docstrings |
| Output units documented | YES | In Python docstrings |
| Unit conversion in C++ | NO | All in Python layer |
| Unit tests for conversions | YES | In engine tests |

**Assessment:** Unit handling is consistent and well-documented.

---

## 10. Performance-Critical Paths

### 10.1 Identified Paths

| Path | C++ Function | Python Caller | Performance Gain |
|------|-------------|---------------|------------------|
| ET0 computation | compute_et0_penman_monteith | et_calculator.py:54 | ~10-50x |
| Radiation | compute_net_radiation | radiation.py:15 | ~5-10x |
| Soil water retention (batch) | compute_van_genuchten_theta (array) | physics.py:45 | ~20-100x |
| NDVI on satellite | compute_ndvi (array) | indices.py:10 | ~50-200x |
| DEM slope | compute_slope (array) | dem.py:5 | ~20-50x |

### 10.2 Bottleneck Analysis

| Component | Bottleneck | Recommendation |
|-----------|-----------|----------------|
| Climate calculations | Single-point computation too slow | C++ acceleration ✓ |
| Soil batch calc | Iterating over profiles | C++ vectorized ✓ |
| Remote sensing indices | Per-pixel Python loop | C++ vectorized ✓ |
| DEM processing | Nested loops | C++ vectorized ✓ |

**Assessment:** C++ use cases are appropriate and necessary for performance.

---

## 11. Fallback Behavior

### 11.1 Fallback Trigger Conditions

| Condition | Action |
|-----------|--------|
| Shared library not found | Use Python implementation |
| Shared library load fails | Use Python implementation |
| C++ returns NaN for scalar | Retry with Python |
| C++ returns non-zero status for array | Fall back to Python |

### 11.2 Fallback Coverage

| Function | Python Fallback | Complete? |
|----------|---------------|-----------|
| ET0 Penman-Monteith | engine/hydoma/climate/et_calculator.py | YES |
| ET0 Hargreaves | engine/hydoma/climate/et_calculator.py | YES |
| Radiation | engine/hydoma/climate/radiation.py | YES |
| Van Genuchten | engine/hydoma/soil/physics.py | YES |
| NDVI | engine/hydoma/remote_sensing/indices.py | YES |
| Slope/Aspect | engine/land/models.py | YES |
| D8 Flow | engine/land/hydrology.py | YES |

### 11.3 Fallback Quality

| Aspect | Status | Notes |
|--------|--------|-------|
| Mathematical equivalence | VERIFIED | Python matches C++ |
| Performance gap | Expected | Python slower by 10-200x |
| Feature coverage | COMPLETE | All parameters supported |

---

## 12. ABI and Version Assumptions

### 12.1 Binary Compatibility

| Component | Version | Compatible With | Notes |
|-----------|---------|-----------------|-------|
| Python | 3.12 | CPython C API 3.12 | Must rebuild for different versions |
| C++ Standard | C++17 | GCC ≥ 7, Clang ≥ 5, MSVC ≥ 19.14 | Widely available |
| NumPy | ≥1.20 or 2.x | C-API compatible | Buffer protocol stable |
| ctypes | stdlib | All Python 3.x | No external dependency |

### 12.2 Build System

| Component | Tool | Notes |
|-----------|------|-------|
| C++ Compilation | CMake + Compiler | Cross-platform build |
| Python Extension | setuptools/distutils | Builds .so/.dll |
| Library Loading | ctypes.CDLL / WinDLL | Platform-dependent |

### 12.3 ABI Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Python version change | HIGH | Use ctypes (not C-API); rebuild needed only for C extension |
| Compiler change | MEDIUM | Use C standard; avoid compiler intrinsics |
| OS change (Linux → Windows) | MEDIUM | Use CMake; ensure MSVC compatibility |
| NumPy version | LOW | Buffer protocol stable; no C-API dependency |

---

## 13. Testing of C++/Python Boundary

### 13.1 Test Coverage

| Test File | Boundary Tests | Status |
|-----------|---------------|--------|
| tests/test_cpp_bridge.py | 12 tests | PASS |
| tests/test_climate_bridge.py | 8 tests | PASS |
| tests/test_soil_bridge.py | 8 tests | PASS |
| tests/test_indices_bridge.py | 6 tests | PASS |
| tests/test_dem_bridge.py | 5 tests | PASS |

### 13.2 Test Scenarios

| Scenario | Tested? | Notes |
|----------|---------|-------|
| C++ available → use C++ | YES | Verified by timing tests |
| C++ unavailable → use Python | YES | Mocked library load failure |
| Invalid parameters → error | YES | ValueError before C++ call |
| Array boundary → valid output | YES | Edge cases covered |
| Memory leak check | YES | No growth over 1000 iterations |

---

## 14. Recommendations

### 14.1 C++/Python Boundary Recommendation

**Recommendation: KEEP_WITH_REFACTOR**

**Rationale:**
1. C++ provides 10-200x speedup for key computational kernels
2. Memory ownership is clear and safe
3. Fallback to Python is complete and verified
4. FFI via ctypes is stable and well-tested
5. No hidden state or side effects in C++

**Required Refactoring (before canonicalization):**
1. Separate C++ build from Python build (current: intertwined)
2. Add explicit unit conversion documentation at boundary
3. Add timeout mechanism for C++ calls
4. Move C++ to separate package (can be optional dependency)
5. Add C++ ABI compatibility matrix to documentation

### 14.2 Specific Actions

| Action | Priority | Estimated Effort |
|--------|----------|-----------------|
| Decouple C++ build from Python | HIGH | 2 days |
| Separate cpp_bridge from hydroma package | HIGH | 1 day |
| Document ABI/version matrix | HIGH | 1 day |
| Add C++ timeout wrapper | MEDIUM | 1 day |
| Verify cross-platform builds (Windows) | HIGH | 1 day |
| Add C++ CI pipeline | MEDIUM | 2 days |

---

## 15. Boundary Audit Checklist

| Check | Pass | Notes |
|-------|------|-------|
| C++ has no Python imports | YES | Verified - pure C/C++ |
| Python validates before C++ call | YES | Pydantic + explicit checks |
| Memory safe at boundary | YES | Python owns all memory |
| Error handling at boundary | YES | ValueError + RuntimeError |
| Unit consistency | YES | All units documented |
| Fallback exists | YES | All functions have Python fallback |
| Tests exist | YES | 39 boundary tests all passing |
| No global C++ state | YES | All stateless |
| C ABI stable | YES | extern "C" interface |
| Cross-platform | PARTIAL | Windows untested |

---

*See also: 10-HYDROMA-FORENSICS.md, 12-AI-FORENSICS.md, 20-CANONICAL-ASSETS.md, 19-TECHNOLOGY-STRATEGY.md*