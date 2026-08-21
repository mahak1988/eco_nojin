# 30. Phase 3 Sprint 1 — Simulation Chain Core

**Date:** 2026-08-17 | **Status:** Active | **Class:** Technical
**Basis:** Doc 28 (Phase 3 kickoff); Doc 27 Phase 3.

> Sprint-1 delivery: `engine/hydroma/simulation/` — inter-model contracts,
> scenario matrix, RothC port, AquaCrop-OSPy 3.1 wrapper, and the
> RUSLE → AquaCrop → RothC chain orchestrator.

## 1) Components (this commit)

| Component | Path | Role |
|---|---|---|
| Data contracts | `simulation/contracts.py` | pydantic inter-model models + honesty labels (`data_source` + `model`) |
| Scenarios | `simulation/scenarios.py` | Baseline/Medium/Intensive matrix (CN, C-factor, P-factor) |
| RothC port | `simulation/runners/rothc_runner.py` | monthly RothC-26.3: 4 active pools + IOM, T/moisture modifiers, 46/54 split |
| AquaCrop wrapper | `simulation/runners/aquacrop_runner.py` | official `aquacrop==3.1.0`; synthetic or user weather; Yield/Biomass parse |
| RUSLE wrapper | in `orchestrator.py` | existing C++ core (analytic fallback, same equation) |
| Orchestrator | `simulation/orchestrator.py` | runs the chain for one site+scenario with full provenance |

## 2) Integration Notes (documented findings)
- **aquacrop 3.1**: weather column ORDER is positional —
  `MinTemp, MaxTemp, Precipitation, ReferenceET, Date` (Date last, matching
  the package's own CSVs); Crop planting/harvest dates are `MM/DD`;
  yield key is `Dry yield (tonne/ha)` (scaled to kg/ha); biomass comes from
  `get_crop_growth()['biomass']` taking the **season max** (tail reads 0
  after harvest).
- **RothC**: temperature modifier `47.9/(1+exp(106.06/(T+18.27)))` equals 1
  at ~10 C (not 25 C); moisture uses the standard piecewise; mass
  conservation is test-enforced.
- **Honesty**: every output carries `data_source="simulated"` + model
  name/version; model output is never presented as measured field data.

## 3) Validation Status (honest)
- RothC: **reference validation against official RothC-26.3 outputs in
  sprint 2** — until then the label reads
  `model="RothC (in-house port, pending reference validation)"`.
- AquaCrop: official FAO package — valid output; default weather is
  synthetic (real weather replacement in sprint 2).

## 4) Tests
- 23 new tests (RothC: mass balance, decay, temperature effect, moisture
  branches; AquaCrop: full wheat season; orchestrator: full chain, erosion
  reduction matches factors, honesty labels).
- Full suite: **454 passed** (from 431).

## 5) Next (Sprint 2)
SWAT+ binary + output wiring to WEAP/HEC-RAS; calibration (Sobol + UQ);
RothC reference validation; real weather; `POST /api/v1/simulation/run`.
