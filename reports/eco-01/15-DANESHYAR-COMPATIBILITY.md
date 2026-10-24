# ECO-01 Daneshyar Compatibility Analysis

**Document ID:** ECO-01-15-DANESHAYAR-COMPATIBILITY  
**Scope:** Knowledge structures for Daneshyar integration  
**Purpose:** Determine what existing assets can support the Daneshyar knowledge framework

---

## 1. Daneshyar Knowledge Types Required

Daneshyar (for the Islamic Republic of Iran) requires a comprehensive knowledge management framework supporting:

| Knowledge Type | Description | Current Support | Confidence |
|----------------|-------------|-----------------|------------|
| OBSERVATION | Raw data from sensors, measurements | PARTIAL | MEDIUM |
| MEASUREMENT | Quantified scientific measurements | PARTIAL | MEDIUM |
| LOCAL_KNOWLEDGE | Indigenous/traditional/local knowledge | PARTIAL | LOW |
| TRADITIONAL_KNOWLEDGE | Cultural/practice knowledge | NONE | UNKNOWN |
| EXPERT_OPINION | Expert judgments and assessments | NONE | UNKNOWN |
| SCIENTIFIC_EVIDENCE | Peer-reviewed or validated results | PARTIAL | MEDIUM |
| MODEL_OUTPUT | Computational model results | YES | HIGH |
| INFERENCE | Logical conclusions from evidence | NONE | UNKNOWN |
| HYPOTHESIS | Testable scientific propositions | NONE | UNKNOWN |
| EXPERIMENTAL_RESULT | Controlled experiment outcomes | NONE | UNKNOWN |

---

## 2. Existing Knowledge Representation

### 2.1 Model Output (Strongest Support)

| Asset | Location | Supports Daneshyar Type | Confidence |
|-------|----------|------------------------|------------|
| Scientific Model Registry | services/models/registry.py | MODEL_OUTPUT | HIGH |
| Provenance Tracking | engine/hydoma/provenance.py | PROVENANCE | HIGH |
| Formula Catalog | engine/hydoma/formulas/catalog.py | SCIENTIFIC_EVIDENCE | HIGH |
| Result Structures | services/models/registry.py:597-623 | MODEL_OUTPUT | HIGH |
| Model Cards | services/models/registry.py:462-555 | SCIENTIFIC_EVIDENCE | HIGH |

**Evidence:** The model registry returns `{slug, fidelity, result, executed_ms}` with provenance tracking. Model cards include validity domains and limitations.

### 2.2 Observation/Measurement (Partial Support)

| Asset | Location | Supports Daneshyar Type | Confidence |
|-------|----------|------------------------|------------|
| Climate Data Models | engine/hydoma/climate/ | OBSERVATION/MEASUREMENT | MEDIUM |
| Soil Measurement Models | engine/hydoma/soil/ | OBSERVATION/MEASUREMENT | MEDIUM |
| Monitoring Service | services/monitoring/ | OBSERVATION | MEDIUM |
| Field Monitoring | services/field_monitoring/ | OBSERVATION | MEDIUM |
| MRV Service | services/mrv/ | MEASUREMENT | MEDIUM |

**Evidence:** Climate and soil models accept observed/measured data as inputs. Monitoring services collect field observations.

### 2.3 Local Knowledge (Insufficient Support)

| Asset | Location | Current Functionality | Gap |
|-------|----------|----------------------|-----|
| daneshyar service | services/daneshyar/ | Basic knowledge entry | No local knowledge framework |
| knowledge service | services/knowledge/ | Knowledge base | No local knowledge distinction |
| irrigation scheduler | engine/hydoma/irrigation/scheduler.py | Hard-coded rules | Local practice not captured |

**Gap:** Local knowledge is not distinguished from scientific fact. No provenance or epistemic status tracking for traditional knowledge.

### 2.4 Expert Opinion (No Support)

No structured representation of expert opinions found in the codebase.

### 2.5 Scientific Evidence (Partial)

| Asset | Location | Evidence Type |
|-------|----------|--------------|
| Model validation flags | services/models/registry.py:466-555 | Scientific validation status |
| Fidelity labels | services/models/registry.py:77 | official/simplified/experimental |
| Unit tests | tests/ | Verification evidence |
| Scientific references | services/models/registry.py:49-356 | External citations |

