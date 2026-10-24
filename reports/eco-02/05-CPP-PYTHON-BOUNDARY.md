# ECO-02: C++/Python Boundary Architecture

## Python Orchestrates, C++ Computes

---

## Source Evidence
- ECO-01/11-CPP-PYTHON-BOUNDARY.md
- ECO-01/10-HYDROMA-FORENSICS.md (Layer 2: Numerical Computation)
- reports/engine-services/INVENTORY.md (10 .cpp, 10 .h, 21 test files)

---

## Boundary Protocol

### Communication Mechanism
1. **ctypes** for function-level binding
2. **pybind11** for object-oriented interface (optional wrappers)
3. **Buffer Protocol** for zero-copy array transfer

### Data Flow
```
Python (Hydroma Engine)
    ↓ (ctypes call)
C++ (Numerical Kernel)
    ↓ (buffer protocol)
Python (receive results)
    ↓ (provenance tag)
Evidence Engine
```

### Directory Structure Boundary
```
D:\HyDroMA\
├── engine/          # Python orchestration (Layer 1: Scientific Computation)
├── services/        # Domain services (MUST NOT import from engine/)
├── c++/             # C++ numerical kernels (Layer 2: Numerical Computation)
└── reports/
```

### Critical Rule
**ECO-LEGACY-001**: `services/` MUST NOT import from `engine/`. The correct flow is:
1. Services call Domain Services (Hydroma)
2. Domain Services call Engine Gateway
3. Engine Gateway calls Hydroma Scientific Engine
4. Scientific Engine calls C++ kernels via ctypes/buffer

---

## C++ Kernel Inventory

| Component | File | Tests |
|-----------|------|-------|
| Core numerical functions | `cpp_core/src/*.cpp` | `cpp_core/tests/*.cpp` |
| Header interfaces | `cpp_core/include/*.h` | - |
| Python bindings | `cpp_core/bindings/*.py` | `cpp_core/tests/test_*.py` |

**Count**: 10 source files, 10 header files, 21 test files

---

## Performance Considerations

### Buffer Protocol Usage
- NumPy arrays allocated in Python
- Passed to C++ via `numpy::array_t<double>` (pybind11)
- Zero-copy: C++ operates directly on Python memory
- No serialization/deserialization overhead

### ctypes Fallback
- Functions exposed as `extern "C"`
- `ctypes.CDLL` loads shared library
- Manual struct definitions for parameter passing

---

## Error Handling Strategy

```python
# Python side
try:
    result = cpp_kernel.compute_et(params)
except CPPError as e:
    log_error(e)
    raise ScientificComputationError(f"C++ kernel failed: {e}")
```

---

## Testing Requirements

1. **C++ unit tests** (21 test files exist)
2. **Python integration tests** via ctypes calls
3. **Buffer protocol verification** (zero-copy confirmed)
4. **Edge case propagation** (NaN, Inf, boundary values)

---

*Generated: 2026-10-08*