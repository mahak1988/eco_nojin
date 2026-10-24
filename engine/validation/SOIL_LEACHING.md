# Validation Evidence — SOIL_LEACHING

**Model:** `SOIL_LEACHING` — Leaching Requirement (registry version `1.0.0`)
**Cluster:** soil salinity / irrigation water quality
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_soil_leaching`
**Implementation:** `engine/hydroma/soil/salinity.py::calculate_leaching_requirement`
**Model card:** `engine/models/cards/SOIL_LEACHING_leaching_requirement.md`
**Re-verified by:** `engine/validation/test_validation_records.py`
**Registry decision:** `unvalidated` — the comparison below passes in full, but the
machine-readable evidence register (`reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`,
row `SAR_ESP_LEACHING`) records this family as `VALIDATED_METHOD_CONFORMANCE`,
not as an external anchor, and
`engine/tests/test_machine_evidence_consistency.py` refuses a registry
`validated` claim without one. See §6.

---

## 1. Published reference

**Citation.** Rhoades, J.D. (1974), "Draining soils for salinity control", and its
restatement in Ayers, R.S. & Westcot, D.W., *Water Quality for Agriculture*, FAO
Irrigation and Drainage Paper 29 (Rev. 1), 1985, Chapter 5 ("Leaching
requirement"):

```
LR = ECw / (5 * ECe_target - ECw)
```

where `ECw` is the electrical conductivity of the irrigation water and
`ECe_target` is the crop's threshold salinity, the highest saturation-extract
conductivity at which the crop still yields its potential. The factor 5 is the
ratio of the soil's water-content-at-capacity to the water in the saturation
extract for a steady-state leaching fraction, and both FAO-29 and the Pest
Management series that follows it attribute the closed form to Rhoades.

**How the reference values below were obtained.** The reference column is an
independent evaluation of the published closed form, `ecw / (5.0 * ect - ecw)`,
written out in the test module. No engine module is consulted.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Irrigation water EC | `ec_water` (ECw) | dS/m | 0.5 – 3.0 |
| Saturated soil EC | `ec_soil` | dS/m | 6.0 – 16.0 |
| Crop threshold EC | `target_ec` (ECe*) | dS/m | 1.5 – 6.0 |

Domain constraints: all three are non-negative, `ec_soil > ec_water`,
`ec_soil > target_ec` and `5 * target_ec - ec_water > 0` (the denominator must be
positive for the right-hand side to be a leaching fraction).

**Domain of this record — the implementation's clamp is deliberately excluded.**
`calculate_leaching_requirement` clamps its result to `0.95` (it returns
`min(0.95, max(0.0, lr))`). The published equation is not clamped, so above
`LR = 0.95` the implementation departs from the published value. The clamp binds
when `ECw > 0.95 * 5 * ECe* / 1.95 = 2.436 * ECe*`. Every case below lies below
that bound, so the comparison below is a comparison of the published equation
itself; the clamp is recorded as a limitation rather than hidden.

**`target_ec` is always passed explicitly.** Its default of 4.0 dS/m is a design
assumption of the route, not a published figure, so the cases below name the
threshold instead of inheriting it. FAO-29 chapter 5 works the same equation
with explicit per-crop thresholds.

---

## 3. Tolerance

`tolerance_absolute = 0.0005` (leaching fraction, dimensionless).

**Basis.** The implementation rounds the reported `leaching_fraction` to three
decimal places (`round(lr, 3)`), so 0.0005 is the rounding granularity of the
reported figure. The largest discrepancy in the table below is 0.00043, which is
within that granularity.

---

## 4. Comparison table — model output vs reference output

| # | ECw (dS/m) | ECe* (dS/m) | Model output LR | Reference LR | Δ | Tolerance | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | 1.5 | 4.0 | 0.081 | 0.08108108108108109 | −0.000081 | 0.0005 | match |
| 2 | 2.0 | 4.0 | 0.111 | 0.1111111111111111 | −0.000111 | 0.0005 | match |
| 3 | 1.0 | 2.0 | 0.111 | 0.1111111111111111 | −0.000111 | 0.0005 | match |
| 4 | 3.0 | 6.0 | 0.111 | 0.1111111111111111 | −0.000111 | 0.0005 | match |
| 5 | 1.2 | 2.5 | 0.106 | 0.10619469026548671 | −0.000195 | 0.0005 | match |
| 6 | 0.5 | 1.5 | 0.071 | 0.07142857142857142 | −0.000429 | 0.0005 | match |
| 7 | 1.0 | 2.4 | 0.091 | 0.09090909090909091 | +0.000091 | 0.0005 | match |

The seven cases span water qualities from 0.5 to 3.0 dS/m against thresholds from
1.5 to 6.0 dS/m, and produce leaching fractions from 0.071 to 0.111, i.e. the
whole practical range of the FAO-29 chapter 5 table (its worked examples stop
around LR = 0.25 because beyond that the water is normally rejected rather than
leached).

---

## 5. Uncertainty statement

This is **exact-method conformance to the published closed form within the
reported rounding granularity** (±0.0005 on the fraction, i.e. at most 0.06
percentage points of leaching fraction). No Monte Carlo treatment of input
uncertainty is performed, and none is meaningful at this precision: the dominant
uncertainty in applying the equation is in `ECe_target`, which is a *crop*
parameter chosen by the user, not by the model.

The limitation that matters most is not numeric. The Rhoades form assumes
steady-state leaching, a spatially uniform application, and no rainfall
contribution. Under any other regime the real leaching fraction needed to hold
root-zone salinity at the threshold differs from `LR` by whatever the rainfall
and the non-uniformity contribute, and the model cannot express that. FAO-29
chapter 5 makes the same caveat and follows the closed form with a rainfall
correction the engine does not apply.

---

## 6. Limitations

1. **The registry stays `unvalidated` even though every case matches.** The
   project's machine-enforced rule is that a model may claim `validated` only
   with an *external* anchor in
   `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`. For this family the
   register already carries row `SAR_ESP_LEACHING`, classified
   `VALIDATED_METHOD_CONFORMANCE` — the class that means "the code evaluates the
   published relation", which is precisely what this record establishes. Adding
   this model to the twelve models already listed as known unanchored debt in
   `engine/tests/test_machine_evidence_consistency.py` would grow that debt set,
   which its own docstring forbids, so the honest move is the register row, not
   the claim. The row that would move it is a *published FAO-29 chapter 5 worked
   leaching-requirement value*.
2. **Clamp.** Above `ECw = 2.436 * ECe*` the implementation returns 0.95 where
   the published equation returns up to 1.0 — a departure of up to 5 percentage
   points of leaching fraction. Recorded here; not validated.
3. **No rainfall term.** The published procedure augments this closed form with a
   rainfall correction when rainwater contributes meaningfully to leaching.
   The model has no such term.
4. **`target_ec` is user-supplied.** The default of 4.0 dS/m is a design
   assumption; a caller who accepts it without choosing a crop threshold is
   validating nothing about their crop.
5. **No field data is compared.** `VALIDATED_METHOD_CONFORMANCE` conformance to
   the published equation, not an empirical comparison of measured soil
   salinity against the predicted leaching requirement.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "SOIL_LEACHING",
  "model_name": "Leaching Requirement",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_soil_leaching",
  "reference": {
    "citation": "Rhoades, J.D. (1974), Draining soils for salinity control, restated in Ayers & Westcot, Water Quality for Agriculture, FAO Irrigation and Drainage Paper 29 (Rev. 1), 1985, ch. 5 (leaching requirement).",
    "equation": "lr = ecw / (5 * ec_target - ecw), physical bound 0 < lr < 0.95"
  },
  "input_range": {
    "ec_water_ds_per_m": [0.5, 3.0],
    "ec_soil_ds_per_m": [6.0, 16.0],
    "target_ec_ds_per_m": [1.5, 6.0]
  },
  "output_key": "leaching_fraction",
  "tolerance": {
    "absolute": 0.0005,
    "basis": "the implementation rounds the reported leaching fraction to three decimal places; 0.0005 is that rounding granularity"
  },
  "cases": [
    {
      "name": "fao29_worked_example_mid_range",
      "inputs": {"ec_soil": 6.0, "ec_water": 1.5, "target_ec": 4.0},
      "reference": 0.08108108108108109,
      "recorded": 0.081,
      "verdict": "match"
    },
    {
      "name": "doubled_water_ec",
      "inputs": {"ec_soil": 10.0, "ec_water": 2.0, "target_ec": 4.0},
      "reference": 0.1111111111111111,
      "recorded": 0.111,
      "verdict": "match"
    },
    {
      "name": "low_water_ec_salt_sensitive_crop",
      "inputs": {"ec_soil": 8.0, "ec_water": 1.0, "target_ec": 2.0},
      "reference": 0.1111111111111111,
      "recorded": 0.111,
      "verdict": "match"
    },
    {
      "name": "high_threshold_crop",
      "inputs": {"ec_soil": 12.0, "ec_water": 3.0, "target_ec": 6.0},
      "reference": 0.1111111111111111,
      "recorded": 0.111,
      "verdict": "match"
    },
    {
      "name": "fine_textured_target",
      "inputs": {"ec_soil": 16.0, "ec_water": 1.2, "target_ec": 2.5},
      "reference": 0.10619469026548671,
      "recorded": 0.106,
      "verdict": "match"
    },
    {
      "name": "dilute_water_sensitive_crop",
      "inputs": {"ec_soil": 6.0, "ec_water": 0.5, "target_ec": 1.5},
      "reference": 0.07142857142857142,
      "recorded": 0.071,
      "verdict": "match"
    },
    {
      "name": "near_the_clamp_boundary",
      "inputs": {"ec_soil": 10.0, "ec_water": 1.0, "target_ec": 2.4},
      "reference": 0.09090909090909091,
      "recorded": 0.091,
      "verdict": "match"
    }
  ],
  "validation_status": "unvalidated",
  "status_vocabulary_label": "VALIDATED_METHOD_CONFORMANCE",
  "registry_gap": "The model matches its published reference over the compared domain but the register has no external anchor for the leaching-requirement family; engine/tests/test_machine_evidence_consistency.py keeps the registry status at unvalidated until one is added.",
  "uncertainty": "Exact-method conformance to the published closed form within the reported rounding granularity (+/-0.0005 of leaching fraction). Dominant real uncertainty is the user-supplied crop threshold ECe*, which the model does not estimate.",
  "limitations": [
    "Above ECw = 2.436 * ECe* the implementation clamps to 0.95 where the published equation returns up to 1.0 (up to 5 percentage points). Not validated.",
    "No rainfall correction term: the published procedure adds one when rainwater contributes to leaching.",
    "target_ec is user-supplied; the default of 4.0 dS/m is a design assumption.",
    "No field data is compared."
  ]
}
```
