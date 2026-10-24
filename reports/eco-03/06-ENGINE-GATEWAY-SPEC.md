# ECO-03: Engine Gateway Specification — Report 06
## Engine Gateway Contract Specification

---

## Executive Summary

The ECO-02/contracts/EngineGatewayContract.md defines the gateway interface at a high level. ECO-03 verifies the actual state and provides a detailed, implementation-ready specification.

**Status**: DESIGNED BUT NOT ENFORCED — No EngineGateway implementation exists in source code.

---

## 1. Request Validation

### Input
- HTTP request or internal API call
- Must include: `model_id`, `parameters`, `units`, `caller_metadata`

### Output
- ValidatedRequest object or ValidationError
- Includes: `normalized_model_id`, `normalized_parameters`, `unit_conversions_applied`

### Owner
- To be implemented in ECO-04 as `engine/gateway/validator.py`

### Dependencies
- Scientific Model Registry (CANON-XXX lookup)
- Unit conversion tables (UNIFORMAT)

### Failure Modes
| Mode | Response |
|------|----------|
| Unknown model_id | 404 Not Found |
| Invalid parameter | 400 Bad Request |
| Unit mismatch | 400 Bad Request + conversion hint |
| Missing required field | 400 Bad Request |
| Caller not authorized | 403 Forbidden |

### Test Requirements
- Test with all 22 CANON-XXX model IDs
- Test with SI and non-SI units
- Test with missing and invalid parameters
- Test with boundary values (NaN, Inf, negative values)

---

## 2. Model Selection

### Input
- `model_id` (CANON-XXX format)
- `model_version` (optional, semver)
- `maturity_preference` (enum: VERIFIED_ONLY, ALLOW_STABLE, ALLOW_EXPERIMENTAL)

### Output
- SelectedImplementation object containing:
  - `backend`: "cpp" or "python"
  - `function_path`: importable function reference
  - `fallback_path`: fallback function reference
  - `performance_profile`: expected runtime
  - `uncertainty_bounds`: model uncertainty metadata

### Owner
- `engine/gateway/model_selector.py` (to be implemented in ECO-04)

### Dependencies
- Scientific Model Registry contract
- C++/Python boundary protocol (cpp_bridge module)

### Failure Modes
| Mode | Response |
|------|----------|
| Model not in registry | 404 Not Found |
| Requested version not available | 404 Not Found |
| Model requires SCIENTIFIC_REVIEW | 403 Forbidden |
| Backend unavailable | Fallback to Python implementation |
| Model deprecated | Warning + redirect to replacement |

### Test Requirements
- Test selection for VERIFIED models only
- Test fallback when C++ unavailable
- Test version pinning
- Test deprecation redirect

---

## 3. Unit Normalization

### Input
- Parameters with declared units (any valid unit string)
- Model requires SI units

### Output
- Parameters converted to SI
- `conversion_log`: list of conversions applied
- `original_units`: preserved for provenance

### Owner
- `engine/gateway/units.py` (to be implemented in ECO-04)

### Dependencies
- UNIFORMAT unit definitions (ADR-005)
- `pint` or custom unit library

### Conversion Boundary
All conversions happen at: `engine/gateway/units.py:convert(value, from_unit, to_unit)`

### Failure Modes
| Mode | Response |
|------|----------|
| Unknown unit | 422 Unprocessable Entity |
| Temperature: C vs K vs F | Auto-convert, log in conversion_log |
| Pressure: kPa vs Pa vs hPa | Auto-convert |
| Time: s vs day vs hour | Auto-convert |
| Area: m² vs km² vs ha | Auto-convert |
| Volume: m³ vs L vs L/s | Auto-convert |
| Water depth: mm vs m | Auto-convert |
| Soil EC: dS/m vs mS/cm | Auto-convert |
| Coordinate: WGS84 vs local | Reproject |

### Test Requirements
- Test all SI conversions
- Test non-SI input acceptance
- Test invalid unit rejection
- Test temperature convention (C/K/F)
- Test compound unit conversions (e.g., mm/day → m/s)

---

## 4. Parameter Validation

### Input
- Validated parameters with constraints
- Model parameter schema (from CANON-XXX contract)

### Output
- ValidatedParameters object or ConstraintError
- Includes: `validated_values`, `constraint_violations`

### Owner
- `engine/gateway/validator.py:validate_parameters()`

### Dependencies
- Scientific Model Contract (parameter schema)

### Failure Modes
| Mode | Response |
|------|----------|
| Parameter out of range | 422 Unprocessable Entity |
| Constraint violation | 422 Unprocessable Entity |
| NaN or Inf input | 422 Unprocessable Entity |
| Missing required parameter | 400 Bad Request |

### Test Requirements
- Test boundary conditions (min, max, epsilon)
- Test NaN and Inf handling
- Test constraint violation reporting

---

## 5. Execution

### Input
- Validated request with model_id, parameters, backend selection

### Output
- Raw computation result (numpy array or scalar)
- `execution_metadata`: timing, backend used, memory usage

### Owner
- Python orchestrator: `engine/hydroma/cpp_bridge/__init__.py`
- C++ kernels: `engine/cpp_core/src/`

### Dependencies
- C++ compiled extension (`hydroma_core.pyd`)
- Python fallback implementations

### Failure Modes
| Mode | Response |
|------|----------|
| C++ crash | Fallback to Python implementation |
| Memory error | 503 Service Unavailable |
| Timeout | 504 Gateway Timeout |
| NaN in output | Flag as uncertain, propagate |
| Division by zero | Return 0 or NaN with warning |

