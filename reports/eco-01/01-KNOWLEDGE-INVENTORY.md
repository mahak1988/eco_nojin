# ECO-01 Knowledge Inventory

**Document ID:** ECO-01-01-KNOWLEDGE-INVENTORY  
**Scope:** engine/ + services/ + ECO-00 reports  
**Purpose:** Identify and classify all knowledge assets discovered in the HyDroMA codebase

---

## 1. Summary

| Category | Total Assets | High Value | Medium Value | Low/Reference Value | Legacy Only |
|----------|-------------|------------|-------------|---------------------|-------------|
| Scientific Models | 22 | 14 | 6 | 2 | 0 |
| Engineering Models | 15 | 9 | 5 | 1 | 0 |
| Algorithms | 38 | 18 | 12 | 8 | 0 |
| Domain Knowledge | 42 | 28 | 10 | 4 | 0 |
| Technologies | 35 | 12 | 14 | 6 | 3 |

---

## 2. Scientific Knowledge Assets

### 2.1 Climate Models

| Asset ID | Name | Location | Status | Confidence |
|----------|------|----------|--------|------------|
| CLIMATE-ET0-PENMAN-MONTEITH | FAO-56 Penman-Monteith ET0 | engine/hydroma/climate/et_calculator.py:54-289 | SCIENTIFICALLY_SUPPORTED | HIGH |
| CLIMATE-ET0-HARGREAVES | Hargreaves-Samani ET0 | engine/hydroma/climate/et_calculator.py:300-380 | SCIENTIFICALLY_SUPPORTED | HIGH |
| CLIMATE-DATA-ASSIMILATION | Climate Data Assimilation Pipeline | engine/hydroma/climate/assimilation.py | IMPLEMENTATION_VERIFIED | LOW |
| CLIMATE-RADIATION | Solar Radiation Model | engine/hydroma/climate/radiation.py | IMPLEMENTATION_VERIFIED | MEDIUM |
| CLIMATE-VARIABILITY | Climate Variability Analysis | engine/hydroma/climate/variability.py | CODE_ONLY | LOW |

### 2.2 Hydrology Models

| Asset ID | Name | Location | Status | Confidence |
|----------|------|----------|--------|------------|
| HYDROLOGY-SCS-CN | SCS-CN Runoff Model | engine/hydroma/models/runoff_model.py:12-145 | SCIENTIFICALLY_SUPPORTED | HIGH |
| HYDROLOGY-DARCY | Darcy Groundwater Flow | engine/hydroma/models/groundwater_model.py:8-92 | SCIENTIFICALLY_SUPPORTED | HIGH |
| HYDROLOGY-THEIS | Theis Analytical Solution | engine/hydroma/models/groundwater_model.py:93-210 | CODE_ONLY | MEDIUM |
| HYDROLOGY-SURFACE-WATER | Surface Water Routing | engine/hydroma/models/surface_water_model.py:5-78 | CODE_ONLY | LOW |
| HYDROLOGY-WATER-DEMAND | Water Demand Estimation | engine/hydroma/models/water_demand.py:10-156 | IMPLEMENTATION_VERIFIED | MEDIUM |

### 2.3 Soil Models

| Asset ID | Name | Location | Status | Confidence |
|----------|------|----------|--------|------------|
| SOIL-VAN-GENUCHTEN | Van Genuchten Soil Water Retention | engine/hydroma/soil/physics.py:45-167 | IMPLEMENTATION_VERIFIED | HIGH |
| SOIL-SALINITY | Soil Salinity Model | engine/hydroma/soil/salinity.py:12-98 | CODE_ONLY | LOW |
| SOIL-CARBON | Soil Carbon Storage | engine/hydroma/soil/carbon.py:8-134 | IMPLEMENTATION_VERIFIED | MEDIUM |
| SOIL-EROSION | Soil Erosion (RUSLE) | engine/hydroma/soil/erosion.py:5-112 | SCIENTIFICALLY_SUPPORTED | MEDIUM |
| SOIL-FRACTIONATION | Soil Fractionation | engine/hydroma/soil/fractionation.py:3-45 | UNKNOWN | LOW |

### 2.4 Watershed Models

| Asset ID | Name | Location | Status | Confidence |
|----------|------|----------|--------|------------|
| WATERSHED-CALCULATOR | Watershed Structure Calculator | engine/hydroma/watershed/calculator.py:15-234 | IMPLEMENTATION_VERIFIED | HIGH |
| WATERSHED-FLOW-DIVISION | Flow Division Analysis | engine/hydroma/watershed/flow.py:10-89 | CODE_ONLY | MEDIUM |
| WATERSHED-SEDIMENT | Sediment Yield | engine/hydroma/watershed/sediment.py:7-76 | CODE_ONLY | LOW |
| WATERSHED-ROUTING | Watershed Routing | engine/hydroma/watershed/routing.py:4-56 | UNKNOWN | LOW |

