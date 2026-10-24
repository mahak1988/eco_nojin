# Final Report — Stage 11: Evidence-Consistency Test Analysis

## A. Three Tests Identified (all in engine/tests/test_machine_evidence_consistency.py)

| # | Test | HEAD line | Working Tree line |
|---|------|-----------|-------------------|
| 1 | test_no_validated_claim_without_external_anchor | 104 | 104 |
| 2 | test_known_violations_shrink_over_time | 101 | 123 |
| 3 | test_corpus_external_anchors_are_reported_distinctly | 191 | 191 |

**Conclusion: There are exactly THREE tests of this type — no fourth test exists.** I confirmed this by checking the file content and running all tests with `-k evidence`.

---

## B. HEAD vs Working Tree Test Outcomes

### Working Tree State (current):
| Test | Result |
|------|--------|
| test_no_validated_claim_without_external_anchor | PASS |
| test_known_violations_shrink_over_time | PASS |
| test_corpus_external_anchors_are_reported_distinctly | FAIL (assert 9 == 14) |

### HEAD State (simulated via git stash):
| Test | Result | Failure message |
|------|--------|-----------------|
| test_no_validated_claim_without_external_anchor | FAIL | Extra unanchored: CANON-002, CANON-011_RAD, ROTGHC_TEMP_FACTOR, RUSLE_LS, SOIL_SALINITY_CLASSIFY |
| test_known_violations_shrink_over_time | PASS | (stale set empty) |
| test_corpus_external_anchors_are_reported_distinctly | PASS | (assert 9 == 9) |

---

## C. CANON-005 Mapping Status — Resolved

**Working Tree:** `CANON-005 → THEIS_DRAWDOWN_USGS` mapping IS present in `EXTERNALLY_ANCHORED_MODELS`.
**HEAD:** No mapping for CANON-005 existed (only CANON-001→ENO_ET0_FAO56_001 and CANON-004→SCS_CN_RUNOFF).

This is the **primary working-tree change** to the test file: the author added 6 new mappings
(including CANON-005→THEIS_DRAWDOWN_USGS) and removed CANON-005 from KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR.

---

## D. Key Test-Logic Defects Identified

### Defect 1: CANON-005 validation_status card derivation changes between HEAD and working tree

**HEAD card (line 91) validation_status field value:**
```
**VALIDATED_METHOD_CONFORMANCE** — ... No *published* drawdown value is stored anywhere
in this repository, so there is nothing to compare against externally; the card's former
"matches reference case" wording claimed exactly that and has been removed.
```

The `_VALIDATION_RULES` regex `\b(?:validated|benchmarked|matches)\b` matches the word
"matches" in this field value → `_classify()` returns `ModelStatus.VALIDATED`.

**Working tree card (line 91) validation_status field value:**
```
**VALIDATED_METHOD_CONFORMANCE** — the implementation reproduces the Theis (1935) closed form
to machine precision against an independent `scipy.special.expi` evaluation (internal
THEIS_REFERENCE, 0.3062 m). A genuine **published** external anchor now exists and is
registered: the USGS ... (s = 1.40636669 m ...) ... The model-card label is kept conservative
by the P0-2 card guard; the registry-level external anchoring is carried by that register row.
```

The working tree card **deliberately removed** the phrase "matches reference case" from
the validation_status field. No standalone "validated", "benchmarked", or "matches" word
appears in the working tree field value → `_classify()` returns `ModelStatus.UNVALIDATED`.

This means:
- In HEAD state: CANON-005 IS in `_validated_models()` (13 models total)
- In working tree: CANON-005 is NOT in `_validated_models()` (validation_status="unvalidated")

### Defect 2: test_known_violations_shrink_over_time relies on KNOWN being a superset of actual stale models

The test logic is:
```python
stale = KNOWN - unanchored  # These are in KNOWN but NOT in unanchored (should be 0)
assert not stale
```

In working tree: KNOWN has 10 entries (CANON-005 removed), unanchored has 10 matching entries.
So `stale = {}` → PASS. But this only works because:
1. CANON-005 was manually removed from KNOWN
2. CANON-005 was manually removed from unanchored (via adding the mapping + card edit)

This is circular reasoning — the test author manually fixed both sides to make the set difference empty,
rather than the test independently detecting the issue.

### Defect 3: test_no_validated_claim_without_external_anchor hardcodes KNOWN instead of detecting

