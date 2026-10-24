# Validation Evidence — SOIL_ESP

**Model:** `SOIL_ESP` — Exchangeable Sodium Percent (registry version `1.0.0`)
**Cluster:** soil chemistry / sodicity
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_soil_esp`
**Implementation:** `engine/hydroma/soil/chemistry.py::calculate_esp`
**Model card:** `engine/models/cards/SOIL_ESP_exchangeable_sodium_percent.md`
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
Chapter 5 ("Exchangeable sodium percentage"): the exchangeable sodium percentage
of a soil is the fraction of the cation exchange complex occupied by sodium,
expressed as a percentage,

```
ESP = 100 * (exchangeable Na) / CEC
```

with exchangeable Na and the cation exchange capacity CEC in the same units
(meq/100 g). The same chapter defines a soil as **sodic at ESP >= 15** and
describes the structural degradation that follows. The management line at
ESP >= 10 used by the route is documented in `engine/hydroma/soil/chemistry.py`
(`AMENDMENT_ESP_THRESHOLD`) as an earlier management trigger, not the
definitional one, and both numbers are reported by name in the response.

**How the reference values below were obtained.** The reference column is an
independent evaluation of the published ratio, `100.0 * na / cec`, written in the
test module. No engine module is consulted.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Exchangeable sodium | `na` | meq/100 g | 1.5 – 10.0 |
| Cation exchange capacity | `cex` (CEC) | meq/100 g | 15.0 – 30.0 |

Domain constraints of the published definition: `na >= 0` and `CEC > 0`. A CEC of
zero has no exchange complex to take a percentage of, and the implementation
raises rather than dividing by it.

---

## 3. Tolerance

`tolerance_absolute = 0.005` (percentage points).

**Basis.** The implementation rounds the reported `esp` to two decimal places.
The tolerance is that rounding granularity, not a loosened scientific claim: the
largest discrepancy in the table below is 0.00333 points, which is exactly
`66.67 - 66.6666...`.

---

## 4. Comparison table — model output vs reference output

| # | Inputs (meq/100 g) | Model output `esp` (%) | Reference output (%) | Δ (points) | Tolerance | Verdict |
|---|---|---|---|---|---|---|
| 1 | Na 6.0, CEC 20.0 | 30.00 | 30.0 | 0.00000 | 0.005 | match |
| 2 | Na 3.0, CEC 25.0 | 12.00 | 12.0 | 0.00000 | 0.005 | match |
| 3 | Na 10.0, CEC 15.0 | 66.67 | 66.66666666666667 | +0.00333 | 0.005 | match |
| 4 | Na 1.5, CEC 30.0 | 5.00 | 5.0 | 0.00000 | 0.005 | match |

The four cases bracket the published decision lines: case 3 and case 1 are well
above the sodic line of 15 (the route reports `classification = sodic`), case 2
sits between the management line of 10 and the definitional line of 15
(moderately sodic), and case 4 is below both (normal). The numeric comparison is
the quantitative claim; the band labels follow from it.

---

## 5. Uncertainty statement

This is an **exact-method conformance check**: it establishes that the
implementation evaluates the published definition of ESP to within its reported
rounding granularity over the compared range. It does not establish that the ESP
of any real soil equals what this ratio predicts, because ESP is a *measured*
quantity: a laboratory determines the exchangeable cations (ammonium acetate
extraction at pH 7, or summation of the exchangeable bases), and a ratio taken
against a CEC estimated from texture and organic matter is an estimate, not a
measurement. The repository records that limit explicitly for the sibling
`SOIL_CEC` model, whose estimator is labelled a design assumption.

Propagated numeric uncertainty is bounded by the reported rounding: at most
0.005 percentage points on the value. No Monte Carlo treatment of input
uncertainty is performed.

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
   exchangeable-sodium table value* or a laboratory exchangeable-cation
   measurement for a known soil.
2. The definition assumes the exchangeable sodium and the CEC are expressed in
   the same units and measured at the same pH; mixing a pH-7 CEC with a
   pH-dependent sodium figure is a soil-chemistry error the equation cannot
   detect.
3. ESP > 100 is arithmetically possible (exchangeable sodium exceeding the total
   exchange capacity) and the implementation does not refuse it; such a result
   indicates inconsistent inputs rather than a soil.
4. No laboratory exchangeable-cation data is compared; the record is a conformance
   check against the published definition, which is what `VALIDATED_METHOD_CONFORMANCE`
   means in this repository's evidence vocabulary.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "SOIL_ESP",
  "model_name": "Exchangeable Sodium Percent",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_soil_esp",
  "reference": {
    "citation": "U.S. Salinity Laboratory (Richards, L.A., ed.), Diagnosis and Improvement of Saline and Alkali Soils, USDA Agriculture Handbook 60, 1954, ch. 5: ESP = 100 x exchangeable Na / CEC; sodic at ESP >= 15.",
    "equation": "esp = 100 * exchangeable_na / cec"
  },
  "input_range": {
    "exchangeable_na_meq_per_100g": [1.5, 10.0],
    "cec_meq_per_100g": [15.0, 30.0]
  },
  "output_key": "esp",
  "tolerance": {
    "absolute": 0.005,
    "basis": "the implementation rounds the reported esp to two decimal places; 0.005 is that rounding granularity"
  },
  "cases": [
    {
      "name": "sodic_well_above_the_handbook60_line",
      "inputs": {"na": 6.0, "cex": 20.0},
      "reference": 30.0,
      "recorded": 30.0,
      "verdict": "match"
    },
    {
      "name": "between_management_and_definitional_lines",
      "inputs": {"na": 3.0, "cex": 25.0},
      "reference": 12.0,
      "recorded": 12.0,
      "verdict": "match"
    },
    {
      "name": "three_times_the_sodic_line",
      "inputs": {"na": 10.0, "cex": 15.0},
      "reference": 66.66666666666667,
      "recorded": 66.67,
      "verdict": "match"
    },
    {
      "name": "normal_below_both_lines",
      "inputs": {"na": 1.5, "cex": 30.0},
      "reference": 5.0,
      "recorded": 5.0,
      "verdict": "match"
    }
  ],
  "validation_status": "unvalidated",
  "status_vocabulary_label": "VALIDATED_METHOD_CONFORMANCE",
  "registry_gap": "The model matches its published reference but the register has no external anchor for the exchangeable-sodium definition; engine/tests/test_machine_evidence_consistency.py keeps the registry status at unvalidated until one is added.",
  "uncertainty": "Exact-method conformance to the published definition within the reported rounding granularity (+/-0.005 percentage points). ESP itself remains a measured quantity; a CEC estimated from texture and organic matter is an estimate, not a measurement.",
  "limitations": [
    "Exchangeable sodium and CEC must be in the same units and measured at the same pH; the equation cannot detect a mismatch.",
    "ESP above 100 is arithmetically accepted and indicates inconsistent inputs, not a soil.",
    "No laboratory exchangeable-cation data is compared."
  ]
}
```
