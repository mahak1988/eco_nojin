# ECO-02: Architecture Decision Log

## Summary of All Architecture Decisions

---

## Source Evidence
- Derived from ECO-01 forensic analysis
- All 14 ADRs in `adr/` directory

---

## ADR Summary Table

| ADR | Title | Status | Tags |
|-----|-------|--------|------|
| ADR-001 | Canonical 7-Layer Architecture | Accepted | architecture, layers, boundaries |
| ADR-002 | Python/C++ Boundary Protocol | Accepted | cpp, python, performance, boundary |
| ADR-003 | AI Isolation Principle | Accepted | ai, isolation, evidence-engine, security |
| ADR-004 | Service Consolidation to Bounded Contexts | Accepted | services, consolidation, bounded-contexts |
| ADR-005 | UNIFORMAT Unit Standardization Protocol | Accepted | units, standardization, si |
| ADR-006 | Scientific Model Maturity Scale | Accepted | maturity, model-quality, validation |
| ADR-007 | Canonical Asset Registry | Accepted | canonical-assets, registry, deduplication |
| ADR-008 | Evidence Chain Architecture | Accepted | evidence-chain, provenance, audit |
| ADR-009 | Research Gaps Registry | Accepted | research-gaps, priorities, roadmap |
| ADR-010 | Import Guard Protocol (ECO-LEGACY-001) | Accepted | import-guard, legacy, boundary, ci-cd |
| ADR-011 | Duplication Elimination Protocol | Accepted | duplication, consolidation, maintainability |
| ADR-012 | Scientific Review Queue | Accepted | scientific-review, validation, peer-review |
| ADR-013 | Knowledge Types Integration (Daneshyar) | Accepted | knowledge-types, daneshyar, trust |
| ADR-014 | Technology Classification Framework | Accepted | technology-strategy, classification, investment |

---

## Decision Chronology

1. **ADR-001** → Establishes overall architecture framework
2. **ADR-002** → Defines C++/Python boundary (supports Layer 2-3)
3. **ADR-005** → Defines unit standardization (supports boundary)
4. **ADR-010** → Prevents legacy violations (enforces boundaries)
5. **ADR-006** → Classifies model maturity
6. **ADR-007** → Establishes canonical asset registry
7. **ADR-004** → Consolidates services
8. **ADR-011** → Eliminates duplication
9. **ADR-008** → Defines evidence chain
10. **ADR-003** → Isolates AI
11. **ADR-013** → Integrates knowledge types
12. **ADR-012** → Establishes review process
13. **ADR-009** → Tracks research gaps
14. **ADR-014** → Classifies all technologies

---

## Key Constraints Enforced

1. **Scientific core stability**: Models cannot be modified by AI
2. **Boundary integrity**: No engine/→services/ imports
3. **Reproducibility**: All computations carry provenance tags
4. **Trust-awareness**: Evidence trust levels drive decisions
5. **Performance**: C++ kernels handle numerics, Python orchestrates

---

## Related Standards

| Standard | Reference |
|----------|-----------|
| FAO-56 | Agricultural Water Management |
| IEEE 754 | Floating-point arithmetic |
| ISO 19115 | Geographic metadata |
| WGS84 | Spatial reference system |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01 all reports*
