# C++ Core Module

This directory contains the C++ source code for performance-critical computations that may eventually be integrated into the larger Python application.

## Purpose
This module provides high-performance implementations of computationally intensive algorithms and models. The C++ implementation allows for fine-grained performance optimization while maintaining compatibility with the Python ecosystem through appropriate binding technologies.

## Requirements
- A modern C++ compiler (C++20 compliant)
- Python development headers and libraries
- A binding library (e.g., pybind11, Cython, ctypes)

## Building and Binding
To use this module within the Python application, it must be compiled and linked to Python using an appropriate binding mechanism. The specific instructions for building and linking are not provided here and must be implemented separately based on the chosen technology.

Until this process is completed and integrated, this directory is considered orphaned and its functionality is not accessible from the main Python application.

## Development Notes
- Code should maintain cross-platform compatibility
- All public APIs should be clearly documented
- Performance-critical sections should be profiled and optimized
- Memory management must be handled carefully to avoid leaks
- Thread-safety should be considered for parallelizable operations
# HyDroMa C++ Core (engine/cpp_core)

C++20 numerical kernels for the HyDroMa engine. Python bindings via pybind11;
pure-C++ tests run without Python.

## Modules

| Header | Kernel | Status |
|---|---|---|
| `hydrology.hpp` | Muskingum–Cunge flood routing | v1, validated vs Numba |
| `soil.hpp` | van Genuchten retention + Mualem K(h) | v1 + 2026-08 K-formula bugfix |
| `erosion.hpp` | RUSLE (point LS factor, erosion) | v1 |
| `climate.hpp` | FAO-56 Penman–Monteith + Hargreaves ET0 | v1 |
| `indices.hpp` | NDVI/EVI/SAVI/NDWI/NBR | v1 |
| `richards.hpp` | **1D Richards** (mixed form, modified Picard/Celia 1990, FV) | v2 |
| `saint_venant.hpp` | **1D Saint-Venant** (Rusanov FV, Manning friction, dry cells) | v2 |
| `crop_water.hpp` | **FAO-56 dual-Kc daily water balance** (Ks, Ke, TEW/REW, auto-irrigation) | v2 |
| `sediment.hpp` | **Distributed RUSLE + SDR (Boyce 1975) + Brune trap efficiency** | v2 |
| `sampling.hpp` | **MC + Latin Hypercube (variance reduction), yield ensemble** | v2 |

## Build & test (MSVC 2019, no CMake needed for the standalone tests)

```bat
call build_msvc.bat      :: v1 tests  (tests\test_hydroma.cpp)
call build_v1.bat        :: v1 tests  (same, all sources)
call build_advanced.bat  :: v2 tests  (tests\test_advanced.cpp, 35 checks)
```

All 70 checks green. The advanced suite covers:

- **Richards:** hydrostatic equilibrium (no drift), infiltration wetting front,
  mass balance closure (ΔS = boundary fluxes), singular-system diagnostics.
- **Saint-Venant:** dam-break stability + mass conservation (< 2 %), Manning
  normal depth sanity.
- **Crop water:** dual-Kc drought stress, auto-irrigation, exact water-balance
  closure (error ~ 0 mm).
- **Sediment:** RUSLE grid, SDR bounds, Brune TE monotonicity.
- **Sampling:** LHS stratification, 108× standard-error reduction vs MC,
  yield ensemble order statistics.
- **Regression:** C++ K(h)/θ(h) matches the Python Numba reference
  (`engine/hydroma/cpp_bridge/soil_physics_fast.py`) to 1e-6.

## Python bindings (pybind11)

```bash
python -m pip install pybind11 cmake
cmake -S . -B build2 -DHYDROMA_BUILD_PYTHON_BINDINGS=ON `
      -Dpybind11_DIR="$(python -m pybind11 --cmakedir)" `
      -DPython_EXECUTABLE="$(python -c 'import sys;print(sys.executable)')"
cmake --build build2 --config Release
```

The module `hydroma_core` (hydroma_core.cp3xx-win_amd64.pyd) exposes all
v1 + v2 kernels with structured options (`RichardsOptions`,
`SaintVenantOptions`, `CropWaterParams`, …). The built .pyd is copied into
`engine/hydroma/cpp_bridge/` so `from engine.hydroma.cpp_bridge import
hydroma_core` works from the project root (verified 2026-08-14 on
Python 3.11: Richards mass balance err = 0.0, Saint-Venant mass balance
= 1.0000, crop water balance ~ 0 mm).

## References

- Richards (1931); Celia, Bouloutas & Zarba (1990) WRR 26(7):1483-1496.
- van Genuchten (1980) SSSAJ 44:892-898; Mualem (1976) WRR 12:513-522.
- FAO Irrigation and Drainage Paper 56 (Allen et al., 1998).
- Renard et al. (1997) RUSLE handbook; Boyce (1975); Brune (1953) Trans. AGU.
- McKay, Beckman & Conover (1979) Technometrics 21:239-245 (LHS).

## Honesty notes

- The Richards solver requires at least one head-specified boundary when the
  profile is (nearly) saturated; all-flux BCs on a saturated column are
  ill-posed (singular system) and reported as `converged=false`.
- The Muskingum–Cunge mass tolerance is ~10 % by design (consistent with the
  Python tests); the Richards scheme conserves mass to numerical precision.
