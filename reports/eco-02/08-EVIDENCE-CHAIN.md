# ECO-02: Evidence Chain Architecture

## Engine → Evidence → Decision → AI → User

---

## Source Evidence
- ECO-01/17-EVIDENCE-ENGINE-COMPATIBILITY.md
- ECO-01/09-SCIENTIFIC-DEPENDENCY-GRAPH.md (Chain-A)
- ECO-01/12-AI-FORENSICS.md (AI isolation)
- ECO-01/16-TASMIMYAR-COMPATIBILITY.md (11 decision elements)

---

## Evidence Chain Diagram (Conceptual)

```
┌─────────────────────────────────────────────────────────────┐
│                    Product Experience                        │
│                    (User Interface)                          │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    Decision Engine (Tasmimyar)               │
│                    - Policy evaluation                       │
│                    - 11 decision elements                     │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    AI Layer (RESEARCH)                        │
│                    - Experimental augmentation               │
│                    - Must not bypass Evidence Engine         │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    Evidence Engine                          │
│                    - Evidence collection                    │
│                    - Provenance tracking                    │
│                    - Validation & audit trail               │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    Domain Services (Hydroma)                │
│                    - Consolidated bounded contexts           │
│                    - 28 domain services → modules            │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    Engine Gateway                            │
│                    - Python/C++ boundary                     │
│                    - ctypes, pybind11, buffer protocol       │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    Scientific Engine                        │
│                    - Python orchestration                     │
│                    - 22 models (VERIFIED→STUB)               │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    C++ Numerical Kernels                     │
│                    - High-performance computation            │
│                    - 10 .cpp, 10 .h, 21 tests                │
└─────────────────────────────────────────────────────────────┘
```

---

## Evidence Types

### From ECO-01/17: Evidence Engine Compatibility Matrix

| Evidence Source | Type | Trust Level |
|-----------------|------|-------------|
| Scientific Models | Computation | HIGH |
| Satellite Data (MODIS, Landsat, Sentinel) | Observation | HIGH |
| Climate Projections (CMIP6) | Projection | MEDIUM |
| Weather Stations | Observation | HIGH |
| AI Output | Prediction | LOW (requires validation) |
| User Input | Manual | VARIABLE |

---

## Decision Elements (Tasmimyar)

From ECO-01/16-TASMIMYAR-COMPATIBILITY.md (11 elements):

1. **Policy Rules** - Governance constraints
2. **Risk Assessment** - Uncertainty quantification
3. **Resource Allocation** - Water distribution priority
4. **Trade-off Analysis** - Multi-objective optimization
5. **Scenario Evaluation** - What-if analysis
6. **Stakeholder Weighting** - Preference modeling
7. **Temporal Constraints** - Time-based rules
8. **Spatial Constraints** - Geographic constraints
9. **Regulatory Compliance** - Legal requirements
10. **Economic Factors** - Cost-benefit analysis
11. **Environmental Limits** - Ecological thresholds

---

## Provenance Tags

Every evidence item must carry:
```json
{
  "source": "CANON-001",
  "model_version": "v2.1",
  "validation_timestamp": "2026-10-08T03:00:00Z",
  "trust_level": "HIGH",
  "provenance_chain": ["CMIP6", "WRF", "Hydroma"],
  "confidence": 0.92
}
```

---

## Chain-A Integration (Scientific)

From ECO-01/09: Climate → ET → Demand → Irrigation
- **Climate**: CMIP6, RegCM, HadGEM2
- **ET**: Penman-Monteith, Hargreaves, Priestley-Taylor
- **Demand**: FAO-56, Blaney-Crop
- **Irrigation**: AquaCrop, SWAT

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/09, 16, 17*