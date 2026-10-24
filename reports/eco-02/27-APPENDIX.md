# ECO-02: Appendices

## A: File Inventory Summary
## B: Open Questions
## C: Migration Checklist

---

## Source Evidence
- reports/engine-services/INVENTORY.md
- ECO-01/24-UNKNOWN-AND-CONFLICTS.md
- ECO-01/22-LEGACY-DEPENDENCY-STRATEGY.md

---

## Appendix A: File Inventory Summary

### Repository Structure
```
D:\HyDroMA\
├── engine/                    # Python scientific engine (290 files)
├── services/                  # Microservices (644 files, 73 services)
├── c++/                       # C++ numerical kernels
│   ├── src/                   # 10 source files
│   ├── include/               # 10 header files
│   └── tests/                 # 21 test files
├── ai/                        # AI augmentation (RESEARCH)
├── reports/
│   ├── eco-00/                # Engine service reports
│   │   ├── INVENTORY.md
│   │   ├── DEPENDENCY-MAP.md
│   │   └── SCIENTIFIC-MODEL-REGISTRY.md
│   ├── eco-01/                # Knowledge registry (24 reports)
│   └── eco-02/                # Architecture definition (this work)
│       ├── *.md               # 27 report files
│       ├── adr/               # 14 ADRs
│       ├── contracts/         # 6 contracts
│       └── diagrams/          # Architecture diagrams
└── ECO-02.md                 # Source requirements
```

### File Counts by Category

| Category | Count | Status |
|----------|-------|--------|
| Python engine files | 290 | In scope |
| Python service files | 644 | Needs consolidation |
| C++ source files | 10 | In scope |
| C++ header files | 10 | In scope |
| C++ test files | 21 | Complete |
| ADRs | 14 | Complete |
| Contracts | 6 | Complete |
| Reports | 27 | Complete (this document is #27) |

---

## Appendix B: Open Questions

### Scientific Questions
| QID | Question | Status |
|-----|----------|--------|
| Q-001 | What is the optimal downscaling method for CMIP6 to regional? | UNKNOWN-001 |
| Q-002 | How to validate AI predictions against scientific models? | CONFLICT-011 |
| Q-003 | What are the uncertainty bounds for ensemble climate projections? | GAP-001 |
| Q-004 | How to integrate indigenous flood knowledge into models? | KT-008 integration |

### Engineering Questions
| QID | Question | Status |
|-----|----------|--------|
| Q-005 | Will buffer protocol overhead be acceptable for small arrays? | Performance test needed |
| Q-006 | How to handle version conflicts between model libraries? | Dependency strategy |
| Q-007 | What is the migration path for legacy services? | ECO-LEGACY-001 |

### Governance Questions
| QID | Question | Status |
|-----|----------|--------|
| Q-008 | Who owns the canonical model registry? | To be assigned |
| Q-009 | How to handle conflicting evidence from multiple sources? | Evidence Engine |
| Q-010 | What is the approval process for new scientific models? | Review queue |

---

## Appendix C: Migration Checklist

### Phase 1: Immediate (P0 - Week 1)
- [ ] Create `reports/eco-02/` directory structure
- [ ] Write canonical architecture document (01-CANONICAL-ARCHITECTURE.md)
- [ ] Implement import guards (ADR-010)
- [ ] Block ECO-LEGACY-001 violations in CI/CD
- [ ] Create canonical model registry (CANON-XXX)
- [ ] Classify all 22 models by maturity (ADR-006)

### Phase 2: Short-term (P1 - Weeks 2-4)
- [ ] Consolidate 73 services to 8 bounded contexts (ADR-004)
- [ ] Eliminate duplicate model implementations (ADR-011)
- [ ] Implement UNIFORMAT unit standardization (ADR-005)
- [ ] Create Evidence Engine interface (ADR-008)
- [ ] Establish AI isolation protocol (ADR-003)
- [ ] Write scientific review queue (ADR-012)

### Phase 3: Medium-term (P2 - Month 2-3)
- [ ] Complete Research Gaps Registry (ADR-009)
- [ ] Implement Knowledge Types integration (ADR-013)
- [ ] Classify all technologies (ADR-014)
- [ ] Create all ADRs (14 total)
- [ ] Write all conceptual contracts (6 total)
- [ ] Generate architecture diagrams (15 total)

### Phase 4: Validation (P3 - Month 3)
- [ ] Run all 66 conceptual scenarios
- [ ] Verify all boundary invariants
- [ ] Complete Final Validation report
- [ ] Produce Machine-Readable Summary

---

## Appendix D: Model Status Quick Reference

| Maturity | Status | Count | Action Required |
|----------|--------|-------|-----------------|
| VERIFIED | CORE | 8 | Maintain, optimize |
| SCIENTIFICALLY_SUPPORTED | IMPORTANT | 7 | Improve validation |
| IMPLEMENTATION_VERIFIED | OPTIONAL | 6 | Document limitations |
| CODE_ONLY | RESEARCH | 0 | N/A |
| STUB | LEGACY/REMOVE | 1 | Replace or remove |

---

## Appendix E: Decision Element → Evidence Mapping

| Decision Element | Evidence Sources | Trust Level |
|------------------|-----------------|------------|
| DE-001 (Policy) | Regulatory documents | HIGH |
| DE-002 (Risk) | Model uncertainty metrics | HIGH/MEDIUM |
| DE-003 (Allocation) | Water availability data | HIGH |
| DE-004 (Trade-off) | Multi-model ensemble | MEDIUM |
| DE-005 (Scenario) | Climate scenarios | MEDIUM |
| DE-006 (Weighting) | Stakeholder input | VARIABLE |
| DE-007 (Temporal) | Seasonal data | HIGH |
| DE-008 (Spatial) | GIS data | HIGH |
| DE-009 (Compliance) | Regulatory knowledge | HIGH |
| DE-010 (Economic) | Cost/benefit data | MEDIUM |
| DE-011 (Environmental) | Ecological thresholds | HIGH |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01 all reports, reports/engine-services/INVENTORY.md*
*This appendix completes the 27 report files for ECO-02*