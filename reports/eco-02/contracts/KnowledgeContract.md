# Knowledge Contract (Daneshyar)

## Purpose
Define the interface contract for the Knowledge Engine (Daneshyar) that manages the 9 knowledge types.

## Scope
Covers knowledge representation, integration, and distribution across architecture layers.

## Contract Terms

### 1. Knowledge Types (9 Types)
Based on ECO-01/15-DANESHYAR-COMPATIBILITY.md:

| Type | ID | Source | Trust Level |
|------|----|--------|-------------|
| Scientific Theory | KT-001 | Peer-reviewed | HIGH |
| Engineering Method | KT-002 | Practice | HIGH |
| Domain Expertise | KT-003 | Local knowledge | MEDIUM |
| Observational Data | KT-004 | Sensors, satellites | HIGH |
| Empirical Formula | KT-005 | Data-derived | MEDIUM |
| Institutional Knowledge | KT-006 | Organizations | MEDIUM |
| Regulatory Knowledge | KT-007 | Laws, policies | HIGH |
| Indigenous Knowledge | KT-008 | Traditional | MEDIUM |
| AI/ML Knowledge | KT-009 | Machine learning | LOW |

### 2. Knowledge Item Format
```json
{
  "knowledge_id": "KTKT-YYYY-XXXX",
  "type": "enum(KT-001..KT-009)",
  "title": "string",
  "description": "string",
  "source": "string (citation or origin)",
  "trust_level": "HIGH | MEDIUM | LOW",
  "valid_from": "ISO 8601",
  "valid_to": "optional ISO 8601",
  "applicability": "geographic or domain scope",
  "references": ["array of related canonical assets"]
}
```

### 3. Integration Contracts

#### To Evidence Engine
- Knowledge items carry provenance tags
- Observational knowledge (KT-004) generates HIGH trust evidence
- Empirical knowledge (KT-005) generates MEDIUM trust evidence
- AI knowledge (KT-009) generates LOW trust evidence

#### To Decision Engine (Tasmimyar)
Knowledge mapping to 11 decision elements:
| Knowledge Type | Decision Element |
|----------------|-----------------|
| KT-001, KT-005 | DE-002 Risk Assessment |
| KT-003 | DE-003 Resource Allocation |
| KT-006 | DE-006 Stakeholder Weighting |
| KT-007 | DE-001, DE-009 Policy Rules |
| KT-008 | DE-008 Spatial Constraints |
| KT-009 | DE-004 Trade-off Analysis |

### 4. Trust Propagation Rules
```python
trust_matrix = {
    "KT-001": "HIGH",      # Scientific theory
    "KT-002": "HIGH",      # Engineering method
    "KT-003": "MEDIUM",    # Domain expertise
    "KT-004": "HIGH",      # Observational data
    "KT-005": "MEDIUM",    # Empirical formula
    "KT-006": "MEDIUM",    # Institutional knowledge
    "KT-007": "HIGH",      # Regulatory knowledge
    "KT-008": "MEDIUM",    # Indigenous knowledge
    "KT-009": "LOW",       # AI/ML knowledge
}
```

### 5. Iranian Domain Knowledge (KT-003)
Special integration for Iranian-specific knowledge:
- Crop coefficients (KBK-001 series)
- Regional climate parameters
- Soil classification
- Water governance structures

### 6. AI Knowledge Isolation
- AI knowledge (KT-009) stored separately
- Only used as evidence input
- Never trusted for core decisions
- Must pass Evidence Engine validation

### 7. Versioning
- Knowledge items versioned
- Changes tracked with timestamps
- Superseded items marked deprecated

## Compliance Verification
Run: `python tools/validate_knowledge_contract.py`

---
*Contract Version: 1.0.0 | Based on: ECO-01/15-DANESHYAR-COMPATIBILITY.md, ECO-01/05-DOMAIN-KNOWLEDGE-REGISTRY.md*
