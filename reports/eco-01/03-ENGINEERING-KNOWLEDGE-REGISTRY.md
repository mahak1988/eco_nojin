# ECO-01 Engineering Knowledge Registry

**Document ID:** ECO-01-03-ENGINEERING-KNOWLEDGE-REGISTRY  
**Scope:** engine/ + services/ engineering calculations  
**Purpose:** Classify and document all engineering models and calculations

---

## 1. Engineering Model Classification

### ENG-01: Water Balance Calculator

| Field | Value |
|-------|-------|
| **asset_name** | Water Balance Calculator |
| **engineering_type** | WATER_RESOURCES |
| **purpose** | Compute water balance for agricultural/irrigation systems |
| **physical_system** | Irrigation system, watershed water budget |
| **equations** | P = ET + Q + ΔS + R |
| **numerical_methods** | Mass balance, iterative reconciliation |
| **optimization_methods** | UNKNOWN |
| **simulation_methods** | Daily time-step water balance |
| **calibration** | UNKNOWN |
| **uncertainty** | Not propagated |
| **numerical_stability_risks** | Accumulation errors over long time series |
| **boundary_conditions** | Mass conservation, steady-state per timestep |
| **source_code** | engine/hydroma/simulation/balance.py:20-134 |
| **status** | VERIFIED |
| **confidence** | HIGH |

### ENG-02: Pipe Flow Calculations

| Field | Value |
|-------|-------|
| **asset_name** | Pipe Flow (Manning/Darcy-Weisbach) |
| **engineering_type** | HYDRAULICS |
| **purpose** | Compute flow in pipes and pressure drop |
| **physical_system** | Water conveyance systems |
| **equations** | Manning's equation, Darcy-Weisbach |
| **numerical_methods** | Iterative (Darcy-Weisbach solves for diameter/friction) |
| **optimization_methods** | UNKNOWN |
| **simulation_methods** | None (steady-state calculation) |
| **calibration** | None |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Iteration convergence for Darcy-Weisbach |
| **boundary_conditions** | Full pipe flow assumed |
| **source_code** | engine/hydroma/hydraulics/pipe_flow.py:8-96 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

### ENG-03: Reservoir Pool Routing

| Field | Value |
|-------|-------|
| **asset_name** | Reservoir Pool Routing (Modified Puls) |
| **engineering_type** | HYDRAUMICS |
| **purpose** | Route flood hydrograph through reservoir |
| **physical_system** | Reservoir, detention basin |
| **equations** | Storage-indentation curve, modified Puls equation |
| **numerical_methods** | Finite difference (storage adjustment) |
| **optimization_methods** | UNKNOWN |
| **simulation_methods** | Time-stepped hydrograph routing |
| **calibration** | Storage curve calibration from bathymetry |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Time step sensitivity; mass balance errors |
| **boundary_conditions** | Known inflow hydrograph and storage-outflow relationship |
| **source_code** | engine/hydroma/reservoir/pool_routing.py:3-78 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

### ENG-04: Storm Rain Frequency Analysis

| Field | Value |
|-------|-------|
| **asset_name** | Storm Rain Frequency Analysis |
| **engineering_type** | STATISTICS |
| **purpose** | Determine design storm rainfall depths for various return periods |
| **physical_system** | Rainfall-runoff design |
| **equations** | Log-Pearson Type III, Gumbel distribution |
| **numerical_methods** | Frequency analysis, linear regression |
| **optimization_methods** | UNKNOWN |
| **simulation_methods** | None |
| **calibration** | Statistical fitting |
| **uncertainty** | Confidence intervals on frequency estimates |
| **numerical_stability_risks** | Regression on limited data |
| **boundary_conditions** | Adequate historical data length |
| **source_code** | engine/hydroma/storm/rain.py:5-67 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

### ENG-05: Pressure Drop Calculation

| Field | Value |
|-------|-------|
| **asset_name** | Pressure Drop Calculation |
| **engineering_type** | PRESSURE_SYSTEMS |
| **purpose** | Compute pressure losses in piping systems |
| **physical_system** | Hydraulic distribution network |
| **equations** | Hazen-Williams, Darcy-Weisbach |
| **numerical_methods** | Direct calculation |
| **optimization_methods** | UNKNOWN |
| **simulation_methods** | None |
| **calibration** | None |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Low |
| **boundary_conditions** | Steady flow |
| **source_code** | engine/hydroma/hydraulics/pressure.py:4-56 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

