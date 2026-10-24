# Validation Evidence — ROTHTC_TEMP_FACTOR

**Model:** `ROTHTC_TEMP_FACTOR` — RothC Temperature Rate Modifier (registry version `1.0.0`)
**Cluster:** soil organic carbon turnover
**Gateway route:** `engine/gateway/model_dispatcher.py::_rothc_gateway_out`
**Implementation:** `engine/hydroma/simulation/runners/rothc_runner.py::temp_factor`
**Model card:** `engine/models/cards/ROTHC_TEMP_FACTOR_temperature_rate_modifier.md`
**Re-verified by:** `engine/validation/test_validation_records.py`

---

## 1. Published reference

**Citation.** Coleman, K., Prout, J.M. & Milne, A.E., *RothC — A Model for the
Turnover of Carbon in Soil*, Rothamsted Research, section 1.6.1, equation (1) —
the documentation of RothC-26.3, the calibration on which the RothC model is run:

```
RM_Tmp = 47.91 / (1 + e^(106.06 / (T + 18.27)))
```

with `T` the average monthly air temperature in degrees Celsius. The official
Fortran, Python and R releases of RothC hard-code the same triple
(`47.91`, `106.06`, `18.27`), and the official code additionally hard-zeros the
modifier below -5 C (`IF (TEMP .LT. -5.0) RM_TMP = 0.0`), which the
implementation reproduces. `47.91` is the value that normalises the modifier to
exactly 1.0 at T = 9.291 C, the Rothamsted mean annual temperature marked on
Figure 2 of the model description; the curve is monotonically increasing with no
optimum and no supra-optimal decline, so the factor legitimately exceeds 1.0 and
multiplies the compartment rate constant k directly.

**How the reference values below were obtained.** The reference column is an
independent evaluation of equation (1) and the official low-temperature guard,
written out in the test module from the published equation. No engine module is
consulted.

**Reference-source note.** The implementation's module-level constants
(`TEMP_FACTOR_NUMERATOR`, `TEMP_FACTOR_A`, `TEMP_FACTOR_B`,
`TEMP_FACTOR_ZERO_BELOW_C`) carry the same citation and record the PDF
extraction artefacts (`47.9`, `106.27/18.06`, a `2C` numerator) that were
considered and rejected. This record's test re-derives the equation from those
four published numbers rather than importing them, so a change to the constants
themselves would be caught.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Mean monthly temperature | `temperature` (T) | °C | −6 – 30 |

Domain of the published equation: all of −5 C and above. Below −5 C the official
code zeros the modifier as a numerical guard (the curve is already about 0.016 at
−5 C), and the model reproduces that guard; case 1 (−6 C) pins it. The remaining
cases are the published tabulated check points: −5, 0, 5, 9.291 (the
normalisation), 10, 20 and 30 C.

---

## 3. Tolerance

`tolerance_absolute = 1e-12` (dimensionless rate modifier).

**Basis.** Equation (1) is a closed form evaluated in double precision and the
model rounds nothing. The probe that produced this record measured `+0.000e+00`
bit-for-bit on every case, including the −6 C guard.
`engine/strict_tests/test_s20_simulation_validation.py::TestRothcSocLaws`
already pins the same equation at `abs=2e-3` for five published tabulated points
and at `abs=2e-3` for the 9.291 C normalisation; here it is pinned across all
eight with an explicitly independent evaluation.

---

## 4. Comparison table — model output vs reference output

| # | T (deg C) | Model output `value` | Reference RM_Tmp | Δ | Verdict |
|---|---|---|---|---|---|
| 1 | −6 | 0.0 | 0.0 (official guard below −5 C) | 0.000e+00 | match |
| 2 | −5 | 0.01618811582303663 | 0.01618811582303663 | 0.000e+00 | match |
| 3 | 0 | 0.143872428330698 | 0.143872428330698 | 0.000e+00 | match |
| 4 | 5 | 0.4971288617505745 | 0.4971288617505745 | 0.000e+00 | match |
| 5 | 9.291 | 1.0000387619991056 | 1.0000387619991056 | 0.000e+00 | match |
| 6 | 10 | 1.0990400705164 | 1.0990400705164 | 0.000e+00 | match |
| 7 | 20 | 2.82149253049831 | 2.82149253049831 | 0.000e+00 | match |
| 8 | 30 | 4.791002710952089 | 4.791002710952089 | 0.000e+00 | match |

