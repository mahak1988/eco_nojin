# Validation Evidence — RUSLE_LS

**Model:** `RUSLE_LS` — Topographic LS Factor (registry version `1.0.0`)
**Cluster:** erosion / hydrology
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_canon_007_rusle_ls`
**Implementation:** native kernel `engine/cpp_core/src/erosion.cpp::ls_factor`, dispatched
through `engine/hydroma/cpp_bridge.py` (Python twin `engine/cpp_core/src/erosion_python.cpp`)
**Model card:** `engine/models/cards/RUSLE_LS_topographic_factor.md`
**Re-verified by:** `engine/validation/test_validation_records.py`

---

## 1. Published reference

**Citation.** Renard, K.G., Foster, G.R., Weesies, G.A., McCool, D.K. &
Yoder, D.C. (eds.), *Predicting Soil Erosion by Water: A Guide to Conservation
Planning with the Revised Universal Soil Loss Equation (RUSLE)*, USDA Agriculture
Handbook 703, 1997, Chapter 4 ("Topographic factor LS"), equations 4-1 to 4-4:

```
theta   = atan(slope / 100)
beta    = (sin(theta) / 0.0896) / (3 * sin(theta)^0.8 + 0.56)
m       = beta / (1 + beta)
L       = (lambda / 22.13)^m
S       = 10.8 * sin(theta) + 0.03     for slope <  9 %
S       = 16.8 * sin(theta) - 0.50     for slope >= 9 %
LS      = L * S
```

`lambda` is the slope length in metres (22.13 m is the standard RUSLE plot
length), the slope is entered as a percentage, and the slope-steepness branch is
the McCool et al. (1987) form that AH-703 adopts. The constant 0.0896 is
`sin(5.14 deg)`, the slope below 5.14 % being the one on which the slope-length
exponent stops falling.

**How the reference values below were obtained.** The reference column is an
independent evaluation of the AH-703 equations, written out in the test module
from the equations above (four arithmetic expressions and one branch). No engine
module is consulted, so a change to the C++ kernel, the bridge or the route
cannot move the reference number.

**Reference-source note.** CANON-007's card, `engine/models/cards/CANON-007_rusle_ls_factor.md`,
records that AH-703 supplies no worked numerical example for the LS factor itself
(the handbook's chapter 4 tables are charts) and that the card therefore stops at
"the implementation reproduces the stated algebra". This record supplies what the
card left open: the stated algebra is evaluated independently here, so the LS
factor now has a reproducible external anchor. No *published numeric table value*
for LS is claimed anywhere in this file — only agreement with the published
equations.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Slope length | `slope_length_m` (lambda) | m | 10 – 200 |
| Slope steepness | `slope_percent` | % | 1 – 25 |

Domain constraints: `slope_length_m > 0` and `slope_percent >= 0`. Both sides of
the published slope-steepness branch are covered (case 2 is below 9 %, cases 1,
3, 5 are at or above 9 %), as is case 4 at 5 % and case 6 at 1 %.

---

## 3. Tolerance

`tolerance_absolute = 1e-9`.

**Basis.** The published equations are a closed form evaluated in double
precision, and the model is that same closed form, so the honest expectation is
agreement to floating-point round-off. The probe that produced this record
measured `+0.000e+00` on every case, and the native kernel and the Python twin
agree to `rel=1e-9` in `engine/tests/test_card_code_agreement.py::TestCanon007RusleLs`.
The tolerance is not loosened to accommodate a rounding step: unlike `SOIL_SAR`
and `SOIL_LEACHING`, this model does not round its output.

---

## 4. Comparison table — model output vs reference output

| # | lambda (m) | slope (%) | Model output `ls_factor` | Reference LS | Δ | Tolerance | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | 22.13 | 10 | 1.1716624795527821 | 1.1716624795527821 | 0.000e+00 | 1e-9 | match |
| 2 | 100 | 8 | 1.8436474024150717 | 1.8436474024150717 | 0.000e+00 | 1e-9 | match |
| 3 | 50 | 15 | 3.1893454630287272 | 3.1893454630287272 | 0.000e+00 | 1e-9 | match |
| 4 | 200 | 5 | 1.376132247286142 | 1.376132247286142 | 0.000e+00 | 1e-9 | match |
| 5 | 10 | 25 | 2.150857445005896 | 2.150857445005896 | 0.000e+00 | 1e-9 | match |
| 6 | 22.13 | 1 | 0.13799460040496625 | 0.13799460040496625 | 0.000e+00 | 1e-9 | match |

Case 1 is the normalisation point of the published formulation: at the standard
plot length of 22.13 m the slope-length factor L is exactly 1, so LS is the
slope-steepness factor S alone (1.1717 at 10 %, against the steepness branch's
0.998 at the 9 % branch point). Cases 3 and 5 cover the steep side, cases 2, 4
and 6 the gentle side. The resulting topsoil-loss multipliers span 0.14 to 3.19,
which is the published operational range of the factor.

---

## 5. Uncertainty statement

The comparison establishes **algebra-exact conformity to the published AH-703
equations**, to floating-point round-off, over the compared slope and length
range. That is the strongest claim available for a topographic factor: the factor
is a pure geometric function of two inputs with no fitted parameters inside it,
so once the algebra matches there is nothing left to be uncertain about in the
factor itself.

What is *not* established is the erosion estimate the factor feeds. RUSLE's
`A = R * K * LS * C * P` carries uncertainty in the rainfall-runoff erosivity R,
the soil erodibility K, the cover-management C and the support practice P that
dwarf anything in LS. The soil-loss models that call this factor inherit that;
this record says nothing about them. In particular the registry records a
`hub-limitation` for the wider RUSLE model (`RUSLE_SOIL_LOSS`) reporting `K`
unavailable rather than an assumed unit value, and that limitation is unaffected
by what is validated here.

---

## 6. Limitations

1. **The 9 % branch is a discontinuity in the published equations, not in the
   model.** At exactly 9 % the two branches give `0.998` and `0.998`; approaching
   from either side is continuous, and the implementation follows the published
   rule (`slope < 9 %` uses the gentle branch, `>= 9 %` the steep one). AH-703
   accepts the resulting kink.
2. **Only the topographic factor is validated.** Not R, K, C, P, and not their
   product. `RUSLE_SOIL_LOSS` remains unvalidated.
3. **No published numeric table for LS is compared.** AH-703 chapter 4 presents
   the factor as a chart; the external anchor here is the published equations
   evaluated independently, not a printed number.
4. **Unit-loss expression is assumed.** LS is a dimensionless multiplier on the
   soil-loss unit of the model that consumes it (t/ha/yr); this record does not
   validate that the caller's soil-loss unit is that one.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`. The reference values are the AH-703
