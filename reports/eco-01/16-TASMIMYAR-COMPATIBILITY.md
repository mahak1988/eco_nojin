# ECO-01 Tasmimyar Compatibility Analysis

**Document ID:** ECO-01-16-TASMIMYAR-COMPATIBILITY  
**Scope:** engine/ + services/ decision support outputs  
**Purpose:** Determine whether existing assets can support the Tasmimyar decision support system

---

## 1. Tasmimyar Requirements

Tasmimyar requires support for decision-support with the following inputs and outputs:

| Tasmimyar Element | Required Input/Output | Current Support | Confidence |
|-------------------|----------------------|-----------------|------------|
| Current State | System status, conditions | PARTIAL | MEDIUM |
| Problem | Identified issues | NONE | UNKNOWN |
| Options | Alternative actions | NONE | UNKNOWN |
| Scenario | Future conditions | PARTIAL | MEDIUM |
| Consequence | Outcomes of actions | PARTIAL | MEDIUM |
| Risk | Probability of adverse outcomes | NONE | UNKNOWN |
| Recommendation | Best action advised | PARTIAL | MEDIUM |
| Rationale | Reasoning for recommendation | NONE | UNKNOWN |
| Confidence | Uncertainty level | PARTIAL | MEDIUM |
| Uncertainty | Quantified uncertainty | NONE | UNKNOWN |
| Evidence | Supporting data | PARTIAL | MEDIUM |

---

## 2. Current Decision Outputs

### 2.1 EPIA (Precision Irrigation Advisor)

**Location:** engine/hydoma/models/epia.py

| Output Type | Currently Available | Tasmimyar Compatible | Notes |
|-------------|--------------------|---------------------|-------|
| Recommendation | YES (irrigation schedule) | PARTIAL | No rationale/explanation |
| Confidence | NO | NO | No uncertainty quantification |
| Risk | NO | NO | No risk assessment |
| Evidence | PARTIAL | PARTIAL | Some input data tracked |
| Options | NO | NO | Single recommendation, no alternatives |
| Rationale | NO | NO | No explanation of decision logic |

### 2.2 Irrigation Scheduler

**Location:** engine/hydoma/irrigation/scheduler.py

| Output Type | Currently Available | Tasmimyar Compatible | Notes |
|-------------|--------------------|---------------------|-------|
| Recommendation | YES (when to irrigate, how much) | PARTIAL | Threshold-based, no uncertainty |
| Confidence | NO | NO | No confidence measure |
| Options | NO | NO | Single optimal, no alternatives |
| Evidence | PARTIAL | PARTIAL | Soil moisture data referenced |
| Risk | NO | NO | No drought/flood risk assessment |

### 2.3 Watershed Calculator

**Location:** engine/hydoma/watershed/calculator.py

| Output Type | Currently Available | Tasmimyar Compatible | Notes |
|-------------|--------------------|---------------------|-------|
| Recommendation | YES (structure design) | PARTIAL | Deterministic, no alternatives |
| Consequence | PARTIAL | PARTIAL | Implied by design outputs |
| Evidence | YES (watershed metrics) | YES | Good data foundation |
| Options | NO | NO | Single design, no trade-offs |

### 2.4 Climate Projection

**Location:** engine/hydoma/scenarios/climate_scenarios.py

| Output Type | Currently Available | Tasmimyar Compatible | Notes |
|-------------|--------------------|---------------------|-------|
| Scenario | YES (climate scenarios) | YES | SSP-based scenarios |
| Consequence | PARTIAL | PARTIAL | Implied by projection changes |
| Evidence | PARTIAL | PARTIAL | Based on IPCC data |
| Uncertainty | NO | NO | No uncertainty quantification |

---

## 3. Scientific Outputs Mapping to Tasmimyar

### Available Scientific Outputs

| Model | Output | Units | Uncertainty | Tasmimyar Use |
|-------|--------|-------|-------------|---------------|
| ET0 (PM) | ET0 value | mm/day | No | Evidence → Scenario |
| ET0 (Hargreaves) | ET0 value | mm/day | No | Evidence → Scenario |
| SCS-CN Runoff | Runoff depth | mm | No | Evidence → Risk assessment |
| Darcy Flow | Flow rate | m³/s | No | Evidence → Risk assessment |
| Van Genuchten | Soil moisture | m³/m³ | No | Evidence → Current State |
| RUSLE | Soil loss | tons/ha/year | No | Evidence → Risk assessment |
| Water Demand | Demand | mm/day | No | Evidence → Problem ID |
| Crop Yield | Yield | kg/ha | No | Evidence → Consequence |
| Radiation | R_n, R_s | MJ/m²/day | No | Evidence → Scenario |
| Slope/Aspect | Terrain metrics | degrees | No | Evidence → Current State |
| Terrain Analysis | Terrain attributes | various | No | Evidence → Current State |
| Soil Salinity | EC, SAR | dS/m | No | Evidence → Current State |

