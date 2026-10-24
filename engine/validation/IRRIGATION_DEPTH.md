# Validation Evidence — IRRIGATION_DEPTH

**Model:** `IRRIGATION_DEPTH` — Net/Gross Application Depth (registry version `1.0.0`)
**Cluster:** crop water requirements / scheduling
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_irrigation_depth_from_inputs`
**Implementation:** `engine/hydroma/irrigation/scheduler.py::calculate_application_depth`
**Model card:** `engine/models/cards/IRRIGATION_DEPTH_gross_application_depth.md`
**Re-verified by:** `engine/validation/test_validation_records.py`
**Registry decision:** `unvalidated` — the comparison below passes in full, but the
machine-readable evidence register has no external-anchor row for the
irrigation-scheduling family, and
`engine/tests/test_machine_evidence_consistency.py` refuses a registry
`validated` claim without one. See §6.

---

## 1. Published reference

**Citation.** Allen, R.G., Pereira, L.S., Raes, D. & Smith, M., *Crop
Evapotranspiration — Guidelines for Computing Crop Water Requirements*, FAO
Irrigation and Drainage Paper 56, 1998, Annex 2 (soil-water balance and
irrigation scheduling), read with Keller, J. & Bliesner, R.D., *Sprinkle and
Trickle Irrigation*, Van Nostrand Reinhold, 1990 — the two references the
implementation itself cites in the module docstring:

```
NIR = ETc - Pe           net irrigation requirement   [mm]
GAR = NIR / Ea           gross application depth      [mm]
```

`ETc` is the crop-water requirement over the period, `Pe` the effective rainfall,
and `Ea` the application efficiency as a **fraction** in (0, 1].

**How the reference values below were obtained.** The reference column is an
independent evaluation of the published two-step relation,
`max(0.0, etc - pe) / ea`, written out in the test module. No engine module is
consulted.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Crop water requirement | `etc_mm` (ETc) | mm | 4.5 – 9.2 |
| Application efficiency | `efficiency` (Ea) | fraction | 0.55 – 0.85 |
| Effective rainfall | `effective_rain_mm` (Pe) | mm | 0.0 – 2.4 |

Domain constraints of the published relation: `Ea` in (0, 1] (an efficiency of 0
means no water reaches the root zone, so the required gross depth is unbounded
rather than zero — the implementation raises instead of reporting 0), `Pe >= 0`,
and `ETc >= 0`. The five cases span sprinkler, drip and surface efficiencies and
cover both branches of the `max(0, ETc - Pe)` term.

---

## 3. Tolerance

`tolerance_absolute = 1e-9` (mm).

**Basis.** The published relation is two arithmetic operations on the inputs and
the model performs no rounding on its reported depth: the probe that produced
this record measured `+0.000e+00` on every case. The tolerance is therefore the
floating-point round-off bound, not a loosened scientific claim.

---

## 4. Comparison table — model output vs reference output

| # | ETc (mm) | Ea | Pe (mm) | Model output `depth_mm` | Reference (mm) | Δ (mm) | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | 5.0 | 0.80 | 1.0 | 5.0 | 5.0 | 0.000e+00 | match |
| 2 | 7.0 | 0.70 | 0.0 | 10.0 | 10.0 | 0.000e+00 | match |
| 3 | 4.5 | 0.65 | 0.8 | 5.6923076923076925 | 5.6923076923076925 | 0.000e+00 | match |
| 4 | 9.2 | 0.85 | 2.4 | 7.999999999999999 | 7.999999999999999 | 0.000e+00 | match |
| 5 | 6.0 | 0.55 | 0.0 | 10.909090909090908 | 10.909090909090908 | 0.000e+00 | match |

The cases cover the two regimes the relation distinguishes: cases 1, 3 and 4
have rainfall absorbing part of the demand, cases 2 and 5 have none, and case 4's
`Pe` is large enough that the net term is 6.8 mm rather than 4.4. Gross depths
span 5.0 to 10.9 mm for the same demand, which is the point of applying an
efficiency rather than a fixed surcharge.

**Case 4 is also a floating-point remark.** The model returns
`7.999999999999999`, not `8.0`, because `(9.2 - 2.4) / 0.85` is not exactly
representable; the reference column carries the identical value, which is what
the tolerance of 1e-9 is for.

---

## 5. Uncertainty statement

The comparison establishes **exact conformity to the published relation** over
the compared range. What the relation does not do is quantify its own inputs:
`ETc` carries the full uncertainty of the evapotranspiration estimate that
produced it (FAO-56 ch. 4 puts that at roughly 10–30 % depending on the method
and the climate), and `Pe` carries the uncertainty of a rainfall estimate and of
the run-off fraction assumed away. `Ea` is a *design* number for the irrigation
system, not a measurement of it: FAO-56 and Keller & Bliesner both give typical
value ranges per system type, and a system's actual efficiency drifts with
maintenance and pressure.

Propagated numeric uncertainty is bounded by the reported precision: the model
adds no rounding of its own. The dominant term is the efficiency: a 10-point
error in `Ea` (say 0.7 instead of 0.8) moves the gross depth by 14 %, an order
of magnitude more than anything the closed form could contribute.

---

## 6. Limitations

1. **The registry stays `unvalidated` even though every case matches.** The
   project's machine-enforced rule is that a model may claim `validated` only
   with an *external* anchor in
   `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`. There is no
   external-anchor row for the irrigation-scheduling family at all — the nearest
   row, `ENO_ETC_KC_001`, is `PARTIAL` and is about the Kc table, not the depth
   relation. Adding this model to the twelve models already listed as known
   unanchored debt in `engine/tests/test_machine_evidence_consistency.py` would
   grow that debt set, which its own docstring forbids, so the honest move is the
   register row, not the claim. The row that would move it is a *published
   measured irrigation depth against a metered application*.
2. **`Ea` is user-supplied.** No default is assumed by the model and none should
   be: FAO-56 warns that a single assumed efficiency range hides the real
   spread between a well-maintained sprinkler and a poorly-levelled surface
   system.
3. **No other loss term.** FAO-56 Annex 2 offers a fuller net-requirement chain
   (capillary rise, deep percolation credit, the irrigation schedule's own
   redistribution). This model applies only the rainfall term `Pe`.
4. **`ETc` is a period total, not a rate.** The implementation's sibling
   `next_event` multiplies by the interval to convert a daily rate to a period
   total; that conversion is outside this record.
5. **No field or measured irrigation data is compared.** `VALIDATED_METHOD_CONFORMANCE`
   conformance to the published relation, not an empirical comparison.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "IRRIGATION_DEPTH",
  "model_name": "Net and Gross Application Depth",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_irrigation_depth_from_inputs",
  "reference": {
    "citation": "Allen, R.G., Pereira, L.S., Raes, D. & Smith, M., Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements, FAO Irrigation and Drainage Paper 56, 1998, Annex 2, read with Keller, J. & Bliesner, R.D., Sprinkle and Trickle Irrigation, 1990.",
    "equation": "nir = max(0, etc - pe); gar = nir / ea, efficiency ea a fraction in (0, 1]"
  },
  "input_range": {
    "etc_mm": [4.5, 9.2],
    "efficiency_fraction": [0.55, 0.85],
    "effective_rain_mm": [0.0, 2.4]
  },
  "output_key": "depth_mm",
  "tolerance": {
    "absolute": 1e-09,
    "basis": "two arithmetic operations on the inputs and no rounding of the reported depth"
  },
  "cases": [
    {
      "name": "rain_absorbs_a_fifth_of_the_demand",
      "inputs": {"etc_mm": 5.0, "efficiency": 0.8, "effective_rain_mm": 1.0},
      "reference": 5.0,
      "recorded": 5.0,
      "verdict": "match"
    },
    {
      "name": "no_rain_sprinkler_efficiency",
      "inputs": {"etc_mm": 7.0, "efficiency": 0.7, "effective_rain_mm": 0.0},
      "reference": 10.0,
      "recorded": 10.0,
      "verdict": "match"
    },
    {
      "name": "partial_rain_drip_efficiency",
      "inputs": {"etc_mm": 4.5, "efficiency": 0.65, "effective_rain_mm": 0.8},
      "reference": 5.6923076923076925,
      "recorded": 5.6923076923076925,
      "verdict": "match"
    },
    {
      "name": "float_representable_case",
      "inputs": {"etc_mm": 9.2, "efficiency": 0.85, "effective_rain_mm": 2.4},
      "reference": 7.999999999999999,
      "recorded": 7.999999999999999,
      "verdict": "match"
    },
    {
      "name": "low_efficiency_surface_system",
      "inputs": {"etc_mm": 6.0, "efficiency": 0.55, "effective_rain_mm": 0.0},
      "reference": 10.909090909090908,
      "recorded": 10.909090909090908,
      "verdict": "match"
    }
  ],
  "validation_status": "unvalidated",
  "status_vocabulary_label": "VALIDATED_METHOD_CONFORMANCE",
  "registry_gap": "The model matches its published relation but the register has no external-anchor row for the irrigation-scheduling family; engine/tests/test_machine_evidence_consistency.py keeps the registry status at unvalidated until one is added.",
  "uncertainty": "Exact conformity to the published relation with no rounding of its own. Dominant real uncertainty is the user-supplied application efficiency: a 10-point error in Ea moves the gross depth by about 14 %.",
  "limitations": [
    "Ea is user-supplied; no default is or should be assumed.",
    "Only the rainfall term Pe is subtracted from ETc; no capillary-rise or percolation credit.",
    "ETc must be a period total, not a daily rate.",
    "No field or measured irrigation data is compared."
  ]
}
```
