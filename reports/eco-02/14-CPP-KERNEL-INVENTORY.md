# ECO-02: C++ Kernel Inventory

## 10 Source Files, 10 Headers, 21 Tests

---

## Source Evidence
- reports/engine-services/INVENTORY.md
- ECO-01/11-CPP-PYTHON-BOUNDARY.md
- ECO-01/10-HYDROMA-FORENSICS.md

---

## C++ Kernel Components

### Source Files (10 files in `c++/`)

| File | Purpose | Python Interface |
|------|---------|------------------|
| `et_calculations.cpp` | ET computation core | `compute_penman_monteith()`, `compute_hargreaves()` |
| `hydrology.cpp` | Streamflow routing | `compute_streamflow()`, `flood_routing()` |
| `crop_water.cpp` | Crop water balance | `crop_water_requirement()`, `irrigation_schedule()` |
| `groundwater.cpp` | Groundwater flow | `groundwater_flow()`, `aquifer_recharge()` |
| `climate_interpolation.cpp` | Spatial interpolation | `interpolate_temperature()`, `interpolate_precipitation()` |
| `radiation.cpp` | Solar radiation | `compute_solar_radiation()`, `daylength()` |
| `soil_water.cpp` | Soil water balance | `soil_water_content()`, `field_capacity()` |
| `reservoir.cpp` | Reservoir operation | `reservoir_release()`, `storage_curve()` |
| `snow_melt.cpp` | Snowmelt modeling | `compute_snowmelt()`, `snow_pack()` |
| `optimization.cpp` | Multi-objective optimization | `pareto_optimize()`, `weighted_objective()` |

### Header Files (10 files in `c++/include/`)

| File | Interface |
|------|-----------|
| `et_calculations.h` | ET computation structs and functions |
| `hydrology.h` | Hydrology data structures |
| `crop_water.h` | Crop water calculation interfaces |
| `groundwater.h` | Groundwater simulation interfaces |
| `climate_interpolation.h` | Interpolation function declarations |
| `radiation.h` | Radiation calculation interfaces |
| `soil_water.h` | Soil water balance interfaces |
| `reservoir.h` | Reservoir operation interfaces |
| `snow_melt.h` | Snowmelt model interfaces |
| `optimization.h` | Optimization algorithm interfaces |

### Test Files (21 files in `c++/tests/`)

| File | Test Coverage |
|------|---------------|
| `test_et_calculations.cpp` | Penman-Monteith, Hargreaves, Makkink |
| `test_hydrology.cpp` | Streamflow, flood routing |
| `test_crop_water.cpp` | Crop water, irrigation scheduling |
| `test_groundwater.cpp` | Groundwater flow, recharge |
| `test_climate_interpolation.cpp` | Temperature, precipitation interpolation |
| `test_radiation.cpp` | Solar radiation, daylength |
| `test_soil_water.cpp` | Soil water, field capacity |
| `test_reservoir.cpp` | Reservoir release, storage |
| `test_snow_melt.cpp` | Snowmelt, snow pack |
| `test_optimization.cpp` | Pareto optimization, weighted objective |
| `test_edge_cases.cpp` | NaN, Inf, boundary values |
| `test_precision.cpp` | Double precision validation |
| `test_buffer_protocol.cpp` | Zero-copy buffer interface |
| `test_integration.cpp` | End-to-end kernel integration |
| `test_performance.cpp` | Performance benchmarks |
| `test_memory.cpp` | Memory leak detection |
| `test_unit_consistency.cpp` | Unit system validation |
| `test_climate_inputs.cpp` | Climate data handling |
| `test_model_coupling.cpp` | Inter-kernel coupling |
| `test_conservation.cpp` | Mass/energy conservation |
| `test_validation.cpp` | Scientific validation against benchmarks |

---

## Python Bindings

Located in `engine/cpp_bindings/`:

| Module | Description |
|--------|-------------|
| `et_bindings.py` | ctypes wrapper for ET calculations |
| `hydrology_bindings.py` | ctypes wrapper for hydrology |
| `crop_water_bindings.py` | ctypes wrapper for crop water |
| `groundwater_bindings.py` | ctypes wrapper for groundwater |
| `__init__.py` | Package initialization |

### Buffer Protocol Usage
```python
# Zero-copy array transfer
import numpy as np
from .et_bindings import compute_et

# Create array in Python (owns memory)
temperature = np.array([25.0, 26.0, 27.0], dtype=np.float64)
# Pass to C++ without copy
result = compute_et(temperature)
```

---

## Coverage Report

| Component | Tests Present | Coverage |
|-----------|---------------|----------|
| ET calculations | ✓ | 95% |
| Hydrology | ✓ | 88% |
| Crop water | ✓ | 92% |
| Groundwater | ✓ | 85% |
| Climate interpolation | ✓ | 90% |
| Radiation | ✓ | 93% |
| Soil water | ✓ | 87% |
| Reservoir | ✓ | 89% |
| Snow melt | ✓ | 82% |
| Optimization | ✓ | 75% |

---

## Integration Points

| Kernel | Scientific Model | Python Layer |
|--------|------------------|--------------|
| et_calculations | CANON-001, 002, 003, 005, 006, 007, 008 | `hydroma/scientific/et/` |
| hydrology | CANON-012 | `hydroma/scientific/hydrology/` |
| crop_water | CANON-004, 009, 010 | `hydroma/scientific/demand/` |
| groundwater | CANON-013 | `hydroma/scientific/groundwater/` |
| climate_interpolation | CANON-014, 015, 016, 017 | `hydroma/scientific/climate/` |
| radiation | CANON-001 input | `hydroma/scientific/meteorology/` |
| soil_water | CANON-010 | `hydroma/scientific/soil/` |
| reservoir | - | `hydroma/scientific/reservoir/` |
| snow_melt | - | `hydroma/scientific/hydrology/` |
| optimization | Decision layer | `services/decision/optimization/` |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, engine-services/INVENTORY.md*