# ECO-01 Domain Knowledge Registry

**Document ID:** ECO-01-05-DOMAIN-KNOWLEDGE-REGISTRY  
**Scope:** engine/ + services/ domain concepts  
**Purpose:** Catalog domain concepts, business rules, entities, workflows, and roles

---

## 1. Domain Concepts Identified

### Territory
No direct representation found. May be implied via watershed or administrative boundaries.

### Land
| Concept | Location | Confidence |
|---------|----------|------------|
| Land Parcel | engine/land/models.py:12-45 | HIGH |
| Land Use Type | engine/hydroma/agriculture/growth_stage.py:5-23 | MEDIUM |
| Land Cover | services/land/models.py | MEDIUM |

### Soil
| Concept | Location | Confidence |
|---------|----------|------------|
| Soil Type | engine/hydroma/soil/physics.py:15-25 | HIGH |
| Soil Properties (theta_r, theta_s, alpha, n) | engine/hydroma/soil/physics.py:45-67 | HIGH |
| Soil Salinity (EC, SAR) | engine/hydroma/soil/salinity.py | MEDIUM |
| Soil Carbon (SOC%, bulk density) | engine/hydroma/soil/carbon.py | MEDIUM |
| Soil Erosion (RUSLE factors) | engine/hydroma/soil/erosion.py | HIGH |
| Soil Moisture | engine/hydroma/soil/physics.py | HIGH |
| CEC (Cation Exchange Capacity) | engine/hydroma/soil/chemistry.py (if present) | LOW |
| pH | engine/hydroma/soil/chemistry.py (if present) | LOW |
| Organic Matter | engine/hydroma/soil/organic_matter.py (if present) | LOW |
| Bulk Density | engine/hydroma/soil/carbon.py | MEDIUM |
| Nutrients | engine/hydroma/soil/nutrients.py (if present) | LOW |

### Water
| Concept | Location | Confidence |
|---------|----------|------------|
| Surface Water | engine/hydroma/models/surface_water_model.py | MEDIUM |
| Groundwater | engine/hydroma/models/groundwater_model.py | HIGH |
| Precipitation | engine/hydroma/climate/et_calculator.py | HIGH |
| Evapotranspiration | engine/hydroma/climate/et_calculator.py | HIGH |
| Runoff | engine/hydroma/models/runoff_model.py | HIGH |
| Streamflow | engine/hydroma/watershed/flow.py | MEDIUM |
| Water Demand | engine/hydroma/models/water_demand.py | MEDIUM |
| Water Balance | engine/hydroma/simulation/balance.py | HIGH |

### Climate
| Concept | Location | Confidence |
|---------|----------|------------|
| Temperature (min, max, mean) | engine/hydroma/climate/et_calculator.py | HIGH |
| Humidity | engine/hydroma/climate/et_calculator.py | HIGH |
| Wind Speed | engine/hydroma/climate/et_calculator.py | HIGH |
| Solar Radiation | engine/hydroma/climate/radiation.py | HIGH |
| Atmospheric Pressure | engine/hydroma/climate/radiation.py | MEDIUM |
| Rainfall | engine/hydroma/climate/assimilation.py | HIGH |
| Climate Variability | engine/hydroma/climate/variability.py | LOW |

### Agriculture
| Concept | Location | Confidence |
|---------|----------|------------|
| Crop Type | engine/hydroma/agriculture/crop_coefficient.py | HIGH |
| Crop Coefficient (Kc) | engine/hydroma/agriculture/crop_coefficient.py | HIGH |
| Growth Stage | engine/hydroma/agriculture/growth_stage.py | HIGH |
| Yield Estimation | engine/hydroma/agriculture/yield_estimation.py | MEDIUM |
| Irrigation Requirement | engine/hydroma/irrigation/scheduler.py | MEDIUM |
| Farming Practice | engine/hydroma/agriculture/practices.py | LOW |

