# 28. Phase 3 Kickoff — Integrated Simulation Chain

**Date:** 2026-08-17 | **Status:** Ready | **Class:** Technical
**Basis:** Doc 27 Phase 3 (weeks 5–10); PDF section 41; no-Docker architecture.

## Strategy
Integrate validated world models via standard wrappers (`run(inputs)->outputs`),
orchestrated in Python with inter-model data contracts. No reimplementation of
validated models.

| Model | Approach | Status |
|---|---|---|
| SWAT+ | binary subprocess + file I/O | download/license from swat.tamu.edu (start early) |
| RUSLE | existing in project | ready |
| AquaCrop | `aquacrop==3.1.0` (FAO OSPy) | on PyPI (verified) |
| RothC | in-house port of reference equations (~200 lines, biochar pools) | sprint 1 |
| WEAP | free for research; or in-house allocation module | decision sprint 2 |
| HEC-RAS | USACE binary; v1 = existing Saint-Venant core | v1 ready |

## Data Contracts
SWAT+ → {runoff_mm, recharge_mm, baseflow_mm} → WEAP, HEC-RAS
RUSLE → {erosion_t_ha_yr, c_factor} → MRV
AquaCrop → {yield_kg_ha, biomass, residue_kg_ha, wue} → RothC
RothC → {soc_change_t_ha_yr, co2e_t_ha} → MRV
Scenarios Baseline/Medium/Intensive: CN (−2..8 / up to −15), Ks, AWC,
C-factor (from NDVI), P-factor (0.45–0.55 / 0.3–0.4).
Shared JSON Schema in `engine/hydroma/simulation/contracts.py` + caching +
`data_source` labels.

## Structure
`engine/hydroma/simulation/`: contracts.py, orchestrator.py, scenarios.py,
runners/{base,swat,aquacrop,rothc,hecras}_runner.py, calibration.py
(Sobol + Monte Carlo UQ, EnKF-lite).

## Sprint 1 (w1–2)
1. pip install aquacrop==3.1.0 + wheat example test.
2. rothc_runner against published data.
3. contracts + orchestrator with RUSLE+AquaCrop + scenarios.
4. ≥10 new tests; keep 385+ green.

## Risks
SWAT+ license/data prep is the longest pole — start early; pin model versions;
verify aquacrop 3.x on Python 3.11.
