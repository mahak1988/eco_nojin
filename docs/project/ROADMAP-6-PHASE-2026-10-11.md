# SIX-PHASE EXECUTION PROGRAM — subagent waves, supervisor-gated

* **Date:** 2026-10-11 · **Model:** each phase is executed by one subagent with a
  disjoint file scope; the supervisor (this session) validates every phase with the
  red-line gates before the next batch starts. Derived from
  `MASTER-AUDIT-AND-PROGRAM-2026-10-11.md` (R-1…R-9) and `PHASE_PLAN.md`.
* **Batch 1 (parallel, disjoint trees):** Phase 1 backend-integrity · Phase 3
  science validation · Phase 5 frontend completion.
* **Batch 2 (parallel, disjoint trees):** Phase 2 offline completion · Phase 4
  compliance reality · Phase 6 refund/CI-e2e + ops wiring.
* **Status:** Phase 1 ACCEPTED (supervisor gates re-run; alembic logging fix) - Phase 3 ACCEPTED (18 published models; supervisor removed two BOMs so the strict suite is green) - Phase 5 ACCEPTED (51 frontend tests, budgets enforced, 12 e2e; three backend gaps closed by the supervisor). Reports: reports/ROADMAP-PHASE-1-2026-10-11.md and reports/ROADMAP-PHASE-3-2026-10-11.md.
* **Status:** Phase 1 ACCEPTED - Phase 3 ACCEPTED - Phase 5 (frontend) ACCEPTED - Phase 5b (marketplace/tourism/finance breadth) ACCEPTED with the supervisor integration: 16 routes mounted, 4 root causes fixed (circular chunk blank SPA, i18next pairing, duplicate catalogue entry, dual-engine schema), 117 routes, 224 unit + 12 e2e green, gateway suite 319. Reports: reports/ROADMAP-PHASE-{1,3}-2026-10-11.md and reports/ROADMAP-PHASE-5B-FRONTEND-2026-10-11.md.
* **Red-line gates for every phase** (run by the subagent, re-run by the supervisor):
  `pytest <its suites> -q -p no:cacheprovider` green · `ruff check .` ≤ 769 ·
  `tools/detect_imports.py --root .` 0 violations · `tools/check_service_boundaries.py`
  0 stale · `app.openapi()` boots · **no test is weakened or deleted** · **no
  `git commit`/`git add`** · file edits via the edit/write tools (PowerShell
  `Set-Content` corrupts UTF-8/Persian) · env `$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"`,
  `$env:SECRET_KEY="test-secret-key"`, interpreter `& "D:\eco_nojin\.venv\Scripts\python.exe"`.

---

## Phase 1 — backend integrity (owner: A15/A04)

**Scope:** `database/hub.py`, `database/config.py`, `services/jobs/**`,
`services/api_gateway/routers/**` (jobs router only), `docs/RELEASE-RUNBOOK.md`.

1. **SQLite WAL gate made actionable**: when the bundled `sqlite3` is older than the
   WAL-reset fix (3.51.3; backports 3.44.6/3.50.7), attempt to use the
   `pysqlite3` drop-in when it is installed; expose `sqlite_wal_deployment_safe()`
   and a `wal_size_report(path)` (the WAL file size + a starvation warning when it
   exceeds 1000 pages ≈ 4 MB). Add a test for both.
2. **Engine jobs over HTTP**: `POST /api/v1/jobs/engine` (202 + job id, idempotent
   via an `Idempotency-Key`-safe path), a worker entry point
   `services/jobs/worker.py::run_forever(poll_seconds)` that drains
   `run_next_engine_job`, and rate limiting. Wire the existing
   `engine_bridge` (already tested) — do not invent a second queue.
3. Document the upgrade decision in the runbook (the sqlite.org facts).

**Exit:** jobs + gateway suites green; a test drives submit → run → completed;
`wal_size_report` tested; boundaries/guard/boot green; the runbook updated.

## Phase 2 — offline completion (owner: A13)

**Scope:** `frontend/src/offline/**`, `frontend/src/**` (integration only),
`frontend/src/**/*.test.ts(x)`.

1. Background Sync registration (a `registerBackgroundSync()` guarded by feature
   detection) and a replay loop with exponential backoff.
2. Conflict semantics: drafts are last-write-wins; a server-authoritative conflict
   (409 on replay) marks the action `needs_review` and never silently retries.
3. An online/offline indicator component wired to the app shell.
4. Tests: replay order, backoff, conflict quarantine, the queue's tier-3 refusal
   stays.

