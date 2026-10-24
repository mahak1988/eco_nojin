# ECO-03.1: Open Questions — Report 16

## Open questions categorized by ECO-04 blocking status

---

## 1. Blocking ECO-04 Start

| ID | Question | Answer | Rationale |
|----|----------|--------|-----------|
| Q1 | How many real blockers remain? | 3 (B-005, B-006, B-011) | See blocker reconciliation |
| Q2 | How many false positives? | 1 (B-004) | Temperature was already consistent |
| Q3 | How many fixed and verified? | 3 (B-001, B-002-imp, B-003) | Import guard confirms |
| Q4 | Is engine→database still present? | YES | 7 violations found |
| Q5 | Is engine→services still present? | NO | 0 violations (FIXED) |
| Q6 | Any circular dependency? | NO | Import guard: 0 violations |
| Q7 | Are import guards implemented? | PARTIAL | Tool exists, not in CI |
| Q8 | How many tests run? | 0 | Environment missing deps |
| Q9 | Test pass/fail breakdown? | 0 passed, 0 failed | Tests cannot collect |
| Q10 | Is pyproject.toml valid? | YES | TOML parses; has metadata |
| Q11 | Actual service count? | 38 domain services | See report 03 |
| Q12 | Actual bounded contexts? | 8 | Verified against source |
| Q13 | Which models are verified? | 11 domain models | See report 05 |
| Q14 | Which are implementation verified only | 5 models | Implementation ≠ scientific |
| Q15 | Which need scientific review? | 5 models | Not ECO-04 blocking |
| Q16 | AI boundary enforced in source? | YES (no imports) | Import guard confirms |
| Q17 | Can ECO-04 start without architecture changes? | YES (with env setup) | Only B-011 blocks |

---

## 2. Questions Requiring ECO-04 Resolution

| ID | Question | Owner | Target Sprint |
|----|----------|-------|--------------|
| Q-A | How to resolve engine→database? | Architecture team | ECO-04.1 |
| Q-B | Where should Evidence Engine live? | Architecture team | ECO-04.3 |
| Q-C | How to implement uncertainty? | Scientific team | ECO-04.6 |
| Q-D | How to implement epistemic types? | Knowledge team | ECO-04.5 |
| Q-E | What is the canonical persistence port interface? | Architecture team | ECO-04.1 |
| Q-F | How should services use Engine Gateway? | Platform team | ECO-04.9 |

---

## 3. Questions Outside ECO-03.1 Scope

| ID | Question | Scope |
|----|----------|-------|
| Q-1 | Should we use FastAPI or something else for the API? | ECO-04 (frontend/API) |
| Q-2 | What is the database schema? | ECO-04 (database) |
| Q-3 | How to optimize C++ performance? | ECO-04 (optimization) |
| Q-4 | What CMS to use? | ECO-04 (admin) |
| Q-5 | How to design the wallet? | ECO-04 (blockchain) |

---

## 4. Scientific Review Questions

| ID | Question | Model | Reviewer |
|----|----------|-------|----------|
| SQ-1 | Theis series convergence proof? | CANON-005 | Hydrogeologist |
| SQ-2 | Climate data assimilation weights? | CANON-018 | Climatologist |
| SQ-3 | Hargreaves validation for Iran? | CANON-002 | Meteorologist |
| SQ-4 | RUSLE LS factor methodology? | CANON-007 | Erosion specialist |
| SQ-5 | Solar radiation atmospheric correction? | CANON-011 | Solar expert |

---

*Report generated: 2026-10-08*
*Status: All questions categorized by ECO-04 blocking impact*