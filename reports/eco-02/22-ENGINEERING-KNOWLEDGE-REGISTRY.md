# ECO-02: Engineering Knowledge Registry

## Engineering Methods and Implementation Knowledge (KT-002)

---

## Source Evidence
- ECO-01/03-ENGINEERING-KNOWLEDGE-REGISTRY.md
- ECO-01/11-CPP-PYTHON-BOUNDARY.md
- reports/engine-services/INVENTORY.md

---

## Numerical Methods

| Method | Application | Implementation |
|--------|-------------|----------------|
| Runge-Kutta (RK4) | ODE integration | `hydrology.cpp` |
| Finite Difference | PDE solving | `groundwater.cpp` |
| Finite Volume | Flow routing | `hydrology.cpp` |
| Newton-Raphson | Nonlinear equation solving | `soil_water.cpp` |
| Brent's Method | Root finding | `optimization.cpp` |
| LU Decomposition | Matrix solving | `hydrology.cpp` |
| FFT (Fast Fourier Transform) | Signal processing | `climate_interpolation.cpp` |
| Kriging | Spatial interpolation | `climate_interpolation.cpp` |
| Inverse Distance Weighting | Simple interpolation | `climate_interpolation.cpp` |

---

## Software Engineering Patterns

| Pattern | Usage | Component |
|---------|-------|-----------|
| Adapter | C++/Python boundary | Engine Gateway |
| Facade | Scientific model access | Hydroma Engine |
| Strategy | Multiple ET methods | ET module |
| Template Method | Model integration | Evidence Engine |
| Observer | Provenance tracking | Evidence Engine |
| Factory | Model instantiation | Scientific Engine |
| Chain of Responsibility | Evidence flow | Evidence Engine |

---

## Data Structures

### Core Data Types
| Type | Description | Used In |
|------|-------------|---------|
| Grid2D | 2D spatial grid | Climate, ET |
| TimeSeries | Temporal data | All models |
| SparseMatrix | Efficiency | MODFLOW |
| Vector | Array operations | C++ kernels |
| HashTable | Fast lookup | Daneshyar |
| Graph | Model dependencies | Dependency graph |
| RingBuffer | Circular buffer | Reservoir simulation |

### C++ Data Structures
| File | Structure | Purpose |
|------|-----------|---------|
| `hydrology.h` | `FlowNetwork` | River network |
| `groundwater.h` | `AquiferGrid` | 3D groundwater grid |
| `crop_water.h` | `CropParameters` | Crop coefficient storage |
| `climate_interpolation.h` | `StationNetwork` | Weather station data |
| `optimization.h` | `ObjectiveFunction` | Multi-objective optimization |

---

## API Design

### Python API (Hydroma Engine)
```python
class HydromaEngine:
    def compute_et(self, method: str, inputs: dict) -> float:
        """Compute ET using specified method."""
        pass
    
    def run_hydrology(self, params: dict, timespan: str) -> TimeSeries:
        """Run hydrology simulation."""
        pass
    
    def optimize_irrigation(self, constraints: dict) -> dict:
        """Optimize irrigation schedule."""
        pass
```

### C++ API (Kernel Interface)
```cpp
// et_calculations.h
double compute_penman_monteith(
    double temp, double humidity, 
    double wind, double radiation
);

// hydrology.h
int streamflow_routing(
    double* inflow, int n,
    double* outflow,
    const RoutingParams& params
);
```

---

## Testing Framework

### C++ Tests (21 files)
| Framework | Purpose |
|-----------|---------|
| Google Test | Unit testing |
| Google Mock | Interface mocking |
| Catch2 | Alternative test framework |

### Python Tests
| Framework | Purpose |
|-----------|---------|
| pytest | Unit and integration tests |
| hypothesis | Property-based testing |
| unittest.mock | Mock objects |

---

## Performance Engineering

### Optimization Strategies
| Strategy | Application | Expected Gain |
|----------|-------------|---------------|
| Vectorization | Numerical loops | 4-10x |
| Memory pooling | Frequent allocations | 2-3x |
| Parallel processing | Independent calculations | N-core linear |
| Zero-copy buffers | C++/Python interface | Eliminates copy |
| Lazy evaluation | Evidence chain | Reduces computation |

### Benchmark Targets
| Operation | Current | Target |
|-----------|---------|--------|
| ET computation (1M points) | 45s | <10s |
| Streamflow routing | 32s | <5s |
| Climate interpolation | 28s | <8s |
| Evidence retrieval | 150ms | <50ms |

---

## Build System

| Component | Build Tool | Dependencies |
|-----------|------------|--------------|
| C++ kernels | CMake | Eigen3, Armadillo |
| Python | setuptools | numpy, scipy |
| C++/Python | pybind11 | boost::python alternative |
| Tests | pytest, gtest | Coverage tools |
| CI/CD | GitHub Actions | All components |

---

## Monitoring and Observability

### Key Metrics
| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| C++ kernel latency | C++ timers | >100ms/error |
| Evidence chain latency | Evidence Engine | >1s/warning |
| Memory usage | System metrics | >80%/alert |
| Test coverage | Code coverage | <80%/block |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/03, reports/engine-services/INVENTORY.md*