### Ecosystem
| Concept | Location | Confidence |
|---------|----------|------------|
| Ecosystem Type | services/ecosystem/models.py | MEDIUM |
| Biodiversity Index | engine/hydroma/ecosystem/biodiversity.py | LOW |
| Habitat Quality | engine/hydroma/ecosystem/habitat.py | LOW |

### Carbon
| Concept | Location | Confidence |
|---------|----------|------------|
| Soil Organic Carbon (SOC) | engine/hydroma/soil/carbon.py | MEDIUM |
| Carbon Stock | engine/hydroma/soil/carbon.py:56-134 | MEDIUM |
| Carbon Flux | engine/hydroma/carbon/flux.py | LOW |

### Monitoring
| Concept | Location | Confidence |
|---------|----------|------------|
| Sensor Data | services/monitoring/models.py | MEDIUM |
| Observation | services/observation/models.py | MEDIUM |
| Measurement | services/measurement/models.py | MEDIUM |
| Quality Control | services/monitoring/qc.py | LOW |

### Knowledge
| Concept | Location | Confidence |
|---------|----------|------------|
| Scientific Knowledge | engine/hydroma/provenance.py | HIGH |
| Local Knowledge | services/knowledge/local.py | LOW |
| Expert Opinion | services/knowledge/expert.py | LOW |
| Research Hypothesis | engine/hydroma/research/hypothesis.py | LOW |

### Observation
| Concept | Location | Confidence |
|---------|----------|------------|
| Weather Station Data | engine/hydroma/climate/assimilation.py | HIGH |
| Soil Sampling | engine/hydroma/soil/measurements.py | MEDIUM |
| Satellite Data | engine/hydroma/remote_sensing/ | MEDIUM |

### Measurement
| Concept | Location | Confidence |
|---------|----------|------------|
| Flow Rate | engine/hydroma/hydraulics/ | MEDIUM |
| Soil Moisture Content | engine/hydroma/soil/physics.py | HIGH |
| Precipitation Depth | engine/hydroma/climate/ | HIGH |
| Water Quality | engine/hydroma/water_quality/ | LOW |

### Model
| Concept | Location | Confidence |
|---------|----------|------------|
| Model Registry | services/models/registry.py | HIGH |
| Model Version | services/models/registry.py | HIGH |
| Fidelity Label | services/models/registry.py | HIGH |
| Model Output | engine/hydroma/provenance.py | HIGH |

### Evidence
| Concept | Location | Confidence |
|---------|----------|------------|
| Scientific Evidence | engine/hydroma/evidence/ | LOW |
| Observational Data | engine/hydroma/observations/ | LOW |
| Validation Data | tests/ | HIGH |

### Research
| Concept | Location | Confidence |
|---------|----------|------------|
| Research Project | engine/hydroma/research/project.py | LOW |
| Experimental Result | engine/hydroma/research/experiment.py | LOW |
| Literature Reference | (not found as structured entity) | LOW |

### Project
| Concept | Location | Confidence |
|---------|----------|------------|
| Project Metadata | services/project/models.py | MEDIUM |
| Project Scope | services/project/models.py | MEDIUM |

### Decision
| Concept | Location | Confidence |
|---------|----------|------------|
| Recommendation | engine/hydroma/models/epia.py | MEDIUM |
| Risk Assessment | services/decision/risk.py | LOW |
| Confidence Level | engine/hydroma/provenance.py | HIGH |

### Workflow
| Concept | Location | Confidence |
|---------|----------|------------|
| ET0 Calculation Workflow | engine/hydroma/climate/et_calculator.py | HIGH |
| Water Balance Workflow | engine/hydroma/simulation/balance.py | HIGH |
| Irrigation Scheduling Workflow | engine/hydroma/irrigation/scheduler.py | MEDIUM |

### User
| Concept | Location | Confidence |
|---------|----------|------------|
| User Profile | services/users/models.py | MEDIUM |
| User Role | services/users/models.py | MEDIUM |
| User Permission | services/users/permissions.py | MEDIUM |

