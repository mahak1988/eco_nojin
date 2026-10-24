# TOURISM ENTITY-MODEL DECISION — PROPOSED (awaiting the product owner)

* **Status:** **PROPOSED — not ratified.** An agent may not close this row; the approver is the
  product owner (see `docs/project/OPEN_DECISIONS.md`). Nothing changes in the code until it is
  signed. · **Authored:** 2026-10-11, P8 (A08)

## Options

| Option | What it means | Cost | Risk |
|---|---|---|---|
| **A — keep the 3-entity model** (`TourismGuide`, `TourismTour`, `TourismBooking`) | The lifecycle already covers guide verification, tour approval, capacity-enforced booking, payment confirmation, regenerative completion and the 800/200/200 bps fee split. The Phase-8 *behaviour* is already real; the 9-entity model adds vocabulary, not capability | none now | proposals/operators/departures/participants/incidents/refunds stay implicit → the museum-grade event registry and refund flows remain unavailable |
| **B — grow to the 9-entity model** (proposal, product, operator, approval, departure, participant, incident, refund) | Full expressiveness: a tour *proposal* that is not yet sellable, a *product* (sellable tour), an *operator profile*, *departures* with dates and capacity, *participants*, *incidents*, *refunds* | one migration + service refactor + tests | a second product plane (the marketplace already has proposals→approval→product); the work must reuse that pattern rather than invent a parallel one |
| **C — hybrid**: 3 entities + a minimal `TourEvent`/departure join now; incidents/refunds when a real requirement lands | Smallest step that makes *events* (festival/expo/seasonal market) and dated departures expressible | one table + join fields | two future migrations |

## Recommendation

**Option C now, Option B as the P8 follow-up.** The gap that hurts today is *dates*: a tour
without departures cannot be scheduled, and no capacity/refund flow can be tested against a
real instance. Incidents and refunds are the next pain point after the first real season, and the
decision for them is better made with operational evidence (eco.md's own principle: a roadmap
item must not be built on speculation).

## Constraints the recommendation respects

* **P-01 honesty**: no entity is added for vocabulary alone — each must carry a rule the current
  model cannot express (departures: date + per-departure capacity; the current capacity is per-tour
  only).
* **The existing 3-entity surface stays working**: the change is additive
  (a departure table + join columns), never a rewrite of the booking flow that the router and its
  33 tourism tests exercise.
* **Certification**: GSTC criteria remain a *design reference*; no entity, field or status may
  claim a GSTC certification (P8's phase card).

## Current verified state (P8, 2026-10-11)

* Guide verification, tour approval, capacity-enforced booking, payment confirmation, regenerative
  completion and the fee split: implemented (`services/tourism/service.py`) and served over
  `/api/v1/tourism`.
* The status payload is honest (`status: live` + `not_yet_available`, KN-01 closed in P1).
* Capacity refusal is enforced at the service and surfaced with a safe detail at the HTTP edge;
  the surface advertises no refund/cancellation path (pinned by
  `services/tourism/tests/test_p8_scope.py`).
