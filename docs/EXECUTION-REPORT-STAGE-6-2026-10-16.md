# Stage 6 Execution Report — Scientific Evidence Chain

**Phase:** P10 — Engine maturity & provenance (W2)  
**Date:** 2026-10-16  
**Base commit:** `2cb974e`  
**Status:** PARTIALLY_COMPLETE  

---

## Summary

Audited the scientific evidence chain for the HyDroMA model registry: the linkage from each
model's `validation_status` claim through its card file, the machine-readable
`FORMULA-EVIDENCE-REGISTER.json`, on-disk reference data, and validation test cases.

Found **7 broken links** across three categories:

| Category | Count | Details |
|---|---|---|
| Register file deleted from working tree | 1 file | `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` — present in HEAD, deleted in working tree |
| Register content drift (9 → 14 expected) | 5 anchors | Reference data + tests vendored (2026-10-15/16) but register JSON never updated |
| Models claiming "validated" with no external anchor | 10 models | `KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR` set; 5/6 blocking tests ERROR on FileNotFoundError |

---

## Files

### Created

| File | Purpose |
|---|---|
| `docs/audits/STAGE-6-SCIENTIFIC-EVIDENCE-CHAIN-AUDIT-2026-10-16.md` | Full audit findings — evidence chain per model, register content analysis, HYRUE/EWSI deep dive |
| `docs/EXECUTION-REPORT-STAGE-6-2026-10-16.md` | This file |

### Read (no changes)

| File | Lines examined |
|---|---|
| `engine/tests/test_machine_evidence_consistency.py` | 1–228 (full) |
| `engine/hydroma/models/hyrue.py` | 1–304 (full) |
| `engine/hydroma/models/ewsi.py` | (from earlier sweep) |
| `engine/models/registry.py` | Lines 1–200, 820–1100, 1600–1700 (gateway dispatch + model specs) |
| `engine/models/maturity.py` | (from earlier sweep) |
| `indicators/*.yaml` (5 files + `_TEMPLATE.yaml`) | (from earlier sweep) |
| `tests/test_cases/*.yaml` (16 files) | hyrue.yaml, ewsi.yaml — parsed test cases |
| `tests/reference_data/*.csv` (12 files) | Verified contents of all reference data |
| `tests/test_theis_usgs_external.py` | Verified USGS reproduction assertion |

### Existing (no changes needed)

| File | Status |
|---|---|
| `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` | **Deleted from working tree** (exists in HEAD, 41 entries, 9 VALIDATED_EXTERNAL) |
| `FORMULA-EVIDENCE-REGISTER.json` (root) | Not in HEAD; existed in history (commits a22737a, 695de04) |
| `engine/validation/` (11 .md records) | Exist; only for carded models |

---

## Decisions Taken

1. **Register restoration is required first.** No evidence-chain analysis can proceed until
   `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` is restored to the working tree.
   The file exists intact in git HEAD.

2. **CANON-005 is under-claimed, not over-claimed.** Its card text
   `"VALIDATED_METHOD_CONFORMANCE"` doesn't match the `\bvalidated\b` regex, so the
   registry parses it as `unvalidated`. Yet CANON-005 has genuine USGS external
   reference data on disk (`tests/reference_data/theis_usgs_worked_example.csv`,
   s = 1.40636669 m reproduced to 3.5e-9 m). The anchor mapping exists in
   `EXTERNALLY_ANCHORED_MODELS` but the register entry `THEIS_DRAWDOWN_USGS` is missing.

3. **HYRUE `days` parameter is a multiplier, not a seasonal integration.** Confirmed by
   reading `hyrue.py:273` (`total_biomass = daily_biomass * days`) and the docstring
   (lines 240–249) which explicitly warns: "A call with days=120 returns 120 times the
   value of the same call with days=1."

---

## Decisions Open (require approver)

| Decision | D-Ref | Awaiting |
|---|---|---|
| Whether CANON-005's card text should be changed to include standalone "validated" so the external anchor is wired correctly | D-07 | Approver |
| Whether CANON-016/017 (C++ kernels) parity against Python should count as "validated" or be downgraded to "method conformance" | D-13 | Approver |
| Whether the `days` multiplier in HYRUE should be deprecated in favor of proper seasonal integration | D-09 | Approver |

---

## Commands & Real Outputs

### Test execution

```
$ pytest engine/tests/test_machine_evidence_consistency.py -v --tb=short

engine/tests/test_machine_evidence_consistency.py::test_no_validated_claim_without_external_anchor FAILED
engine/tests/test_machine_evidence_consistency.py::test_known_violations_shrink_over_time      FAILED
engine/tests/test_machine_evidence_consistency.py::test_maturity_levels_are_resolved           PASSED
engine/tests/test_machine_evidence_consistency.py::test_every_indicator_has_an_evidence_record  FAILED
engine/tests/test_machine_evidence_consistency.py::test_evidence_register_entries_are_complete  FAILED
engine/tests/test_machine_evidence_consistency.py::test_corpus_external_anchors_are_reported_distinctly FAILED

5 failed, 1 passed, 1 warning in 28.69s
```