### Organization
| Concept | Location | Confidence |
|---------|----------|------------|
| Organization | services/organization/models.py | MEDIUM |
| Tenant | services/organization/models.py | MEDIUM |

### Service
| Concept | Location | Confidence |
|---------|----------|------------|
| Service Registry | services/_registry/registry.py | HIGH |
| Service Contract | services/_contracts/ | HIGH |

---

## 2. Business Rules Catalog

| Rule ID | Rule Name | Description | Location | Confidence |
|---------|-----------|-------------|----------|------------|
| RULE-BR-001 | Irrigation Trigger Threshold | Trigger irrigation when available water < PWP + safety margin | engine/hydroma/irrigation/scheduler.py:45-67 | MEDIUM |
| RULE-BR-002 | Crop Coefficient Lookup | Select Kc based on crop type and growth stage | engine/hydroma/agriculture/crop_coefficient.py:15-34 | HIGH |
| RULE-BR-003 | Reference Crop Assumption | ET0 assumes reference crop (0.12m, green, well-watered) | engine/hydroma/climate/et_calculator.py:6-25 | HIGH |
| RULE-BR-004 | Runoff Threshold | No runoff when P ≤ 0.2S | engine/hydorama/models/runoff_model.py:67-78 | HIGH |
| RULE-BR-005 | Soil Salinity Impact | Reduce yield when EC > threshold | engine/hydroma/soil/salinity.py:23-56 | LOW |
| RULE-BR-006 | Growth Stage Transition | Transition based on accumulated GDD | engine/hydoma/agriculture/growth_stage.py:30-56 | MEDIUM |
| RULE-BR-007 | Water Balance Closure | Mass conservation enforced | engine/hydroma/simulation/balance.py:20-56 | HIGH |
| RULE-BR-008 | DEM Preprocessing | Fill pits before flow direction | engine/land/dem.py:12-34 | MEDIUM |
| RULE-BR-009 | Radiation Conversion | Convert from various units to MJ/m²/day | engine/hydoma/climate/radiation.py:23-45 | MEDIUM |
| RULE-BR-010 | Data Assimilation Priority | Prefer station data over interpolated | engine/hydoma/climate/assimilation.py:15-34 | MEDIUM |

### Undocumented Rules (Suspected)
| Rule ID | Location | Suspected Rule | Confidence |
|---------|----------|----------------|------------|
| RULE-UR-001 | engine/hydroma/climate/et_calculator.py:100-150 | Default humidity when missing | LOW |
| RULE-UR-002 | engine/hydoma/irrigation/scheduler.py:80-100 | Default safety factor for irrigation | LOW |
| RULE-UR-003 | engine/hydoma/watershed/calculator.py:50-70 | Maximum watershed area threshold | LOW |

---

## 3. Domain Entities

### Scientific Engine Entities (Pydantic V2)
| Entity | Fields | Location | Confidence |
|--------|--------|----------|------------|
| ClimateData | temperature, humidity, wind, radiation, precipitation | engine/hydoma/climate/models.py | HIGH |
| SoilProperties | theta_r, theta_s, alpha, n, Ksat, bulk_density | engine/hydoma/soil/physics.py:15-25 | HIGH |
| WatershedData | area, slope, land_use, soil_type | engine/hydoma/watershed/models.py | HIGH |
| RunoffResult | runoff_depth, peak_flow, time_to_peak | engine/hydoma/models/runoff_model.py:12-30 | HIGH |
| ET0Result | et0, temp_min, temp_max, method | engine/hydoma/climate/et_calculator.py:54-60 | HIGH |
| WaterDemand | crop_et, net_demand, gross_demand | engine/hydoma/models/water_demand.py | MEDIUM |
| GroundwaterResult | drawdown, flow_rate, storage | engine/hydoma/models/groundwater_model.py | MEDIUM |

