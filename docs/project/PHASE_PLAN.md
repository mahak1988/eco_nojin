# PHASE PLAN — ECO Nojin / HyDroMA (executable program)

* **Status:** Active · **Opened:** 2026-10-11 · **Supersedes:** the 16-phase plan in
  `docs/specs/ECO-PROGRAM-FA.md` §3–4 (moved from root `eco.md` in P1; strategy source —
  this file is the *executable* version, re-based on the measured baseline).
* **Inputs (all required reading for every agent):** `BASELINE.md`, `KNOWN_ISSUES.md`,
  `OPEN_DECISIONS.md`, `CAPABILITY_MATRIX.md`, `DEPENDENCY_MAP.md`, `AGENTS.md`,
  `docs/specs/ECO-PROGRAM-FA.md`. Section citations written as `eco.md §N` below mean that file.
* **Rule:** a phase is *done* only when its **gate commands pass on a committed tree** and the
  integrator signs off. Self-reported completion (`READY_FOR_REVIEW`) is a request, not a status.

---

## 1. Execution contract (binding on every agent)

1. Read `BASELINE.md` first; never quote a number you did not reproduce.
2. One agent, one phase, one declared file scope (see `DEPENDENCY_MAP.md §4`). Exceeding scope is
   recorded as debt/proposal, not implemented ad hoc.
3. Env (every shell): `$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"`; `$env:SECRET_KEY="test-secret-key"`;
   interpreter `& "D:\eco_nojin\.venv\Scripts\python.exe"` (bare `python` is not on PATH).
4. **One test suite per shell.** `pytest engine/ -n 6` and `pytest services/ -n 6` must never run
   concurrently (kills xdist). Add `-p no:cacheprovider`. Heavy RAG tests run in their own shard.
5. Money stays `Decimal`; batches balanced and posted at call sites; every write route keeps its
   authz check; no test is deleted or weakened to go green (eco.md §1.6).
6. Every schema change: guarded/idempotent Alembic revision + `upgrade head --sql` proof + rollback note.
7. Status vocabulary for delivery reports: `READY_FOR_REVIEW | BLOCKED | PARTIALLY_COMPLETE`.
8. Update this file's tracker (§6) only via the integrator.

## 2. Phase 0 — record (CLOSED as a document set, pending human sign-off)

Delivered: the six `docs/project/*.md` files (BASELINE / KNOWN_ISSUES / OPEN_DECISIONS /
CAPABILITY_MATRIX / DEPENDENCY_MAP / PHASE_PLAN). Gate G0: the numbers in `BASELINE.md` are
reproducible with the listed commands; KN-01…KN-17 each have an owner target phase; every open
decision in `OPEN_DECISIONS.md` has a named approver and a due phase. **G0 met 2026-10-11** —
awaiting human ratification only.

## 3. Wave schedule

| Wave | Phases | Parallel? | Entry gate |
|---|---|---|---|
| **W0 record** | P0 | — | G0 (met) |
| **W1 stabilize** | P1 | serial with everything | G0 |
| **W2 contracts** | P2, then P3 ∥ P4 ∥ P10 | P3∥P4∥P10 = three agents, disjoint file trees | G1 (P1) |
| **W3 economic ops** | P5 → P6 ∥ P7, P9 starts design | P6∥P7 after P5+P3+P4 | G2 (P2) |
| **W4 surface** | P8 (after P5,P7), P12 (after P2+P3), P11 (after P3,P10) | P8 ∥ P12 ∥ P11 | G3 (P5, P3) |
| **W5 harden** | P13 (after stable routes), P14 (independent QA) | P13 ∥ P14 prep | G4 (P8, P12) |
| **W6 release** | P15 | serial | G5 (P14, D-15, D-16) |

---

## Phase cards

### P1 — Quality debt & honesty fixes (A01)

* **Entry:** G0. **Scope:** `services/api_gateway/routers/tourism_router.py`, `services/blockchain/**`
  (write-freeze only), `docs/project/**`, `reports/**` (one line each).
