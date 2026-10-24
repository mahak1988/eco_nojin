# ECO-02: Evidence Engine Compatibility

## Evidence Source Integration and Validation

---

## Source Evidence
- ECO-01/17-EVIDENCE-ENGINE-COMPATIBILITY.md
- ECO-01/10-HYDROMA-FORENSICS.md (Hydroma 4-layer model)
- ECO-01/09-SCIENTIFIC-DEPENDENCY-GRAPH.md

---

## Hydroma 4-Layer Model

From ECO-01/10-HYDROMA-FORENSICS.md:

| Layer | Name | Purpose | Evidence Interface |
|-------|------|---------|-------------------|
| L1 | Scientific Computation | Core science algorithms | Direct from C++ kernels |
| L2 | Numerical Computation | High-performance numerics | C++ kernels via ctypes |
| L3 | Integration | Model coupling, orchestration | Python engine |
| L4 | Provenance & Output | Audit trail, evidence tags | Evidence Engine |

---

## Evidence Sources Matrix

| Source Type | Examples | Trust Level | Validation Required |
|-------------|----------|-------------|---------------------|
| Scientific Models | Penman-Monteith, FAO-56 | HIGH | Peer-review check |
| Observational Data | Weather stations, satellites | HIGH | Quality check |
| Climate Projections | CMIP6, RegCM, WRF | MEDIUM | Ensemble validation |
| AI Output | ML predictions | LOW | Evidence Engine validation |
| User Input | Manual parameters | VARIABLE | Confirmation flag |

---

## Evidence Validation Pipeline

```
Source Data
    ↓
[Ingestion]
    ↓
[Format Validation] — Check structure
    ↓
[Unit Validation] — Check SI units (UNIFORMAT)
    ↓
[Provenance Tagging] — Assign evidence tags
    ↓
[Trust Level Assignment] — HIGH/MEDIUM/LOW
    ↓
[Evidence Storage] — Evidence Engine database
    ↓
[Distribution to Consumers] — Decision, AI, Knowledge
```

---

## Evidence Tag Schema

```json
{
  "evidence_id": "EVID-2026-XXX",
  "source": "CANON-001",
  "source_type": "scientific_model",
  "trust_level": "HIGH",
  "validation_timestamp": "2026-10-08T03:00:00Z",
  "provenance_chain": ["CMIP6", "WRF", "hydroma/et"],
  "confidence": 0.92,
  "units": "mm/day",
  "validation_method": "benchmark_against_modis",
  "validated_by": "evidence_engine_v2.1"
}
```

---

## Cross-Validation Matrix

| Evidence Source | Validates Against | Frequency | Status |
|-----------------|-------------------|-----------|--------|
| MODIS ET | Penman-Monteith, Hargreaves | Monthly | ACTIVE |
| Landsat | Land use, soil data | Quarterly | ACTIVE |
| Sentinel-2 | Crop parameters | Monthly | ACTIVE |
| Weather stations | Interpolated climate | Daily | ACTIVE |
| CMIP6 ensemble | Individual climate models | Annual | PENDING |

---

## Evidence Engine Components

### 1. Ingestion Service
- Accepts data from all sources
- Handles format conversion
- Initial validation

### 2. Validation Service
- Runs cross-validation checks
- Applies trust level algorithms
- Logs all validations

### 3. Storage Service
- Stores evidence with full provenance
- Version control for evidence
- Query interface for consumers

### 4. Distribution Service
- Pushes evidence to Decision Engine
- Provides evidence to AI (with validation)
- Updates Knowledge Registry

---

## Scientific Review Queue Integration

From ECO-01/23-SCIENTIFIC-REVIEW-QUEUE.md:

| Priority | Evidence Items | Review Frequency |
|----------|---------------|------------------|
| P0 | CONFLICT-006, UNKNOWN-003 | Immediate |
| P1 | GAP-003, GAP-004, CONFLICT-003 | Monthly |
| P2 | GAP-006, GAP-009, CONFLICT-005 | Quarterly |
| P3 | GAP-011, GAP-014 | Annually |

---

## Evidence Engine Interface

### To Scientific Engine
```python
class EvidenceEngine:
    def get_validated_evidence(self, model_id, time_range):
        """Returns evidence with provenance tags"""
        pass
    
    def validate_model_output(self, model_id, output_data):
        """Validates and tags model output"""
        pass
```

### From Scientific Engine
```python
class ScientificEngine:
    def emit_evidence(self, evidence_data, provenance_chain):
        """Sends evidence to Evidence Engine"""
        pass
```

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/10, 17*