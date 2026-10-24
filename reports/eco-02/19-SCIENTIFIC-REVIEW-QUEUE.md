# ECO-02: Scientific Review Queue

## P0-P3 Review Priorities with Evidence Status

---

## Source Evidence
- ECO-01/23-SCIENTIFIC-REVIEW-QUEUE.md
- ECO-01/07-MODEL-QUALITY-MATRIX.md
- ECO-01/24-UNKNOWN-AND-CONFLICTS.md

---

## Review Queue by Priority

### P0 - Critical (Immediate Review Required)

| Item ID | Subject | Status | Due Date | Reviewer |
|---------|---------|--------|----------|----------|
| CONFLICT-006 | Groundwater model parameter conflict | OPEN | ASAP | Senior hydrologist |
| UNKNOWN-003 | Validation status of legacy models | OPEN | ASAP | Science team |
| GAP-001 | Climate model downscaling methods | OPEN | 2 weeks | Climate scientist |
| GAP-007 | Climate change impact on water availability | OPEN | 1 month | Climate scientist |

### P1 - High (Monthly Review)

| Item ID | Subject | Status | Due Date | Reviewer |
|---------|---------|--------|----------|----------|
| CONFLICT-003 | Disagreement on crop coefficients | IN_REVIEW | 2 weeks | Agronomist |
| UNKNOWN-001 | Exact formulation of legacy equations | OPEN | 1 month | Numerical lead |
| UNKNOWN-004 | Parameter values for crop coefficients | OPEN | 1 month | Agronomist |
| GAP-003 | Iranian crop coefficients | PARTIAL | 3 months | Local agronomist |
| GAP-004 | Groundwater depletion rates | OPEN | 3 months | Hydrologist |
| GAP-005 | Irrigation efficiency measurement | OPEN | 3 months | Agronomist |
| GAP-008 | Soil moisture spatial distribution | PARTIAL | 3 months | Soil scientist |
| CONFLICT-010 | Numerical precision issues | IN_REVIEW | 1 month | C++ lead |

### P2 - Medium (Quarterly Review)

| Item ID | Subject | Status | Due Date | Reviewer |
|---------|---------|--------|----------|----------|
| CONFLICT-005 | Climate model ensemble disagreement | OPEN | 2 months | Climate scientist |
| CONFLICT-011 | Boundary condition discrepancies | OPEN | 2 months | Hydrologist |
| CONFLICT-012 | Historical vs. projected data conflict | OPEN | 2 months | Climate scientist |
| GAP-006 | Socio-economic response to water policies | RESEARCH | 6 months | Social scientist |
| GAP-009 | Reservoir operation optimization | RESEARCH | 6 months | Operations lead |
| GAP-011 | Water allocation fairness metrics | OPEN | 3 months | Policy lead |
| GAP-012 | Drought early warning system | PARTIAL | 3 months | Meteorologist |
| GAP-005 | Precipitation data sources conflict | IN_REVIEW | 2 months | Meteorologist |

### P3 - Low (Annual Review)

| Item ID | Subject | Status | Due Date | Reviewer |
|---------|---------|--------|----------|----------|
| GAP-013 | Urban water demand forecasting | RESEARCH | 6 months | Urban planner |
| GAP-014 | Wastewater reuse potential | RESEARCH | 6 months | Environmental engineer |

---

## Review Process

### Step 1: Evidence Collection
- Gather all relevant evidence
- Tag with provenance chain
- Assign initial trust level

### Step 2: Peer Review
- At least 2 reviewers per item
- Review checklist:
  - [ ] Scientific validity
  - [ ] Implementation accuracy
  - [ ] Unit consistency
  - [ ] Provenance traceability

### Step 3: Decision
- APPROVE: Mark as VERIFIED or SCIENTIFICALLY_SUPPORTED
- REQUEST_CHANGES: Address concerns, re-review
- REJECT: Remove or downgrade model

### Step 4: Documentation
- Update model registry
- Update evidence tags
- Notify Evidence Engine

---

## Model Status Changes

| Model | Current Status | Review Item | Recommended Status |
|-------|----------------|-------------|-------------------|
| AUDIT-MODEL-016 (RegCM) | IMPLEMENTATION_VERIFIED | CONFLICT-005 | SCIENTIFICALLY_SUPPORTED |
| AUDIT-MODEL-017 (HadGEM2) | IMPLEMENTATION_VERIFIED | CONFLICT-005 | SCIENTIFICALLY_SUPPORTED |
| AUDIT-MODEL-014 (WRF) | IMPLEMENTATION_VERIFIED | CONFLICT-005 | SCIENTIFICALLY_SUPPORTED |
| AUDIT-MODEL-022 (Sentinel-2) | VERIFIED | CONFLICT-011 | VERIFIED (no change) |

---

## Review Metrics

| Metric | Target | Current |
|--------|--------|---------|
| P0 resolution rate | 100% within 1 week | 50% |
| P1 resolution rate | 100% within 1 month | 75% |
| P2 resolution rate | 100% within 3 months | 60% |
| P3 resolution rate | 100% within 6 months | 50% |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/23*