**Gap:** No evidence linking to specific research projects, experiments, or peer-reviewed publications beyond model references.

### 2.6 Hypothesis/Experimental Results (No Support)

No structured entity for hypotheses or experimental results found.

---

## 3. Knowledge Structure Mapping

### 3.1 Observation/Measurement Chain

```
Current Structure:
Weather Station
  ↓ (data ingestion)
Climate Assimilation (engine/hydoma/climate/assimilation.py)
  ↓
ClimateData model (pydantic schema)
  ↓
ET0 Calculation (engine/hydoma/climate/et_calculator.py)
  ↓
ET0Result (with provenance)

Gap for Daneshyar:
Observation needs:
  - Timestamp (partially supported)
  - Location (partially supported)
  - Observer identity (NOT supported)
  - Measurement method (NOT supported)
  - Accuracy/precision (NOT supported)
  - Observation type (weather/sensor/model) (partially via provenance)
```

### 3.2 Local Knowledge Structure

```
Current Structure:
services/daneshyar/ (basic)
  ↓
services/knowledge/ (knowledge base)

Gap for Daneshyar:
Local Knowledge needs:
  - Originator identity (elders, community) 
  - Cultural context
  - Epistemic status (traditional ≠ scientific)
  - Confidence level (high medium low)
  - Verification status
  - Provenance of local knowledge
  - Separation from scientific facts
```

### 3.3 Evidence Structure

```
Current Structure:
MODEL_CARDS in services/models/registry.py
  ↓ (includes)
Valid domain, limitations, references

Gap for Daneshyar:
Evidence needs:
  - Evidence type (observation/measurement/model_output/expert_opinion)
  - Strength/confidence
  - Source attribution
  - Temporal validity
  - Spatial scope
  - Peer review status
  - Relationship to hypotheses
```

---

## 4. Provenance Compatibility

### 4.1 Current Provenance Support

| Feature | Implemented | Location | Daneshyar Compatible |
|---------|------------|----------|---------------------|
| Source tracking | YES | engine/hydoma/provenance.py | PARTIAL |
| Timestamp tracking | YES | engine/hydoma/provenance.py | YES |
| Version tracking | YES | services/models/registry.py | YES |
| Confidence levels | YES | services/models/registry.py (fidelity) | PARTIAL |
| Epistemic status | PARTIAL | Model cards have validity domain | PARTIAL |
| Knowledge type distinction | NO | - | NO |
| Local knowledge separator | NO | - | NO |

### 4.2 Provenance Enhancement Needed

| Enhancement | Required For | Implementation Hint |
|------------|--------------|---------------------|
| Knowledge type tagging | All Daneshyar types | Add `knowledge_type` enum to provenance |
| Epistemic status flag | Scientific vs traditional | Add `epistemic_status` field |
| Confidence scoring | All evidence | Use current `confidence` field in provenance |
| Spatial/temporal scope | Observation/evidence | Extend provenance schema |
| Source identity | Local knowledge, observations | Extend provenance with `source_entity` |

---

## 5. Existing Assets That Can Be Reused

### Directly Reusable
| Asset | Daneshyar Type Supported | Notes |
|-------|--------------------------|-------|
| Model Registry | Model output, Scientific evidence | Strong provenance chain |
| Formula Catalog | Scientific evidence | Equations documented with references |
| Provenance Tracking | Partial provenance | Need extension for knowledge types |
| Model Cards | Scientific evidence | Validity and limitations documented |
| Climate Data Models | Observation, Measurement | Accept timestamped, located data |
| Soil Models | Observation, Measurement | Accept measured parameters |

### Partially Reusable
| Asset | Daneshyar Type | Enhancement Needed |
|-------|---------------|-------------------|
| Monitoring Service | Observation | Add observer identity, accuracy |
| MRV Service | Measurement | Add verification status |
| Local Knowledge (basic) | Local Knowledge | Complete framework overhaul |
| Audit Service | Evidence | Extend to evidence records |

### Not Reusable (Missing)
| Daneshyar Type | Gap | Required |
|----------------|-----|----------|
| Traditional Knowledge | No structure | Dedicated entity |
| Expert Opinion | No structure | Opinion model with confidence |
| Hypothesis | No structure | Research hypothesis entity |
| Inference | No structure | Logical conclusion tracking |
| Experimental Results | No structure | Experiment result model |

---

## 6. Epistemic Status Model

