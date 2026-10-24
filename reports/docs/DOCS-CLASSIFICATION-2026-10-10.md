# R-6 — Documentation Classification (`docs/architecture` + `docs/databases`)

**Date:** 2026-10-10
**Origin:** `reports/security/SECURITY-FINDINGS-2026-10-10.md` — F-4 / R-6
("183 architectural documents with no test … classify them (audit artefact vs.
documentation) and either move the two audit artefacts under `reports/` or mark
the directory informative in the master directive").
**Scope:** `docs/architecture/**`, `docs/databases/**` only. No source, `engine/`,
`services/`, `tools/check_security.py` or `pyproject.toml` touched. Nothing
deleted. Two file moves permitted (only if unambiguously artefacts).

---

## Summary (evidence first)

**The R-6 premise is not reproducible in the current tree.** The finding states
`docs/databases/` has 2 files and `docs/architecture/` has 181 files and that
they "are tracked". They are **not present** in the working tree and have
**never existed** in any commit on any branch:

| Evidence command | Result |
|---|---|
| `Get-ChildItem docs -Force` | only `docs/adr/` (one file `014-import-guard-policy.md`) |
| `git ls-tree -r HEAD -- docs/` | one path: `docs/adr/014-import-guard-policy.md` |
| `git log --all --oneline -- 'docs/architecture/*' 'docs/databases/*'` | empty (never committed) |
| `git branch -a` / `git worktree list` / `git stash list` | only `master` @ `d6fac05`; worktree at same commit; no hidden history |
| `git check-ignore docs/architecture|docs/databases` | not ignored (so would be tracked if present — they are simply absent) |
| whole-tree scan for dirs named `architecture`/`databases` | only top-level `architecture/` (2 YAML files) |

`docs/architecture/` (181) and `docs/databases/` (2) therefore cannot be
classified 1:1 — there are **0** files to classify under those paths. No file is
moved and nothing is deleted.

The F-4 note that the two artefacts "were both included in the final machine
report" refers to the **security session's own outputs**, which already live
under `reports/` (see "The two audit artefacts" below) — separate from the
non-existent doc directories.

---

## What actually exists in the docs / architecture space (classified)

| File | Class | Reason | Recommended action |
|---|---|---|---|
| `docs/adr/014-import-guard-policy.md` | (b) Architecture documentation — **stays** | The only tracked doc under `docs/`. ADR-014 for the externalised import-guard policy (`tools/import_guard_policy.json`); recent (2026-10-09); named by `ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`; consistent with the master directive's architecture-enforcement intent. | Keep in `docs/`. |
| `architecture/eco-nojin-architecture.yaml` | (b) Architecture contract — **stays** | Top-level `architecture/` (untracked). Canonical architecture descriptor; referenced by `ECO-NOJIN MASTER EXECUTION SPECIFICATION.md:730`. This is live config, not prose. | Keep. Recommend tracking in git. |
| `architecture/rules.yaml` | (b) Architecture contract — **stays** | Defines `AR-01..AR-10` consumed by `tools/detect_imports.py` and pinned by `engine/tests/test_architecture_rules.py`. Live machine contract. | Keep. Recommend tracking in git. |
| `data/reports/*.json` (123 files) | (c)-adjacent: runtime data, **not architecture docs** | Runtime report JSON (`report_<uuid>.json`), not documentation and not audit artefacts; belongs in `data/`, outside `docs/`. | No doc action; excluded from `docs/` domain. |

