# Model Card: CANON-015 — Watershed Calculator

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-015` |
| **name** | Watershed Calculator |
| **version** | `1.0.0` |
| **scientific_domain** | Hydrology (Watershed Delineation) |
| **intended_use** | Aggregate flow direction and accumulation across a watershed to delineate catchments, identify stream networks, and route overland flow to outlets. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Combines D8 flow direction (CANON-008) with flow accumulation. Watershed delineation: starting from an outlet cell, trace upstream following reverse flow direction arrows. Stream network: cells where flow accumulation exceeds a threshold (cells or km²).<br><br>**Time of concentration** — the only Tc equation implemented in this module is **Kirpich (Tc in minutes, metric):**<br>Tc = 0.0195 · L^0.77 · S^−0.385<br>where L = longest flow path [m] and S = average slope **[m/m]**. `engine/hydroma/watershed/calculator.py:850`. For L = 1000 m and S = 0.01 (1 %), Tc = 23.44 minutes (23.44415647503955).<br><br>**Divergence of record:** this card used to advertise `Tc = L / (v × S^0.5)` ("velocity form"). No such equation exists anywhere in the tree, and no velocity parameter is accepted by any function here. The card now states what the module implements. |
| **equation_conventions** | Uses D8 8-connected flow. Catchment area = sum of all upstream cells × cell_area. Stream threshold in number of cells or area. Flow path length in metres. Kirpich slope in **m/m** (a duplicate in `engine/land/drainage.py` formerly fed percent and labelled the result hours; it now delegates to `calculator.calculate_kirpich_tc`). |
| **assumptions** | (1) Single flow direction (D8). (2) Uniform rainfall excess over the watershed. (3) No groundwater contribution. (4) Channel networks follow the D8-derived flow paths. |
| **applicability_domain** | Gridded DEM-based watershed analysis. Valid for catchments with clear topographic structure. Not suitable for flat or heavily modified terrain without preprocessing. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `dem` (2D array, metres), `cell_size_m` (float, >0), `outlet_row` (int), `outlet_col` (int), `stream_threshold_cells` (int, optional) |
| **output_schema** | `watershed_mask` (2D boolean array), `catchment_area_km2` (float, km²), `stream_network` (2D boolean array), `flow_path_length_km` (float, km) |
| **units** | DEM in metres, cell size in metres, area in km², lengths in km. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — single-pass computation. |
| **boundary_conditions** | Watershed boundary: defined by the outlet location. Flow exits at the grid edge. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | D8 grid traversal. Downstream tracing for watershed delineation. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | O'Callaghan, P.L., Mark, D.M. (1984). "The Extraction of Drainage Networks." *Computer Graphics and Image Processing* 23: 323–347. Kirpich, P.Z. (1940). "Time of Concentration in Small Agricultural Watersheds." *Civil Engineering* 10(6): 362. |
| **reference_cases** | **No published watershed reference case is stored in this repository.** `engine/land/tests/test_kirpich_agreement.py` and `engine/strict_tests/test_s06_watershed_design.py` carry the synthetic anchors. **Retired citation:** a "McCool 1989 reference data" entry appeared here; McCool's work concerns the RUSLE LS steepness factor (CANON-007), not watershed delineation, and no McCool reference data exists in the tree. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/strict_tests/test_s18_scientific_validation.py::TestWatershedDesignIndependent` — the check-dam / structure sizing routes (rational method and geometry), which are what the gateway exposes. `engine/land/tests/test_kirpich_agreement.py` — the canonical Kirpich implementation and the drainage duplicate's agreement with it. `engine/hydroma/watershed/calculator.py` also holds the Muskingum routing, Strahler ordering and Horton ratios, exercised by `engine/strict_tests/test_s06_watershed_design.py`. There is no strict_tests/test_s06_hydrology_watershed.py. |
| **analytical_tests** | Synthetic watershed with known catchment area; check-dam sizing through the broad-crested weir law. |
| **numerical_tests** | Catchment area equals sum of upstream cells × cell_area. Kirpich Tc decreases with slope and increases with length. |
| **physical_consistency_tests** | Watershed mask is contiguous. Outlet cell is on the watershed boundary. Kirpich Tc is positive, finite and monotone in L and S. |
| **empirical_validation** | Synthetic DEMs and closed-form structure geometry only. **No published watershed benchmark is stored in the repository** — there is no Kirpich Tc reference table, no Theis reference, no published catchment delineation case. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity on DEM resolution and outlet location. No formal UQ. |
| **known_limitations** | (1) Depends on D8 accuracy; single flow direction introduces dispersion errors. (2) **There is no watershed delineation code in this module.** `engine/hydroma/watershed/calculator.py` implements structure sizing, Strahler/Horton morphometry, Kirpich Tc and Muskingum routing; the D8 flow direction and accumulation it consumes live in `engine/land/hydrology`, and the terrain attributes in `engine/land/terrain_analysis.py`. The card's `implementation_status` formerly implied the module delineates catchments itself. (3) Bransby-Williams, California Tc, Snyder and unit-hydrograph methods are not implemented anywhere in the tree. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production, but not a delineator — `engine/hydroma/watershed/calculator.py` provides: structure sizing (`design_check_dam`, `design_contour_trench`, `design_half_moon`, `design_terrace`, `design_gully_plug`), Strahler ordering and Horton ratios, **Kirpich Tc** (`calculate_kirpich_tc`, line 829) and Muskingum routing. The D8 direction/accumulation it consumes come from `engine/land/hydrology.py`; terrain attributes from `engine/land/terrain_analysis.py`. |
| **verification_status** | The structure-sizing routes are checked against the rational method and the trapezoid/weir closed forms (`test_s18::TestWatershedDesignIndependent`). Kirpich Tc and the `engine/land/drainage.py` duplicate are shown to agree (see §7). No published reference case exists for any of it. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — every implemented quantity is re-derived independently inside a test. **No externally published value for this module is stored in the repository**, so nothing here is `VALIDATED_EXTERNAL`. **Retired claims:** "Validated against benchmark cases" (the benchmark cases were synthetic) and the "McCool 1989 reference data" citation (McCool's work concerns the RUSLE LS factor, CANON-007, not this module). |
| **provenance** | `data_source: "simulated"`; `model: "Watershed Calculator v1.0"`; `computed: True` |