Cases 2, 3, 6, 7 and 8 reproduce the published tabulated values
`0.016`, `0.144`, `1.099`, `2.822` and `4.791` to the three decimals the RothC
documentation prints them to. Case 5 confirms the normalisation: at the Rothamsted
mean annual temperature the modifier is 1.000, i.e. the site at which the model
was calibrated is the site at which the modifier is unity — which is exactly what
the implementation's docstring claims and what `engine/strict_tests/
test_s20_rothc_soc_model.py` asserts at `abs=2e-3` with the same 9.291 input.

---

## 5. Uncertainty statement

This is **exact-method conformance** to equation (1): it establishes that the
engine evaluates the published RothC-26.3 temperature rate modifier to
floating-point round-off over the compared range, and that it reproduces the
official low-temperature guard the equation itself omits.

The temperature modifier is one of four rate modifiers in RothC (temperature,
moisture, plant-retention and plant-cover). Its uncertainty is not separable in
the model: all four multiply the compartment rate constants jointly, so a
temperature-driven change in the modelled carbon turnover lands as the product of
the temperature modifier and whatever the moisture and cover modifiers happen to
be. The comparison here says nothing about the full model steady state, the
initial pool split `IOM = 0.049 * SOC^1.139`, the clay-modifier equations, or
the decomposition rates themselves.

The published equation is a fit over a limited range of the global climate
(roughly −10 to 40 C). Extrapolating the exponential outside that range gives
values the calibration cannot support; the guard below −5 C prevents the
worst of that but does not bound the top, where the curve is still climbing at
30 C.

---

## 6. Limitations

1. **Only the temperature modifier is validated.** The other three RothC rate
   modifiers, the pool rates and the steady-state behaviour are separate claims;
   `ROTHC_STEADY_STATE` and `ROTHC_COMPACTION` remain unvalidated.
2. **The −5 C guard is not in the published equation.** It is in the official
   code. This record credits the conformance to both, and says which is which.
3. **The exponent `106.06 / (T + 18.27)` is undefined at T = −18.27 C**, where
   the denominator crosses zero. The guard below −5 C means the model never
   evaluates it, so the model cannot fail there — but the equation is undefined
   at that temperature and this record does not assert a value for it.
4. **No measured carbon turnover is compared.** `VALIDATED_METHOD` conformance to
   the published modifier, not a validation of the RothC model.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "ROTHTC_TEMP_FACTOR",
  "model_name": "RothC Temperature Rate Modifier",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_rothc_gateway_out",
  "reference": {
    "citation": "Coleman, K., Prout, J.M. & Milne, A.E., RothC - A Model for the Turnover of Carbon in Soil, Rothamsted Research, section 1.6.1, equation (1) (RothC-26.3); low-temperature guard from the official Fortran, Python and R releases.",
    "equation": "rm_tmp = 47.91 / (1 + exp(106.06 / (T + 18.27))) for T >= -5 C, else 0.0"
  },
  "input_range": {
    "temperature_c": [-6.0, 30.0]
  },
  "output_key": "value",
  "tolerance": {
    "absolute": 1e-12,
    "basis": "a closed form evaluated in double precision with no rounding of the reported modifier"
  },
  "cases": [
    {
      "name": "below_the_official_guard",
      "inputs": {"temperature": -6.0},
      "reference": 0.0,
      "recorded": 0.0,
      "verdict": "match"
    },
    {
      "name": "published_check_point_at_the_guard",
      "inputs": {"temperature": -5.0},
      "reference": 0.01618811582303663,
      "recorded": 0.01618811582303663,
      "verdict": "match"
    },
    {
      "name": "published_check_point_freezing",
      "inputs": {"temperature": 0.0},
      "reference": 0.143872428330698,
      "recorded": 0.143872428330698,
      "verdict": "match"
    },
    {
      "name": "published_check_point_spring",
      "inputs": {"temperature": 5.0},
      "reference": 0.4971288617505745,
      "recorded": 0.4971288617505745,
      "verdict": "match"
    },
    {
      "name": "rothamsted_normalisation_point",
      "inputs": {"temperature": 9.291},
      "reference": 1.0000387619991056,
      "recorded": 1.0000387619991056,
      "verdict": "match"
    },
    {
      "name": "published_check_point_ten_celsius",
      "inputs": {"temperature": 10.0},
      "reference": 1.0990400705164,
      "recorded": 1.0990400705164,
      "verdict": "match"
    },
    {
      "name": "published_check_point_twenty_celsius",
      "inputs": {"temperature": 20.0},
      "reference": 2.82149253049831,
      "recorded": 2.82149253049831,
      "verdict": "match"
    },
    {
      "name": "published_check_point_thirty_celsius",
      "inputs": {"temperature": 30.0},
      "reference": 4.791002710952089,
      "recorded": 4.791002710952089,
      "verdict": "match"
    }
  ],
  "validation_status": "validated",
  "status_vocabulary_label": "VALIDATED_METHOD",
  "uncertainty": "Exact-method conformance to RothC-26.3 equation (1) and the official low-temperature guard to floating-point round-off. The modifier is one of four joint rate modifiers, so its effect on modelled carbon turnover is not separable from the others.",
  "limitations": [
    "Only the temperature modifier is validated; the other RothC rate modifiers, pool rates and steady state are not.",
    "The -5 C guard is in the official code, not in the published equation.",
    "The exponent is undefined at T = -18.27 C, which the guard prevents the model reaching.",
    "No measured carbon turnover is compared."
  ]
}
```
