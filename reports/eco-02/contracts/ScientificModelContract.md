# Scientific Model Contract

## Purpose
Define the interface contract for all scientific models in the HyDroMA system.

## Scope
Applies to all models implementing scientific computation, whether in C++ kernels or Python orchestration.

## Contract Terms

### 1. Model Identification
```json
{
  "model_id": "string (CANON-XXX format)",
  "name": "string",
  "version": "string (semantic versioning)",
  "maturity": "enum: VERIFIED | SCIENTIFICALLY_SUPPORTED | IMPLEMENTATION_VERIFIED | CODE_ONLY | STUB",
  "canonical_equation": "string (equation or reference)",
  "references": ["array of citations"]
}
```

### 2. Input Requirements
- All inputs must declare units (SI standard)
- Required inputs marked with `required: true`
- Optional inputs marked with `required: false`
- Default values documented

### 3. Output Specification
```json
{
  "output_name": "string",
  "units": "string (SI)",
  "type": "float | array | grid",
  "dimensions": ["optional dimension info"]
}
```

### 4. Validation Requirements
- Models must pass `test_validation.cpp` / `test_validation.py`
- Benchmarks against observational data required for VERIFIED status
- Cross-model validation documented

### 5. Boundary Compliance
- C++ models: Interface via ctypes, pybind11, or buffer protocol
- Python models: Must not import from `services/` (ECO-LEGACY-001)
- AI models: Must go through Evidence Engine

### 6. Provenance Requirements
All outputs must carry:
```json
{
  "source_model": "CANON-XXX",
  "timestamp": "ISO 8601",
  "parameters": {"dict of input parameters"},
  "units": "SI units used",
  "confidence": "float 0.0-1.0",
  "provenance_chain": ["list of upstream sources"]
}
```

### 7. Performance Requirements
- Defined runtime targets per operation
- Memory limits per kernel
- Batch processing support

### 8. Test Coverage
- Minimum 80% code coverage for C++ kernels
- All edge cases (NaN, Inf, boundary values) tested
- Integration tests with Evidence Engine

## Compliance Verification
Run: `python tools/validate_model_contract.py --model CANON-XXX`

## Violation Response
- VERIFIED → DOWNGRADE to SCIENTIFICALLY_SUPPORTED
- CORE → RECLASSIFY as LEGACY
- REPEAT violations → REMOVE

---
*Contract Version: 1.0.0 | Based on: ECO-01/02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, ECO-01/07-MODEL-QUALITY-MATRIX.md*
