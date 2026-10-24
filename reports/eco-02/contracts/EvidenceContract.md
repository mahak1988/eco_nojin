# Evidence Contract (Provenance)

## Purpose
Define the interface contract for the Evidence Engine that ensures provenance tracking and trust level assignment.

## Scope
Covers evidence collection, validation, provenance tagging, and distribution to decision consumers.

## Contract Terms

### 1. Evidence Item Format
All evidence must carry standardized provenance tags:

```json
{
  "evidence_id": "EVID-YYYY-XXXXXX",
  "source_id": "CANON-XXX or data source ID",
  "source_type": "scientific_model | observational | climate_projection | ai_prediction | user_input",
  "trust_level": "HIGH | MEDIUM | LOW",
  "confidence": 0.0-1.0,
  "timestamp": "ISO 8601",
  "units": "string (SI standard)",
  "value": "data payload or reference",
  "provenance_chain": ["array of upstream evidence IDs"],
  "validation_method": "string (benchmark, cross-validation, etc.)",
  "validated_by": "component that performed validation",
  "geospatial_ref": "EPSG:4326 or specified projection",
  "temporal_ref": "ISO 8601 time range"
}
```

### 2. Trust Level Assignment Rules

| Source Type | Default Trust Level | Validation Required |
|-------------|--------------------|-------------------%-----|
| Scientific Models (VERIFIED) | HIGH | Benchmark against observations |
| Scientific Models (SCIENTIFICALLY_SUPPORTED) | MEDIUM | Cross-validation with other models |
| Observational Data | HIGH | Quality flags, outlier detection |
| Climate Projections (CMIP6 ensemble) | MEDIUM | Ensemble consistency check |
| AI Predictions | LOW | Evidence Engine validation required |
| User Input | VARIABLE | Confirmation flag required |

### 3. Evidence Chain Contract

The evidence chain MUST follow: `Engine → Evidence → Decision → AI → User`

#### Engine → Evidence
- Scientific Engine emits evidence with provenance
- Evidence Engine validates and tags
- Trust level assigned based on model maturity

#### Evidence → Decision
- Only validated evidence passes
- Trust-weighted scoring applied
- Provenance traceable to source

#### Decision → AI
- AI receives evidence through Decision Engine
- AI cannot directly access Engine or raw Evidence
- AI output must carry evidence of its inputs' provenance

#### AI → User
- AI recommendations include confidence levels
- User warned of LOW trust AI outputs

### 4. Validation Pipeline

```python
class EvidenceValidator:
    def validate(self, evidence_item) -> EvidenceItem:
        """
        Pipeline:
        1. Format validation (structure, required fields)
        2. Unit validation (SI compliance, UNIFORMAT)
        3. Provenance validation (chain completeness)
        4. Trust level assignment
        5. Confidence scoring
        6. Storage with timestamp
        """
        pass
```

### 5. Cross-Validation Protocol

| Evidence Source | Validates Against | Frequency |
|-----------------|-------------------|-----------|
| MODIS ET | Penman-Monteith output | Monthly |
| GPM IMERG | Rain gauge networks | Daily |
| CMIP6 | Weather station network | Monthly |
| AI predictions | Scientific models | Real-time |

### 6. Storage Requirements
- Immutable evidence store
- Version-controlled provenance
- Queryable by evidence_id, source, trust_level, timestamp
- Audit trail for all transformations

### 7. Distribution API
```python
class EvidenceEngine:
    def get_evidence(self, criteria) -> List[EvidenceItem]:
        """Query evidence by source, trust, time, geography"""
        pass
    
    def emit_evidence(self, item: EvidenceItem) -> str:
        """Register new evidence, return evidence_id"""
        pass
    
    def validate_chain(self, evidence_ids: List[str]) -> bool:
        """Verify complete provenance chain"""
        pass
```

### 8. Monitoring
- Evidence ingestion rates
- Trust level distribution
- Validation failure rates
- Chain integrity checks

## Compliance Verification
Run: `python tools/validate_evidence_contract.py`

---
*Contract Version: 1.0.0 | Based on: ECO-01/17-EVIDENCE-ENGINE-COMPATIBILITY.md, ECO-01/08-EQUATION-AND-UNIT-FORENSICS.md*
