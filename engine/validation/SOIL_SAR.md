# Validation Evidence — SOIL_SAR

**Model:** `SOIL_SAR` — Sodium Adsorption Ratio (registry version `1.0.0`)
**Cluster:** soil chemistry / irrigation-water quality
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_soil_sar`
**Implementation:** `engine/hydroma/soil/chemistry.py::calculate_sar`
**Model card:** `engine/models/cards/SOIL_SAR_sodium_adsorption_ratio.md`
**Re-verified by:** `engine/validation/test_validation_records.py`
**Registry decision:** `unvalidated` — the comparison below passes in full, but the
machine-readable evidence register (`reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`,
row `SAR_ESP_LEACHING`) records this family as `VALIDATED_METHOD_CONFORMANCE`,
not as an external anchor, and
`engine/tests/test_machine_evidence_consistency.py` refuses a registry
`validated` claim without one. See §6.

---

## 1. Published reference

**Citation.** U.S. Salinity Laboratory (Richards, L.A., ed.), *Diagnosis and
Improvement of Saline and Alkali Soils*, USDA Agriculture Handbook 60, 1954,
Chapter 6 ("Quality of Irrigation Water"), sodium-hazard section: the sodium
adsorption ratio of a water is

```
SAR = Na / sqrt((Ca + Mg) / 2)
```

with Na, Ca and Mg the concentrations of sodium, calcium and magnesium in
**milliequivalents per litre (meq/L)**. The same definition is restated as
eq. (5) of Ayers, R.S. & Westcot, D.W., *Water Quality for Agriculture*, FAO
Irrigation and Drainage Paper 29 (Rev. 1), 1985.

**How the reference values below were obtained.** The reference column is an
independent evaluation of the published closed form written from the equation
above, not a copy of the engine's arithmetic: `na / math.sqrt((ca + mg) / 2)`
computed directly in the test module. No engine module is consulted when the
reference number is produced.

**Independent check that does not use the equation at all.** The single ratio the
formula reduces to is `SAR = Na * sqrt(2) / sqrt(Ca + Mg)`, so for the first case
(Na=10, Ca+Mg=6) the value must equal `10 * 1.4142135623730951 / 2.449489742783178`
= 5.773502691896258, which is what the model returns to its documented rounding.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Sodium concentration | `na` | meq/L | 2.0 – 20.0 |
| Calcium concentration | `ca` | meq/L | 2.0 – 20.0 |
| Magnesium concentration | `mg` | meq/L | 1.0 – 20.0 |

Domain constraints of the published definition that the comparison respects:
`na, ca, mg >= 0` and `ca + mg > 0` (the denominator is the square root of the
mean divalent concentration; with no divalent cations the ratio is undefined and
the implementation raises rather than returning an arbitrary number). The
irrigation-water quality range of Handbook 60 chapter 6 is 0.5–40 meq/L per ion;
every case below lies inside it.

---

## 3. Tolerance

`tolerance_absolute = 0.005` (milli-units of `(meq/L)^0.5`).

**Basis.** The implementation rounds its reported `sar` to two decimal places
(`round(sar, 2)` in `calculate_sar`). The tolerance is therefore exactly the
documented rounding granularity of the reported figure, the same basis
`engine/strict_tests/test_s18_scientific_validation.py` uses for this model. It is
not a loosened scientific claim: halving it to 0.0025 would demand a number the
reported field cannot carry.

---

## 4. Comparison table — model output vs reference output

| # | Inputs (meq/L) | Model output `sar` | Reference output | Δ (model − ref) | Tolerance | Verdict |
|---|---|---|---|---|---|---|
| 1 | Na 10, Ca 4, Mg 2 | 5.77 | 5.773502691896258 | −0.00350 | 0.005 | match |
| 2 | Na 5, Ca 8, Mg 4 | 2.04 | 2.041241452319315 | −0.00124 | 0.005 | match |
| 3 | Na 20, Ca 2, Mg 1 | 16.33 | 16.329931618554521 | +0.00007 | 0.005 | match |
| 4 | Na 2, Ca 20, Mg 20 | 0.45 | 0.4472135954999579 | +0.00279 | 0.005 | match |

The four cases span the whole of Handbook 60's sodium-hazard ladder: case 3 is
`very_high_sodium` (SAR >= 9, water unsuitable without amendment), case 1 is
`medium_sodium` (3–6), case 2 is `low_sodium` (< 3) and case 4 is the low end of
the same class. The model's classification bands are the published ones and are
reported by the route as `classification`; the numeric comparison is the
quantitative claim and the bands follow from it.

---

## 5. Uncertainty statement

The comparison is **exact-method, not empirical**: it establishes that the
implementation evaluates the published definition of SAR to within its reported
rounding granularity, over the input range of the Handbook 60 chapter 6 table.
It does **not** establish that the SAR computed from a given water sample agrees
with the sodium hazard that sample poses in a given soil. That depends on the
soil's exchangeable sodium percentage, its calcium/magnesium chemistry and its
clay mineralogy, none of which the SAR definition carries.

Propagated numeric uncertainty is therefore bounded by the reported rounding:
`+/- 0.005` on the value, i.e. at most about 0.09 % of the 5.77 figure above and
at most 1.1 % of the 0.45 figure. There is no Monte Carlo treatment of input
uncertainty; a caller holding ion concentrations with a stated error should
propagate it through the closed form itself, which is three arithmetic
operations.

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
   the claim. The row that would move it is a *published Handbook 60
   sodium-hazard table value*: one number printed in the source that this
   record's reference column is not re-derived from.
2. Only the numeric ratio is compared here. The hazard bands, the
   `suitable_for_irrigation` flag and the management text are the published
   classes of Handbook 60 / FAO-29 applied to that number; they are not
   independently re-derived in this record.
3. The definition assumes equilibrium ion activities approximated by
   concentrations. Waters whose ionic strength is far from the range of the
   Handbook 60 tables (brines, very dilute rain) are outside what the equation
   describes, even though the implementation will still evaluate it.
4. No field or laboratory data is compared: the record is a conformance check
   against the published equation, which is what `VALIDATED_METHOD_CONFORMANCE`
   means in this repository's evidence vocabulary.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`. `reference` is independently re-derived from