### 2.5 Agriculture / Crop Models

| Asset ID | Name | Location | Status | Confidence |
|----------|------|----------|--------|------------|
| AGRICULTURE-EPIA | Precision Irrigation Advisor (EPIA) | engine/hydroma/models/epia.py | COMPOSITE | MEDIUM |
| AGRICULTURE-PHENOLOGY | Phenology Detection | engine/hydroma/models/hpheno.py | COMPOSITE | MEDIUM |
| AGRICULTURE-CROP-COEFFICIENT | Crop Coefficient Calculation | engine/hydroma/agriculture/crop_coefficient.py:8-67 | IMPLEMENTATION_VERIFIED | HIGH |
| AGRICULTURE-GROWTH-STAGE | Growth Stage Classification | engine/hydroma/agriculture/growth_stage.py:5-89 | SCIENTIFICALLY_SUPPORTED | MEDIUM |
| AGRICULTURE-YIELD-ESTIMATION | Yield Estimation | engine/hydroma/agriculture/yield_estimation.py:3-112 | CODE_ONLY | LOW |

### 2.6 Land / GIS Models

| Asset ID | Name | Location | Status | Confidence |
|----------|------|----------|--------|------------|
| LAND-TERRAIN | Terrain Analysis | engine/land/terrain_analysis.py:15-178 | VERIFIED | HIGH |
| LAND-HYDROLOGY | Land Hydrology | engine/land/hydrology.py:8-145 | VERIFIED | HIGH |
| LAND-SLOPE-ASPECT | Slope/Aspect Calculation | engine/land/models.py:45-112 | VERIFIED | HIGH |
| LAND-FLOW-ROUTING | D8 Flow Routing | engine/land/hydrology.py:50-112 | IMPLEMENTATION_VERIFIED | HIGH |

### 2.7 Carbon Models

| Asset ID | Name | Location | Status | Confidence |
|----------|------|----------|--------|------------|
| CARBON-STORAGE | Carbon Storage Estimation | engine/hydroma/soil/carbon.py:56-134 | CODE_ONLY | LOW |
| CARBON-FLUENT | Carbon Flux Modeling | engine/hydroma/carbon/fluent.py:3-67 | UNKNOWN | LOW |

---

## 3. Engineering Knowledge Assets

| Asset ID | Name | Location | Engineering Type | Status |
|----------|------|----------|-----------------|--------|
| ENG-WATER-BALANCE | Water Balance Calculator | engine/hydroma/simulation/balance.py:20-134 | CALCULATION | VERIFIED |
| ENG-SORPTION-ISOTHERM | Sorption Isotherm | engine/hydroma/soil/sorption.py:5-78 | MODEL | CODE_ONLY |
| ENG-PIPE-FLOW | Pipe Flow Calculations | engine/hydroma/hydraulics/pipe_flow.py:8-96 | CALCULATION | CODE_ONLY |
| ENG-DRAINAGE | Drainage System Design | engine/hydroma/drainage/design.py:12-145 | DESIGN | CODE_ONLY |
| ENG-IRRIGATION-SCHEDULING | Irrigation Scheduling | engine/hydroma/irrigation/scheduler.py:10-189 | OPTIMIZATION | COMPOSITE |
| ENG-RESERVOIR-POOL | Reservoir Pool Routing | engine/hydroma/reservoir/pool_routing.py:3-78 | SIMULATION | CODE_ONLY |
| ENG-STORM-RAIN | Storm Rain Analysis | engine/hydroma/storm/rain.py:5-67 | STATISTICAL | CODE_ONLY |
| ENG-FREQUENCY-ANALYSIS | Frequency Analysis | engine/hydroma/flood/frequency.py:8-112 | STATISTICAL | UNKNOWN |
| ENG-PRESSURE-DROP | Pressure Drop Calculation | engine/hydroma/hydraulics/pressure.py:4-56 | CALCULATION | CODE_ONLY |
| ENG-PUMP-CURVE | Pump Curve Analysis | engine/hydroma/hydraulics/pump.py:10-89 | CALCULATION | CODE_ONLY |
| ENG-SEWER-PERFORMANCE | Sewer Performance | engine/hydroma/sanitary/sewer.py:6-78 | CALCULATION | CODE_ONLY |
| ENG-OVERLAY | GIS Overlay Analysis | engine/land/overlay.py:3-56 | GIS_METHOD | UNKNOWN |
| ENG-INTERPOLATION | Spatial Interpolation | engine/land/interpolation.py:8-98 | NUMERICAL_METHOD | CODE_ONLY |
| ENG-DIGITAL-ELEVATION | DEM Processing | engine/land/dem.py:5-78 | GIS_METHOD | VERIFIED |
| ENG-WATER-SURFACE | Water Surface Profile | engine/hydroma/hydraulics/water_surface.py:2-67 | NUMERICAL_METHOD | CODE_ONLY |

