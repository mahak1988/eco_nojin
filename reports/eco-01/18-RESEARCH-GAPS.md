# ECO-01 Research Gaps

**Document ID:** ECO-01-18-RESEARCH-GAPS  
**Scope:** engine/ + services/ scientific gaps  
**Purpose:** Identify research gaps revealed by the codebase inspection

---

## 1. Research Gap Taxonomy

### Gap Types
- **Missing Model**: Scientific capability not implemented
- **Missing Coupling**: Two models that should interact but don't
- **Missing Data**: Required data not captured or processed
- **Missing Validation**: No validation against real-world data
- **Missing Uncertainty**: No uncertainty quantification
- **Missing Local Adaptation**: Global models not adapted to local conditions
- **Missing Temporal Dynamics**: Time-varying processes not modeled
- **Missing Spatial Dynamics**: Spatial heterogeneity not captured
- **Missing Feedback Loop**: No monitoring → research → model update path
- **Missing Scientific Integration**: Models operate independently without integration

---

## 2. Research Gap Catalog

### RESEARCH-GAP-01: Soil Salinity Scientific Basis

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-01 |
| **Problem** | Soil salinity model lacks documented scientific methodology |
| **Existing Knowledge** | SCS-CN, Van Genuchten, FAO salinity guidelines exist |
| **Current Implementation** | engine/hydoma/soil/salinity.py - equations not documented |
| **Known Limitation** | No scientific references; unclear if matches FAO-56 or standard methods |
| **Gap** | Missing scientific basis for salinity calculation method |
| **Hypothesis** | The current implementation may follow FAO-56 salinity approach but this is not documented |
| **Potential Variables** | EC (dS/m), SAR, pH, soil texture, leaching fraction |
| **Potential Data** | Soil EC measurements, irrigation water EC, crop tolerance tables |
| **Potential Experiment** | Compare current implementation outputs with FAO-56 standard calculations |
| **Potential Validation** | Validate against USDA soil salinity labs database |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | LOW |
| **Risk** | HIGH - salinity results may be incorrect without verified method |
| **Next Research Action** | Document equations; compare with FAO-56; REQUIRES_SCIENTIFIC_REVIEW |

---

### RESEARCH-GAP-02: Climate Data Assimilation Weighting

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-02 |
| **Problem** | Data assimilation weights are not documented or justified |
| **Existing Knowledge** | Ensemble methods, Kalman filtering, inverse distance weighting |
| **Current Implementation** | engine/hydoma/climate/assimilation.py - weighted average |
| **Known Limitation** | No documentation of source priority or weight calculation |
| **Gap** | Missing methodology for combining multiple climate data sources |
| **Hypothesis** | Simple averaging may not be optimal; weighted methods may produce better results |
| **Potential Variables** | Source accuracy, temporal coverage, spatial resolution, sensor type |
| **Potential Data** | Multi-source weather station data, satellite estimates, model reanalysis |
| **Potential Experiment** | Compare simple averaging vs. accuracy-weighted merging against validation stations |
| **Potential Validation** | Cross-validation against independent weather stations |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | LOW |
| **Risk** | MEDIUM - poor data assimilation affects all downstream calculations |
| **Next Research Action** | Implement weight documentation; benchmark methods |

---

### RESEARCH-GAP-03: Theis Well Function Convergence

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-03 |
| **Problem** | Theis well function series expansion convergence behavior undocumented |
| **Existing Knowledge** | Theis (1935) well function W(u), standard series expansions |
| **Current Implementation** | engine/hydoma/models/groundwater_model.py:93-210 |
| **Known Limitation** | Series expansion may diverge for very small u values; truncation error not documented |
| **Gap** | Missing convergence analysis and error bounds for well function |
| **Hypothesis** | Series expansion fails for u < some threshold; approximation W(u) = -0.5772 - ln(u) needed |
| **Potential Variables** | u value (dimensionless time), series terms, truncation order |
| **Potential Data** | Standard Theis well function tables (Hantush, 1964) |
| **Potential Experiment** | Compare series expansion results with published W(u) values |
| **Potential Validation** | Validate against standard pumping test analysis software |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | HIGH - numerical overflow could produce incorrect groundwater results |
| **Next Research Action** | Document convergence region; add error checking; REQUIRES_SCIENTIFIC_REVIEW |

---

### RESEARCH-GAP-04: Missing Uncertainty Quantification

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-04 |
| **Problem** | No scientific model provides uncertainty estimates on outputs |
| **Existing Knowledge** | Monte Carlo, first-order error analysis, Bayesian methods |
| **Current Implementation** | All 22 models output point estimates only |
| **Known Limitation** | No input uncertainty propagation; no confidence intervals |
| **Gap** | Missing uncertainty quantification across the entire model chain |
| **Hypothesis** | Implementing uncertainty propagation would improve decision confidence |
| **Potential Variables** | Input parameter distributions, model structural uncertainty, parameter correlation |
| **Potential Data** | Input uncertainty distributions, Monte Carlo simulation results |
| **Potential Experiment** | Apply Monte Carlo to ET0, propagate to water demand |
| **Potential Validation** | Compare with literature uncertainty estimates |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | HIGH |
| **Risk** | HIGH - decisions made without uncertainty awareness |
| **Next Research Action** | Prototype uncertainty propagation for 2-3 key models |

