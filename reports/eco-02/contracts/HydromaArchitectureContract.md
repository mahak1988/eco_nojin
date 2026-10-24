# Hydroma Architecture Contract

## Purpose
Define the boundary contract for the Hydroma Scientific Engine (4-layer architecture).

## Scope
Covers the scientific computation layers from C++ kernels to Evidence Engine integration.

## Contract Terms

### 1. Layer Structure (Hydroma 4-Layer Model)
Based on ECO-01/10-HYDROMA-FORENSICS.md:

| Layer | Name | Interface | Data Flow |
|-------|------|-----------|-----------|
| L1 | Scientific Computation | Python API | Algorithms |
| L2 | Numerical Computation | C++ kernels | High-performance numerics |
| L3 | Integration | Engine Gateway | Model coupling |
| L4 | Provenance & Output | Evidence Engine | Audit trail |

### 2. Data Interfaces

#### L1 → L2 Interface (Python to C++)
```python
# ctypes binding contract
def compute_et(method: str, params: numpy.ndarray) -> numpy.ndarray:
    """
    All numerical computation delegated to C++
    - Input: numpy array (owns memory, SI units)
    - Output: numpy array (new allocation or zero-copy)
    - Throws: CPPComputationError on failure
    """
    pass
```

#### L2 → L3 Interface (C++ to Python)
- Buffer protocol for zero-copy
- Error codes translated to Python exceptions
- Performance metrics logged

#### L3 → L4 Interface (Integration to Evidence)
All outputs must include provenance tags:
```python
evidence_tag = {
    "source": "CANON-XXX",
    "model_version": "v1.0.0",
    "computation_time_ms": 125,
    "units": "mm/day",
    "trust_level": "HIGH",
    "provenance_chain": [...],
    "validation_status": "verified"
}
```

### 3. Performance Contract
- Numerical kernels: <10s for 1M element computation
- Memory: No leaks across kernel boundary
- Scalability: Linear scaling with cores for batch operations

### 4. Error Handling
```python
class HydromaComputationError(Exception):
    """Base exception for all computation errors"""
    def __init__(self, message, evidence_tag=None, recovery_suggestion=None):
        ...

class CPPError(HydromaComputationError):
    """Error from C++ kernel"""
    def __init__(self, error_code, message):
        ...
```

### 5. Testing Requirements
- Unit tests for each layer
- Integration tests across layers
- Performance benchmarks
- Memory leak detection

### 6. CI/CD Contract
- All layers tested in CI pipeline
- Performance regressions block merge
- Memory leaks fail build
- Evidence tags validated

## Compliance Verification
Run: `python tools/validate_hydroma_contract.py`

---
*Contract Version: 1.0.0 | Based on: ECO-01/10-HYDROMA-FORENSICS.md, ECO-01/11-CPP-PYTHON-BOUNDARY.md*
