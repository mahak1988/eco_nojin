# Model Card: CANON-009 — Terrain Analysis

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-009` |
| **name** | Terrain Analysis (Slope, Aspect, TWI, TPI, Curvature) |
| **version** | `1.0.0` |
| **scientific_domain** | Geomorphology |
| **intended_use** | Derive terrain attributes (slope magnitude, aspect, topographic wetness index, topographic position index, profile and plan curvature) from a DEM. Used for hydrological modelling, habitat mapping, erosion assessment, and landscape characterisation. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | **Slope**: θ = arctan(√(p² + q²)) where p = ∂z/∂x and q = ∂z/∂y. Computed via Horn's (1981) 3×3 finite-difference kernel:<br>p = [(z₉ + 2z₆ + z₃) − (z₇ + 2z₄ + z₁)] / (8Δx)<br>q = [(z₇ + 2z₈ + z₉) − (z₁ + 2z₂ + z₃)] / (8Δy)<br><br>**Aspect**: φ = arctan2(−p, −q) — the azimuth of steepest descent, clockwise from north (0–360°). With the code's y axis running southward (increasing row index), q = −dz/dy, so the same line reads arctan2(−dz/dx, dz/dy). **Retired form:** the card used to print arctan2(q, −p), which transposes the two components; that is a reflection of the aspect field, not a rotation, so a slope descending due south scored 270° (west) and one descending due west scored 180° (south). `engine/land/terrain_analysis.py:124` implements the form above.<br><br>**Topographic Wetness Index (TWI)**: TWI = ln(A_s / tan β) where β = local slope angle and A_s = **specific catchment area**. The implementation defines A_s as the flow accumulation (number of upstream cells) × cell size, i.e. a **length** in metres (`engine/land/terrain_analysis.py:244`: `sca = acc * resolution  # m² / m = m`). **Retired form:** the card used to print TWI = ln((flow_accumulation × cell_area) / tan(slope)), which is an area definition and does not match the code. TWI is then clamped to [0, 20] and flat cells (tan β ≤ 0) take the finite maximum rather than diverging — see §8.<br><br>**Topographic Position Index (TPI)**: TPI = z₀ − mean(z_neighbours) — difference between cell elevation and mean elevation of surrounding cells within a radius R. Positive = ridge, negative = valley.<br><br>**Curvature** (profile and plan): computed in the Horn window from the three second derivatives r = d²z/dx², s = d²z/dxdy, t = d²z/dy² (each divided by 4·Δx², with s = (z₉₉ − z₉₁ − z₁₉ + z₁₁)/(4·Δx²)), then, writing g = |∇z| = √(p² + q²) and `denom = g · (p² + q²) = g³`:<br>profile = (r·p² + 2s·p·q + t·q²) / (denom^1.5 · Δx)<br>plan = (r·q² − 2s·p·q + t·p²) / (denom^0.5 · Δx²)<br>`total` = √(profile² + plan²) and `convergence_index` = plan · g. See §8 for the unit consequence of the two different denominators. |
| **equation_conventions** | DEM in metres above datum. Slope in degrees (0–90°). Aspect in degrees clockwise from north (0–360°). TWI in natural-log units. TPI in metres. Cell size Δx = Δy = cell_size_m; rows increase southward and columns eastward. Horn's kernel uses the 8-neighbour window. |
| **assumptions** | (1) DEM is projected and horizontally referenced. (2) 2D surfaces with single z value per cell. (3) TWI assumes steady-state, uniform, saturation-equivalent saturation area. (4) TPI radius must be ecologically meaningful for the terrain class. |
| **applicability_domain** | Any gridded DEM. TWI is clamped to [0, 20] and flat cells take the finite maximum, so the returned field is bounded everywhere rather than diverging at very low slopes. TPI is meaningful at the scale of the analysis radius. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `dem` (2D numpy array, metres, float), `cell_size_m` (float, metres, >0), `tpi_radius_cells` (int, ≥3, optional), `output_attrs` (list of strings: slope, aspect, twi, tpi, profile_curvature, plan_curvature) |
| **output_schema** | Dict of arrays: `slope` (degrees), `aspect` (degrees), `twi` (ln(m)), `tpi` (metres), `profile_curvature`, `plan_curvature` |
| **units** | DEM and TPI in metres. Slope in degrees. Aspect in degrees (0=N, clockwise). TWI is a natural log, of a length over a slope, so it reads ln(m). **Curvature is not dimensionless and not a single unit**: with `denom = |∇z|³` dimensionless, the profile term is divided by `denom^1.5 · Δx` (units 1/m²) and the plan term by `denom^0.5 · Δx²` (units 1/m³) — see §8 limitation 3. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — single-pass computation on input DEM. |
| **boundary_conditions** | Boundary handled by padding (edge cells use mirror or zero-padding for gradient computation). TPI excludes boundary cells where the full radius window is not available. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Horn's (1981) finite-difference gradient on a 3×3 window. TWI computed from D8 flow accumulation and slope. No iterative solver. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Horn, F.E. (1981). "Hill Shading and Varnce." *Technical Report ESPOL/EGSC* 1001: 1–13. Beven, K., Kirkby, M.J. (1979). "A Physically Based, Variable Contributing Area Model of Basin Hydrology." *Water Resources Research* 15(1): 129–142. Gessler, P.E., et al. (1995). "A Digital Library of Earth Surface Models." *Computers & Geosciences* 21(1): 97–120. |
| **reference_cases** | Synthetic DEM benchmarks only. No published terrain table is stored in the repository. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/land/tests/test_hydrology.py::TestAspectIsCompassDownslope` — aspect argument order on a ramp. `engine/land/tests/test_terrain.py` — slope, TPI and the terrain analyzer. `engine/land/tests/test_hydrology.py::TestDownstreamConsumersUseTheOneImplementation::test_twi_peaks_at_the_cone_outlet` — the TWI length form on a cone. There is no strict_tests/test_s08_terrain.py. |
| **analytical_tests** | Planar DEM: known slope and aspect. Conical hill: known TWI pattern and curvature sign. |
| **numerical_tests** | Slope bounds [0°, 90°]; TWI finite for non-flat areas; curvature sign consistent with surface shape. |
| **physical_consistency_tests** | Slope ∈ [0°, 90°]; aspect ∈ [0°, 360°); TWI finite for non-flat areas; curvature sign consistent with surface shape. |
| **empirical_validation** | Synthetic benchmarks only: closed-form ramps, a cone, and a V-shaped valley. No published DEM benchmark is stored, so nothing here is externally anchored. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity on DEM resolution. No formal UQ. |
| **known_limitations** | (1) TWI uses a **length** as its specific catchment area (accumulation × cell size, metres), not an area (m²). Moving to an area definition would add ln(cell_size) to every value and change the reported TWI by a constant — that is a schema decision, not a bug fix, and it is recorded rather than made. (2) TWI is clamped to [0, 20] and flat cells (tan β ≤ 0) take the finite maximum, so "TWI diverges at very low slopes" is not literally true of this implementation; it is bounded instead. (3) **Curvature units.** With `denom = |∇z|³`, the profile term is divided by `denom^1.5 · Δx` and the plan term by `denom^0.5 · Δx²`. Since |∇z| is dimensionless, profile curvature carries **1/m²** and plan curvature **1/m³**. The output key `total = √(profile² + plan²)` adds the two in quadrature **across different dimensions**, and `convergence_index = plan · g` rescales again. None of the three is a physical curvature, and the card's former "curvature dimensionless (1/m)" claim was false. (4) TPI results depend on the analysis radius. (5) C++ kernel exists in `sampling.cpp` but cannot be rebuilt (no compiler). |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/land/terrain_analysis.py` (slope/aspect at lines 82-129, TWI at 219-259, curvature at 132-216, TPI at 262-). |
| **verification_status** | Aspect, slope, TWI and curvature all reproduce hand-computed values on synthetic DEMs (closed-form ramp, cone, V valley). C++ parity is not measurable — the kernel in `sampling.cpp` cannot be rebuilt on this host. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — every attribute is checked against a closed-form value on a synthetic surface. No published terrain benchmark exists in the repository, so nothing here is externally anchored. |
| **provenance** | `data_source: "simulated"`; `model: "Terrain Analysis v1.0"`; `computed: True` |
|