All 5 failures are `FileNotFoundError: reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`.

### Registry counts

```
Total registered models: 72
Models WITH cards: 32
Models WITHOUT cards: 40
```

The task brief stated "27 models without scientific cards" — verified count is 40 (includes
infrastructure/utility models: ECON_*, MRV_*, SIM_*, etc.).

### Committed register content

```
Total entries: 41
VALIDATED_EXTERNAL: 9
VALIDATED_METHOD_CONFORMANCE: 8
PARTIAL: 5
REGRESSION_ANCHOR_STABLE: 2
UNVALIDATED: 17
```

The test asserts `len(external) == 14`. Gap: 5 missing entries.

---

## Remaining Debt

| Item | Description | Proposed Phase |
|---|---|---|
| D-23 | Register JSON deleted from working tree | P10 next sprint |
| D-24 | 5 VALIDATED_EXTERNAL entries missing from register JSON | P10 next sprint |
| D-25 | 10 models over-claim "validated" without external evidence | W6 (retire from KNOWN set) |
| D-26 | CANON-005 under-claimed (has evidence but not registered) | P10 next sprint |
| D-27 | 40 models without cards (36 with zero test coverage) | P10 next sprint |
| D-28 | HYRUE `days` multiplier not a true seasonal integration | D-09 (awaiting decision) |
| D-29 | EWSI VPD ramp flatlines at 4.0 kPa (60% of declared range) | P10 next sprint |
| D-30 | `test_sodicity_classifier.py` missing (reference data exists) | P10 next sprint |

---

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| The 10 over-claim models may be used in production as "validated" | High | Tests currently ERROR (not FAIL cleanly) — once register restored, the test will catch new violations |
| HYRUE seasonal yield estimates may be inflated 2.5× | Medium | Fixed in Stage 18: `compute` now supports seasonal mode (array `par` input sums daily biomass) alongside scalar mode (days multiplier, for constant-conditions estimates only). Docstring updated with explicit warning. Gateway dispatch uses `compute_checked` for input validation (Stage 19B). Audit walkthrough in `STAGE-6-SCIENTIFIC-EVIDENCE-CHAIN-AUDIT-2026-10-16.md:319-332` corrected: YAML validation cases use generic HYRUE params (eps=2.5, t_opt=25), not wheat params. |
| EWSI water-stress values are flat (max stress) for VPD > 4 kPa | Medium | Affects HYRUE crop yields in dry seasons; register already documents the limitation |
| 36 of 40 no-card models have zero test coverage | High | All default to `unverified/unvalidated` in registry; but no test enforces this |
| `reports/` directory deletion also lost all historical P0–P15 phase reports | Informational | Documents were re-based to `docs/specs/` and `docs/audits/`; see AGENTS.md §Repository layout |

---

## Integration Needs

| Need | Owner | Status |
|---|---|---|
| Restore `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` from HEAD | Integrator | Pending |
| Add 5 missing entries to register JSON | P10 agent | Pending (blocked on restore) |
| Create cards for 40 no-card models (at minimum stubs) | P10 agent | Pending |
| Add `test_sodicity_classifier.py` | P10 agent | Pending |
| Decide CANON-005 card-text fix (D-07) | Approver | Pending |

---

## Reproduction Steps

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
$env:SECRET_KEY = "test-secret-key"
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest engine/tests/test_machine_evidence_consistency.py -v --tb=short
```

To verify the register content:
```powershell
git show HEAD:reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json
```

---

## Per-Criterion Status

| Criterion | Status | Evidence |
|---|---|---|
| Evidence tests can run | BLOCKED | Register file missing from working tree |
| Evidence tests can pass | BLOCKED | Register has 9/14 required external anchors |
| Known violations set is accurate | PASS | 10 models verified against cards + register + on-disk evidence |
| 40 no-card models verified | PASS | Count confirmed against `get_registry().list_ids()` × 72 |
| HYRUE `days` behavior documented | PASS | `hyrue.py:240-249` docstring explicitly warns about multiplier vs integration |
| EWSI VPD ramp documented | PASS | Register entry notes "VPD ramp saturates at 4 kPa"; `ewsi.py` code verified |
| CANON-005 USGS anchor on disk | PASS | `tests/reference_data/theis_usgs_worked_example.csv` + `tests/test_theis_usgs_external.py` confirmed |
| 10 over-claim models traced to evidence | PASS | Per-model evidence class mapped in audit report §4 |
| Reference data for 5 new anchors on disk | PASS | 5 CSV files verified in `tests/reference_data/` |

**Final status: PARTIALLY_COMPLETE** — audit complete; remediation blocked on register file restoration.