### Service Entities
| Entity | Fields | Location | Confidence |
|--------|--------|----------|------------|
| ServiceInfo | name, version, status, domain | services/_registry/ | HIGH |
| ModelDescriptor | model_id, name, domain, status | services/models/registry.py | HIGH |
| ProvenanceRecord | source, timestamp, version, method | engine/hydoma/provenance.py | HIGH |

---

## 4. Domain Terminology Glossary

| Term | Definition | Standard |
|------|------------|----------|
| ET0 | Reference crop evapotranspiration, daily depth in mm | FAO-56 |
| Kc | Crop coefficient, ratio of crop ET to ET0 | FAO-56 |
| CN | Curve Number, dimensionless parameter for runoff estimation | USDA SCS |
| S | Potential maximum precipitation depth (inches or mm) | USDA SCS |
| Q | Direct runoff depth (same units as P) | USDA SCS |
| R_a | Extraterrestrial radiation (MJ/m²/day) | FAO-56 |
| R_s | Solar (global) radiation at crop surface (MJ/m²/day) | FAO-56 |
| R_n | Net radiation at crop surface (MJ/m²/day) | FAO-56 |
| T | Transmissivity (m²/day) | Standard hydrogeology |
| S (storativity) | Dimensionless drainable porosity | Standard hydrogeology |
| K | Hydraulic conductivity (m/day or m/s) | Standard hydrogeology |
| D8 | Deterministic 8-cell flow direction algorithm | O'Callaghan & Mark (1984) |
| TWI | Topographic Wetness Index = ln(alpha / tan(beta)) | Beven & Kirkby (1979) |

---

## 5. Workflows

### WF-01: ET0 Calculation Pipeline
| Step | Action | Location |
|------|--------|----------|
| 1 | Acquire climate data | engine/hydoma/climate/assimilation.py |
| 2 | Validate and preprocess | engine/hydoma/climate/et_calculator.py:20-50 |
| 3 | Compute radiation components | engine/hydoma/climate/radiation.py |
| 4 | Apply Penman-Monteith | engine/hydoma/climate/et_calculator.py:54-289 |
| 5 | Store results with provenance | engine/hydoma/provenance.py |

### WF-02: Water Balance Simulation
| Step | Action | Location |
|------|--------|----------|
| 1 | Input precipitation | engine/hydoma/simulation/balance.py |
| 2 | Compute ET0 and crop ET | engine/hydoma/climate + agriculture |
| 3 | Compute runoff (SCS-CN) | engine/hydoma/models/runoff_model.py |
| 4 | Compute drainage | engine/hydoma/drainage/ |
| 5 | Reconcile balance | engine/hydoma/simulation/balance.py:50-80 |

### WF-03: Irrigation Scheduling
| Step | Action | Location |
|------|--------|----------|
| 1 | Get current soil moisture | engine/hydoma/soil/physics.py |
| 2 | Get forecast ET demand | engine/hydoma/models/water_demand.py |
| 3 | Compute water deficit | engine/hydoma/irrigation/scheduler.py |
| 4 | Apply irrigation rule | engine/hydoma/irrigation/scheduler.py:45-67 |
| 5 | Output irrigation schedule | engine/hydoma/irrigation/scheduler.py |

### WF-04: Watershed Design
| Step | Action | Location |
|------|--------|----------|
| 1 | Input DEM | engine/land/ |
| 2 | Terrain analysis | engine/land/terrain_analysis.py |
| 3 | Hydrologic analysis | engine/land/hydrology.py |
| 4 | Runoff estimation | engine/hydoma/models/runoff_model.py |
| 5 | Structure design | engine/hydoma/watershed/calculator.py |

---

## 6. Roles and Responsibilities

