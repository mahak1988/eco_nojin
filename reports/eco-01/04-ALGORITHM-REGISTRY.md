# ECO-01 Algorithm Registry

**Document ID:** ECO-01-04-ALGORITHM-REGISTRY  
**Scope:** engine/ + services/ algorithms  
**Purpose:** Catalog all algorithms with classification, complexity, and assessment

---

## 1. Taxonomy Legend

**Algorithm Type:**
- NUMERICAL_METHOD - Mathematical computation method
- OPTIMIZATION_METHOD - Finding optimal solution
- SIMULATION_METHOD - Time/event-based simulation
- STATISTICAL_METHOD - Statistical computation
- MACHINE_LEARNING - ML algorithms
- GIS_METHOD - Geospatial computation
- DATA_PROCESSING_METHOD - Data transformation
- IMAGE_PROCESSING - Image analysis
- CONTROL_FLOW - Control logic

**Complexity:** LOW (simple), MEDIUM (moderate), HIGH (complex)

---

## 2. Complete Algorithm Catalog

### Algorithm ALG-001: Newton-Raphson Root Finding

| Field | Value |
|-------|-------|
| **algorithm_name** | Newton-Raphson Iterative Root Finding |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Mathematics / Numerical Analysis |
| **purpose** | Find roots of real-valued functions |
| **input** | Function f(x), derivative f'(x), initial guess x0, tolerance, max iterations |
| **output** | Root x where f(x) = 0 |
| **complexity** | MEDIUM |
| **time_complexity** | O(k) where k = iterations until convergence |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/soil/physics.py:89-123 |
| **used_by** | Van Genuchten inverse calculation |
| **assumptions** | Differentiable function; good initial guess |
| **failure_modes** | Derivative → 0; oscillation; divergence |
| **known_issues** | No convergence check documented; fallback for divergence? |
| **scientific_basis** | Standard numerical methods; Newton (1665) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-002: Hargreaves ET0

| Field | Value |
|-------|-------|
| **algorithm_name** | Hargreaves Temperature-Based ET |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Agriculture / Climate |
| **purpose** | Estimate ET0 from temperature data |
| **input** | T_min, T_max, R_a, elevation, latitude, day_of_year |
| **output** | ET0 (mm/day) |
| **complexity** | LOW |
| **time_complexity** | O(1) |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/climate/et_calculator.py:300-380 |
| **used_by** | Water demand estimation, irrigation scheduling |
| **assumptions** | Temperature correlates with solar radiation |
| **failure_modes** | Very cold/hot climates → over/underestimation |
| **scientific_basis** | Hargreaves & Samani (1985) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-003: Penman-Monteith

| Field | Value |
|-------|-------|
| **algorithm_name** | FAO-56 Penman-Monteith |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Agriculture / Climate |
| **purpose** | Compute reference crop ET0 |
| **input** | T_mean, T_min, T_max, wind_speed, humidity, radiation, elevation |
| **output** | ET0 (mm/day) |
| **complexity** | HIGH |
| **time_complexity** | O(1) per timestep |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/climate/et_calculator.py:54-289 |
| **used_by** | Water demand estimation, irrigation scheduling, EPIA |
| **assumptions** | Reference crop: 0.12m tall, green, well-watered |
| **failure_modes** | Missing radiation → defaults; missing wind → underestimation |
| **scientific_basis** | FAO-56 Allen et al. (1998) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-004: SCS-CN Runoff

| Field | Value |
|-------|-------|
| **algorithm_name** | SCS Curve Number Runoff |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Hydrology |
| **purpose** | Estimate direct runoff from precipitation |
| **input** | P (precipitation), CN (curve number) |
| **output** | Q (runoff depth) |
| **complexity** | LOW |
| **time_complexity** | O(1) |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/models/runoff_model.py:45-98 |
| **used_by** | Flood estimation, watershed analysis |
| **assumptions** | Homogeneous watershed; constant CN |
| **failure_modes** | Very low rainfall → no runoff; CN too high → excessive runoff |
| **scientific_basis** | USDA SCS (1972) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-005: Darcy's Law

| Field | Value |
|-------|-------|
| **algorithm_name** | Darcy Groundwater Flow |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Hydrogeology |
| **purpose** | Compute flow through porous media |
| **input** | K (conductivity), A (area), dh (head difference), dl (distance) |
| **output** | Q (flow rate) |
| **complexity** | LOW |
| **time_complexity** | O(1) |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/models/groundwater_model.py:8-92 |
| **used_by** | Groundwater flow analysis |
| **assumptions** | Laminar flow; saturated media |
| **failure_modes** | Unconfined flow → variable saturated thickness |
| **scientific_basis** | Darcy's Law (1856) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-006: Theis Well Function