### ENG-06: Pump Curve Analysis

| Field | Value |
|-------|-------|
| **asset_name** | Pump Curve Analysis |
| **engineering_type** | PUMP_SYSTEMS |
| **purpose** | Analyze pump performance and operating points |
| **physical_system** | Pumping stations, pipeline systems |
| **equations** | Pump curve: H = a - bQ - cQ², system curve: H = ... |
| **numerical_methods** | Curve intersection (operating point finding) |
| **optimization_methods** | System curve matching |
| **simulation_methods** | None |
| **calibration** | Pump manufacturer curves |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Quadratic solution convergence |
| **boundary_conditions** | Known pump and system curves |
| **source_code** | engine/hydroma/hydraulics/pump.py:10-89 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

### ENG-07: Irrigation Scheduler

| Field | Value |
|-------|-------|
| **asset_name** | Irrigation Scheduling |
| **engineering_type** | OPTIMIZATION |
| **purpose** | Schedule irrigation based on water demand and soil moisture |
| **physical_system** | Irrigation system |
| **equations** | Water balance based scheduling |
| **numerical_methods** | Optimization algorithms |
| **optimization_methods** | UNKNOWN (possibly greedy/local search) |
| **simulation_methods** | Time-stepped scheduling |
| **calibration** | UNKNOWN |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Convergence of scheduling algorithm |
| **boundary_conditions** | Water availability, soil moisture |
| **source_code** | engine/hydroma/irrigation/scheduler.py:10-189 |
| **status** | COMPOSITE |
| **confidence** | MEDIUM |

### ENG-08: Watershed Flow Division

| Field | Value |
|-------|-------|
| **asset_name** | Watershed Flow Division |
| **engineering_type** | HYDROLOGY |
| **purpose** | Route surface runoff and divide flow to sub-watersheds |
| **physical_system** | Watershed drainage network |
| **equations** | D8 flow direction, flow accumulation |
| **numerical_methods** | Recursive flow tracing |
| **optimization_methods** | None |
| **simulation_methods** | None (static routing) |
| **calibration** | None |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Stack overflow for large watersheds |
| **boundary_conditions** | Known flow direction grid |
| **source_code** | engine/hydroma/watershed/flow.py:10-89 |
| **status** | CODE_ONLY |
| **confidence** | MEDIUM |

### ENG-09: Sewer Performance

| Field | Value |
|-------|-------|
| **asset_name** | Sanitary Sewer Performance |
| **engineering_type** | SANITARY_SEWER |
| **purpose** | Analyze sewer system capacity and performance |
| **physical_system** | Sanitary sewer systems |
| **equations** | Manning's equation for open channel flow |
| **numerical_methods** | Direct calculation |
| **optimization_methods** | None |
| **simulation_methods** | None |
| **calibration** | None |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Low |
| **boundary_conditions** | Known pipe geometry, slope |
| **source_code** | engine/hydroma/sanitary/sewer.py:6-78 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

### ENG-10: Spatial Interpolation

| Field | Value |
|-------|-------|
| **asset_name** | Spatial Interpolation Methods |
| **engineering_type** | GIS_SPATIAL |
| **purpose** | Interpolate spatial data from point/area samples |
| **physical_system** | Geographic surfaces |
| **equations** | Inverse Distance Weighting (IDW), Kriging, Spline |
| **numerical_methods** | Weighted averaging, variogram analysis |
| **optimization_methods** | Parameter fitting (for kriging) |
| **simulation_methods** | None |
| **calibration** | Variogram fitting |
| **uncertainty** | Kriging provides error estimates |
| **numerical_stability_risks** | IDW singularity for coincident points |
| **boundary_conditions** | Convex hull of input points |
| **source_code** | engine/land/interpolation.py:8-98 |
| **status** | CODE_ONLY |
| **confidence** | MEDIUM |

### ENG-11: Overlay Analysis