---

## 4. Missing Decision Capabilities

### 4.1 Problem Identification
**Gap:** No mechanism to identify problems from current state data.

| Tasmimyar Requirement | Missing Component | Implementation Needed |
|----------------------|-------------------|----------------------|
| Problem detection | Threshold exceedance alert system | Risk indicator computation |
| Problem scope | Spatial/temporal extent of issue | Problem boundary definition |
| Problem severity | Urgency or importance | Priority scoring system |

### 4.2 Alternatives Generation
**Gap:** All models produce single "optimal" outputs, not sets of alternatives.

| Tasmimyar Requirement | Missing Component | Implementation Needed |
|----------------------|-------------------|----------------------|
| Option generation | Multiple scenarios/actions | Alternative generator module |
| Option evaluation | Comparison of alternatives | Multi-criteria evaluation |
| Option trade-offs | Pareto frontier identification | Trade-off visualization |

### 4.3 Risk Assessment
**Gap:** No probabilistic risk assessment.

| Tasmimyar Requirement | Missing Component | Implementation Needed |
|----------------------|-------------------|----------------------|
| Risk probability | Likelihood of adverse outcomes | Probabilistic risk model |
| Risk impact | Consequence of adverse outcomes | Impact assessment |
| Risk aggregation | Combined risk from multiple factors | Bayesian network or similar |

### 4.4 Confidence Quantification
**Gap:** No confidence measures on model outputs.

| Tasmimyar Requirement | Missing Component | Implementation Needed |
|----------------------|-------------------|----------------------|
| Model confidence | Certainty of prediction | Uncertainty propagation |
| Data quality | Input data reliability | Data quality metrics |
| Method confidence | Algorithm reliability | Model validation scores |

### 4.5 Rationale Generation
**Gap:** No explanation of why a recommendation was chosen.

| Tasmimyar Requirement | Missing Component | Implementation Needed |
|----------------------|-------------------|----------------------|
| Decision rationale | Reasoning behind recommendation | Explainable AI or rule tracing |
| Evidence linkage | Why evidence supports conclusion | Evidence weight assignment |
| Trade-off explanation | Why one option over another | Trade-off articulation |

---

## 5. Available Evidence for Decision Support

### Scientific Evidence Currently Available

| Evidence Type | Available | Source | Quality |
|---------------|-----------|--------|---------|
| Current State | YES | Climate, soil, water models | HIGH |
| Scientific Fact | YES | FAO-56, SCS-CN, Darcy | HIGH |
| Model Output | YES | All 22 registered models | VARIES |
| Measurement | YES | Input data to models | MEDIUM |
| Validation | YES | Unit tests against standards | HIGH |
| Projection | YES | Climate scenarios (IPCC-based) | MEDIUM |

### Missing Evidence Types

| Evidence Type | Needed For | Gap Status |
|---------------|------------|------------|
| Local Knowledge | Regional adaptation | UNKNOWN |
| Expert Opinion | Judgment calls | UNKNOWN |
| Field Observation | Ground truth | PARTIAL |
| Monitoring Data | Validation of predictions | PARTIAL |
| Historical Records | Trend analysis | UNKNOWN |
| Economic Data | Cost-benefit analysis | NONE |
| Social Factors | Acceptance/ feasibility | NONE |

---

## 6. Decision Flow Analysis

### Current (Implicit) Decision Flows

```
WF-IRRIGATION:
Soil Moisture + ET Demand
    → Threshold Check (engine/hydoma/irrigation/scheduler.py)
    → Irrigation Recommendation
    → (No uncertainty, no alternatives)
```

```
WF-WATERSHED-DESIGN:
DEM + Climate + Soil
    → Runoff Calculation (SCS-CN)
    → Structure Design (engine/hydoma/watershed/calculator.py)
    → Design Recommendation
    → (No alternatives, no risk assessment)
```

