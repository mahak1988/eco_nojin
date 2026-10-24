# Model Card: CANON-008 — D8 Flow Direction and Flow Accumulation

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-008` |
| **name** | D8 Flow Direction and Flow Accumulation |
| **version** | `1.0.0` |
| **scientific_domain** | Hydrology (Watershed Delineation) |
| **intended_use** | Determine flow direction on a raster DEM and compute upslope flow accumulation. Used as a prerequisite for watershed delineation, stream network extraction, and overland flow routing. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | D8 algorithm (O'Callaghan & Mark, 1984):<br>1. For each cell, identify the steepest downslope neighbour among 8 connected cells (360° flow direction).<br>2. Flow direction θ = arctan2(dy, dx) where dy, dx are the elevation differences to the downslope neighbour. Direction encoded as: E=1, SE=2, S=4, SW=8, W=16, NW=32, N=64, NE=128 (ESRI convention).<br>3. Flow accumulation: for each cell, FA = 1 + Σ(FA of upslope neighbours).<br>θ valid range: 0–360° (clockwise from north). A flat cell (no downslope neighbour) is assigned to itself or a depression-flattened outlet. |
| **equation_conventions** | Grid-based raster with cells at (row, col) positions. Neighbour search via 3×3 window. Slope in rise/run (dimensionless). Flow direction encoded as Powers-of-2. Flow accumulation counts the number of upslope cells draining through each cell. |
| **assumptions** | (1) Single flow direction (one downslope neighbour per cell). (2) DEM is preprocessed for depression filling/flat resolution. (3) Flow is along cell centres; no sub-grid representation of divergent/convergent flow. (4) No flow width correction at cell boundaries. |
| **applicability_domain** | Gridded DEM data on a regular square lattice. Valid for 8-connected flow. Not suitable for highly divergent terrain (use D-inf or MFD instead). |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `dem` (2D numpy array, metres, float), `cell_size` (float, metres, >0), `flat_resolution_strategy` ("min" or "max") |
| **output_schema** | `flow_direction` (2D array, Powers-of-2 encoding), `flow_accumulation` (1D or 2D array, cell count, ≥1), `slope_degrees` (2D array, degrees, ≥0) |
| **units** | DEM in metres, cell size in metres, slope in degrees. Flow accumulation is dimensionless (cell count). |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — single-pass computation. |
| **boundary_conditions** | Boundary cells: edges of the DEM grid. Flow directions at edges that point outside the grid are clipped; accumulation only counts in-grid contributors. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Deterministic grid traversal (recursive or iterative D8). Not iterative in the numerical sense. |
| **solver_configuration** | Not applicable. Order of execution may affect recursion depth for large grids (iterative DFS used). |
| **convergence_criteria** | Not applicable — finite algorithm. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | O'Callaghan, P.L., Mark, D.M. (1984). "The Extraction of Drainage Networks from Digital Elevation Data." *Computer Graphics and Image Processing* 23: 323–347. McCool, D.K. et al. (1989). "Slope-Percentage and Slope-Gradient Methods for Determining Slope-Slope Relationships." *Transactions of the ASAE* 32(5): 1670–1677. |
| **reference_cases** | McCool 1989 reference data in conftest.py — D8 flow path on a synthetic DEM. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s06_hydrology_watershed.py` — D8 flow direction against McCool 1989; flow accumulation checks. |
| **analytical_tests** | Synthetic DEM with known flow paths and accumulation counts. |
| **numerical_tests** | Flow accumulation sum equals total cell count; D8 directions form a DAG (no cycles after flattening). |
| **physical_consistency_tests** | Flow accumulation ≥ 1; flow direction points to a lower-elevation neighbour; no flow divergence > 8 cells. |
| **empirical_validation** | Benchmarked against McCool (1989) reference. ECO-03.1 confirmed. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity on DEM resolution and depression filling strategy. No formal UQ. |
| **known_limitations** | (1) Single-direction D8 cannot represent flow dispersion. (2) Sensitivity to DEM preprocessing (filling, smoothing). (3) Grid resolution must be adequate to terrain heterogeneity. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/land/hydrology.py` (D8FlowDirectionCalculator). |
| **verification_status** | Verified — matches McCool (1989) reference. |
| **validation_status** | Validated against benchmark. |
| **provenance** | `data_source: "simulated"`; `model: "D8 Flow Direction v1.0"`; `computed: True` |
