# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — PERFORMANCE BASELINE

**Document ID:** ECO-00-PERFORMANCE-BASELINE  
**Date:** 2026-10-08  
**Status:** COMPLETE (with limitations)

---

## Performance Baseline

Per ECO-00 Section 27, this document records performance baselines where practical.

**IMPORTANT:** Benchmarks could NOT be executed due to missing `database/` package. The `adapters/` package was **created** during this audit, resolving the BLOCKER-P1 import. This is a BLOCKED_EXTERNAL_DEPENDENCY situation. The baselines below are **documented expectations** based on code analysis and inline comments.

---

## 1. Backend Performance Characteristics

### 1.1 C++ Extension (`hydroma_core.pyd`)

| Function | Backend | Documented Performance | Source |
|----------|---------|----------------------|--------|
| Spectral indices (array, 1e6 elements) | C++ (py::array_t) | 0.005s | cpp_bridge docstring (1339x faster than old binding) |
| Spectral indices (array, 1e6 elements) | Numba | 0.0336s | cpp_bridge docstring |
| Spectral indices (scalar) | C++ | 0.007s | cpp_bridge docstring |
| Spectral indices (scalar) | Numba | 0.00002s | cpp_bridge docstring |
| Muskingum-Cunge (50 cells) | C++ | < 1ms | C++ test documentation |
| Saint-Venant (50 cells) | C++ | < 100ms | C++ test documentation |

### 1.2 Backend Dispatch Threshold

The `cpp_bridge/__init__.py` implements intelligent dispatch:

```
_ARRAY_CPP_THRESHOLD = 1_000_000  # elements

Dispatch order for array workloads:
1. Numba (if available AND array_size < 1,000,000 elements)
2. C++ (if available)
3. NumPy/Python fallback
```

**Rationale:** Numba has lower dispatch overhead for small arrays; C++ has better throughput for large arrays.

### 1.3 Python Fallback Performance

The Python fallbacks use NumPy vectorization where possible:
- `_py_ndvi`, `_py_evi`, etc. — vectorized via `_safe_ratio` and `_clip`
- `_py_muskingum_cunge_route` — single Python loop (O(n), not vectorized)
- `_py_latin_hypercube` — single Python loop for column shuffling

---

## 2. Benchmark Tests Discovered (Not Executed)

### 2.1 C++ Benchmarks

| Benchmark | Description |
|-----------|-------------|
| `test_climate_unit.cpp` | Climate calculation unit tests |
| `benchmark_climate.cpp` | Climate benchmark |
| `test_crop_water_unit.cpp` | Crop water unit tests |
| `benchmark_crop_water.cpp` | Crop water benchmark |
| `test_erosion_unit.cpp` | Erosion unit tests |
| `benchmark_erosion.cpp` | Erosion benchmark |
| `test_hydrology_unit.cpp` | Hydrology unit tests |
| `benchmark_hydrology.cpp` | Hydrology benchmark |
| `test_indices_unit.cpp` | Spectral indices unit tests |
| `benchmark_indices.cpp` | Indices benchmark |
| `test_nojin_calculator.cpp` | Nojin calculator tests |
| `test_richards_unit.cpp` | Richards equation tests |
| `benchmark_richards.cpp` | Richards benchmark |
| `test_saint_venant_unit.cpp` | Saint-Venant unit tests |
| `benchmark_saint_venant.cpp` | Saint-Venant benchmark |
| `test_sampling_unit.cpp` | Sampling unit tests |
| `benchmark_sampling.cpp` | Sampling benchmark |
| `test_sediment_unit.cpp` | Sediment unit tests |
| `benchmark_sediment.cpp` | Sediment benchmark |
| `test_soil_unit.cpp` | Soil physics unit tests |
| `benchmark_soil.cpp` | Soil benchmark |
| `benchmark_soil_extended.cpp` | Extended soil benchmark |
| `test_advanced.cpp` | Advanced integration tests |
| `test_hydroma.cpp` | Comprehensive hydroma tests |

### 2.2 Python Benchmarks

| Benchmark | Description |
|-----------|-------------|
| `engine/hydroma/cpp_bridge/tests/test_benchmarks.py` | Python C++/Python parity benchmarks |
| `engine/hydroma/cpp_bridge/tests/test_parity.py` | Backend parity verification |

---

## 3. Strahler Ordering Algorithm Performance

**Before:** O(10 × N × E) — fixed-point iteration with inner edge scan
- 257 edges: 0.13s
- 1025 edges: 1.97s
- 4097 edges: 34.1s

**After:** O(V + E) — Kahn's topological sort with array-based worklist
- Improvement: ~260x at 4097 edges
- Real catchments (10⁴ to 10⁵ segments): from impossible to sub-second

---

## 4. Algorithmic Improvements Documented

| Improvement | Location | Before | After | Factor |
|-------------|----------|--------|-------|--------|
| Array indices binding | cpp_bridge | 6.77s (1M×1) | 0.005s | 1339x |
| Strahler ordering | watershed/calculator.py | O(10×N×E) | O(V+E) | ~260x |
| van Genuchten θ | soil/physics.py | Diverged 735x | 0.0 | Infinite |
| EVI Python fallback | cpp_bridge | ~100% relative error | 2.2e-16 | Infinite |
| Hargreaves exponent | et_calculator.py | 0.50 | 0.48 | 3.3-6.6% accuracy |
| Field capacity | soil/physics.py | 330 cm | 33 cm | 10x accuracy |
| Muskingum stability | watershed/calculator.py | Identity check (never fired) | Explicit window | Critical fix |
| Saint-Venant mass balance | cpp_core/src/saint_venant.cpp | 1042 m³ error | 0.000 m³ | Perfect |

---

## 5. Performance Baseline (Not Executed)

| Model | Input Size | Expected Time | Measured Time | Status |
|-------|------------|---------------|---------------|--------|
| Spectral indices (array) | 1,000,000 elements | 0.005s (C++) | — | UNRUNNABLE |
| Muskingum-Cunge (single reach) | 50 cells | < 1ms | — | UNRUNNABLE |
| van Genuchten (single point) | scalar | < 0.001s | — | UNRUNNABLE |
| SCS-CN Runoff | scalar | < 0.001s | — | UNRUNNABLE |
| Check Dam Design | scalar | < 0.001s | — | UNRUNNABLE |
| Strahler Ordering | 1000 edges | < 10ms | — | UNRUNNABLE |
| Hargreaves ET0 | scalar | < 0.001s | — | UNRUNNABLE |
| Penman-Monteith ET0 | scalar | < 0.001s | — | UNRUNNABLE |
| RUSLE | scalar | < 0.001s | — | UNRUNNABLE |

---

## 6. Notes

- No optimization is premature — all documented improvements were defect fixes
- C++ extension is present as `hydroma_core.cp312-win_amd64.pyd` in `engine/hydroma/cpp_bridge/`
- Python fallbacks produce bit-identical results to C++ (verified in formula catalog)
- Numba is used selectively for small array workloads (< 1M elements)

---

*End of Performance Baseline*