---

## 4. Algorithm Assets

| Asset ID | Name | Location | Type | Complexity |
|----------|------|----------|------|------------|
| ALG-HARGREAVES | Hargreaves ET0 | engine/hydroma/climate/et_calculator.py:300-380 | WEATHER | LOW |
| ALG-PENMAN-MONTEITH | Penman-Monteith | engine/hydroma/climate/et_calculator.py:54-289 | WEATHER | HIGH |
| ALG-NEWTON-RAPHSON | Newton-Raphson Root Finding | engine/hydroma/soil/physics.py:89-123 | NUMERICAL | MEDIUM |
| ALG-HALF-CELL | Half-Cell Integration | engine/hydroma/models/groundwater_model.py:45-78 | NUMERICAL | MEDIUM |
| ALG-D8 | D8 Flow Direction | engine/land/hydrology.py:50-89 | GIS | LOW |
| ALG-TRAPEZOIDAL | Trapezoidal Integration | engine/hydroma/carbon/flux.py:15-34 | NUMERICAL | LOW |
| ALG-CONJUGATE-GRADIENT | Conjugate Gradient | engine/hydroma/optimization/cg.py:5-67 | OPTIMIZATION | HIGH |
| ALG-SCS-CN | SCS Curve Number | engine/hydroma/models/runoff_model.py:45-98 | RUNOFF | LOW |
| ALG-THEIS | Theis Well Function | engine/hydroma/models/groundwater_model.py:93-210 | GROUNDWATER | MEDIUM |
| ALG-VAN-GENUCHTEN | Van Genuchten Iteration | engine/hydroma/soil/physics.py:45-98 | SOIL | MEDIUM |
| ALG-RUSLE | RUSLE Erosion | engine/hydroma/soil/erosion.py:10-67 | SOIL | MEDIUM |
| ALG-HAAR-WAVELET | Wavelet Decomposition | engine/hydroma/remote_sensing/wavelet.py:3-89 | REMOTE_SENSING | HIGH |
| ALG-KALMAN-FILTER | Kalman Filter | engine/hydroma/analysis/kalman.py:8-112 | STATISTICAL | HIGH |
| ALG-MARKOV-RANDOM-FIELD | MRF Segmentation | engine/hydroma/image/mrf.py:5-78 | IMAGE_PROCESSING | HIGH |
| ALG-DIJKSTRA | Dijkstra Pathfinding | engine/land/network.py:10-67 | GRAPH | MEDIUM |
| ALG-TRAPEZOIDAL-RULE | Trapezoidal Rule | engine/hydroma/utils/numerical.py:5-23 | NUMERICAL | LOW |

*Note: Full list continues in ALGORITHM-REGISTRY.md*

---

## 5. Domain Knowledge Assets

### 5.1 Scientific Terminology and Concepts

| Concept | Domain | Definition Location | Confidence |
|---------|--------|-------------------|------------|
| ET0 (Reference Evapotranspiration) | Climate | engine/hydroma/climate/et_calculator.py:1-53 | HIGH |
| Curve Number (CN) | Hydrology | engine/hydroma/models/runoff_model.py:12-30 | HIGH |
| Hydraulic Conductivity (K) | Soil/Water | engine/hydroma/soil/physics.py:15-25 | HIGH |
| Field Capacity | Soil | engine/hydroma/soil/physics.py:45-67 | HIGH |
| Wilting Point | Soil | engine/hydroma/soil/physics.py:68-89 | HIGH |
| Saturation Vapor Pressure | Climate | engine/hydroma/climate/et_calculator.py:54-78 | HIGH |
| Solar Radiation | Climate | engine/hydroma/climate/radiation.py:1-45 | HIGH |
| D8 (Flow Direction) | GIS | engine/land/hydrology.py:50-89 | HIGH |
| Manning's n | Hydraulics | engine/hydroma/hydraulics/ | MEDIUM |
| van Genuchten Parameters | Soil | engine/hydroma/soil/physics.py:45-105 | HIGH |

### 5.2 Domain Entities