| Role | Primary Domain | Key Capabilities | Confidence |
|------|---------------|-----------------|------------|
| Hydrologist | Water | Runoff, flow routing, groundwater | HIGH |
| Agronomist | Agriculture | Crop coefficients, growth stages, irrigation scheduling | HIGH |
| Climate Scientist | Climate | Weather data, ET, radiation | HIGH |
| Soil Scientist | Soil | Soil properties, salinity, carbon, erosion | HIGH |
| GIS Specialist | Land | DEM processing, terrain analysis, spatial methods | HIGH |
| Water Resources Engineer | Engineering | Hydraulic design, pipe flow, pump curves | MEDIUM |
| Researcher | Research | Model calibration, validation, experiment design | LOW |

---

## 7. Decision Logic Catalog

| Decision Point | Logic Type | Inputs | Outputs | Location |
|----------------|-----------|--------|---------|----------|
| Irrigation Need | Threshold | Soil moisture, ET demand | Irrigate / Wait | engine/hydoma/irrigation/scheduler.py |
| Crop Selection | Lookup/Rule | Soil type, climate zone | Compatible crops | engine/hydoma/agriculture/crop_match.py |
| Erosion Control | Risk assessment | RUSLE factors, slope | Best practices | engine/hydoma/soil/erosion.py |
| Flood Risk | Threshold | Runoff (SCS-CN) | Risk level | engine/hydoma/models/runoff_model.py |
| Salinity Management | Threshold | Soil EC, crop tolerance | Management action | engine/hydoma/soil/salinity.py |
| Drainage Requirement | Threshold | Water table depth | Drainage capacity | engine/hydoma/drainage/design.py |

---

## 8. Provenance and Verification Mechanisms

### Provenance Tracking
| Mechanism | Description | Location | Confidence |
|-----------|-------------|----------|------------|
| ResultProvenance Enum | Source attribution for calculated results | engine/hydoma/provenance.py:12-89 | HIGH |
| Model Version Registry | Track model versions and fidelity | services/models/registry.py | HIGH |
| Audit Trail | Log all computation steps | engine/hydoma/audit.py | MEDIUM |

### Verification Mechanisms
| Mechanism | Description | Location | Confidence |
|-----------|-------------|----------|------------|
| Formula Catalog | Centralized equation registry | engine/hydoma/formulas/catalog.py | HIGH |
| Unit Tests | Model verification tests | tests/ | HIGH |
| Integration Tests | Cross-model validation | tests/integration/ | MEDIUM |
| FAO Example Tests | ET0 validated against FAO examples | tests/test_et0.py | HIGH |

---

## 9. Domain Knowledge Reusability Assessment

| Knowledge Asset | Scientific Value | Domain Value | Independence | Documentation | Future Role |
|----------------|-----------------|-------------|--------------|---------------|-------------|
| FAO-56 Methodology | HIGH | HIGH | HIGH | Excellent | Hydroma Core |
| SCS-CN Runoff | HIGH | HIGH | HIGH | Good | Hydroma Core |
| Darcy's Law | HIGH | HIGH | HIGH | Good | Hydroma Core |
| van Genuchten Model | HIGH | HIGH | MEDIUM | Good | Hydroma Core |
| RUSLE Erosion | HIGH | HIGH | HIGH | Good | Hydroma Core |
| D8 Flow Direction | HIGH | HIGH | HIGH | Excellent | Hydroma Core |
| Horn's Method | HIGH | HIGH | HIGH | Excellent | Hydroma Core |
| Climate Data Model | MEDIUM | HIGH | LOW | Poor | Integration |
| Irrigation Scheduling | MEDIUM | HIGH | LOW | Fair | Composite |
| Phenology Models | MEDIUM | MEDIUM | LOW | Poor | Reference |
| Carbon Accounting | LOW | MEDIUM | LOW | Poor | Reference |
| Wavelet Analysis | LOW | LOW | LOW | Poor | Reference |
| MRF Segmentation | LOW | LOW | LOW | Poor | Reference |

---

*See also: 01-KNOWLEDGE-INVENTORY.md, 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, 06-TECHNOLOGY-REGISTRY.md*