---

### RESEARCH-GAP-05: Crop Coefficient Adaptation

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-05 |
| **Problem** | Crop coefficients use fixed FAO-56 values, not locally calibrated |
| **Existing Knowledge** | FAO-56 Kc curves; local calibration methods |
| **Current Implementation** | engine/hydoma/agriculture/crop_coefficient.py - standard FAO curves |
| **Known Limitation** | No mechanism for local calibration or adjustment |
| **Gap** | Missing local adaptation framework for crop coefficients |
| **Hypothesis** | Locally calibrated Kc values would improve ETc estimates by 10-20% |
| **Potential Variables** | Climate zone, soil type, cultivar, management practice |
| **Potential Data** | Local yield data, soil data, climate data, farmer observations |
| **Potential Experiment** | Compare FAO-56 Kc vs. locally calibrated Kc |
| **Potential Validation** | Validate against local ET measurements using lysemeters |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | MEDIUM - affects irrigation scheduling accuracy |
| **Next Research Action** | Design calibration data collection protocol |

---

### RESEARCH-GAP-06: Temporal Dynamics Missing

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-06 |
| **Problem** | Models run independently, no temporal coupling |
| **Existing Knowledge** | Coupled hydrological models, data assimilation |
| **Current Implementation** | Each model runs standalone with single-time inputs |
| **Known Limitation** | No time series simulation; no model chaining |
| **Gap** | Missing temporal coupling between models (e.g., ET0 → soil moisture → runoff over time) |
| **Hypothesis** | Temporally coupled simulation would improve watershed behavior prediction |
| **Potential Variables** | Time step, state variables, feedback loops |
| **Potential Data** | Time series weather, soil moisture, streamflow |
| **Potential Experiment** | Build time-stepped coupled model: weather → ET → soil moisture → runoff |
| **Potential Validation** | Compare simulated vs. observed streamflow hydrograph |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | HIGH - static models miss dynamic behavior |
| **Next Research Action** | Design temporal integration architecture |

---

### RESEARCH-GAP-07: Missing Spatial Dynamics

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-07 |
| **Problem** | Models operate on single points, not spatial fields |
| **Existing Knowledge** | Distributed hydrological models, GIS-based analysis |
| **Current Implementation** | Soil, ET0, runoff models take single point inputs |
| **Known Limitation** | No spatial heterogeneity within watershed |
| **Gap** | Missing spatial integration across watershed units |
| **Hypothesis** | Spatially distributed modeling would improve runoff prediction accuracy |
| **Potential Variables** | Spatial variability of soil, land use, slope |
| **Potential Data** | Spatial maps of soil, land use, elevation, climate |
| **Potential Experiment** | Compare lumped vs. distributed SCS-CN modeling |
| **Potential Validation** | Validate with spatially distributed streamflow data |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | MEDIUM - point models may misrepresent watershed behavior |
| **Next Research Action** | Design spatial discretization approach |

---

### RESEARCH-GAP-08: Feedback Loop Missing

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-08 |
| **Problem** | No closed feedback from monitoring to model improvement |
| **Existing Knowledge** | Model updating, data assimilation, machine learning |
| **Current Implementation** | One-way computation: input → model → output |
| **Known Limitation** | No monitoring results feed back to improve models |
| **Gap** | Missing learning loop for continuous model improvement |
| **Hypothesis** | Closed feedback loop would improve prediction accuracy over time |
| **Potential Variables** | Prediction error, model parameters, input quality |
| **Potential Data** | Observed vs. predicted values, recalibration datasets |
| **Potential Experiment** | Implement error-driven parameter updating |
| **Potential Validation** | Monitor prediction accuracy improvement over time |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | MEDIUM - models may drift from reality over time |
| **Next Research Action** | Design monitoring-to-research workflow |

---

### RESEARCH-GAP-09: Soil Organic Matter Modeling

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-09 |
| **Problem** | No comprehensive soil organic matter (SOM) dynamics model |
| **Existing Knowledge** | CENTURY model, RothC, DAYCENT, microbe models |
| **Current Implementation** | Only carbon stock estimation (engine/hydoma/soil/carbon.py) |
| **Known Limitation** | No decomposition, transport, or SOM dynamics |
| **Gap** | Missing process-based SOM modeling |
| **Hypothesis** | SOM dynamics affect water retention, carbon storage, and productivity |
| **Potential Variables** | Climate, soil type, vegetation, management |
| **Potential Data** | Long-term SOM monitoring, litter input data, soil climate |
| **Potential Experiment** | Implement simplified CENTURY or RothC model |
| **Potential Validation** | Compare with long-term flux tower data |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | LOW - current carbon stock estimate is useful as-is |
| **Next Research Action** | Assess current carbon model limitations; identify extension points |

