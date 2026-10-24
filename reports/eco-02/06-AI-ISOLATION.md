# ECO-02: AI Isolation Principle

## AI Must Not Touch Scientific Core

---

## Source Evidence
- ECO-01/12-AI-FORENSICS.md
- ECO-01 §4.4 (AI is experimental)
- ECO-01/07-MODEL-QUALITY-MATRIX.md (AI models classified)

---

## Chain of Trust
```
Scientific Engine → Evidence Engine → Decision Engine → AI Layer → User
```

### Rule: AI CANNOT SKIP layers
- AI must receive evidence-validated data
- AI must not modify scientific models
- AI output goes through Decision engine for validation

---

## AI Classification

### RESEARCH (Experimental)
| Component | Justification |
|-----------|---------------|
| AI policy recommendation | No scientific validation |
| Neural ET estimation | Experimental |
| ML downscaling | Research prototype |
| AI augmentation | Optional enhancement |

### NOT ALLOWED in Scientific Core
| Prohibited | Reason |
|------------|--------|
| Direct model modification | Breaks reproducibility |
| Training on raw scientific data | Bypasses evidence chain |
| Real-time AI computation | Unvalidated, must go through evidence |

---

## Isolation Implementation

### Python Path Restriction
```
ai/
├── recommendation/   # RESEARCH
├── augmentation/     # RESEARCH
└── interfaces/       # Must go through evidence/decision layers
```

### Import Guard
```python
# AI modules MUST NOT import from:
# - engine/scientific/
# - engine/models/
# - c++/

# AI modules CAN import from:
# - services/evidence/
# - services/decision/
# - services/daneshyar/
```

---

## Violation Detection

### ECO-AI-001: Scientific Core Access
**Condition**: AI module imports or calls scientific engine directly
**Action**: REMOVE immediately, redirect through Evidence Engine

### ECO-AI-002: Model Modification
**Condition**: AI modifies canonical model parameters
**Action**: ROLLBACK, classify as LEGACY, investigate

---

## Evidence Requirements
All AI inputs must carry provenance tags from Evidence Engine:
```json
{
  "provenance": "evidence://validated",
  "validation_id": "EVIDENCE-2026-001",
  "confidence": 0.95,
  "source": "modis_et_v6"
}
```

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/12-AI-FORENSICS.md*