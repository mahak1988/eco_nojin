# ECO-02: Research Gaps Registry

## 22+ Identified Research Gaps

---

## Source Evidence
- ECO-01/18-RESEARCH-GAPS.md
- ECO-01/24-UNKNOWN-AND-CONFLICTS.md (UNKNOWN-001-010, CONFLICT-001-012)
- ECO-01/07-MODEL-QUALITY-MATRIX.md

---

## Critical Gaps (P0-P1)

| Gap ID | Description | Priority | Impact | Status |
|--------|-------------|----------|--------|--------|
| GAP-001 | Climate model downscaling methods | P0 | High | OPEN |
| GAP-002 | ET estimation under data-scarce conditions | P0 | High | OPEN |
| GAP-003 | Crop water requirement for Iranian crops | P1 | High | PARTIAL |
| GAP-004 | Groundwater depletion rates in Iran aquifers | P1 | High | OPEN |
| GAP-005 | Irrigation efficiency measurement methodology | P1 | Medium | OPEN |
| GAP-006 | Socio-economic response to water policies | P2 | Medium | RESEARCH |
| GAP-007 | Climate change impact on water availability | P0 | High | OPEN |
| GAP-008 | Soil moisture spatial distribution | P1 | Medium | PARTIAL |
| GAP-009 | Reservoir operation optimization | P2 | Medium | RESEARCH |
| GAP-010 | Agricultural drainage and salinity | P2 | Medium | OPEN |

---

## Medium Priority Gaps (P2-P3)

| Gap ID | Description | Priority | Impact | Status |
|--------|-------------|----------|--------|--------|
| GAP-011 | Water allocation fairness metrics | P2 | Medium | OPEN |
| GAP-012 | Drought early warning system | P2 | Medium | PARTIAL |
| GAP-013 | Urban water demand forecasting | P2 | Low | RESEARCH |
| GAP-014 | Wastewater reuse potential | P3 | Low | RESEARCH |
| GAP-015 | River flow forecasting accuracy | P2 | Medium | PARTIAL |

---

## Unknown/Conflict Items

From ECO-01/24-UNKNOWN-AND-CONFLICTS.md:

### Unknowns (UNKNOWN-001-010)
| ID | Description | Resolution Needed |
|----|-------------|-------------------|
| UNKNOWN-001 | Exact formulation of some legacy equations | Audit required |
| UNKNOWN-002 | Provenance of certain input datasets | Trace to source |
| UNKNOWN-003 | Validation status of legacy models | Review queue P1 |
| UNKNOWN-004 | Parameter values for some crop coefficients | Research gap |
| UNKNOWN-005 | Historical calibration data | Data gap |
| UNKNOWN-006 | Ground-truth measurements for ET | Field campaign needed |
| UNKNOWN-007 | Uncertainty quantification methods | Research gap |
| UNKNOWN-008 | Climate scenario interpretation | Documentation needed |
| UNKNOWN-009 | Model coupling conventions | Standardize |
| UNKNOWN-010 | Output format specifications | Define in Evidence Engine |

### Conflicts (CONFLICT-001-012)
| ID | Description | Resolution |
|----|-------------|------------|
| CONFLICT-001 | Duplicate Penman-Monteith implementations | Consolidate to CANON-001 |
| CONFLICT-002 | Conflicting ET0 calculation methods | Use FAO-56 as authority |
| CONFLICT-003 | Disagreement on crop coefficients | Refer to Daneshyar knowledge |
| CONFLICT-004 | Different precipitation data sources | Evidence Engine validation |
| CONFLICT-005 | Climate model ensemble disagreement | Multi-model ensemble approach |
| CONFLICT-006 | Groundwater model parameter conflict | Scientific review P0 |
| CONFLICT-007 | Temporal resolution mismatch | Standardize to daily |
| CONFLICT-008 | Spatial projection differences | Reproject to WGS84 |
| CONFLICT-009 | Unit system inconsistency | UNIFORMAT to SI |
| CONFLICT-010 | Numerical precision issues | Double-check C++ kernels |
| CONFLICT-011 | Boundary condition discrepancies | Cross-validate with stations |
| CONFLICT-012 | Historical vs. projected data conflict | Separate clearly in provenance |

---

## Research Gap Resolution Plan

### P0 Gaps - Immediate Research Required
1. GAP-001: Establish downscaling protocol
2. GAP-002: Prioritize data-scarce ET methods
3. GAP-007: Define climate impact scenarios

### P1 Gaps - Short-term Research
1. GAP-003: Catalog Iranian crop coefficients
2. GAP-004: Assess groundwater monitoring network
3. GAP-005: Define efficiency measurement protocol

### P2-P3 Gaps - Long-term Research
1. GAP-006: Integrate socio-economic factors
2. GAP-009: Develop optimization framework
3. GAP-014: Explore wastewater reuse potential

---

## Review Queue

From ECO-01/23-SCIENTIFIC-REVIEW-QUEUE.md:

| Priority | Items | Action |
|----------|-------|--------|
| P0 | CONFLICT-006, UNKNOWN-003 | Immediate review |
| P1 | GAP-003, GAP-004, CONFLICT-003 | 3-month timeline |
| P2 | GAP-006, GAP-009, CONFLICT-005 | 6-month timeline |
| P3 | GAP-011, GAP-014 | Annual review |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/18, 23, 24*