The test compares `unanchored - KNOWN` against `KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR`:
- If a model is validated + unanchored + NOT in KNOWN → it appears as an "extra" item
- This is what happened in HEAD: 5 models (CANON-002, CANON-011_RAD, ROTGHC_TEMP_FACTOR,
  RUSLE_LS, SOIL_SALINITY_CLASSIFY) were validated in working tree cards but had no mapping
  and were not in KNOWN → test failed

These models are validated in the **working tree** because their cards were updated by
concurrent agent work (e.g., CANON-002 card updated to "VALIDATED_METHOD — validated against
the published FAO-56 equations"). But in HEAD, these cards do NOT derive VALIDATED.

### Defect 4: test_corpus_external_anchors_are_reported_distinctly asserts a hardcoded count of 14

The test asserts `len(external) == 14`, but the working tree register only has 9
VALIDATED_EXTERNAL entries. To reach 14, the test author must have added 5 new
VALIDATED_EXTERNAL rows to the register (including SAXTON_RAWLS_2006_AWC which is only
METHOD_CONFORMANCE, not external). 

This test conflates registry row count with the actual evidence-class distinction —
it doesn't verify that the 14 models are externally validated (VALIDATED_EXTERNAL), only
that there are 14 total. The 5 added rows are a mix of VALIDATED_EXTERNAL and
VALIDATED_METHOD_CONFORMANCE.

---

## E. The Two-Layer Validation Distinction

The codebase has TWO distinct validation-checking mechanisms that are NOT reconciled:

1. **Registry derivation** (`_classify()` with `_VALIDATION_RULES`):
   - Input: `validation_status` field value from model card
   - Regex: `\bvalidated\b|\bbenchmarked\b|\bmatches\b` (positive) vs
     `not validated`, `cannot validate`, `not benchmarked`, `not applicable`, `\bn/a\b` (negative)
   - Output: `ModelStatus.VALIDATED` or `UNVALIDATED`
   - For CANON-005: HEAD→matches→VALIDATED, WT→no match→UNVALIDATED

2. **POSITIVE_CLAIM regex** (`test_validation_records.py:94`):
   - Input: Full card text (not just validation_status field)
   - Regex: `\b(?:validated|benchmarked|matches)\b`
   - Used only in `test_the_status_comes_from_a_card_row_not_a_hand_edit`
   - NOT parametrized over CANON-005 (which is not in CLUSTER_MODEL_IDS)

These two mechanisms can give different results for the same card.

---

## F. CANON-005: The Complete Picture

| Question | Answer |
|----------|--------|
| Is CANON-005 in the working tree register (FORMULA-EVIDENCE-REGISTER.json)? | Yes — maps to THEIS_DRAWDOWN_USGS |
| What is CANON-005's validation_status field value in HEAD? | VALIDATED_METHOD_CONFORMANCE (contains "matches reference case") |
| What is CANON-005's validation_status field value in working tree? | VALIDATED_METHOD_CONFORMANCE (no standalone "matches"/"validated" word) |
| Does the working tree card have an external anchor? | Yes — USGS worked example, 1.40636669 m, reproduced to 3.5e-9 m |
| Does CANON-005 derive as VALIDATED from the registry (_classify)? | HEAD: YES; Working tree: NO |
| Is CANON-005 in `_validated_models()`? | HEAD: YES; Working tree: NO |
| Is CANON-005 in KNOWN? | HEAD: YES; Working tree: NO (manually removed) |
| Is CANON-005 in unanchored? | HEAD: YES (validated+no mapping); Working tree: NO (not validated+has mapping) |
| Was there a "deleted register" issue? | Yes — CANON-005's FORMULA-EVIDENCE-REGISTER.json entry was
  deleted in the working tree at session start, causing the registry to return
  UNVALIDATED. It was restored during Stage 10, making CANON-005 a VALIDATED_EXTERNAL. |

---

## G. Summary of What Was Done So Far (Session)

1. Located the three evidence-consistency tests in test_machine_evidence_consistency.py
2. Verified there are no other tests of this type (confirmed by -k evidence filter)
3. Confirmed register status: present in HEAD, restored in working tree
4. Extracted CANON-005 card field values from both HEAD and working tree
5. Verified _VALIDATION_RULES regex behavior on CANON-005's card text
6. Confirmed CANON-005 is NOT in _validated_models() in working tree (but IS in HEAD)
7. Analyzed the two-layer validation system (registry derivation vs POSITIVE_CLAIM)
8. Identified 4 test-logic defects
9. Ran HEAD simulation (git stash) to collect actual test outcomes
10. Restored working tree via git stash pop
