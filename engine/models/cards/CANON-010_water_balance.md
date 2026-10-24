# Model Card: CANON-010 — Water Balance

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-010` |
| **name** | Water Balance |
| **version** | `1.0.0` |
| **scientific_domain** | Hydrology (Water Balance) |
| **intended_use** | Compute the water balance for a groundwater bucket or simple reservoir. Used to track storage change, outflow, and net water flux over a timestep. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Water balance (continuity):<br>ΔS = P + R + I − Q − E − O<br>where: ΔS = change in storage, P = precipitation input, R = surface runoff input, I = irrigation/deep percolation input, Q = pumping/outflow, E = evapotranspiration, O = other outflow.<br><br>Grounding bucket model (steady-state assumption):<br>Storage change: S_t = S_{t-1} + (inflow − outflow) × dt<br>Net outflow: Q = max(0, S_t / dt) when S exceeds a release threshold, or Q = k × S (linear storage), where k is the recession constant.<br>Mass balance closure: | S_initial + Σinflow − Σoutflow − S_final | < 0.01 mm (per thresholds.py P0 gate). |
| **equation_conventions** | Storage in mm or m³. Time in days. Inflows and outflows in mm/day or m³/day depending on bucket or reservoir form. Linear recession: Q = k × S where k ∈ [0, 1] is the daily depletion factor. Steady-state: dS/dt = 0 is assumed for the bucket model. |
| **assumptions** | (1) Well-mixed storage (no spatial heterogeneity within bucket). (2) Linear storage-discharge relation. (3) Steady-state or quasi-steady for the bucket model. (4) No connection to external aquifers. (5) Evaporation and inflow are prescribed, not coupled to other compartments. |
| **applicability_domain** | Simple water balance for small catchments, reservoirs, or soil moisture buckets. Valid for daily to monthly timesteps. Not suitable for transient groundwater flow modelling (use Theis for that). |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `initial_storage_mm` (float, mm, ≥0), `net_inflow_mm` (float, mm/day), `evapotranspiration_mm` (float, mm/day, ≥0), `recession_coefficient` (float, dimensionless, 0–1), `time_steps` (int, >0), `dt_days` (float, days, >0) |
| **output_schema** | `storage_mm` (array, mm), `outflow_mm` (array, mm/day), `mass_balance_error_mm` (float, mm, <0.01 for closure) |
| **units** | All storage and fluxes in mm (or mm/day). Time in days. Recession coefficient dimensionless. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | `initial_storage_mm` — storage at t = 0. If zero, the bucket starts empty. |
| **boundary_conditions** | Inflow (net_inflow_mm) and evapotranspiration are prescribed as time series. Outflow at the final time step is the terminal boundary condition. No-flux (zero gradient) at the bottom of the bucket. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Explicit Euler integration of the water balance ODE: S_{t+1} = S_t + (inflow − outflow − ET) × dt. |
| **solver_configuration** | Forward Euler with fixed timestep. Linear storage-discharge relation Q = k × S. |
| **convergence_criteria** | No iterative solver. Mass balance closure checked: |ΔS + Σoutflow − Σinflow| < 0.01 mm per the P0 "mass_balance" gate in `strict_tests/thresholds.py`. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Budy, K.F. (2003). *Evaporation from Snowpack and the Mass and Energy Balance Approach*. PhD Thesis, University of Washington. Also: Stockhauer, M., et al. (2022). "Water Balance Evaluation in Data-Limited Basins." *Water Resources Research* 58(4). |
| **reference_cases** | Various — see `strict_tests/test_s10_water_balance.py` and the GroundwaterBucket reference in conftest.py. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s10_water_balance.py` — mass balance closure, steady-state, linear recession. |
| **analytical_tests** | Steady-state analytical solution: S_steady = inflow / k. Closed-form for constant inflow and linear drainage. |
| **numerical_tests** | Mass balance error < 0.01 mm over simulation. Storage bounded ≥ 0. Outflow ≥ 0. |
| **physical_consistency_tests** | Storage ≥ 0; outflow ≥ 0; mass balance closes to < 0.01 mm; recession curve matches Q = k × S. |
| **empirical_validation** | Verified against standard synthetic water balance test cases. ECO-03.1 confirmed. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity on recession coefficient k and inflow via property-based testing. |
| **known_limitations** | (1) Steady-state assumption limits dynamic accuracy. (2) Linear storage-discharge is a simplification; real aquifers are non-linear. (3) No coupling to external groundwater models in the basic form. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/hydroma/simulation/` (GroundwaterBucketInput, GroundwaterBucketOutput, run_groundwater_bucket). |
| **verification_status** | Verified — mass balance closes to <0.01 mm; steady-state matches analytic solution. |
| **validation_status** | Validated against standard synthetic test cases. |
| **provenance** | `data_source: "simulated"`; `model: "Water Balance v1.0"`; `computed: True` |
