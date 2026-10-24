# Validation Evidence — IRRIGATION_INTERVAL

**Model:** `IRRIGATION_INTERVAL` — Irrigation Interval (registry version `1.0.0`)
**Cluster:** crop water requirements / scheduling
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_irrigation_interval_solution`
**Implementation:** `engine/hydroma/irrigation/scheduler.py::calculate_interval`
**Model card:** `engine/models/cards/IRRIGATION_INTERVAL_scheduling_interval.md`
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
irrigation scheduling), and Keller, J. & Bliesner, R.D., *Sprinkle and Trickle
Irrigation*, Van Nostrand Reinhold, 1990 — the two references the implementation
itself cites in the module docstring:

```
I = (TAW * p) / ETc        irrigation interval         [days]
```

`TAW` is the total available water in the root zone (mm), `p` the
management-allowed depletion as a **fraction** in (0, 1], and `ETc` the peak
daily crop-water requirement (mm/day). FA0-56's worked scheduling example for a
loamy soil under peak wheat demand is exactly this relation and is the case 1
below.

**How the reference values below were obtained.** The reference column is an
independent evaluation of the published relation,
`max(1, round(TAW * p / ETc))`, written out in the test module. No engine module
is consulted.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Peak crop water demand | `etc_mm_per_day` (ETc) | mm/day | 2.5 – 8.0 |
| Total available water | `raw_mm` (TAW) | mm | 45 – 140 |
| Management-allowed depletion | `allowable_depletion` (p) | fraction | 0.30 – 0.55 |

Domain constraints of the published relation: `ETc > 0`, `TAW >= 0`, `p` in
(0, 1]. The implementation raises on the last two rather than reporting a number
a scheduler would read as "no irrigation needed" — a zero-day interval and a
negative depletion are both nonsense, and both are rejected with a message that
names the fraction, not the percentage, so `0.55` is passed and not `55`.

`p` values here are the published FAO-56 depletion fractions for small grains,
the range 0.40–0.55 being the interval FAO-56 chapter 8 gives for most crops
under standard conditions.

---

## 3. Tolerance

`tolerance_absolute = 0` days.

**Basis.** The output is an integer number of days: the published relation is
evaluated, rounded to the nearest whole day, and floored at 1 (a season shorter
than one interval still receives one application). Agreement is therefore exact
equality of the integer, and the tolerance is not loosened to accommodate more.
Python's round-half-to-even on a tie is exercised by case 2 (140 x 0.5 / 4 = 17.5,
whose nearest even integer is 18) and asserted here, so a change of rounding
convention would be caught.

---

## 4. Comparison table — model output vs reference output

| # | ETc (mm/day) | TAW (mm) | p | Model output `interval_days` | Reference (days) | Verdict |
|---|---|---|---|---|---|---|
| 1 | 6.0 | 100 | 0.55 | 9 | 9 | match |
| 2 | 4.0 | 140 | 0.50 | 18 | 18 | match |
| 3 | 5.0 | 100 | 0.50 | 10 | 10 | match |
| 4 | 8.0 | 100 | 0.55 | 7 | 7 | match |
| 5 | 2.5 | 60 | 0.40 | 10 | 10 | match |
| 6 | 3.0 | 45 | 0.30 | 4 | 4 | match |

Case 1 is the FAO-56 / Keller & Bliesner scheduling example (100 mm available in
the root zone, 55 % depletion allowed, 6 mm/day peak demand, 9-day interval).
The six cases span the published depletion range and demand rates, and the
intervals they produce (4 to 18 days) are the range in which the published
relation is actually used — FAO-56 notes that a scheduling interval computed this
way is then shortened by whatever the system's own scheduling constraints
impose.

---

## 5. Uncertainty statement

The comparison establishes **exact conformity to the published relation** over
the compared range, including its integer rounding and its one-day floor. There
is no residual numeric uncertainty: the model adds nothing to the
independently-evaluated relation.

The real uncertainty is all in the inputs, and one of them is decisive. `TAW`
depends on the difference between field capacity and permanent wilting point
integrated over the root depth — two soil water constants that in this
repository are held in a table whose published attribution has been withdrawn
(see `engine/data/soil_table.py` and `engine/data/SOIL_TABLE_CONFLICTS.md`, which
records that `SOIL_AWC` sits 30–157 % away from Saxton & Rawls (2006) depending
on the texture and the head correction). A caller who takes `TAW` from that
table and asks this model for an interval gets an interval whose uncertainty is
the table's, not the relation's. This record validates the scheduling relation;
it says nothing about the soil water constants fed into it.

---

## 6. Limitations

1. **The registry stays `unvalidated` even though every case matches.** The
   project's machine-enforced rule is that a model may claim `validated` only
   with an *external* anchor in
   `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`. There is no
   external-anchor row for the irrigation-scheduling family at all — the nearest
   row, `ENO_ETC_KC_001`, is `PARTIAL` and is about the Kc table, not the
   scheduling relation. Adding this model to the twelve models already listed as
   known unanchored debt in `engine/tests/test_machine_evidence_consistency.py`
   would grow that debt set, which its own docstring forbids, so the honest move
   is the register row, not the claim. The row that would move it is a *published
   observed irrigation interval from a scheduling trial*.
2. **`TAW` is user-supplied and is where the uncertainty lives.** The soil water
   constant table behind it is documented in this repository as a design
   assumption with published attribution withdrawn.
3. **Peak demand is assumed constant over the interval.** FAO-56's procedure
   substitutes the peak ETc of the period for a varying demand; the relation
   then has to be re-evaluated whenever the demand changes materially.
4. **Rounding convention pinned, not generalised.** The nearest-integer and
   one-day-floor behaviour is asserted for the six cases above; the round-half-
   to-even tie appears once (case 2) and is asserted there.
5. **No field or measured irrigation schedule is compared.** `VALIDATED_METHOD_CONFORMANCE`
   conformance to the published relation.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "IRRIGATION_INTERVAL",
  "model_name": "Irrigation Interval",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_irrigation_interval_solution",
  "reference": {
    "citation": "Allen, R.G., Pereira, L.S., Raes, D. & Smith, M., Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements, FAO Irrigation and Drainage Paper 56, 1998, Annex 2, read with Keller, J. & Bliesner, R.D., Sprinkle and Trickle Irrigation, 1990.",
    "equation": "interval_days = max(1, round(TAW * p / ETc)), p a fraction in (0, 1], ETc in mm/day"
  },
  "input_range": {
    "etc_mm_per_day": [2.5, 8.0],
    "raw_mm_taw": [45.0, 140.0],
    "allowable_depletion_fraction": [0.3, 0.55]
  },
  "output_key": "interval_days",
  "tolerance": {
    "absolute": 0.0,
    "basis": "the output is an integer number of days: the relation is evaluated, rounded to the nearest whole day and floored at one, so agreement is exact equality"
  },
  "cases": [
    {
      "name": "fao56_scheduling_example_silt_loam_wheat",
      "inputs": {"etc_mm_per_day": 6.0, "raw_mm": 100.0, "allowable_depletion": 0.55},
      "reference": 9,
      "recorded": 9,
      "verdict": "match"
    },
    {
      "name": "large_root_zone_light_demand",
      "inputs": {"etc_mm_per_day": 4.0, "raw_mm": 140.0, "allowable_depletion": 0.5},
      "reference": 18,
      "recorded": 18,
      "verdict": "match"
    },
    {
      "name": "moderate_demand_standard_depletion",
      "inputs": {"etc_mm_per_day": 5.0, "raw_mm": 100.0, "allowable_depletion": 0.5},
      "reference": 10,
      "recorded": 10,
      "verdict": "match"
    },
    {
      "name": "peak_demand_driven_shortening",
      "inputs": {"etc_mm_per_day": 8.0, "raw_mm": 100.0, "allowable_depletion": 0.55},
      "reference": 7,
      "recorded": 7,
      "verdict": "match"
    },
    {
      "name": "shallow_root_zone_drip_demand",
      "inputs": {"etc_mm_per_day": 2.5, "raw_mm": 60.0, "allowable_depletion": 0.4},
      "reference": 10,
      "recorded": 10,
      "verdict": "match"
    },
    {
      "name": "small_root_zone_small_grain_depletion",
      "inputs": {"etc_mm_per_day": 3.0, "raw_mm": 45.0, "allowable_depletion": 0.3},
      "reference": 4,
      "recorded": 4,
      "verdict": "match"
    }
  ],
  "validation_status": "unvalidated",
  "status_vocabulary_label": "VALIDATED_METHOD_CONFORMANCE",
  "registry_gap": "The model matches its published relation but the register has no external-anchor row for the irrigation-scheduling family; engine/tests/test_machine_evidence_consistency.py keeps the registry status at unvalidated until one is added.",
  "uncertainty": "Exact conformity to the published relation including its integer rounding and one-day floor. The model adds no residual numeric uncertainty; the decisive one is the user-supplied TAW.",
  "limitations": [
    "TAW is user-supplied and carries the soil water-constant uncertainty, which this record does not validate.",
    "Peak ETc is assumed constant over the interval; the relation must be re-evaluated when demand changes materially.",
    "The rounding convention and one-day floor are asserted for these six cases only.",
    "No field or measured irrigation schedule is compared."
  ]
}
```