equations evaluated independently in the test module, not values read from the
model.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "RUSLE_LS",
  "model_name": "RUSLE Topographic LS Factor",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_canon_007_rusle_ls",
  "reference": {
    "citation": "Renard, K.G., Foster, G.R., Weesies, G.A., McCool, D.K. & Yoder, D.C. (eds.), Predicting Soil Erosion by Water: A Guide to Conservation Planning with the Revised Universal Soil Loss Equation (RUSLE), USDA Agriculture Handbook 703, 1997, ch. 4, eqs. 4-1 to 4-4 (slope-steepness branch from McCool et al. 1987).",
    "equation": "theta = atan(s/100); beta = (sin theta/0.0896)/(3 sin^0.8 theta + 0.56); m = beta/(1+beta); L = (lambda/22.13)^m; S = 10.8 sin theta + 0.03 below 9 %, else 16.8 sin theta - 0.50; LS = L*S"
  },
  "input_range": {
    "slope_length_m": [10.0, 200.0],
    "slope_percent": [1.0, 25.0]
  },
  "output_key": "ls_factor",
  "tolerance": {
    "absolute": 1e-09,
    "basis": "a closed form with no fitting parameters, so agreement is to floating-point round-off; the model does not round its output"
  },
  "cases": [
    {
      "name": "ah703_reference_plot_at_10_percent",
      "inputs": {"slope_length_m": 22.13, "slope_percent": 10.0},
      "reference": 1.1716624795527821,
      "recorded": 1.1716624795527821,
      "verdict": "match"
    },
    {
      "name": "long_gentle_slope_below_the_9_percent_branch",
      "inputs": {"slope_length_m": 100.0, "slope_percent": 8.0},
      "reference": 1.8436474024150717,
      "recorded": 1.8436474024150717,
      "verdict": "match"
    },
    {
      "name": "short_steep_slope_above_the_branch",
      "inputs": {"slope_length_m": 50.0, "slope_percent": 15.0},
      "reference": 3.1893454630287272,
      "recorded": 3.1893454630287272,
      "verdict": "match"
    },
    {
      "name": "very_long_gentle_slope",
      "inputs": {"slope_length_m": 200.0, "slope_percent": 5.0},
      "reference": 1.376132247286142,
      "recorded": 1.376132247286142,
      "verdict": "match"
    },
    {
      "name": "very_short_steep_slope",
      "inputs": {"slope_length_m": 10.0, "slope_percent": 25.0},
      "reference": 2.150857445005896,
      "recorded": 2.150857445005896,
      "verdict": "match"
    },
    {
      "name": "near_flat_reference_plot",
      "inputs": {"slope_length_m": 22.13, "slope_percent": 1.0},
      "reference": 0.13799460040496625,
      "recorded": 0.13799460040496625,
      "verdict": "match"
    }
  ],
  "validation_status": "validated",
  "status_vocabulary_label": "VALIDATED_METHOD",
  "uncertainty": "Algebra-exact conformity to the published AH-703 equations to floating-point round-off. The factor itself carries no parameter uncertainty; the erosion estimate it feeds inherits all of R, K, C and P's uncertainty.",
  "limitations": [
    "The 9 % slope-steepness branch is a published discontinuity the model reproduces rather than smooths.",
    "Only the topographic factor is validated; RUSLE_SOIL_LOSS remains unvalidated.",
    "No printed numeric table for LS is compared, only the published equations evaluated independently.",
    "The soil-loss unit the factor multiplies is whatever the consuming model uses."
  ]
}
```
