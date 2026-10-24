# ECO-03: Uncertainty Contract — Report 09
## First-Class Uncertainty Specification

---

## Executive Summary

ECO-02 contracts define uncertainty as a requirement but ECO-03 verification finds **no uncertainty implementation exists in code**. Uncertainty is DESIGNED BUT NOT ENFORCED.

---

## 1. Uncertainty Type

| Type | Definition | ECO-02 Status | ECO-03 Code Status | Evidence |
|------|------------|---------------|-------------------|----------|
| Systematic | Bias from model structure or calibration | Required | NOT IMPLEMENTED | No uncertainty module exists |
| Random | Stochastic variability | Required | NOT IMPLEMENTED | Only random sampling in `latin_hypercube()` |
| Model Form | Structural uncertainty in model choice | Required | NOT IMPLEMENTED | No model ensemble comparison |
| Parameter | Uncertainty in input parameters | Required | NOT IMPLEMENTED | No parameter confidence intervals |

**Status**: NOT VERIFIED — Uncertainty types defined in contracts but not implemented.

---

## 2. Uncertainty Value & Confidence

### Current State
- No `uncertainty` field in any result type
- `ResultProvenance` in `engine/hydroma/provenance.py` does NOT include uncertainty
- No confidence scoring on model outputs

**Evidence**:
```python
# engine/hydroma/provenance.py (exists but minimal)
class ResultProvenance:
    MODEL_OUTPUT = "model_output"
    OBSERVATION = "observation"
    # No uncertainty field, no confidence field
```

**Status**: NOT VERIFIED

---

## 3. Confidence Interval

### Current State
- No confidence interval calculation
- No statistical uncertainty propagation

**Evidence**: Searching `engine/hydroma/` for "confidence" yields no results in computation code.

**Status**: NOT VERIFIED

---

## 4. Error Bounds

### Current State
- No error bound tracking
- C++ kernels return point estimates only

**Evidence**: `engine/cpp_core/src/climate.cpp` — `penman_monteith_et0()` returns single `double`, no error bounds.

**Status**: NOT VERIFIED

---

## 5. Source of Uncertainty

| Source | ECO-02 Requirement | ECO-03 Code Status | Evidence |
|--------|-------------------|-------------------|----------|
| Input data quality | Required | NOT IMPLEMENTED | No data quality metadata |
| Model selection | Required | NOT IMPLEMENTED | No model selection uncertainty |
| Parameter uncertainty | Required | NOT IMPLEMENTED | No parameter distributions |
| Numerical methods | Required | NOT IMPLEMENTED | No numerical error tracking |

**Status**: NOT VERIFIED

---

## 6. Propagation Method

### Current State
- No uncertainty propagation
- Monte Carlo sampling exists (`latin_hypercube()`, `monte_carlo_uniform()`) but used for sampling, NOT uncertainty propagation
- No first-order or second-order uncertainty methods

**Evidence**:
```python
# engine/hydroma/cpp_bridge/__init__.py
def _py_monte_carlo_uniform(n_samples, bounds, seed=None):
    """Uniform Monte Carlo sampling — for sampling, not uncertainty propagation."""
    rng = _np.random.default_rng(seed)
    lo = _np.asarray([b[0] for b in bounds], dtype=float)
    hi = _np.asarray([b[1] for b in bounds], dtype=float)
    return rng.uniform(lo, hi, size=(n_samples, len(bounds)))
```

**Status**: NOT VERIFIED — Sampling exists but uncertainty propagation does not.

---

## 7. Unknown Uncertainty

### ECO-02 Requirement
> "unknown uncertainty" must be represented

### ECO-03 Verification
**Status**: NOT VERIFIED

- No `UNKNOWN` uncertainty category in code
- No handling for "unknown unknowns"
- When uncertainty data is absent, code implicitly returns point estimate without warning

**Finding**: This violates INV-011: "Uncertainty absence is not certainty."

---

## 8. Uncertainty Categories (Reconciled)

| Category | Value | Meaning | ECO-03 Status |
|----------|-------|---------|---------------|
| `unknown` | None/NULL | No uncertainty data available | NOT HANDLED — treated as certainty |
| `not_measured` | explicit None | Uncertainty was not measured | NOT HANDLED |
| `not_modeled` | explicit None | Uncertainty was not modeled | NOT HANDLED |
| `low_confidence` | 0.0-0.3 | Low confidence in result | NOT HANDLED |
| `high_uncertainty` | 0.3-0.7 | High uncertainty band | NOT HANDLED |
| `high_confidence` | 0.7-1.0 | High confidence in result | NOT HANDLED |
| `validated` | 0.9+ | Validated against observations | NOT HANDLED |

---

## 9. Uncertainty Contract Specification (For ECO-04)

```python
# engine/uncertainty/__init__.py (TO BE IMPLEMENTED in ECO-04)

class UncertaintyType(Enum):
    SYSTEMATIC = "systematic"
    RANDOM = "random"
    MODEL_FORM = "model_form"
    PARAMETER = "parameter"
    UNKNOWN = "unknown"

class Uncertainty:
    """First-class uncertainty representation."""
    type: UncertaintyType
    value: float  # standard deviation or variance
    confidence: float  # 0.0 to 1.0
    confidence_interval: Tuple[float, float]  # [lower, upper]
    source: str  # what generated this uncertainty
    propagation_method: str  # "monte_carlo", "first_order", "analytical"
    
    @staticmethod
    def unknown() -> "Uncertainty":
        """Explicit representation of unknown uncertainty."""
        return Uncertainty(
            type=UncertaintyType.UNKNOWN,
            value=float('nan'),
            confidence=0.0,
            confidence_interval=(float('-inf'), float('inf')),
            source="undefined",
            propagation_method="undefined"
        )
```

---

## 10. Findings

1. **NOT VERIFIED**: Uncertainty is defined as a contract requirement but NO implementation exists in code.

2. **BLOCKING**: The absence of uncertainty data in current implementations is treated as certainty, violating INV-011.

3. **DESIGNED BUT NOT ENFORCED**: Monte Carlo sampling exists but is NOT used for uncertainty propagation.

4. **NOT VERIFIED**: No confidence intervals, error bounds, or confidence scores exist on any model output.

5. **BLOCKING**: All scientific model outputs lack uncertainty metadata — this must be addressed in ECO-04 before results can be trusted.

---

## 11. Uncertainty Invariants

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Uncertainty absence ≠ certainty | VIOLATED | All outputs implicitly certain |
| Uncertainty type must be explicit | NOT ENFORCED | No uncertainty type field |
| Confidence must be propagated | NOT ENFORCED | No confidence field |
| Unknown uncertainty must be representable | NOT ENFORCED | No UNKNOWN category |
| All uncertainty must be traceable | NOT ENFORCED | No uncertainty provenance |

---

*Report generated: 2026-10-08*
*Status: NOT VERIFIED — requires implementation in ECO-04*