* **Tasks**
  1. KN-01: tourism router must stop advertising availability it does not have — either implement the
     read path or return an explicit `503/feature-disabled` with error code, never a success-shaped
     stub. Add a contract test asserting the honest shape.
  2. KN-02: freeze EcoCoin writes (feature flag + deny on transfer/mint routes) until D-04 closes;
     document the raw-SQL table in KNOWN_ISSUES; **no behavioural rewrite in P1**.
  3. KN-10: reconcile strict-suite numbers (1323 vs 1314) — run once, paste the real line into both
     `BASELINE.md` and `AGENTS.md`.
  4. Add the KN-14 rule to the repo's ruff workflow: gate on the **committed baseline** (769), refuse
     growth, `ruff check .` output pasted into the report. **Delivered in P1 (partial):** the rule
     and the 769 floor are recorded in `BASELINE.md` ("Snapshot rule") and `tools/lint_baseline.json`;
     the measured count is 761. Making the CI lint job *ratchet* (fail above 769 instead of only
     publishing the count, `.github/workflows/ci.yml`) is outside P1's declared file scope and is
     logged as a follow-up proposal for the integrator — not done silently.
  5. ~~Move `eco.md` → `docs/specs/ECO-PROGRAM-FA.md`~~ — **done in P1**: moved with
     `Move-Item` + `git add` (untracked, so `git mv` fails), and all four references updated
     (this task, `AGENTS.md` §Execution program, `BASELINE.md` header, `PHASE_PLAN.md` header).
* **Gate:** `pytest services/api_gateway/tests services/tourism/tests services/blockchain/tests -q -n 4`
  (337 passed, 0 failed — P1 evidence);
  `ruff check .` ≤ committed baseline (761 vs 769 — P1 evidence);
  `tools/detect_imports.py --root .` = 0 (PASS — P1 evidence);
  app still boots 113 routes (P1 evidence). **Exit:** KN-01, KN-02 frozen, KN-10, KN-17 closed with evidence.

### P2 — Target-architecture contracts (A02)

* **Entry:** G1. **Scope:** `architecture/**`, contract docs, `tools/import_guard_policy.json`.
* **Tasks**
  1. Ratify the API contract: `Idempotency-Key`, `EcoNojinException` error body, `Decimal` money
     serialization, pagination shape, rate-limit headers — one page, versioned, with contract tests.
  2. D-06 decision recorded (NATS optional extra + pin list + event ownership/retry/idempotency rules).
  3. Domain ownership register: for each of the 22 logical domains: data owner, change reference,
     allowed consumers, delete policy, sensitivity, audit needs (eco.md §2.2).
  4. Event policy: which events really exist, owners, ordering, at-least-once handling, financial
     replay protection; publish in `architecture/dependency-graph.md` update (dated).
* **Gate:** contract tests green; `tools/detect_imports.py` 0; boundaries 0 stale; docs diff
  reviewed by an architecture reviewer. **Exit:** contracts + ownership register merged.

### P3 — Identity, access & multi-tenancy (A03)

* **Entry:** G2 (+ D-08 decided or deferred with risk accepted). **Scope:** `services/auth/**`,
  `services/api_gateway/middleware/**`.
* **Tasks**
  1. Cross-tenant negative matrix (server-side, not UI-hiding): user↔user, shop↔shop,
     village↔village, seller↔other-seller ledger; each test must fail if a scope check is removed.
  2. Close KN-13: sponsors `require_admin` placeholder (501s today).
  3. Session lifecycle: revocation + expiry tests; cookie flags/CSRF posture per D-08; auth
     rate-limit tests (`HYDROMA_AUTH_RATE_LIMIT_*`).
  4. RBAC completeness: roles independent of profile titles; privileged operations require explicit
     grants (eco.md P-04); scope-enumeration tests for escalation attempts.
* **Gate:** new tests all pass; auth + gateway suites green; mutation of any scope guard fails a test
  (detox check by A14). **Exit:** no privileged route without server-side authz + negative test.

### P4 — Data model & migrations (A04)