| Field | Value |
|-------|-------|
| **algorithm_name** | Theis Transient Flow Solution |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Hydrogeology |
| **purpose** | Compute drawdown in confined aquifer over time |
| **input** | Q, T, S, r, t |
| **output** | s (drawdown) |
| **complexity** | MEDIUM |
| **time_complexity** | O(n) where n = series terms for W(u) convergence |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/models/groundwater_model.py:93-210 |
| **used_by** | Pumping test analysis |
| **assumptions** | Confined aquifer; infinite extent; Darcian flow |
| **failure_modes** | u → 0 (large r/small t): W(u) → large values; numerical overflow; u → ∞: W(u) → 0 |
| **scientific_basis** | Theis (1935); series expansion of exponential integral |
| **status** | REQUIRES_SCIENTIFIC_REVIEW |
| **confidence** | MEDIUM |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

### Algorithm ALG-007: Van Genuchten Forward Model

| Field | Value |
|-------|-------|
| **algorithm_name** | Van Genuchten Soil Water Retention (Forward) |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Soil Physics |
| **purpose** | Compute water content from pressure |
| **input** | psi (pressure), theta_r, theta_s, alpha, n |
| **output** | theta (water content) |
| **complexity** | LOW |
| **time_complexity** | O(1) |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/soil/physics.py:45-85 |
| **used_by** | Soil moisture calculations |
| **assumptions** | Empirical relationship; no hysteresis |
| **failure_modes** | n=1 → m=0 → division by zero |
| **scientific_basis** | van Genuchten (1980) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-008: Van Genuchten Inverse Model

| Field | Value |
|-------|-------|
| **algorithm_name** | Van Genuchten Inverse (Pressure from Content) |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Soil Physics |
| **purpose** | Compute pressure from water content |
| **input** | theta, theta_r, theta_s, alpha, n |
| **output** | psi (pressure) |
| **complexity** | MEDIUM |
| **time_complexity** | O(k) Newton-Raphson iteration |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/soil/physics.py:89-167 |
| **used_by** | Soil moisture calculations |
| **assumptions** | Same as forward; requires theta within bounds |
| **failure_modes** | theta < theta_r or > theta_s → invalid; iteration convergence |
| **scientific_basis** | van Genuchten (1980) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-009: D8 Flow Direction

| Field | Value |
|-------|-------|
| **algorithm_name** | D8 Deterministic 8-Cell Flow Direction |
| **algorithm_type** | GIS_METHOD |
| **domain** | GIS / Hydrology |
| **purpose** | Determine flow direction on raster DEM |
| **input** | DEM (2D elevation grid) |
| **output** | Flow direction (0-7 for 8 directions) |
| **complexity** | LOW |
| **time_complexity** | O(n*m) for n×m grid |
| **space_complexity** | O(n*m) |
| **implementation_location** | engine/land/hydrology.py:50-89 |
| **used_by** | Flow accumulation, watershed delineation |
| **assumptions** | Flow to single steepest downslope neighbor |
| **failure_modes** | Flat areas → pits; parallel flow channels |
| **scientific_basis** | O'Callaghan & Mark (1984) |
| **status** | VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-010: Horn's Method (Slope/Aspect)

| Field | Value |
|-------|-------|
| **algorithm_name** | Horn's Finite Difference for Slope and Aspect |
| **algorithm_type** | GIS_METHOD |
| **domain** | GIS / Terrain Analysis |
| **purpose** | Compute slope and aspect from DEM |
| **input** | DEM (3x3 window), cell size |
| **output** | Slope (degrees), Aspect (degrees) |
| **complexity** | LOW |
| **time_complexity** | O(1) per cell |
| **space_complexity** | O(1) |
| **implementation_location** | engine/land/models.py:45-112 |
| **used_by** | Terrain analysis, hydrology, watershed |
| **assumptions** | Planar surface within 3x3 window |
| **failure_modes** | Flat areas → aspect undefined; noisy DEM → noisy output |
| **scientific_basis** | Horn (1981) |
| **status** | VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-011: RUSLE

