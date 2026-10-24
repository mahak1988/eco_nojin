# ECO-02: Knowledge Registry (Daneshyar)

## 9 Knowledge Types Compatibility

---

## Source Evidence
- ECO-01/15-DANESHYAR-COMPATIBILITY.md
- ECO-01/05-DOMAIN-KNOWLEDGE-REGISTRY.md
- ECO-01/03-ENGINEERING-KNOWLEDGE-REGISTRY.md
- ECO-01/02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md
- ECO-01/01-KNOWLEDGE-INVENTORY.md

---

## 9 Knowledge Types

From ECO-01/15-DANESHYAR-COMPATIBILITY.md:

| Type ID | Knowledge Type | Description | Examples |
|---------|----------------|-------------|----------|
| KT-001 | Scientiﬁc Theory | Peer-reviewed principles | FAO-56, Penman-Monteith |
| KT-002 | Engineering Method | Practical implementation | AquaCrop, SWAT |
| KT-003 | Domain Expertise | Local/specialized knowledge | Iranian crop coefficients |
| KT-004 | Observational Data | Measured/observed data | Weather stations, satellites |
| KT-005 | Empirical Formula | Derived from data | Hargreaves, Makkink |
| KT-006 | Institutional Knowledge | Organizational wisdom | Water authority policies |
| KT-007 | Regulatory Knowledge | Legal/regulatory | Water rights, environmental laws |
| KT-008 | Indigenous Knowledge | Traditional/local | Qanat management, floodplains |
| KT-009 | AI/ML Knowledge | Machine learning patterns | Predictive models, recommendations |

---

## Knowledge Graph Structure

```
Scientiﬁc Theory (KT-001)
    ↓ (informs)
Engineering Method (KT-002)
    ↓ (applied to)
Domain Expertise (KT-003)
    ↓ (uses)
Observational Data (KT-004)
    ↓ (fits)
Empirical Formula (KT-005)
    ↓ (augmented by)
AI/ML Knowledge (KT-009)
```

### Cross-references
- Institutional Knowledge (KT-006) ↔ Decision Engine
- Regulatory Knowledge (KT-007) ↔ Policy evaluation
- Indigenous Knowledge (KT-008) ↔ Local adaptation

---

## Canonical Asset Mapping

| CANON ID | Knowledge Type | Maturity |
|----------|----------------|----------|
| CANON-001 | KT-001 (Scientiﬁc Theory) | VERIFIED |
| CANON-002 | KT-005 (Empirical) | SCIENTIFICALLY_SUPPORTED |
| CANON-003 | KT-005 (Empirical) | SCIENTIFICALLY_SUPPORTED |
| CANON-004 | KT-002 (Engineering) | SCIENTIFICALLY_SUPPORTED |
| CANON-005 | KT-005 (Empirical) | IMPLEMENTATION_VERIFIED |
| CANON-006 | KT-005 (Empirical) | IMPLEMENTATION_VERIFIED |
| CANON-007 | KT-001 (Scientiﬁc Theory) | SCIENTIFICALLY_SUPPORTED |
| CANON-008 | KT-005 (Empirical) | SCIENTIFICALLY_SUPPORTED |
| CANON-009 | KT-002 (Engineering) | VERIFIED |
| CANON-010 | KT-002 (Engineering) | SCIENTIFICALLY_SUPPORTED |
| CANON-011 | KT-002 (Engineering) | SCIENTIFICALLY_SUPPORTED |
| CANON-012 | KT-002 (Engineering) | IMPLEMENTATION_VERIFIED |
| CANON-013 | KT-002 (Engineering) | SCIENTIFICALLY_SUPPORTED |
| CANON-014 | KT-002 (Engineering) | IMPLEMENTATION_VERIFIED |
| CANON-015 | KT-004 (Observational) | IMPLEMENTATION_VERIFIED |
| CANON-016 | KT-001 (Scientiﬁc Theory) | IMPLEMENTATION_VERIFIED |
| CANON-017 | KT-001 (Scientiﬁc Theory) | IMPLEMENTATION_VERIFIED |
| CANON-018 | KT-001 (Scientiﬁc Theory) | VERIFIED |
| CANON-019 | KT-004 (Observational) | VERIFIED |
| CANON-020 | KT-004 (Observational) | VERIFIED |
| CANON-021 | KT-004 (Observational) | VERIFIED |
| CANON-022 | KT-004 (Observational) | VERIFIED |

---

## Epistemic Status Tracking

From ECO-01/08-EQUATION-AND-UNIT-FORENSICS.md:

| Status | Definition | Count |
|--------|------------|-------|
| VERIFIED | Scientifically validated | 8 |
| SCIENTIFICALLY_SUPPORTED | Theory-supported, partial validation | 7 |
| IMPLEMENTATION_VERIFIED | Code matches, not field-validated | 6 |
| CODE_ONLY | Implementation only | 0 |
| STUB | Placeholder | 1 |

---

## Knowledge Integration Points

1. **Daneshyar** (Knowledge) ←→ **Evidence Engine**: Validated knowledge sources
2. **Daneshyar** ←→ **Tasmimyar** (Decision): Policy-relevant knowledge
3. **Daneshyar** ←→ **AI Layer**: Training data only (with evidence tags)
4. **Daneshyar** ←→ **Scientific Engine**: Model selection and parameterization

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/15*