### Test Requirements
- Test C++ execution path
- Test Python fallback path
- Test parity between C++ and Python results
- Test error propagation

---

## 6. Uncertainty Propagation

### Input
- Validated parameters with optional uncertainty values
- Model uncertainty metadata from registry

### Output
- Result with uncertainty bounds
- `uncertainty_type`: systematic, random, model_form, parameter
- `confidence_interval`: [lower, upper]
- `confidence_level`: 0.0-1.0

### Owner
- `engine/gateway/uncertainty.py` (to be implemented in ECO-04)

### Dependencies
- Scientific Model Contract (uncertainty schema)
- Uncertainty Contract (ECO-03 §09)

### Failure Modes
| Mode | Response |
|------|----------|
| No uncertainty data | Propagate with warning: "absence of uncertainty data ≠ certainty" |
| Invalid confidence value | 422 Unprocessable Entity |
| Propagation method undefined | Use model default from registry |

### Test Requirements
- Test uncertainty propagation for VERIFIED models
- Test confidence interval calculation
- Test "unknown" uncertainty handling

---

## 7. Provenance Capture

### Input
- Validated request
- Execution metadata
- Caller identity (if available)

### Output
- Provenance tag:
```json
{
  "source_model": "CANON-XXX",
  "model_version": "1.0.0",
  "execution_id": "uuid",
  "caller": "agent_or_service_id",
  "input_parameters": {"param": "value", "unit": "unit"},
  "computation_time_ms": 125,
  "backend": "cpp|python",
  "confidence": 0.92,
  "timestamp": "ISO-8601"
}
```

### Owner
- `engine/hydroma/provenance.py` (exists but minimal)

### Dependencies
- Evidence Engine (for storage)

### Failure Modes
| Mode | Response |
|------|----------|
| Provenance capture fails | Log error, computation may proceed without provenance (WARNING) |
| Storage failure | Log, retry, then fail computation |

### Test Requirements
- Test provenance tag generation
- Test provenance tag immutability
- Test provenance chain integrity

---

## 8. Result Normalization

### Input
- Raw computation result
- Provenance tag

### Output
- NormalizedResult object:
```json
{
  "model_id": "CANON-XXX",
  "timestamp": "ISO-8601",
  "values": {...},
  "units": "SI units",
  "provenance": {...},
  "uncertainty": {...},
  "epistemic_status": "MODEL_OUTPUT",
  "trust_level": "HIGH|MEDIUM|LOW"
}
```

### Owner
- `engine/gateway/normalizer.py` (to be implemented in ECO-04)

### Dependencies
- Evidence Engine contract
- Model maturity classification

### Failure Modes
| Mode | Response |
|------|----------|
| Invalid output format | 500 Internal Error |
| Missing provenance | Reject, require provenance |

### Test Requirements
- Test output format compliance
- Test trust level assignment based on model maturity
- Test epistemic status tagging

---

## 9. Error Normalization

### Input
- Any error from execution, validation, or provenance

### Output
- Standardized error response:
```json
{
  "error_code": "string",
  "message": "human-readable",
  "model_id": "CANON-XXX",
  "error_type": "VALIDATION|COMPUTATION|SYSTEM|UNKNOWN",
  "details": {...}
}
```

### Owner
- `engine/gateway/error_handler.py` (to be implemented in ECO-04)

### Failure Modes
| Mode | Response |
|------|----------|
| Unknown error type | Wrap as UNKNOWN |
| Security-sensitive info leak | Strip details, log internally |

### Test Requirements
- Test each error type produces correct response
- Test no sensitive info in error response

---

## 10. Engine Gateway Boundary Enforcement

**Critical Finding**: The Engine Gateway exists as a contract (ECO-02/contracts/EngineGatewayContract.md) but has NO implementation. Services bypass it by importing engine modules directly.

**Verification**: 
- ECO-02/EngineGatewayContract.md defines the contract at `reports/eco-02/contracts/EngineGatewayContract.md`
- No gateway module exists in codebase
- Services import engine directly: `services/models/registry.py:22`, `services/validation/formula_checks.py:22`

**Status**: DESIGNED BUT NOT ENFORCED

---

## 11. Implementation Status Summary

| Component | ECO-02 Status | ECO-03 Status | Evidence |
|-----------|---------------|---------------|----------|
| Request validation | DEFINED | DESIGNED BUT NOT ENFORCED | No gateway module exists |
| Model selection | DEFINED | DESIGNED BUT NOT ENFORCED | No canonical model contract enforcement |
| Unit normalization | DEFINED | DESIGNED BUT NOT ENFORCED | UNIFORMAT defined, no runtime enforcement |
| Parameter validation | DEFINED | DESIGNED BUT NOT ENFORCED | No schema validation at runtime |
| Execution | PARTIAL | VERIFIED (partial) | cpp_bridge exists with 56 functions, Python fallbacks |
| Uncertainty propagation | DEFINED | NOT VERIFIED | No uncertainty module exists |
| Provenance capture | PARTIAL | VERIFIED (partial) | `engine/hydroma/provenance.py` exists but minimal |
| Result normalization | DEFINED | NOT VERIFIED | No normalizer module exists |
| Error normalization | DEFINED | NOT VERIFIED | No error handler exists |
| Business logic prevention | DEFINED | DESIGNED BUT NOT ENFORCED | Gateway must not contain business logic — no enforcement |

**Engine Gateway MUST NOT contain business logic**:
- Status: DESIGNED (documented constraint) but NOT ENFORCED
- Evidence: No gateway exists to contain any logic, let alone business logic

---

*Report generated: 2026-10-08*
*Status: DESIGNED BUT NOT ENFORCED*