| Entity Type | Count | Location | Notes |
|-------------|-------|----------|-------|
| Pydantic Models | ~45 | engine/land/models.py, engine/hydroma/models/*.py | Strict V2 schema |
| Data Classes | ~22 | engine/hydroma/data/ | Immutable data structures |
| Enums | ~34 | engine/hydroma/enums/ | Scientific status enums |
| Named Tuples | ~18 | engine/hydroma/utils/ | Lightweight data |

### 5.3 Business Rules

| Rule ID | Description | Location | Confidence |
|---------|-------------|----------|------------|
| RULE-IRRIGATION-THRESHOLD | Trigger irrigation when soil moisture < threshold | engine/hydroma/irrigation/scheduler.py:45-67 | MEDIUM |
| RULE-CROP-COEFFICIENT | Apply Kc curve based on growth stage | engine/hydroma/agriculture/crop_coefficient.py:15-34 | HIGH |
| RULE-FLOOD-DETERMINATION | Flood risk based on SCS-CN runoff | engine/hydroma/models/runoff_model.py:78-98 | MEDIUM |
| RULE-DRAINAGE-CRITERIA | Minimum drainage capacity | engine/hydroma/drainage/design.py:23-45 | LOW |
| RULE-SALINITY-TOLERANCE | Crop salt tolerance thresholds | engine/hydroma/soil/salinity.py:23-56 | LOW |

### 5.4 Workflows

| Workflow ID | Description | Steps | Confidence |
|-------------|-------------|-------|------------|
| WF-ET0-CALCULATION | ET0 calculation pipeline | Weather → Radiation → ET0 | HIGH |
| WF-WATER-BALANCE | Water balance simulation | Precipitation → ET → Runoff → Drainage | HIGH |
| WF-WATERSHED-DESIGN | Watershed infrastructure design | DEM → Terrain → Hydrology → Routing → Design | HIGH |
| WF-IRRIGATION-SCHEDULING | Irrigation decision workflow | Soil moisture → ET → Demand → Schedule | MEDIUM |

### 5.5 Roles

| Role | Domain | Permissions | Confidence |
|------|--------|-------------|------------|
| Hydrologist | Water | Read/write hydrology models | MEDIUM |
| Agronomist | Agriculture | Read/write crop models | MEDIUM |
| Climate Scientist | Climate | Read/write climate data | MEDIUM |
| Engineer | Engineering | Design calculations | LOW |
| Researcher | Research | Experimental data | LOW |

### 5.6 Decision Logic

| Decision Point | Logic | Location | Confidence |
|----------------|-------|----------|------------|
| Irrigation Trigger | Soil moisture threshold + ET demand | engine/hydroma/irrigation/scheduler.py | MEDIUM |
| Drainage Requirement | Water table depth + soil permeability | engine/hydroma/drainage/design.py | LOW |
| Flood Risk | Rainfall intensity + CN value | engine/hydroma/models/runoff_model.py | MEDIUM |
| Crop Selection | Climate zone + soil type | engine/hydroma/agriculture/crop_match.py | LOW |

### 5.7 Provenance Mechanisms

| Mechanism | Location | Description | Confidence |
|-----------|----------|-------------|------------|
| Provenance Tracking | engine/hydroma/provenance.py:12-89 | ResultProvenance enum + tracking metadata | HIGH |
| Audit Trail | engine/hydroma/audit.py | Calculation audit records | MEDIUM |
| Model Versioning | engine/hydroma/models/registry.py | Fidelity-labeled model versions | HIGH |

### 5.8 Verification Mechanisms

| Mechanism | Location | Description | Confidence |
|-----------|----------|-------------|------------|
| Formula Catalog | engine/hydroma/formulas/catalog.py | Equation registry with provenance | HIGH |
| Unit Tests | tests/ | Model verification tests | HIGH |
| Integration Tests | tests/integration/ | Cross-model validation | MEDIUM |

---

## 6. Technology Inventory Summary

| Technology | Category | Strategic Classification |
|------------|----------|-------------------------|
| C++ (cpp_core) | Performance Computing | CORE |
| Python 3.12 | Application Logic | CORE |
| NumPy | Numerical Computing | CORE |
| Pydantic V2 | Data Modeling | CORE |
| Structlog | Logging | OPTIONAL |
| Rasterio | GIS Processing | IMPORTANT |
| xarray | Data Processing | IMPORTANT |

*Full technology inventory in TECHNOLOGY-REGISTRY.md*

---

## 7. Confidence Assessment

| Dimension | High | Medium | Low | Unknown |
|-----------|------|--------|-----|---------|
| Implementation Verification | 14 | 6 | 2 | 0 |
| Scientific Validation | 4 | 8 | 9 | 1 |
| Documentation Quality | 8 | 9 | 5 | 0 |

---

*End of Knowledge Inventory - Full details in respective registry reports*