the published equation; `recorded` is the value the gateway returned when the
record was written. `test_validation_records.py` re-runs each case.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "SOIL_SAR",
  "model_name": "Sodium Adsorption Ratio",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_soil_sar",
  "reference": {
    "citation": "U.S. Salinity Laboratory (Richards, L.A., ed.), Diagnosis and Improvement of Saline and Alkali Soils, USDA Agriculture Handbook 60, 1954, ch. 6; restated as eq. (5) of Ayers & Westcot, Water Quality for Agriculture, FAO Irrigation and Drainage Paper 29 (Rev. 1), 1985.",
    "equation": "sar = na / sqrt((ca + mg) / 2)"
  },
  "input_range": {
    "na_meq_l": [2.0, 20.0],
    "ca_meq_l": [2.0, 20.0],
    "mg_meq_l": [1.0, 20.0]
  },
  "output_key": "sar",
  "tolerance": {
    "absolute": 0.005,
    "basis": "the implementation rounds the reported sar to two decimal places; 0.005 is that rounding granularity"
  },
  "cases": [
    {
      "name": "handbook60_medium_sodium",
      "inputs": {"na": 10.0, "ca": 4.0, "mg": 2.0},
      "reference": 5.773502691896258,
      "recorded": 5.77,
      "verdict": "match"
    },
    {
      "name": "handbook60_low_sodium",
      "inputs": {"na": 5.0, "ca": 8.0, "mg": 4.0},
      "reference": 2.041241452319315,
      "recorded": 2.04,
      "verdict": "match"
    },
    {
      "name": "handbook60_very_high_sodium",
      "inputs": {"na": 20.0, "ca": 2.0, "mg": 1.0},
      "reference": 16.329931618554521,
      "recorded": 16.33,
      "verdict": "match"
    },
    {
      "name": "low_end_of_table",
      "inputs": {"na": 2.0, "ca": 20.0, "mg": 20.0},
      "reference": 0.4472135954999579,
      "recorded": 0.45,
      "verdict": "match"
    }
  ],
  "validation_status": "unvalidated",
  "status_vocabulary_label": "VALIDATED_METHOD_CONFORMANCE",
  "registry_gap": "The model matches its published reference but the register has no external anchor for the sodium-hazard family; engine/tests/test_machine_evidence_consistency.py keeps the registry status at unvalidated until one is added.",
  "uncertainty": "Exact-method conformance to the published definition within the reported rounding granularity (+/-0.005 on the ratio). No empirical field or laboratory comparison; no Monte Carlo treatment of input uncertainty.",
  "limitations": [
    "Only the numeric ratio is validated; the hazard bands and the suitable_for_irrigation flag follow from it.",
    "Concentrations stand in for ion activities; brines and very dilute waters are outside the equation's described range.",
    "No independent measured water samples are compared."
  ]
}
```
