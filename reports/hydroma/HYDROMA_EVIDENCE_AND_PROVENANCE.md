# HYDROMA EVIDENCE AND PROVENANCE

**Generated**: 2026-10-09  
**Purpose**: Document evidence collection, provenance tracking, and traceability

---

## 1. Evidence Chain Architecture

```
Data Source
    ↓
Raw Data Version
    ↓
Data Transforms
    ↓
Ready Data
    ↓
Model Execution (Registry ID + Version)
    ↓
Parameters & Configuration
    ↓
Computation Result
    ↓
Uncertainty & Limitations
    ↓
Interpretation
    ↓
Decision/Recommendation
```

Each link generates an `Evidence` object with:
- **id**: Unique UUID
- **source**: EvidenceSource (MEASUREMENT, MODEL, SIMULATION, etc.)
- **evidence_type**: EvidenceType (QUANTITATIVE, QUALITATIVE, CITATION)
- **value**: The evidence content
- **confidence**: [0.0, 1.0]
- **provenance**: Chain of upstream evidence IDs
- **metadata**: Context (model version, data version, config)

---

## 2. Evidence Engine Implementation

**File**: `engine/evidence/__init__.py` (217 lines)

### Components
| Class | Status | Description |
|-------|--------|-------------|
| `EvidenceEngine` | ✅ PASS | In-memory evidence store with validation |
| `Evidence` | ✅ PASS | Dataclass with full provenance |
| `EvidenceSource` | ✅ PASS | 6 source types |
| `EvidenceType` | ✅ PASS | 3 representation types |
| `ValidationResult` | ✅ PASS | Quality validation results |

### API
```python
engine = EvidenceEngine()

# Collect evidence
ev = Evidence(
    source=EvidenceSource.MODEL,
    evidence_type=EvidenceType.QUANTITATIVE,
    value=2.678,
    confidence=1.0,
    provenance=["model_run_2026_10_09", "C-CPP-04"],
    metadata={"model_id": "CANON-002", "equation": "Hargreaves"}
)
engine.collect(ev)

# Validate evidence
result = engine.validate(ev.id)
# result.is_valid = True, result.issues = []

# Convert to Fact for Knowledge Engine
fact = engine.to_fact(ev.id, "ET0 at reference station = 2.68 mm/day")
```

---

## 3. Provenance Tracking

### Traceability Links
Each `Evidence` item tracks:
1. **Source data version** — via metadata
2. **Model version** — via provenance chain
3. **Execution configuration** — via metadata
4. **Computation result** — via value
5. **Test status** — via ValidationResult
6. **Uncertainty** — via confidence + metadata

### Knowledge Engine Integration
```python
# EvidenceEngine.to_fact() bridges Evidence → Knowledge
# DecisionEngine consumes Facts for reasoning
```

---

## 4. Evidence Collection Status

| Evidence ID | Source | Confidence | Verified |
|-------------|--------|------------|----------|
| (5 UUID evidence items from verification) | MODEL | 1.0 | ✅ All validated |

---

## 5. Provenance Chain Verification

**Test**: `engine/tests/test_evidence_chain.py`
- ✅ Input data → Evidence → Fact → Decision chain preserves IDs
- ✅ Every evidence item has non-empty provenance
- ✅ Provenance chain is acyclic
- ✅ Confidence propagates through chain

---

## 6. Persistence Adapter (Planned)

**File**: `engine/ports/evidence_adapter.py`
```python
class EvidenceAdapter(ABC):
    @abstractmethod
    def store_computation_record(self, record: ComputationRecord) -> str:
        pass
    @abstractmethod
    def retrieve_by_trace(self, trace_id: str) -> ComputationRecord:
        pass
```

**Status**: Interface defined, in-memory implementation available. External persistence (PostgreSQL/File) deferred.