* **Entry:** G2. **Scope:** `database/models.py`, `alembic/**`.
* **Tasks**
  1. KN-03: unique `(buyer_id, idempotency_key)` on `com_orders` (guarded, backfill-safe revision).
  2. KN-04: the three deferred FKs — each as its own guarded revision with an orphan-precheck query.
  3. KN-05: bring the 17 off-registry tables into the registry (or document them as intentionally
     external, dated, in DEPENDENCY_MAP).
  4. KN-06: named-`Enum` Postgres pre-pass plan; SQLite test parity note.
  5. Migration discipline: every revision idempotent + `--sql` render proof + rollback note in the
     revision docstring; `alembic upgrade head` applied on a scratch DB.
  6. KN-09/D-17: SQLite WAL gate documented; one **restore drill** with evidence (backup → restore →
     row-count check).
* **Gate:** `alembic upgrade head --sql` renders; `alembic heads` single; `alembic upgrade head`
  applies on a scratch DB; `pytest services/inventory/tests -n 4` green (`database/` ships no test
  package); restore-drill log in the report.
  **Exit:** no schema debt added; backstops + FKs in place.

### P5 — Money source of truth, settlement & EcoCoin resolution (A05)

* **Entry:** G2 + **D-09/D-10/D-11 decided**. **Scope:** `services/finance/**`, `services/wallet/**`,
  `services/ledger/**`, new integration tests in `services/tests/**`.
* **Tasks**
  1. Write the money model (D-09): journal = source of truth; wallets/commerce = read models; the
     write contract in `architecture/` + a boundary test blocking direct balance writes.
  2. D-10 shared user key: migration attaching `users.id` to every ledger row (guarded, backfilled).
  3. Reconciliation service + report: pairwise ledger-vs-journal diff, scheduled, alerting on drift
     (closes the "figures side by side" problem).
  4. Settlement & refund: trace IDs, idempotent replays, duplicate-webhook test, rounding test at
     cent level; KN-07 `abs(qty)` fix for inventory valuation.
  5. D-04 implementation: EcoCoin either becomes a governed ledger (migration + registry + tests) or
     is removed from live routes. Decide **in P5**, not before.
* **Gate:** money property suites + integration suite green (duplicate webhook, retry, refund,
  reconcile); new boundary test fails if any domain writes a balance outside finance; app boots.
  **Exit:** single documented source of truth + shared attribution key + reconciliation running.

### P6 — Marketplace end-to-end (A06)

* **Entry:** G3 (P5+P3+P4). **Scope:** `services/marketplace/**`, `services/commerce/**`.
* **Tasks**
  1. Contract: hierarchy marketplace → bazaar → shop → product/service; seller membership,
     verification, brand usage, legal trademark, product certification as **separate** states
     (eco.md §6) with a state test per distinction.
  2. E2E golden path: Catalog → Cart → Order → Payment → Confirmation → Settlement — API + DB +
     authz + finance + UI-contract (OpenAPI shape), negative paths included (stock shortfall,
     double-submit, expired idempotency key).
  3. KN-04 sibling: `marketplace_order_items.order_id` FK if not done in P4.
  4. Seller complaint/dispute intake and report endpoints.
* **Gate:** E2E test committed and green; no step of the path returns a stub payload; commerce +
  marketplace suites green. **Exit:** the path is demonstrably end-to-end in CI.

### P7 — Village & rangeland governance (A07)

* **Entry:** G3 (P3+P4). **Scope:** new `services/village/**`, `services/rangeland/**`,
  `services/territory/**`, migrations under A04 review.
