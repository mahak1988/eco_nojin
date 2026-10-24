# ECO-02: Tasmimyar Decision Engine

## 11 Decision Elements Architecture

---

## Source Evidence
- ECO-01/16-TASMIMYAR-COMPATIBILITY.md
- ECO-01/17-EVIDENCE-ENGINE-COMPATIBILITY.md
- ECO-01/15-DANESHYAR-COMPATIBILITY.md

---

## 11 Decision Elements

From ECO-01/16:

| Element | Description | Knowledge Type | Evidence Required |
|---------|-------------|----------------|-------------------|
| DE-001 | Policy Rules | KT-007 (Regulatory) | Legal documents |
| DE-002 | Risk Assessment | KT-001 (Scientific) | Model uncertainty |
| DE-003 | Resource Allocation | KT-003 (Domain) | Water availability |
| DE-004 | Trade-off Analysis | KT-002 (Engineering) | Multi-model output |
| DE-005 | Scenario Evaluation | KT-004 (Observational) | Climate scenarios |
| DE-006 | Stakeholder Weighting | KT-006 (Institutional) | Stakeholder input |
| DE-007 | Temporal Constraints | KT-005 (Empirical) | Seasonal patterns |
| DE-008 | Spatial Constraints | KT-003 (Domain) | Geographic limits |
| DE-009 | Regulatory Compliance | KT-007 (Regulatory) | Water law database |
| DE-010 | Economic Factors | KT-003 (Domain) | Cost data |
| DE-011 | Environmental Limits | KT-001 (Scientific) | Ecological thresholds |

---

## Decision Engine Architecture

```
┌─────────────────────────────────────────────────┐
│          Decision Engine (Tasmimyar)            │
├─────────────────────────────────────────────────┤
│  DE-006 Stakeholder Weighting                   │
│                                                 │
│  DE-001 Policy Rules ──→ DE-009 Regulatory     │
│  DE-002 Risk Assessment                          │
│  DE-003 Resource Allocation                      │
│  DE-004 Trade-off Analysis                       │
│  DE-005 Scenario Evaluation                      │
│  DE-006 Stakeholder Weighting                    │
│  DE-007 Temporal Constraints                     │
│  DE-008 Spatial Constraints                      │
│  DE-009 Regulatory Compliance                    │
│  DE-010 Economic Factors                         │
│  DE-011 Environmental Limits                    │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│          Evidence Engine                        │
│  - Validated evidence only                      │
│  - Provenance tags required                     │
└─────────────────────────────────────────────────┘
```

---

## Decision Flow

### Step 1: Evidence Ingestion
- Receive evidence from Evidence Engine
- Validate provenance tags
- Assign trust levels

### Step 2: Multi-Criteria Evaluation
```
Input: Evidence E with trust T
For each Decision Element DE_i:
    Evaluate DE_i(E) → Score S_i
    Apply weight W_i (from DE-006)
    Result: R_i = S_i * W_i * T
Aggregate(R_1...R_11) → Final Decision D
```

### Step 3: Output
- Decision with provenance chain
- Confidence interval
- Alternative recommendations

---

## Trade-off Analysis (DE-004)

### Multi-Objective Optimization
1. **Economic Objective**: Minimize cost
2. **Social Objective**: Maximize equity
3. **Environmental Objective**: Minimize ecological impact
4. **Technical Objective**: Maximize reliability

### Pareto Front Generation
- Uses `optimization.cpp` C++ kernel
- Generates set of non-dominated solutions
- Decision-maker selects from Pareto front

---

## Scenario Evaluation (DE-005)

### Supported Scenarios
| Scenario | Description | Climate Models |
|----------|-------------|----------------|
| SCEN-001 | Baseline (current conditions) | Historical |
| SCEN-002 | RCP 4.5 (moderate warming) | CMIP6, RegCM |
| SCEN-003 | RCP 8.5 (high warming) | CMIP6, HadGEM2 |
| SCEN-004 | Stakeholder-defined | User-provided |

---

## Risk Assessment (DE-002)

### Risk Factors
| Factor | Source | Weight |
|--------|--------|--------|
| Model uncertainty | SCIENTIFIC-KNOWLEDGE-REGISTRY | 0.3 |
| Climate variability | CMIP6 ensemble spread | 0.25 |
| Data quality | Evidence Engine validation | 0.2 |
| Stakeholder disagreement | DE-006 weighting | 0.15 |
| Implementation error | Testing results | 0.1 |

---

## Integration Points

### Input
- Evidence Engine (validated evidence)
- Daneshyar (knowledge base for constraints)
- Stakeholder interface (preferences)

### Output
- Decision recommendation
- Policy rules
- Resource allocation plans

### Feedback Loop
```
Decision → Evidence Engine → Validates inputs → Daneshyar (updates)
```

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/16*