None of the above are audit artefacts; therefore **0 files move** (the "at most
2 moves" allowance is not exercised).

### Cross-check: master directive §40 / mandatory documents

`HYDROMA-MASTER.md` §40 is the "قانون تکمیل واقعی" (completion chain
نید ← «</think>`hydroma.current.attach` — значит модели PYTHON и метаданные C++ согласованы.</think>TASK 1 is now fully grounded. Let me write the classification report and, in parallel, run the required verifications plus a final full-run stability confirmation.<tool_call>
<function=write>
<parameter=content>
# R-6 — Documentation Classification (`docs/architecture` + `docs/databases`)

**Date:** 2026-10-10
**Origin:** `reports/security/SECURITY-FINDINGS-2026-10-10.md` — F-4 / R-6
("183 architectural documents with no test … classify them (audit artefact vs.
documentation) and either move the two audit artefacts under `reports/` or mark
the directory informative in the master directive").
**Scope:** `docs/architecture/**`, `docs/databases/**` only. No `engine/`,
`services/` source, `tools/check_security.py` or `pyproject.toml` touched.
Nothing deleted. (≤ 2 moves allowed, only for unambiguous artefacts.)

---

## Result up front (evidence first)

**The R-6 premise is not reproducible in the current tree.** F-4 claims
`docs/databases/` (2 files) and `docs/architecture/` (181 files) are "tracked".
Those directories **do not exist** in the working tree and have **never** existed
in any commit on any branch. There are therefore **0 files under
`docs/architecture` / `docs/databases` to classify**, no file is moved, and
nothing is deleted.

| Evidence command | Result |
|---|---|
| `Get-ChildItem docs -Force` | only `docs/adr/` → one file `014-import-guard-policy.md` |
| `git ls-tree -r HEAD --name-only -- docs/` | one path: `docs/adr/014-import-guard-policy.md` |
| `git log --all --oneline -- 'docs/architecture/*' 'docs/databases/*'` | **empty** — never committed |
| `git branch -a` / `git worktree list` / `git stash list` | only `master` @ `d6fac05`; sibling worktree at same commit; no hidden history |
| `git check-ignore docs/architecture|docs/databases` | not ignored (so they would be tracked if present) |
| whole-tree scan for dirs named `architecture`/`databases` | only top-level `architecture/` (2 files) |

F-4 remark that the artefacts "were both included in the final machine report"
refers to the **security session's own outputs**, which already live under
`reports/` (see below) — not to the missing doc directories.

---

## What actually exists in the docs / architecture space (classified)

| File | Class | Reason | Recommended action |
|---|---|---|---|
| `docs/adr/014-import-guard-policy.md` | **(b) Architecture documentation — stays** | Only tracked file under `docs/`. ADR-014 for the externalised import-guard policy (`tools/import_guard_policy.json`); dated 2026-10-09; named in `ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`; aligns with the master directive's architecture-enforcement intent. | Keep in `docs/`. |
| `architecture/eco-nojin-architecture.yaml` | **(b) Architecture contract — stays** | Top-level `architecture/` (untracked). Canonical architecture descriptor, referenced by `ECO-NOJIN MASTER EXECUTION SPECIFICATION.md:730`. Live machine config, not prose. | Keep; recommend `git add` (currently untracked). |
| `architecture/rules.yaml` | **(b) Architecture contract — stays** | Defines `AR-01..AR-10`, consumed by `tools/detect_imports.py` and pinned by `engine/tests/test_architecture_rules.py`. Live machine contract. | Keep; recommend `git add`. |
| `data/reports/*.json` (123 files) | **runtime data — not architecture docs** | `report_<uuid>.json` runtime output; belongs in `data/`, outside `docs/`. | No doc action; out of `docs/` domain. |

**Class (a) audit artefacts found here: none. Class (c) stale/superseded: none**
(no superseded content to archive — the two ADR/rules files are current).

---

## The "two audit artefacts" — identified by content

The session's final machine report and its machine-readable twin already reside
under `reports/`, so R-6's "re-home the two audit artefacts" is already
satisfied and **nothing is moved**:

* `reports/security/SECURITY-FINDINGS-2026-10-10.md` — the final human-readable report.
* `reports/security/venv-integrity-2026-10-10.json` — the machine-readable twin.

(Other `*-MACHINE*-SUMMARY*.json/md` twins, e.g.
`reports/eco-04/36-FINAL-MACHINE-SUMMARY.json`, are likewise already under
`reports/`.)

---

## Cross-check against the master directive

`HYDROMA-MASTER.md` §40 is the "قانون تکمیل واقعی" completion chain
(requirement → design → implementation → executed test → evidence → acceptance),
and §4.1 enumerates 14 items that must be re-verified — it is **not** a list of
14 document filenames, so no filename mapping applies. Regardless, there is no
`docs/architecture` set to cross-reference against it.

---

## Recommendations

1. **Do not create** `docs/architecture/` / `docs/databases/` scaffolding to match
   the stale finding — nothing needs re-homing.
2. Correct/retire **F-4 / R-6** in `reports/security/SECURITY-FINDINGS-2026-10-10.md`
   (the "183 documents" figure is not reproducible) and mark it resolved.
3. `architecture/*.yaml` are live contracts — commit them; they are the real
   "architecture" surface, not documentation debt.
4. No documentation-freshness tool (`tools/check_docs_freshness.py`) was added:
   with no `docs/architecture` tree to keep fresh, such a tool would guard a
   non-existent path (optional per task, and unjustified by the evidence).

**Net change from R-6: 0 files moved, 0 deleted, 0 created under
`docs/architecture` / `docs/databases`.** This report is the sole new artefact.