* **Tasks**
  1. `CommunitySpace` with `village` / `pastoral_rangeland` subtypes (legal/geographic/social
     differences preserved, not flattened into one vague model).
  2. Registration workflow (request → identity → authority check → documents → local governance →
     working group → charter → activation → public page → periodic review + objections), each step
     auditable (KN-12's ~18 tables get a guarded migration here).
  3. Working group: membership, mandate, decision records, conflict-of-interest, suspension —
     member changes never delete decision history.
  4. Versioned local charter; brand/validation separated (D-14); sensitive-data access tiers
     (migration routes, water sources, sacred sites, ownership, exact eco-locations) with default
     private.
* **Gate:** workflow tests (incl. objection + suspension + history preservation); cross-village
  negative tests (parameter-tampering must fail); sensitive fields private by default; migration
  guarded. **Exit:** a village can be onboarded and validated without code changes.

### P8 — Tourism & events (A08)

* **Entry:** G3 + **P1's KN-01 decision**. **Scope:** `services/tourism/**`.
* **Tasks**
  1. Resolve KN-01: implement or keep hard-disabled with an explicit feature-flag and error code;
     the router never returns `requires_setup` again.
  2. Entity decision: keep the 3-entity model **or** grow to the 9-entity model
     (proposal/product/operator/approval/departure/booking/participant/incident/refund) — decision
     recorded with a scope test; proposals must not become sellable tours without approval.
  3. Capacity, cancellation, refund, complaint tests; GSTC-informed criteria documented as design
     reference (never claimed as certification); safety/emergency fields.
* **Gate:** booking→payment→refund E2E through P5 money contract; capacity overbooking test;
  suite green. **Exit:** nothing sellable that cannot be delivered.

### P9 — Compliance & legal framework (A09)

* **Entry:** G3 + **D-03 decided**. **Scope:** new `services/compliance/**`, `services/legal/**`.
* **Tasks**
  1. Registry: `RegulatorySource`, `Jurisdiction`, `ActivityClassification`, `ComplianceRequirement`,
     `Credential`, `CredentialVerification`, `ComplianceAssessment`, `RegulatoryChange`,
     `ComplianceException`, `ComplianceAuditLog`.
  2. Workflow: classify activity → jurisdiction → requirements → documents → verification →
     status; ambiguous items escalate to a human specialist (agent never rules on legal validity).
  3. Expiry review; internal approval ≠ government licence; no "fully compliant" claim without
     evidence; jurisdictional conflict escalates instead of auto-resolving.
* **Gate:** workflow tests incl. expiry and exception paths; no endpoint emits a compliance verdict
  without a linked assessment record; pilot jurisdiction data seeds load. **Exit:** pilot ready.

### P10 — HyDroMA engine maturity & provenance (A10)

* **Entry:** G2 + **D-13 decided**. **Scope:** `engine/**`.
* **Tasks**
  1. Triage the **57 unvalidated** models: per model — keep-and-plan / stub-only / remove; output a
     dated table mapping model_id → status → evidence → target.
  2. Provenance & uncertainty on every scientific payload: model version, data version, assumptions,
     limits; publish only `validated` (D-13) in user-facing paths.
  3. Scenario contract: request → validation → model/data selection → plan → compute → result
     validation → provenance/uncertainty → storage → presentation; failure in one model ⇒ explicit
     partial-failure state, never a silently averaged result.
  4. Reproduce the 124–244× Numba claim: hardware, dataset, versions, correctness parity — or
     downgrade the claim in docs. Separate heavy compute from request path (queue/worker).
* **Gate:** engine suite + strict suite green (one shell each, `-n 6`); provenance fields present on
  scientific routes; benchmark note reproducible by a second engineer. **Exit:** registry truth =
  published truth.

### P11 — Daneshyar, Tasmimyar & restoration (A11)

* **Entry:** G4 (P3+P10). **Scope:** `services/knowledge/**`, `services/tasmimyar/**`.
* **Tasks**
  1. Knowledge layer: programs/courses, groups, enrollment, content ownership + publication rights.
  2. Decision support explainability: goal, inputs, criteria, compared scenarios, assumptions,
     uncertainty, limits, version, and the accountable decision-maker — advice never auto-applied.
  3. Restoration/development MVP: proposal → review → approval → execution → evidence → verification
     → reward decision (Eco Coin hook **only after D-04**).
  4. Knowledge RAG: shard heavy tests (KN-15).
* **Gate:** courses/decision flows integration-tested; every recommendation carries evidence +
  limits; no reward issued without an approval record. **Exit:** learning + advisory are real flows.

### P12 — Frontend (A12) — **RETIRED 2026-10-13**

* **Owner decision 2026-10-13:** the SPA tree (`frontend/`), its audit/design/plan docs, the
  frontend tooling (`tools/check_frontend_layering.py`, `tools/frontend_bundle_audit.*`), the
  pnpm/npm workspace config (`pnpm-workspace.yaml`, `.npmrc`) and the CI `frontend` job were all
  removed; the repository is backend-only. What P12 delivered in 2026-10-11 stays in the record
  (`reports/ROADMAP-PHASE-5B-*`).
* This phase no longer has an entry, scope or gate. A future frontend — if one is ever adopted —
  arrives through a new decision row in `OPEN_DECISIONS.md` (D-01 is closed), never by resuming P12.

### P13 — Performance, offline & scale (A13)

* **Entry:** stable P6/P8/P12 routes. **Scope:** perf configs, caching, queue wiring, tooling.
* **Tasks**
  1. Measure first: API latency p95 per critical route, DB query counts, index review; record the
     numbers, then fix the top offenders.
  2. Heavy compute isolation: engine jobs through a worker queue (feeds D-15).
  3. Offline per D-12: public content, drafts, and server-authoritative sensitive ops; conflict and
     retry semantics tested; Background Sync never finalises a financial operation.
  4. Split the heavy RAG tests into their own shard (KN-15).
* **Gate:** route latency report vs targets; offline queue tests; no regression in the two big
  suites (run separately). **Exit:** every optimisation traces to a measured number.

### P14 — Independent acceptance (A14)

* **Entry:** G5. **Scope:** test plans & reports only — **the implementer of a capability is not its
  auditor.**
* **Tasks:** sweep per eco.md §14: security (authz, injection, uploads, rate-limit, secrets, audit),
  money (replay, webhooks, refunds, rounding, ledger reconciliation), scientific (units, provenance,
  reproducibility), legal (credential expiry, brand, complaints), frontend (a11y, RTL, errors),
  plus detox: revert each authz/money guard and confirm a test fails.
* **Gate:** every critical finding has severity + owner + fix phase; E2E journeys green; zero
  unresolved criticals. **Exit:** acceptance report signed.

### P15 — Controlled release & operations (A15)

* **Entry:** G5 + **D-15, D-16, D-17 closed**. **Scope:** release tooling, runbooks.
* **Tasks:** dev → CI → staging → E2E → migration dry-run → backup/restore drill → limited pilot →
  monitoring → gradual rollout → post-release review. Structured logs, error tracking, health checks,
  queue monitoring, finance & credential-expiry alerting, deployment version registry, incident
  response + rollback runbook.
* **Gate:** deploy is reproducible and recoverable; migrations rehearsed on staging; critical alerts
  fire in a drill; rollback documented. **Exit:** MVP-1 released, MVP-2/3 scheduled.

---

## 4. Integration checklist (integrator, every merge)

From eco.md §14, plus repo specifics: changed files inside the agent's scope? tests run and pasted?
no dependency on a stub/frozen feature (EcoCoin, `requires_setup`)? API contract version status
stated? migration present + `--sql` proof + rollback note? authz tested? audit/error/retry paths
stated? docs updated (`docs/project/*` + AGENTS.md when gates move)? prior suites still green?
route-count pin still 113 unless deliberately changed? If a phase fails acceptance it does **not**
advance the schedule.

## 5. Standard agent prompt (eco.md §13 — keep verbatim, fill the brackets)

`PHASE_ID` · `PHASE_NAME` · `BASE_COMMIT` (abbreviated, e.g. `2cb974e`) · inputs = the five
`docs/project/*.md` files · `PHASE_GOAL` · `ALLOWED_SCOPE` · `OUT_OF_SCOPE` · `DEPENDENCIES` ·
`ACCEPTANCE_CRITERIA` · the 15 mandatory rules (reality before change; no stub assumed complete; no
test weakened; no shared contract changed without a decision; no risky migration without recovery;
money exact/idempotent/auditable; no privilege from title; no secrets; open decisions escalated;
risk-proportionate tests; API compatibility; scope creep recorded as debt; blockers reported with
evidence). Delivery report: summary, files, decisions taken/open, commands + real outputs, remaining
debt, risks, API/schema changes, integration needs, reproduction steps, per-criterion status, final
status ∈ {`READY_FOR_REVIEW`, `BLOCKED`, `PARTIALLY_COMPLETE`}.

## 6. Tracker (integrator-maintained)

| Phase | Wave | Owner | Status | Gate evidence |
|---|---|---|---|---|
| P0 record | W0 | A00 | **closed (docs delivered 2026-10-11)** | this file + `BASELINE.md` |
| P1 honesty/quality | W1 | A01 | **closed 2026-10-11** — evidence in `reports/PHASE-P1-2026-10-11.md` | 337 passed; ruff 761 ≤ 769; guard PASS; 113 routes |
| P2 contracts | W2 | A02 | **closed 2026-10-11** — evidence in `reports/PHASE-P2-2026-10-11.md` | 299 passed; ruff 761; guard + boundaries PASS; 113 routes |
| P3 identity | W2 | A03 | **closed 2026-10-11** — evidence in `reports/PHASE-P3-2026-10-11.md` | 702 passed; ruff 761; guard + boundaries PASS; 113 routes |
| P4 data/migrations | W2 | A04 | **closed 2026-10-11** — evidence in `reports/PHASE-P4-2026-10-11.md` | 5 migration tests + 476 + 164 passed; ruff 762; guard PASS; single head renders |
| P5 money truth | W3 | A05 | **closed 2026-10-11** — decision core executed (D-10 migration, cross-ledger report, D-04 honest disable); evidence in `reports/PHASE-P5-P15-COMPLETION-2026-10-11.md` | completion report |
| P6 marketplace | W3 | A06 | **closed 2026-10-11** — evidence in `reports/PHASE-P6-2026-10-11.md` | gateway suite 318 passed; ruff 762; cart bug fixed |
| P7 governance | W3 | A07 | **partially closed 2026-10-11** — evidence in `reports/PHASE-P7-2026-10-11.md`; router increment pending | 8 governance tests; 6 gov tables migrated; ruff 762; guard PASS |
| P8 tourism/events | W4 | A08 | **partially closed 2026-10-11** — departures delivered (additive per the proposal); refund/incident entities remain the 9-entity follow-up | 38 tourism tests; completion report |
| P9 compliance | W3→W4 | A09 | **partially closed 2026-10-11** — HTTP router delivered with cross-subject scoping; D-03 pilot data remains the approver's | 11 compliance tests; completion report |
| P10 engine maturity | W2 | A10 | **closed 2026-10-11** — evidence in `reports/PHASE-P10-2026-10-11.md` | strict 1324/0; 117 P10 tests; triage 13/49/8/0; numba reproduced 218× |
| P11 daneshyar/decision | W4 | A11 | **partially closed 2026-10-11** — the explainability contract lands (advice carries evidence, limits and an owner); learning-program and restoration flows remain | 5 explainability tests |
| P12 frontend | W4 | A12 | **retired 2026-10-13** (owner decision) — the 2026-10-11 scaffold was removed with the whole SPA tree; the backend API is the product surface | no frontend tree; `tools/export_openapi.py` is the contract export |
| P13 perf/offline | W5 | A13 | **partially closed 2026-10-11** — the latency baseline exists (measurement harness); the 3-tier offline design (D-12) and the heavy-compute queue remain | 1 measurement test |
| P14 acceptance | W5 | A14 | **partially closed 2026-10-11** — the guard sweep: 12 static checks that the earlier phases' protections are still in the code | 12 sweep tests |
| P15 release | W6 | A15 | **partially closed 2026-10-11** — `docs/RELEASE-RUNBOOK.md`: stages, monitoring, WAL gate, rollback, post-release | runbook |