| Field | Value |
|-------|-------|
| **asset_name** | GIS Overlay Analysis |
| **engineering_type** | GIS_SPATIAL |
| **purpose** | Overlay multiple spatial layers for analysis |
| **physical_system** | Multi-criteria analysis |
| **equations** | Boolean/set operations on raster layers |
| **numerical_methods** | Raster algebra |
| **optimization_methods** | Weighted overlay |
| **simulation_methods** | None |
| **calibration** | None |
| **uncertainty** | Not quantified |
| **numerical_stability_risks** | Low |
| **boundary_conditions** | All layers same extent |
| **source_code** | engine/land/overlay.py:3-56 |
| **status** | UNKNOWN |
| **confidence** | LOW |

### ENG-12: Frequency Analysis

| Field | Value |
|-------|-------|
| **asset_name** | Hydrologic Frequency Analysis |
| **engineering_type** | STATISTICS |
| **purpose** | Determine flow/drought frequencies for design |
| **physical_system** | Hydrologic extremes |
| **equations** | Log-Pearson Type III, Gumbel, Weibull plotting position |
| **numerical_methods** | Frequency factor method, regression |
| **optimization_methods** | None |
| **simulation_methods** | None |
| **calibration** | Statistical fitting |
| **uncertainty** | Confidence intervals on frequency estimates |
| **numerical_stability_risks** | Small sample sizes |
| **boundary_conditions** | Stationary climate assumption |
| **source_code** | engine/hydroma/flood/frequency.py:8-112 |
| **status** | UNKNOWN |
| **confidence** | LOW |

### ENG-13: Wavelets (Remote Sensing)

| Field | Value |
|-------|-------|
| **asset_name** | Wavelet Decomposition for Remote Sensing |
| **engineering_type** | SIGNAL_PROCESSING |
| **purpose** | Multi-resolution analysis of satellite imagery |
| **physical_system** | Earth observation data |
| **equations** | Wavelet transform (Haar, Daubechies) |
| **numerical_methods** | Fast wavelet transform |
| **optimization_methods** | None |
| **simulation_methods** | None |
| **calibration** | None |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Choice of wavelet affects results |
| **boundary_conditions** | Image dimensions must allow decomposition |
| **source_code** | engine/hydroma/remote_sensing/wavelet.py:3-89 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

### ENG-14: Digital Elevation Model Processing

| Field | Value |
|-------|-------|
| **asset_name** | DEM Processing Suite |
| **engineering_type** | GIS_SPATIAL |
| **purpose** | Process, clean, and reproject DEM data |
| **physical_system** | Digital terrain |
| **equations** | Filtering, interpolation, projection transforms |
| **numerical_methods** | Gaussian filtering, spline interpolation |
| **optimization_methods** | None |
| **simulation_methods** | None |
| **calibration** | None |
| **uncertainty** | UNKNOWN |
| **numerical_stability_risks** | Edge effects, interpolation artifacts |
| **source_code** | engine/land/dem.py:5-78 |
| **status** | VERIFIED |
| **confidence** | HIGH |

### ENG-15: Kalman Filter

| Field | Value |
|-------|-------|
| **asset_name** | Kalman Filter for Time Series Analysis |
| **engineering_type** | CONTROL_SYSTEMS |
| **purpose** | State estimation and data assimilation for hydrological time series |
| **physical_system** | Dynamic systems with noisy observations |
| **equations** | Standard Kalman filter prediction-update equations |
| **numerical_methods** | Matrix operations, inversion |
| **optimization_methods** | None |
| **simulation_methods** | Time series state estimation |
| **calibration** | Process noise, observation noise covariance |
| **uncertainty** | Covariance propagation |
| **numerical_stability_risks** | Covariance matrix non-positive definite; numerical divergence |
| **boundary_conditions** | Linear system assumption |
| **source_code** | engine/hydroma/analysis/kalman.py:8-112 |
| **status** | CODE_ONLY |
| **confidence** | LOW |

---

## 2. Numerical Methods Catalog

