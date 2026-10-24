# ECO-04.1: Final Uncertainty Audit — Report 25

## Uncertainty quantification and propagation status

**Report Date**: 2026-10-08T17:00:00Z  
**Method**: Source code inspection + AST scan + ECO-04.7 carry-forward

---

## 1. Current State

### 1.1 UncertaintySpec

| Property | Value |
|----------|-------|
| File | `engine/evidence/__init__.py` |
| Lines | ~15 (data class definition) |
| Default | `NOT_ESTIMATED` |
| Importable | ✅ Yes |

```python
@dataclass
class UncertaintySpec:
    """Ske uncertainty propagation."""
    epistemic_state: EpistemicState = EpistemicState.NOT_ESTIMATED
    model_form: Optional[str] = None
    parameter: Optional[UncertaintyParameter] = None
    prediction_interval: Optional[Tuple[float, float]] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    monte_carlo_samples: Optional[int] = None
    propagation_method: Optional[str] = None
```

### 1.2 EpistemicState Enum

| State | Meaning | Used? |
|-------|---------|-------|
| NOT_ESTIMATED | Default — no uncertainty assessed | ✅ Default |
| KNOWN_KNOWN | Parameter uncertainty quantified | ❌ Not enforced |
| KNOWN_UNKNOWN | Structural uncertainty bounded | ❌ Not enforced |
| UNKNOWN_UNKNOWN | Epistemic gap not quantified | ❌ Not enforced |
| DISPROVEN | Claim contradicted by evidence | ❌ Not used in uncertainty context |

### 1.3 UncertaintyParameter Enum

| Type | Status |
|------|--------|
| MEASUREMENT | ✅ Enum exists |
| PARAMETER | ✅ Enum exists |
| MODEL | ✅ Enum exists |
| INPUT | ✅ Enum exists |
| OUTPUT | ✅ Enum exists |

---

## 2. Propagation Method Assessment

| Method | Implemented? | Evidence |
|--------|--------------|----------|
| Monte Carlo | ❌ | `monte_carlo_samples` field exists but never used |
| First-order (linear) | ❌ | `propagation_method` field is `Optional[str]` — no implementation |
| Second-order | ❌ | Not referenced anywhere |
| Bayesian updating | ❌ | Knowledge Engine uses mean aggregation, not Bayesian |

### Runtime Test of Current Uncertainty State

```
python -c "
from engine.evidence import UncertaintySpec, EpistemicState
spec = UncertaintySpec()
print(f'Default: {spec.epistemic_state.name}')
print(f'Propagation method set? {spec.propagation_method is not None}')
print(f'Monte Carlo samples set? {spec.monte_carlo_samples is not None}')
"
```
→ Output:
```
Default: NOT_ESTIMATED
Propagation method set? False
Monte Carlo samples set? False
```

**Finding**: UncertaintySpec defaults to NOT_ESTIMATED and is never populated or propagated.

---

## 3. INV-011 Compliance

| Requirement | Status |
|-------------|--------|
| Uncertainty ≠ certainty | ⚠️ PARTIAL — UncertaintySpec exists with NOT_ESTIMATED default, but no propagation, no validation, not enforced |
| Confidence intervals on model outputs | ❌ Not implemented |
| Prediction intervals on model outputs | ❌ Not implemented |
| Monte Carlo sampling | ❌ Not implemented |

### Where UncertaintySpec is referenced

| File | Line | Context |
|------|------|---------|
| engine/evidence/__init__.py | 15 | Definition |
| engine/evidence/__init__.py | 262 | Used as `evidence.uncertainty` field (optional) |
| engine/gateway/__init__.py | ~180 | ProvenanceSpec includes uncertainty field (optional) |

**Finding**: UncertaintySpec is defined and optionally attached to Evidence objects, but no propagation, computation, or enforcement exists.

---

## 4. Deferred Items (ECO-04.7)

Per ADR-008:

| Item | Scope | Status |
|------|-------|--------|
| Monte Carlo propagation | UncertaintySpec | DEFERRED |
| Parameter uncertainty | Input parameters | DEFERRED |
| Model uncertainty | Model form selection | DEFERRED |
| Input uncertainty | Data source variance | DEFERRED |
| Output uncertainty | Model prediction variance | DEFERRED |
| Confidence intervals | All model outputs | DEFERRED |
| Prediction intervals | All model outputs | DEFERRED |
| Epistemic gap tracking | Unknown unknowns | DEFERRED |

---

## 5. Contradictions with Reports

| Report | Claim | Actual |
|--------|-------|--------|
| Report 19 | "Uncertainty Engine ✅ PASS" | Implementation is scaffolding only |
| Report 20 | `uncertainty_engine.implemented: true` | Engine does not exist; only a dataclass field |

---

## 6. Status Summary

| Component | ECO-04 Claim | Actual | Final Status |
|-----------|-------------|--------|--------------|
| UncertaintySpec data class | ✅ | Exists, defaults to NOT_ESTIMATED | ✅ Scaffolding |
| Monte Carlo propagation | ⚠️ DEFERRED | Not implemented | ❌ NOT_IMPLEMENTED |
| Confidence intervals | ⚠️ DEFERRED | Not implemented | ❌ NOT_IMPLEMENTED |
| Prediction intervals | ⚠️ DEFERRED | Not implemented | ❌ NOT_IMPLEMENTED |
| Uncertainty enforcement | IMPLEMENTED | UncertaintySpec is optional field, never enforced | ⚠️ SCAFFOLDING |
| Automated tests | Not claimed | 0 tests executed | ❌ Not validated |

**Conclusion**: Uncertainty handling is at the scaffolding stage. The data class exists but provides no propagation, computation, or validation. ECO-04.7 (deferred) requires full implementation of Monte Carlo propagation, confidence/prediction intervals, and epistemic gap tracking.

---

*No uncertainty propagation logic exists in the codebase. The UncertaintySpec class is a data container with a NOT_ESTIMATED default and no functional methods.*