**Exit:** `npm test` green with the new cases; `npm run build` green; no backend files.

## Phase 3 — science validation (owner: A10)

**Scope:** `engine/**`, `docs/project/ENGINE-MODEL-TRIAGE-2026-10-11.md`.

1. Validate the **soil/hydrology/crop-water cluster first** (10 models, chosen by
   downstream use): each gets an evidence record
   (`engine/validation/<MODEL_ID>.md`) with the published reference, the input
   range, the tolerance, the comparison table (model vs reference), and the
   uncertainty statement.
2. A pytest per model (`engine/validation/test_validation_records.py`) that
   **re-runs** the comparison against the recorded values and fails on tolerance
   breach — evidence that the record describes the current code.
3. Raise the registry status **only where the evidence exists**, exactly the way
   the registry derives it (read `engine/models/registry.py` first; do not hand-edit
   cards without following the derivation).
4. Regenerate the triage table.

**Exit:** engine/strict_tests + the new validation tests green; the triage table
shows the moved models; **no model is marked validated without its record**; mypy
engine 0.

## Phase 4 — compliance reality (owner: A09)

**Scope:** `services/compliance/**`, `tools/seed_compliance_pilot.py`,
`docs/project/OPEN_DECISIONS.md` (D-03 note only).

1. Replace the pilot's placeholder requirement text with **real-shaped** text: each
   requirement names its authority (the pilot sources already seeded), the
   obligation, the evidence a subject must produce, and the citation date — the
   reviewer sign-off flag per source.
2. Add the renewal workflow: an expiring credential raises a
   `renewal_due` state (the service already expires; add the due-date view) and an
   assessment cannot be renewed without fresh evidence.
3. Tests: renewal gating, evidence freshness, and the pilot seed staying idempotent.

**Exit:** compliance suites green; `tools/seed_compliance_pilot.py` prints the real
requirement count with citations; boundaries/guard green.

## Phase 5 — frontend completion (owner: A12)

**Scope:** `frontend/**` (no backend).

1. **i18n**: i18next with `fa` (default, RTL) + `en`; every user-visible string in
   the three pages moves into the catalogue; a test asserts the RTL default.
2. **Village page wired to the live governance endpoints** (`/api/v1/village-governance`):
   list spaces, the workflow steps, the decision log — with permission-aware UI
   (the server stays the authority; the UI only hides).
3. **Dashboard with real data**: job stats (`/api/v1/jobs`), marketplace stats
   (`/api/v1/marketplace/stats`), the finance wallet balance — via the typed client.
4. **MapLibre** village boundary map (react-map-gl or maplibre-gl) that renders the
   **public centroid only** — never the private exact boundary (the governance rule),
   with a test that the private field is never requested.
5. **Budgets**: per-route-group bundle budgets in the vite config + a size-limit
   check in `npm run build`; **a11y**: aria labels + keyboard paths + an axe check
   on the three journeys.

**Exit:** `npm run typecheck` · `npm test` · `npm run build` all green; the RTL and
privacy tests exist; no backend file touched.

## Phase 6 — refund e2e, CI browser, ops wiring (owner: A08/A14)

**Scope:** `services/tourism/**` (settlement wiring), `.github/workflows/**`,
`frontend/e2e/**`, `docs/RELEASE-RUNBOOK.md`.

1. Wire the tourism refund to the **money contract**: an approved refund posts a
   compensating journal entry through the finance contract (a reversing balanced
   batch), and the settlement reference is recorded on the refund.
2. Playwright: default to the **bundled** Chromium in CI (the local override stays
   behind the env var) and add the install step to the workflow; an e2e journey for
   the refund request flow (server-mocked).
3. The runbook: the finance alert for refunds-without-settlement and the WAL monitor
   from Phase 1.

**Exit:** tourism suites + the new money test green; the CI job runs the bundled
browser; e2e specs pass locally with the bundled channel unset where available.

---

## Supervisor protocol (this session)

1. Read the subagent's report; **re-run the red-line gates myself**.
2. Diff-review the subagent's files for scope violations and honesty violations
   (comments claiming more than the code does; weakened tests).
3. A phase that fails a gate is **not** accepted: the supervisor fixes the smallest
   possible delta and records it, or sends it back.
4. Each accepted phase updates `PHASE_PLAN.md`'s tracker and gets a short report in
   `reports/PHASE-<n>-<date>.md`.
5. Nothing is committed; the tree stays reviewable as a whole.
