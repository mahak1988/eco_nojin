# Tasmimyar Decision Engine Contract

## Purpose
Define the interface contract for the Decision Engine (Tasmimyar) that evaluates policy decisions using 11 decision elements.

## Scope
Covers decision evaluation, policy rule application, multi-criteria analysis, and integration with Evidence Engine and Knowledge Layer.

## Contract Terms

### 1. 11 Decision Elements
Based on ECO-01/16-TASMIMYAR-COMPATIBILITY.md:

| Element ID | Name | Input Source | Output Type |
|-----------|------|--------------|-------------|
| DE-001 | Policy Rules | KT-007 (Regulatory) | Boolean (compliant/violates) |
| DE-002 | Risk Assessment | KT-001, KT-002 | Float (0.0-1.0 risk score) |
| DE-003 | Resource Allocation | KT-003, Evidence | Quantity (water allocation) |
| DE-004 | Trade-off Analysis | Multiple evidence types | Pareto front |
| DE-005 | Scenario Evaluation | Climate scenarios | Scenario scores |
| DE-006 | Stakeholder Weighting | KT-006 | Weight coefficients |
| DE-007 | Temporal Constraints | KT-005 | Time window |
| DE-008 | Spatial Constraints | KT-003 | Geographic bounds |
| DE-009 | Regulatory Compliance | KT-007 | Compliance status |
| DE-010 | Economic Factors | Domain data | Cost/benefit |
| DE-011 | Environmental Limits | KT-001 | Threshold values |

### 2. Decision Input Format
```json
{
  "decision_id": "DEC-YYYY-XXXXXX",
  "scenario": "scenario identifier",
  "context": {
    "temporal": {"start": "ISO 8601", "end": "ISO 8601"},
    "spatial": {"bbox": [min_lon, min_lat, max_lon, max_lat]},
    "stakeholders": ["list of stakeholder IDs"]
  },
  "evidence": [{
    "evidence_id": "EVID-YYYY-XXXXXX",
    "trust_level": "HIGH/MEDIUM/LOW",
    "confidence": 0.0-1.0
  }],
  "knowledge": [{
    "knowledge_id": "KT-...",
    "type": "KT-001..KT-009"
  }]
}
```

### 3. Decision Evaluation Process

1. **Evidence Filtering**: Only HIGH/MEDIUM trust evidence used
2. **Weight Assignment**: DE-006 stakeholder weighting applied
3. **Multi-Criteria Scoring**: Each DE element scored independently
4. **Aggregation**: Weighted sum with trust factors
5. **Validation**: Result checked against DE-001 and DE-009
6. **Output Generation**: Decision with full provenance

### 4. Decision Output Format
```json
{
  "decision_id": "DEC-YYYY-XXXXXX",
  "timestamp": "ISO 8601",
  "scores": {
    "DE-001": {"result": true, "confidence": 0.95, "evidence": ["EVID-..."]},
    "DE-002": {"result": 0.23, "confidence": 0.88, "evidence": ["EVID-..."]},
    "...": "..."
  },
  "final_decision": {
    "recommendation": "string",
    "confidence": 0.78,
    "alternatives_considered": 3,
    "pareto_optimal": true
  },
  "provenance": {
    "evidence_chain": ["EVID-..."],
    "knowledge_sources": ["KT-..."],
    "stakeholder_input": ["SH-..."]
  }
}
```

### 5. Scenario Evaluation Protocol

Supported scenarios (DE-005):
| Scenario ID | Description | Climate Models |
|-------------|-------------|----------------|
| SCEN-001 | Baseline | Historical data |
| SCEN-002 | RCP 4.5 | CMIP6, RegCM |
| SCEN-003 | RCP 8.5 | CMIP6, HadGEM2 |
| SCEN-004 | Stakeholder-defined | User-provided |

### 6. Risk Assessment (DE-002)
Risk factors and weights:
| Factor | Weight | Description |
|--------|--------|-------------|
| Model uncertainty | 0.30 | From model registry |
| Climate variability | 0.25 | From ensemble spread |
| Data quality | 0.20 | Evidence Engine validation |
| Stakeholder disagreement | 0.15 | DE-006 weighting |
| Implementation error | 0.10 | Test coverage |

### 7. Trade-off Analysis (DE-004)
Multi-objective optimization using C++ kernel:
1. **Economic**: Minimize cost
2. **Social**: Maximize equity
3. **Environmental**: Minimize ecological impact
4. **Technical**: Maximize reliability

Pareto front generated using `optimization.cpp` kernel.

### 8. Integration Requirements
- Must receive evidence from Evidence Engine ONLY
- Knowledge items queried from Daneshyar
- AI input pre-validated by Evidence Engine
- Decisions logged with full provenance

### 9. Testing Contract
- Unit tests for each decision element
- Integration tests with Evidence Engine
- Scenario evaluation tests
- Performance tests for optimization

## Compliance Verification
Run: `python tools/validate_tasmimyar_contract.py`

---
*Contract Version: 1.0.0 | Based on: ECO-01/16-TASMIMYAR-COMPATIBILITY.md, ECO-01/12-AI-FORENSICS.md*