### Current State
The codebase does not distinguish between knowledge types epistemologically. All model outputs are treated equally regardless of whether they are:
- Scientific measurements
- Traditional/local knowledge
- Expert opinions
- Model predictions
- Hypotheses

### Required Epistemic Status Model

```python
class EpistemicStatus(Enum):
    OBSERVATION = "observation"
    MEASUREMENT = "measurement"
    LOCAL_KNOWLEDGE = "local_knowledge"
    TRADITIONAL_KNOWLEDGE = "traditional_knowledge"
    EXPERT_OPINION = "expert_opinion"
    SCIENTIFIC_EVIDENCE = "scientific_evidence"
    MODEL_OUTPUT = "model_output"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    EXPERIMENTAL_RESULT = "experimental_result"

class KnowledgeEntity(PydanticModel):
    epistemic_status: EpistemicStatus
    source: str
    source_type: str
    confidence: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    validity_start: datetime
    validity_end: Optional[datetime]
    spatial_scope: Optional[Geometry]
    provenance: List[ProvenanceEntry]
    peer_reviewed: bool
    # Local knowledge specific
    cultural_context: Optional[str]
    originator: Optional[str]
```

---

## 7. Key Findings

1. ✅ **Model output support is strong** - existing provenance and model registry can support Daneshyar's MODEL_OUTPUT type
2. ✅ **Observation/measurement partial support** - climate and soil data models accept observations, but lack full metadata
3. ⚠️ **Local knowledge support is missing** - despite having a daneshyar service, it does not implement a local knowledge framework
4. ❌ **No expert opinion structure** - opinions cannot be tracked separately from facts
5. ❌ **No hypothesis framework** - cannot record or track research hypotheses
6. ⚠️ **Epistemic status unclear** - all data treated equally; no distinction between local knowledge and scientific fact
7. ⚠️ **Provenance exists but needs extension** - current provenance covers calculations but not knowledge types

---

## 8. Recommendations

### Phase 1: Immediate (Post-ECO-01)
1. Extend provenance model to include `epistemic_status` field
2. Add knowledge type enum to model output structures
3. Ensure provenance tracks whether output is model_result, observation, or inference

### Phase 2: Architecture Design
1. Design LocalKnowledge entity with cultural context, origin, and verification status
2. Design ExpertOpinion entity with opinion holder, confidence, and rationale
3. Design Hypothesis entity with experiment linkage
4. Design Evidence entity linking observations to conclusions

### Phase 3: Implementation
1. Migrate existing provenance to include epistemic status
2. Implement knowledge type tagging on all existing entities
3. Add local knowledge input interfaces
4. Add hypothesis tracking system

---

## 9. Asset Reuse Summary

| Existing Asset | Can Reuse For Daneshyar | Modification Required |
|----------------|------------------------|----------------------|
| Provenance Engine | ✅ YES - as foundation | Add epistemic status fields |
| Model Registry | ✅ YES - model outputs | Add knowledge type tagging |
| Formula Catalog | ✅ YES - scientific evidence | Add evidence metadata |
| Climate Data Models | ✅ YES - observations | Extend with observer metadata |
| Soil Models | ✅ YES - measurements | Extend with measurement context |
| Monitoring Service | ✅ YES - observations | Add observation metadata |
| Knowledge Service | PARTIAL - basic KB | Major extension needed |
| Local Knowledge (service) | ❌ NO | Complete redesign |

---

## 10. Separation of Concerns Assessment

**Critical Principle:** Local Knowledge ≠ Scientific Fact

| Aspect | Scientific Fact | Local Knowledge | Current Support |
|--------|-----------------|-----------------|-----------------|
| Epistemic Status | Verified through peer review | Based on cultural/practice experience | NO |
| Source Attribution | Institution/researcher | Community/elders | NO |
| Validation Method | Empirical testing | Community consensus | NO |
| Confidence Level | Statistical/quantitative | Qualitative/trusted | NO |
| Provenance | Methodology + data | Oral tradition + practice | NO |
| Temporal Scope | Time-bound | Generational | NO |

**Finding:** The codebase currently does NOT distinguish between these knowledge types. Any future Daneshyar implementation must establish this boundary explicitly.

---

*See also: 16-TASMIMYAR-COMPATIBILITY.md, 05-DOMAIN-KNOWLEDGE-REGISTRY.md, 20-CANONICAL-ASSETS.md*