### Required Tasmimyar Decision Flow

```
CURRENT STATE
    ↓
PROBLEM IDENTIFICATION (missing)
    ↓
EVIDENCE COLLECTION
    ↓
OPTION GENERATION (missing)
    ↓
SCENARIO MODELING (partial)
    ↓
CONSEQUENCE ANALYSIS (partial)
    ↓
RISK ASSESSMENT (missing)
    ↓
CONFIDENCE EVALUATION (missing)
    ↓
RECOMMENDATION (partial - single option)
    ↓
RATIONALE (missing)
```

---

## 7. Scientific Output Uncertainty

### Current State
No scientific model in the codebase provides uncertainty quantification on outputs.

### Required for Tasmimyar
Tasmimyar requires:
1. **Output uncertainty** - standard deviation/range on all predictions
2. **Input data uncertainty** - quality metrics on input data
3. **Model structural uncertainty** - confidence in the model itself
4. **Scenario uncertainty** - range of possible futures

### Gap Analysis

| Model | Output Uncertainty | Input Uncertainty | Model Uncertainty |
|-------|-------------------|-------------------|-------------------|
| ET0 (PM) | NO | NO | NO |
| ET0 (Hargreaves) | NO | NO | NO |
| SCS-CN | NO | NO | NO |
| Darcy | NO | NO | NO |
| Theis | NO | NO | NO |
| Van Genuchten | NO | NO | NO |
| RUSLE | NO | NO | NO |
| Water Demand | NO | NO | NO |
| Crop Yield | NO | NO | NO |
| Radiation | NO | NO | NO |
| Climate Projection | NO | NO | NO |

**All models: NO uncertainty quantification.**

---

## 8. Recommendations for Tasmimyar Integration

### Phase 1: Evidence Infrastructure (Post-ECO-01, Architecture Phase)
1. ✅ **Leverage existing scientific models** - strong foundation for evidence
2. ⚠️ **Extend provenance** - add epistemic status, confidence levels
3. ❌ **Add uncertainty quantification** - to all scientific model outputs
4. ❌ **Add decision framework** - problem identification, alternatives

### Phase 2: Decision Layer (Future)
1. **Decision Context Entity** - links current state, problem, options
2. **Risk Model** - probabilistic assessment of outcomes
3. **Confidence Model** - uncertainty propagation through chain
4. **Rationale Generator** - explanation of decision logic
5. **Alternative Generator** - produces multiple options for comparison

### Phase 3: Integration
1. Connect scientific evidence → decision context
2. Connect decision outputs → action planning
3. Connect monitoring → validation loop
4. Connect research → model updates

---

## 9. Available Assets That Can Be Reused

| Asset | Tasmimyar Use | Modification Needed |
|-------|---------------|---------------------|
| Model Registry (22 models) | Evidence/Scientific Facts | Add uncertainty output |
| Provenance Tracking | Evidence chain | Add epistemic status |
| Climate Models | Current State/Scenario | Add uncertainty |
| Soil Models | Current State | Add uncertainty |
| Watershed Calculator | Problem Identification | Extract decision logic |
| Irrigation Scheduler | Alternative Actions | Expose options |
| Water Demand Model | Problem Identification | Add thresholds |
| SCS-CN Runoff | Risk Assessment | Add probability |
| EPIA | Partial Recommendation | Add rationale, options |

---

## 10. Summary: Tasmimyar Readiness

| Capability | Status | Confidence |
|-----------|--------|------------|
| Scientific Evidence Base | ✅ READY | HIGH |
| Current State Representation | ✅ PARTIAL | MEDIUM |
| Scenario Modeling | ✅ PARTIAL | MEDIUM |
| Problem Identification | ❌ MISSING | UNKNOWN |
| Alternative Generation | ❌ MISSING | UNKNOWN |
| Risk Assessment | ❌ MISSING | UNKNOWN |
| Confidence Quantification | ❌ MISSING | UNKNOWN |
| Rationale Generation | ❌ MISSING | UNKNOWN |
| Recommendation Engine | ⚠️ PARTIAL (single output) | MEDIUM |

**Overall Assessment:** Scientific evidence base is strong and ready for reuse. Decision logic layer is essentially missing and must be designed as part of future architecture.

---

*See also: 15-DANESHYAR-COMPATIBILITY.md, 10-HYDROMA-FORENSICS.md, 20-CANONICAL-ASSETS.md*