| Field | Value |
|-------|-------|
| **algorithm_name** | Revised Universal Soil Loss Equation |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Soil Science / Erosion |
| **purpose** | Estimate annual soil loss |
| **input** | R, K, LS, C, P factors |
| **output** | A (soil loss) |
| **complexity** | LOW |
| **time_complexity** | O(1) |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/soil/erosion.py:10-67 |
| **used_by** | Erosion assessment |
| **assumptions** | Steady-state; annual average |
| **failure_modes** | LS factor errors propagate |
| **scientific_basis** | Renard et al. (1997) |
| **status** | IMPLEMENTATION_VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-012: Conjugate Gradient

| Field | Value |
|-------|-------|
| **algorithm_name** | Conjugate Gradient Optimization |
| **algorithm_type** | OPTIMIZATION_METHOD |
| **domain** | Mathematics / Optimization |
| **purpose** | Minimize quadratic objective functions |
| **input** | Objective function, gradient, initial point, tolerance |
| **output** | Optimal point |
| **complexity** | HIGH |
| **time_complexity** | O(n*k) where n=dimensions, k=iterations |
| **space_complexity** | O(n) |
| **implementation_location** | engine/hydroma/optimization/cg.py:5-67 |
| **used_by** | Parameter optimization |
| **assumptions** | Quadratic objective; exact line search |
| **failure_modes** | Non-quadratic objective → slow convergence |
| **scientific_basis** | Standard optimization method |
| **status** | CODE_ONLY |
| **confidence** | LOW |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

### Algorithm ALG-013: Trapezoidal Integration

| Field | Value |
|-------|-------|
| **algorithm_name** | Trapezoidal Rule for Numerical Integration |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Mathematics |
| **purpose** | Approximate definite integral |
| **input** | Function values at grid points, spacing |
| **output** | Integral approximation |
| **complexity** | LOW |
| **time_complexity** | O(n) |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/utils/numerical.py:5-23 |
| **used_by** | Accumulated radiation, energy balance |
| **assumptions** | Function sufficiently smooth |
| **failure_modes** | Low accuracy for oscillatory functions |
| **scientific_basis** | Standard numerical integration |
| **status** | VERIFIED |
| **confidence** | HIGH |
| **reusability** | HIGH |
| **novelty** | KNOWN |

### Algorithm ALG-014: Kalman Filter

| Field | Value |
|-------|-------|
| **algorithm_name** | Kalman Filter (Linear) |
| **algorithm_type** | OPTIMIZATION_METHOD |
| **domain** | Control Theory / Statistics |
| **purpose** | Estimate state of linear system from noisy measurements |
| **input** | State transition model, observation model, noise covariances |
| **output** | State estimate with covariance |
| **complexity** | MEDIUM |
| **time_complexity** | O(n²) per timestep (matrix operations) |
| **space_complexity** | O(n²) |
| **implementation_location** | engine/hydroma/analysis/kalman.py:8-112 |
| **used_by** | Time series assimilation |
| **assumptions** | Linear system; Gaussian noise |
| **failure_modes** | Non-linear system → extended kalman required; divergence |
| **scientific_basis** | Kalman (1960) |
| **status** | CODE_ONLY |
| **confidence** | LOW |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

### Algorithm ALG-015: IDW (Inverse Distance Weighting)

| Field | Value |
|-------|-------|
| **algorithm_name** | Inverse Distance Weighting Interpolation |
| **algorithm_type** | DATA_PROCESSING_METHOD |
| **domain** | Spatial Statistics |
| **purpose** | Interpolate values from sparse sample points |
| **input** | Sample points (x, y, value), query point, power parameter |
| **output** | Interpolated value at query point |
| **complexity** | LOW |
| **time_complexity** | O(n) per query point |
| **space_complexity** | O(n) |
| **implementation_location** | engine/land/interpolation.py:12-45 |
| **used_by** | Spatial data interpolation |
| **assumptions** | Closer points more similar |
| **failure_modes** | Coincident points → singularity; power too low → uniform; too high → nearest neighbor |
| **scientific_basis** | Snyder (1967) |
| **status** | CODE_ONLY |
| **confidence** | MEDIUM |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

### Algorithm ALG-016: Modified Puls (Reservoir Routing)

