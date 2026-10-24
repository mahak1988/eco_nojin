# Engine Gateway Contract

## Purpose
Define the interface contract for the Engine Gateway that manages the Python/C++ boundary.

## Scope
Covers all interactions between Python orchestration layer and C++ numerical kernels.

## Contract Terms

### 1. Supported Interfaces
The Engine Gateway MUST support all three interface mechanisms:

#### 1.1 ctypes (Primary)
```python
import ctypes
lib = ctypes.CDLL("libhydroma_kernels.so")
lib.compute_penman_monteith.restype = ctypes.c_double
lib.compute_penman_monteith.argtypes = [
    ctypes.c_double,  # temperature
    ctypes.c_double,  # humidity
    ctypes.c_double,  # wind_speed
    ctypes.c_double,  # radiation
]
```

#### 1.2 pybind11 (Complex Objects)
```cpp
// C++ binding code
PYBIND11_MODULE(hydroma_kernels, m) {
    m.def("compute_et_batch", &compute_et_batch, 
          "Compute ET for batch of parameters");
}
```

#### 1.3 Buffer Protocol (Arrays)
```python
# Zero-copy transfer
import numpy as np
from hydroma.cpp_bindings import et_kernel

# Array owns memory, passed without copy
temperature = np.asarray(data, dtype=np.float64)
result = et_kernel.compute_bulk(temperature)
```

### 2. Data Format Requirement
- All arrays: `numpy.float64` (IEEE 754 double)
- All units: SI units before C++ call
- Memory layout: C-contiguous for multi-dimensional

### 3. Error Translation
| C++ Error Code | Python Exception | Recovery |
|----------------|------------------|----------|
| CPP_SUCCESS | None | Continue |
| CPP_INVALID_INPUT | ValueError | Check input |
| CPP_OUT_OF_MEMORY | MemoryError | Retry or fail |
| CPP_COMPUTATION_ERROR | ComputationError | Log, retry |
| CPP_TIMEOUT | TimeoutError | Reduce workload |

### 4. Performance SLA
- Function call overhead: <1ms
- Zero-copy buffer transfer: <100μs
- Memory alignment: 64-byte boundary for SIMD

### 5. Security Requirements
- No pointer access from Python to C++
- Input validation at boundary
- Buffer overrun protection
- Stack overflow protection

### 6. Testing Contract
```bash
# Required tests
pytest tests/test_ctypes_boundary.py
pytest tests/test_buffer_protocol.py
pytest tests/test_pybind11_interface.py
./cpp_tests/test_integration  # Native C++ tests
```

### 7. Monitoring
- Function call latency logged
- Memory usage tracked
- Error rates aggregated
- Performance regressions detected

## Compliance Verification
Run: `python tools/validate_gateway_contract.py`

---
*Contract Version: 1.0.0 | Based on: ECO-01/11-CPP-PYTHON-BOUNDARY.md, ECO-01/10-HYDROMA-FORENSICS.md*