| Method | Type | Location | Status |
|--------|------|----------|--------|
| Finite Difference (Horn's method) | Spatial | engine/land/hydrology.py:50-89 | VERIFIED |
| Newton-Raphson | Root finding | engine/hydroma/soil/physics.py:89-123 | IMPLEMENTATION_VERIFIED |
| Series Expansion (Theis W(u)) | Special function | engine/hydroma/models/groundwater_model.py:93-210 | REQUIRES_REVIEW |
| Trapezoidal Rule | Integration | engine/hydroma/utils/numerical.py:5-23 | VERIFIED |
| Iterative Convergence | Solver | engine/hydroma/hydraulics/pump.py | CODE_ONLY |
| Linear Regression | Statistics | engine/hydroma/storm/rain.py | CODE_ONLY |

## 3. Optimization Methods Catalog

| Method | Location | Status |
|--------|----------|--------|
| Conjugate Gradient | engine/hydroma/optimization/cg.py | CODE_ONLY |
| Greedy Scheduling | engine/hydroma/irrigation/scheduler.py | COMPOSITE |
| Weighted Overlay | engine/land/overlay.py | UNKNOWN |

## 4. Simulation Methods Catalog

| Method | Location | Status |
|--------|----------|--------|
| Daily Water Balance | engine/hydroma/simulation/balance.py | VERIFIED |
| Time-stepped Routing | engine/hydroma/watershed/flow.py | CODE_ONLY |
| Hydrograph Routing | engine/hydroma/reservoir/pool_routing.py | CODE_ONLY |

---

## 4. Engineering Capabilities Reusability Matrix

| Capability | Scientific Value | Technical Quality | Independence | Reusability | Migration Complexity | Future Role |
|------------|-----------------|-------------------|--------------|-------------|---------------------|-------------|
| Water Balance | HIGH | HIGH | HIGH | HIGH | LOW | Hydroma Core |
| D8 Flow Direction | HIGH | HIGH | HIGH | HIGH | LOW | Hydroma Core |
| Slope/Aspect | HIGH | HIGH | HIGH | HIGH | LOW | Hydroma Core |
| Penman-Monteith | HIGH | HIGH | MEDIUM | HIGH | MEDIUM | Hydroma Core |
| SCS-CN Runoff | HIGH | HIGH | HIGH | HIGH | LOW | Hydroma Core |
| Darcy Flow | HIGH | HIGH | HIGH | HIGH | LOW | Hydroma Core |
| Van Genuchten | HIGH | HIGH | MEDIUM | HIGH | MEDIUM | Hydroma Core |
| RUSLE | HIGH | MEDIUM | HIGH | MEDIUM | LOW | Hydroma Core |
| Pipe Flow | MEDIUM | LOW | HIGH | MEDIUM | LOW | Engineering |
| Pump Curves | MEDIUM | LOW | HIGH | MEDIUM | LOW | Engineering |
| DEM Processing | HIGH | HIGH | HIGH | HIGH | LOW | Hydroma Core |
| Spatial Interpolation | MEDIUM | MEDIUM | HIGH | MEDIUM | LOW | GIS |
| Kalman Filter | MEDIUM | LOW | MEDIUM | MEDIUM | MEDIUM | Analysis |
| Wavelet Analysis | LOW | MEDIUM | LOW | LOW | HIGH | Reference |

---

## 5. Calibration & Uncertainty Assessment

| Model | Calibration Available | Uncertainty Quantified | Confidence |
|-------|----------------------|----------------------|------------|
| Water Balance | UNKNOWN | No | MEDIUM |
| ET0 (PM) | FAO Standardized | No (in code) | HIGH |
| SCS-CN | CN values from tables | No | HIGH |
| Darcy Flow | K from field tests | No | HIGH |
| Van Genuchten | Parameters from literature | No | HIGH |
| RUSLE | C, P factors local | No | MEDIUM |
| Theis | T, S from pumping tests | No | MEDIUM |
| Kalman Filter | Covariance tuning | Yes (built-in) | LOW |
| Pump Curves | From manufacturer | No | LOW |
| Frequency Analysis | Statistical fitting | Yes (CI) | LOW |

---

## 6. Numerical Stability Risks

| Model | Risk | Severity | Mitigation Needed |
|-------|------|----------|-------------------|
| Theis W(u) | Series expansion divergence for small u | MEDIUM | Convergence check |
| Kalman Filter | Covariance divergence | HIGH | Stability monitoring |
| Iterative Pump | Non-convergence | MEDIUM | Timeout, fallback |
| Wavelet | Boundary effects | LOW | Padding |
| Spatial Interpolation | Coincident points singularity | LOW | Epsilon perturbation |
| Water Balance | Accumulation errors | MEDIUM | Periodic reset |

---

*See also: 04-ALGORITHM-REGISTRY.md, 07-MODEL-QUALITY-MATRIX.md, 08-EQUATION-AND-UNIT-FORENSICS.md*