| Field | Value |
|-------|-------|
| **algorithm_name** | Modified Puls Reservoir Routing |
| **algorithm_type** | SIMULATION_METHOD |
| **domain** | Hydraulics |
| **purpose** | Route hydrograph through storage |
| **input** | Inflow hydrograph, storage-outflow curve |
| **output** | Outflow hydrograph |
| **complexity** | MEDIUM |
| **time_complexity** | O(n) for n timesteps |
| **space_complexity** | O(n) |
| **implementation_location** | engine/hydroma/reservoir/pool_routing.py:3-78 |
| **used_by** | Flood routing |
| **assumptions** | Storage is function of outflow only |
| **failure_modes** | Non-monotonic storage curve → instability |
| **scientific_basis** | Standard reservoir routing |
| **status** | CODE_ONLY |
| **confidence** | LOW |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

### Algorithm ALG-017: Haar Wavelet Transform

| Field | Value |
|-------|-------|
| **algorithm_name** | Haar Wavelet Decomposition |
| **algorithm_type** | SIGNAL_PROCESSING |
| **domain** | Signal Processing |
| **purpose** | Multi-resolution analysis of data |
| **input** | Signal (power-of-2 length), level |
| **output** | Approximation + detail coefficients |
| **complexity** | MEDIUM |
| **time_complexity** | O(n) |
| **space_complexity** | O(n) |
| **implementation_location** | engine/hydroma/remote_sensing/wavelet.py:3-89 |
| **used_by** | Satellite image analysis |
| **assumptions** | Signal length is power of 2 |
| **failure_modes** | Non-power-of-2 input; edge effects |
| **scientific_basis** | Haar (1909); Mallat (1989) fast wavelet |
| **status** | CODE_ONLY |
| **confidence** | LOW |
| **reusability** | LOW |
| **novelty** | KNOWN |

### Algorithm ALG-018: MRF (Markov Random Field) Segmentation

| Field | Value |
|-------|-------|
| **algorithm_name** | Iterative MRF Image Segmentation |
| **algorithm_type** | IMAGE_PROCESSING |
| **domain** | Image Processing / Computer Vision |
| **purpose** | Segment images with spatial consistency |
| **input** | Image, initial labels, neighborhood model |
| **output** | Segmented image |
| **complexity** | HIGH |
| **time_complexity** | O(n*k) per iteration, k iterations |
| **space_complexity** | O(n) |
| **implementation_location** | engine/hydroma/image/mrf.py:5-78 |
| **used_by** | Land cover classification |
| **assumptions** | Markov property holds; known neighborhood structure |
| **failure_modes** | Convergence to local optimum; slow |
| **scientific_basis** | Besag (1975) |
| **status** | CODE_ONLY |
| **confidence** | LOW |
| **reusability** | LOW |
| **novelty** | KNOWN |

### Algorithm ALG-019: Dijkstra Pathfinding

| Field | Value |
|-------|-------|
| **algorithm_name** | Dijkstra's Shortest Path |
| **algorithm_type** | GRAPH_THEORY |
| **domain** | Graph Theory / Network Analysis |
| **purpose** | Find shortest path in weighted graph |
| **input** | Graph, source node, edge weights |
| **output** | Shortest path distances and predecessors |
| **complexity** | MEDIUM |
| **time_complexity** | O(V²) simple / O((V+E) log V) with heap |
| **space_complexity** | O(V) |
| **implementation_location** | engine/land/network.py:10-67 |
| **used_by** | Watershed flow path analysis |
| **assumptions** | Non-negative edge weights |
| **failure_modes** | Negative weights → Bellman-Ford needed |
| **scientific_basis** | Dijkstra (1956) |
| **status** | CODE_ONLY |
| **confidence** | MEDIUM |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

### Algorithm ALG-020: Growing Degree Days

| Field | Value |
|-------|-------|
| **algorithm_name** | Growing Degree Days (Thermal Time) |
| **algorithm_type** | NUMERICAL_METHOD |
| **domain** | Agriculture / Phenology |
| **purpose** | Accumulate heat units for plant development |
| **input** | Daily temperature, base temperature |
| **output** | Accumulated GDD |
| **complexity** | LOW |
| **time_complexity** | O(1) per day |
| **space_complexity** | O(1) |
| **implementation_location** | engine/hydroma/models/hpheno.py:20-45 |
| **used_by** | Phenology prediction |
| **assumptions** | Linear temperature-response relationship |
| **failure_modes** | Upper temperature threshold needed; heat stress not modeled |
| **scientific_basis** | Standard agronomy |
| **status** | COMPOSITE |
| **confidence** | MEDIUM |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

### Algorithm ALG-021: Log-Pearson Type III Frequency

