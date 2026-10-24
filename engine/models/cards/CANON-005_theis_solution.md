# Model Card: CANON-005 — Theis Groundwater Drawdown

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-005` |
| **name** | Theis Non-Equilibrium Groundwater Drawdown |
| **version** | `1.0.0` |
| **scientific_domain** | Groundwater Hydrology |
| **intended_use** | Estimate drawdown in a confined aquifer due to a fully penetrating well at a specified observation point. Used for well spacing, pumping impact analysis, and aquifer parameter estimation. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Theis (1935) solution:<br>s = (Q / (4πT)) * W(u)<br>where:<br>  u = (r²S) / (4Tt)<br>  W(u) = −E₁(−u) = ∫_u^∞ (e^{−x}/x) dx  (exponential integral)<br>  s = drawdown [m]<br>  Q = pumping rate [m³/day]<br>  T = transmissivity [m²/day]<br>  S = storativity [dimensionless]<br>  r = radial distance from well [m]<br>  t = time since pumping started [days] |
| **equation_conventions** | Q positive for pumping (extraction). Drawdown s ≥ 0 indicates water level drop. u → 0 (large t or short r) gives W(u) → large (early time, large drawdown). u → ∞ (small t or large r) gives W(u) → 0 (no drawdown). E₁ computed via scipy.special.expi (−expi(−u)). |
| **assumptions** | (1) Confined, homogeneous, isotropic, infinite areal extent aquifer. (2) Fully penetrating line-source well. (3) Constant discharge, instantaneous storage release. (4) Horizontal flow only (vertical gradients negligible). (5) No recharge or leakage. (6) Radial (cylindrical) symmetry. |
| **applicability_domain** | Confined aquifers with known T and S. Valid for t > 0 after pump start. Not applicable to unconfined aquifers (use Dupuit or Neuman). Not for fractured rock without modification. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `model_type` (Literal["analytical"]), `transmissivity_m2day` (float, m²/day, >0), `storativity` (float, dimensionless, 0..1), `pumping_rate_m3day` (float, m³/day, ≥0), `observation_distance_m` (float, m, >0), `time_days` (float, days, >0) |
| **output_schema** | `drawdown_m` (float, m, ≥0), `model_description` (str) |
| **units** | Transmissivity in m²/day, storativity dimensionless, pumping rate in m³/day, distance in m, time in days. Drawdown in m. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Initial hydraulic head: s = 0 (no drawdown) at t = 0 everywhere. |
| **boundary_conditions** | Boundary condition: s → 0 as r → ∞ (no-flow at infinite distance). Outer boundary is at infinity; no inner boundary resistance (well is a line sink). |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Analytical closed-form solution via exponential integral. No spatial or temporal discretization. |
| **solver_configuration** | Not applicable — scipy.special.expi computes W(u). |
| **convergence_criteria** | Not applicable — exact analytical solution (limited by floating-point precision of scipy.special.expi). |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Theis, C.V. (1935). "The Source of Water Resulting from the Charging of a Well." *Transactions of the American Geophysical Union* 16(2): 512–513. Ferris, J.G. (1962). "Hydrogeologic Environment of the Piezometer." *Ground Water* 1(1): 8–12. Jacob, C.E. (1953). "Modeling a Leaky Artesian Basin." *Transactions of the American Geophysical Union* 34(2): 277–287. |
| **reference_cases** | THEIS_REFERENCE in conftest.py: T=2000 m²/day, S=0.0002, Q=760 m³/day, r=30 m, t=1 day. Drawdown is **0.3062 m** (0.3061683368958959 m measured 2026-10-10; u = 2.25e−5, W(u) = −E₁(−u) = 10.124802083725804, s = Q/(4πT)·W(u)). The value this card formerly printed, "approximately 0.018 m", was wrong by a factor of 17; the engine and an independent hand calculation both give 0.3062 m. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s04_groundwater.py` — Theis reference case checks drawdown against analytic value. |
| **analytical_tests** | Direct comparison against Theis analytic solution for known (Q, S, T, r, t): for THEIS_REFERENCE the closed form gives 0.3061683368958959 m and the engine returns the same value, so the equation is reproduced exactly. |
| **numerical_tests** | Property-based check: drawdown decreases with distance and increases with time (monotonicity). |
| **physical_consistency_tests** | Drawdown ≥ 0; drawdown decreases with r; drawdown increases with t for t < peak time; bounded by Q/(4πT) upper limit. |
| **empirical_validation** | Not validated against field data. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Series convergence of W(u) undocumented — this is the known P0 blocker. Input sensitivity on T, S, r, t via property-based testing. |
| **known_limitations** | (1) Scientific status: REQUIRES_SCIENTIFIC_REVIEW. Series convergence of the exponential integral is undocumented in the implementation. (2) Only model file in the engine that declares bounded inputs (gt, lt validators on input dataclass). (3) No REFERENCES dict declared in the file — citation is only recorded here. (4) Modflow integration path (mock_mode) is a stub that fabricates synthetic results without flagging them. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/hydroma/models/groundwater_model.py` (GroundwaterModel class). |
| **verification_status** | Implementation matches the design intent, and matches the Theis closed form on the reference case (0.3061683368958959 m, engine vs hand calculation). |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — the implementation reproduces the Theis (1935) closed form to machine precision against an independent `scipy.special.expi` evaluation (internal THEIS_REFERENCE, 0.3062 m). A genuine **published** external anchor now exists and is registered: the USGS *Python for Hydrology* worked example (s = 1.40636669 m for T=1000 m²/day, S=3e-4, Q=4088 m³/day, r=1000 m, t=10 d) is reproduced by the engine to 3.5e-9 m — vendored at `tests/reference_data/theis_usgs_worked_example.csv`, registered as `THEIS_DRAWDOWN_USGS`, locked by `tests/test_theis_usgs_external.py`. The model-card label is kept conservative by the P0-2 card guard; the registry-level external anchoring is carried by that register row. |
| **provenance** | `data_source: "simulated"`; `model: "Theis (1935)"`; `computed: True` |
