# ECO-04: Uncertainty Report — Report 08

## Uncertainty propagation implementation status

---

## 1. Current State

Per ECO-04.md §24: "Uncertainty باید first-class data باشد."

**Status**: NOT IMPLEMENTED

---

## 2. Uncertainty Requirements

Each output must specify one of:
- `uncertainty = known` (with metadata)
- `uncertainty = not_estimated` (explicitly not calculated)

Never: `uncertainty = 0` (without scientific justification)

Required fields:
| Field | Type | Implemented? |
|-------|------|-------------|
| uncertainty_type | Enum | ❌ |
| value | Float | ❌ |
| unit | String | ❌ |
| method | String | ❌ |
| confidence_level | Float | ❌ |
| distribution | String | ❌ |
| source | String | ❌ |
| propagation_method | String | ❌ |

---

## 3. Current Implementation

The Engine Gateway defines `UncertaintySpec` with:

```python
@dataclass
class UncertaintySpec:
    uncertainty_type: str = "NOT_ESTIMATED"
    value: float | None = None
    unit: str | None = None
    method: str | None = None
    confidence_level: float | None = None
```

This is a **placeholder** that defaults to `"NOT_ESTIMATED"`, which satisfies the requirement that uncertainty must be explicitly not estimated. However:
- No actual uncertainty propagation is implemented
- No confidence intervals are calculated
- No propagation methods exist

---

## 4. INV-011 Status

Per ECO-04.md §24: "absence of uncertainty != certainty"

| Criterion | Status |
|-----------|--------|
| Uncertainty field in outputs | ⚠️ Partial (gateway placeholder only) |
| Explicit "not_estimated" when unknown | ✅ YES |
| Propagation methods | ❌ NOT IMPLEMENTED |
| Confidence intervals | ❌ NOT IMPLEMENTED |
| Distribution tracking | ❌ NOT IMPLEMENTED |

---

## 5. Status

**Status**: PARTIALLY IMPLEMENTED (gateway placeholder) + DEFERRED_TO_ECO_04.7 (full propagation)

The gateway provides the scaffolding (`UncertaintySpec` with `NOT_ESTIMATED` default), but actual uncertainty propagation and confidence interval calculation is deferred to ECO-04.7.

---

*Report generated: 2026-10-08*
*Status: Scaffolding in gateway, propagation deferred to ECO-04.7*