---

### RESEARCH-GAP-10: Water-Energy-Food Nexus

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-10 |
| **Problem** | No integrated assessment across water, energy, and food systems |
| **Existing Knowledge** | WEF Nexus frameworks, integrated assessment models |
| **Current Implementation** | Separate water, agriculture, and energy models |
| **Known Limitation** | No cross-domain optimization or trade-off analysis |
| **Gap** | Missing WEF nexus integration |
| **Hypothesis** | WEF nexus approach would reveal trade-offs and synergies |
| **Potential Variables** | Water productivity, energy use, crop yield, economic value |
| **Potential Data** | Water use, energy consumption, crop yields, market prices |
| **Potential Experiment** | Implement simple WEF nexus optimization |
| **Potential Validation** | Compare with integrated assessment results |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | LOW - current models are useful separately |
| **Next Research Action** | Map WEF connections in current codebase |

---

### RESEARCH-GAP-11: Groundwater-Surface Water Interaction

| Field | Value |
|-------|-------|
| **Research ID** | RESEARCH-GAP-11 |
| **Problem** | No model linking groundwater and surface water systems |
| **Existing Knowledge** | Coupled groundwater-surface water models |
| **Current Implementation** | Separate groundwater (Darcy, Theis) and surface water models |
| **Known Limitation** | No exchange flux computation |
| **Gap** | Missing GW-SW interaction modeling |
| **Hypothesis** | GW-SW exchange affects both groundwater levels and streamflow |
| **Potential Variables** | Hydraulic conductivity at interface, baseflow, seepage |
| **Potential Data** | Streamflow, groundwater levels, bed properties |
| **Potential Experiment** | Implement simple baseflow separation and GW-SW exchange |
| **Potential Validation** | Compare with observed baseflow |
| **Novelty Status** | KNOWN_APPLICATION |
| **Confidence** | MEDIUM |
| **Risk** | MEDIUM - may miss important hydrological processes |
| **Next Research Action** | Survey existing GW-SW coupling methods |

---

## 3. Gap Categorization

| Category | Count | Priority |
|----------|-------|----------|
| Missing Validation | 3 | HIGH |
| Missing Uncertainty | 4 | HIGH |
| Missing Coupling | 3 | MEDIUM |
| Missing Method Documentation | 2 | HIGH |
| Missing Local Adaptation | 1 | MEDIUM |
| Missing Temporal Dynamics | 1 | HIGH |
| Missing Spatial Dynamics | 1 | MEDIUM |
| Missing Feedback Loop | 1 | HIGH |
| Missing Scientific Integration | 2 | MEDIUM |

---

## 4. Novelty Assessment

| Gap | Novelty Status | Rationale |
|-----|----------------|-----------|
| Salinity basis | KNOWN_APPLICATION | Standard FAO method, just undocumented |
| Data assimilation | KNOWN_APPLICATION | Standard methods exist |
| Theis convergence | KNOWN_APPLICATION | Standard series expansion |
| Uncertainty | KNOWN_APPLICATION | Standard methods (Monte Carlo, etc.) |
| Crop calibration | KNOWN_APPLICATION | Standard local calibration |
| Temporal coupling | KNOWN_APPLICATION | Standard in hydrology |
| Spatial dynamics | KNOWN_APPLICATION | Standard GIS hydrology |
| Feedback loop | KNOWN_APPLICATION | Standard adaptive management |
| SOM modeling | KNOWN_APPLICATION | CENTURY/RothC established |
| WEF Nexus | KNOWN_APPLICATION | Established framework |
| GW-SW interaction | KNOWN_APPLICATION | Standard hydrogeology |

**Conclusion:** No novel methods identified. All gaps can be addressed with established approaches.

---

## 5. Research Priority Ranking

| Priority | Gap | Reason |
|----------|-----|--------|
| P0 | Soil Salinity (RESEARCH-GAP-01) | Scientific basis unknown |
| P0 | Theis Convergence (RESEARCH-GAP-03) | Potential numerical failure |
| P0 | Missing Uncertainty (RESEARCH-GAP-04) | Affects all decisions |
| P0 | Climate Data Assimilation (RESEARCH-GAP-02) | Affects all climate inputs |
| P1 | Temporal Dynamics (RESEARCH-GAP-06) | Missing system integration |
| P1 | Feedback Loop (RESEARCH-GAP-08) | Missing learning capability |
| P1 | Crop Calibration (RESEARCH-GAP-05) | Regional accuracy improvement |
| P2 | Spatial Dynamics (RESEARCH-GAP-07) | Scale issues |
| P2 | SOM Modeling (RESEARCH-GAP-09) | Extension, not critical |
| P3 | WEF Nexus (RESEARCH-GAP-10) | Integration opportunity |
| P3 | GW-SW Interaction (RESEARCH-GAP-11) | Domain extension |

---

*See also: 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, 23-SCIENTIFIC-REVIEW-QUEUE.md, 15-DANESHYAR-COMPATIBILITY.md*