| Field | Value |
|-------|-------|
| **algorithm_name** | Log-Pearson Type III Frequency Analysis |
| **algorithm_type** | STATISTICAL_METHOD |
| **domain** | Hydrology / Statistics |
| **purpose** | Determine frequency of hydrologic events (floods) |
| **input** | Time series of annual peak flows, return period |
| **output** | Discharge at specified return period |
| **complexity** | MEDIUM |
| **time_complexity** | O(n log n) for data sort |
| **space_complexity** | O(n) |
| **implementation_location** | engine/hydroma/flood/frequency.py:15-78 |
| **used_by** | Flood design |
| **assumptions** | Stationary climate; log-transformed data normal |
| **failure_modes** | Insufficient data; non-stationarity |
| **scientific_basis** | US Water Resources Council (1977); Chow (1964) |
| **status** | CODE_ONLY |
| **confidence** | LOW |
| **reusability** | MEDIUM |
| **novelty** | KNOWN |

---

## 3. Algorithm Dependency Graph (Partial)

```
Climate Data Assimilation
    ├─→ Penman-Monteith ET0 ──→ Water Demand ──→ Irrigation Scheduling
    ├─→ Hargreaves ET0 ──────→ Water Demand
    └─→ Radiation Model ──────→ Penman-Monteith

DEM
    ├─→ D8 Flow Direction ──→ Flow Accumulation ──→ Watershed Delineation
    ├─→ Slope/Aspect ───────→ RUSLE (LS factor)
    └─→ Terrain Analysis ─────→ Watershed Analysis

Soil Properties
    └─→ Van Genuchten ──→ Water Retention Curve
    └─→ Sorption Isotherm ──→ Carbon Transport

Groundwater
    ├─→ Darcy Flow (steady-state)
    └─→ Theis Solution (transient)
```

## 4. Algorithm Quality Assessment

| Algorithm | Correctness | Robustness | Documentation | Test Coverage | Status |
|-----------|------------|-----------|---------------|---------------|--------|
| Penman-Monteith | PASS | PASS | HIGH | HIGH | IMPLEMENTATION_VERIFIED |
| Hargreaves | PASS | MEDIUM | MEDIUM | MEDIUM | IMPLEMENTATION_VERIFIED |
| Newton-Raphson | PASS | MEDIUM | LOW | MEDIUM | IMPLEMENTATION_VERIFIED |
| SCS-CN | PASS | PASS | HIGH | HIGH | IMPLEMENTATION_VERIFIED |
| Darcy's Law | PASS | PASS | HIGH | HIGH | IMPLEMENTATION_VERIFIED |
| Theis | PARTIAL | LOW | MEDIUM | LOW | REQUIRES_REVIEW |
| Van Genuchten (Forward) | PASS | PASS | HIGH | HIGH | IMPLEMENTATION_VERIFIED |
| Van Genuchten (Inverse) | PARTIAL | MEDIUM | MEDIUM | MEDIUM | IMPLEMENTATION_VERIFIED |
| D8 Flow Direction | PASS | HIGH | HIGH | HIGH | VERIFIED |
| Horn's Slope/Aspect | PASS | HIGH | HIGH | HIGH | VERIFIED |
| RUSLE | PASS | MEDIUM | HIGH | HIGH | IMPLEMENTATION_VERIFIED |
| Conjugate Gradient | UNKNOWN | LOW | LOW | LOW | CODE_ONLY |
| Trapezoidal Integration | PASS | HIGH | LOW | HIGH | VERIFIED |
| Kalman Filter | UNKNOWN | LOW | LOW | LOW | CODE_ONLY |
| IDW Interpolation | PASS | MEDIUM | LOW | LOW | CODE_ONLY |
| Modified Puls | PARTIAL | LOW | LOW | Low | CODE_ONLY |
| Haar Wavelet | UNKNOWN | MEDIUM | LOW | Low | CODE_ONLY |
| MRF Segmentation | UNKNOWN | LOW | LOW | None | CODE_ONLY |
| Dijkstra | PASS | HIGH | LOW | High | CODE_ONLY |
| Growing Degree Days | PASS | HIGH | MEDIUM | Medium | COMPOSITE |
| Log-Pearson III | PARTIAL | LOW | Low | Low | CODE_ONLY |

---

*See also: 04-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, 07-MODEL-QUALITY-MATRIX.md, 08-EQUATION-AND-UNIT-FORENSICS.md*