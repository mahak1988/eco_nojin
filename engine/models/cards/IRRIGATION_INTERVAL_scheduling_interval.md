# Model Card: IRRIGATION_INTERVAL — Irrigation Interval

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `IRRIGATION_INTERVAL` |
| **name** | Irrigation Interval |
| **version** | `1.0.0` |
| **scientific_domain** | Irrigation scheduling |
| **intended_use** | Report how many days a scheduler should wait between applications, from the root-zone total available water, the management-allowed depletion and the peak crop demand. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | I = (TAW * p) / ETc — FAO Irrigation and Drainage Paper 56 (Allen et al. 1998), Annex 2, read with Keller & Bliesner (1990). `TAW` is the total available water in the root zone (mm), `p` the management-allowed depletion **fraction** and `ETc` the peak daily demand (mm/day). |
| **equation_conventions** | The result is rounded to the nearest whole day and floored at one: a season shorter than one interval still gets one application. `p` is a fraction in (0, 1]; both bounds are enforced because a percentage written where a fraction belongs is a factor of 100 on the schedule. |
| **assumptions** | (1) Peak demand is constant over the interval — the relation is re-evaluated when the demand changes materially. (2) `TAW` is supplied by the caller and carries the soil water-constant uncertainty, which this model does not own. |
| **applicability_domain** | `ETc > 0`, `TAW >= 0`, `p` in (0, 1]. `ETc <= 0` has no finite answer and is rejected rather than reported as a zero-day interval, which a scheduler would read as "no irrigation needed". |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `etc_mm_per_day` (float, mm/day, > 0), `raw_mm` (float, mm, TAW, >= 0), `allowable_depletion` (float, fraction, in (0, 1]) |
| **output_schema** | `interval_days` (int, days), `units` |
| **units** | Demand in mm/day; TAW in mm; depletion as a fraction; the interval in days. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/irrigation/scheduler.py::calculate_interval`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_irrigation_interval_solution`. |
| **verification_status** | Verified — the implementation reproduces the published relation exactly, including its integer rounding and its one-day floor, over six comparison cases spanning the published depletion range; see `engine/validation/IRRIGATION_INTERVAL.md`. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — the implementation reproduces the published FAO-56 Annex 2 / Keller & Bliesner scheduling interval exactly, including its integer rounding and its one-day floor, over six comparison cases spanning the published depletion range; the evidence record is `engine/validation/IRRIGATION_INTERVAL.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. The registry is left at `unvalidated` for this model, because the machine-readable evidence register has no external-anchor row for the irrigation-scheduling family and `engine/tests/test_machine_evidence_consistency.py` will not credit a registry-level claim for it without one. The row to add is a published observed irrigation interval from a scheduling trial. |
| **provenance** | `data_source: "computed"`; `model: "FAO-56 Annex 2 / Keller & Bliesner 1990"`; `computed: True` |
| **validation_record** | `engine/validation/IRRIGATION_INTERVAL.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/strict_tests/test_s08_irrigation.py` |
