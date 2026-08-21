# 31. Phase 3 Sprint 2 — Calibration, UQ & Chain API

**Date:** 2026-08-17 | **Status:** Active | **Class:** Technical
**Basis:** Doc 30 (sprint 1); Doc 28.

> Sprint-2 delivery (part 1): Sobol' sensitivity + uncertainty analysis,
> structural RothC validation (analytic equilibrium), and the
> `POST /api/v1/simulation/run` endpoint with persistence.

## 1) Components (this commit)

| Component | Path | Role |
|---|---|---|
| Calibration/UQ | `simulation/calibration.py` | Saltelli sampling + Sobol' first/total indices — pure numpy |
| Ishigami test | `tests/unit/test_simulation_calibration.py` | implementation verified against the analytical function |
| RothC structural validation | new RothC tests | analytic equilibrium of all 4 pools + convergence + CO2 mass balance |
| Persistence table | `simulation_runs` (migration b1c2d3e4f5a6) | stores chain results |
| API router | `services/api_gateway/routers/simulation.py` | POST /run + GET /runs |
| Model | `SimulationRun` in database/models.py | site/scenario/outputs/status |

## 2) Sobol' (Saltelli 2010)
- Estimators: `S1_i = mean(f(B)·(f(AB_i) − f(A)))/Var`,
  `ST_i = mean((f(A) − f(AB_i))²)/(2·Var)` — with corrected indexing for the
  interleaved matrix layout.
- **Ishigami test** (N=8192): S1=(0.307, 0.431, −0.016),
  ST=(0.553, 0.447, 0.236) vs analytical (0.3139, 0.4424, 0) and
  (0.5576, 0.4424, 0.2437) — implementation verified.
- Distributions: uniform (bounds) and normal (mu/sigma); seed for
  reproducibility.

## 3) RothC Structural Validation (no reference data)
- For the monthly-discrete scheme: `pool_eq = in_pool/(1 − exp(−k_m))` with
  `k_m = RATE/12·T·W·P` and `total_dec = input/(1 − X_STAB)` (the stabilized
  fraction recycles through BIO/HUM until all C is respired).
- Model at 3000 years matches the analytic equilibrium for all 4 pools
  within <2%: DPM 0.86, RPM 17.05, BIO 7.45, HUM 285.6.
- Convergence: SOC identical at 3000 vs 10000 years; steady-state respired C
  ≈ annual input (mass balance).
- **Reference validation (official RothC-26.3 outputs) remains in sprint 2**
  — the model label stays `pending reference validation` until then.

## 4) API
```
POST /api/v1/simulation/run   ChainInputs JSON -> run chain + persist
GET  /api/v1/simulation/runs?site_id=...  list runs
```
- Each run stored with `status=ok|partial` (a failed stage = partial + message).
- Migration applies to SQLite dev and PostgreSQL.

## 5) Tests
- 11 new tests (calibration 6, API 3, RothC structural 2); full suite:
  **465 passed**.

## 6) Next (rest of sprint 2)
SWAT+ binary + output wiring to WEAP/HEC-RAS; RothC reference validation
with official data; real weather (ERA5 via CDS); chain outputs to the MRV
dashboard.
