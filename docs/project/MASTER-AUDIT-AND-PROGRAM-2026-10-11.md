# MASTER AUDIT, DEVELOPMENT & VALIDATION PROGRAM — ECO Nojin / HyDroMA

* **Date:** 2026-10-11 · **Owner:** A00 (repository analysis) · **Program:** `PHASE_PLAN.md`
* **Method:** every number below was measured on this tree on 2026-10-11 (gates,
  static scans, test suites, diff review). Web research is cited by source and
  limited to what was actually fetched or what the repository already pins.

---

## 1. Audit — where the project stands

### 1.1 Measured state (2026-10-11)

| Dimension | Value | How measured |
|---|---|---|
| Reaches / routes | 115 routes / 641 OpenAPI paths | `app.openapi()` |
| ORM tables | 158 (150 registry + alembic_version + escrow_items + gov/com/tourism additions) | scratch `alembic upgrade head` |
| Tests green | gateway 319 · new suites 240 · frontend 8 + e2e 4 · migration/bridge/freeze ~40 | this session's runs |
| Scientific models | 70 registered: 13 validated / 49 validation backlog / 8 explainability surfaces | `engine/models/registry.py` |
| Money plane | journal-as-source-of-truth ratified (D-09), `users.id` shared key (D-10), finance-only writers (D-11), 6 guarded revisions | `MONEY-CONTRACT-v1.md` |
| Lint / types / architecture | ruff 768 (baseline 769) · mypy engine 0 · import guard 0 violations · boundaries 145/145 declared | gate commands |
| Frontend | real scaffold: typed client from the live OpenAPI (641 paths), 3 pages, offline queue, Playwright e2e | `frontend/` |
| Changed files | 358 in the working tree, 18 phase reports, 0 commits | `git status` |

### 1.2 What the audit proves (strengths, with evidence)

1. **The honesty infrastructure works.** Three real lies were found and closed this
   program: the tourism `requires_setup` payload (P1), 15 fabricated EcoCoin
   endpoints (P5), and a governance activation gate that had no charter check
   (P7). Each is pinned by a test that fails if the lie returns.
2. **The guards catch real bugs, not hypothetical ones.** The E2E golden path found
   a live 500 on every `/cart` route (P6); the engine-job bridge found three
   pre-existing `services/jobs` bugs — schema-persisted-as-model, UUID validation,
   naive-datetime subtraction (P13) — one of which broke the production jobs list.
3. **The money plane is now structurally sound**: a ratified source of truth, a
   shared attribution key, a sole writer, and a static scan that fails the build
   when an unauthorized writer appears.
4. **Access control was genuinely broken and is now closed**: five exploitable
   gaps (public order listing, body-derived buyer identity, cross-seller image
   mutation, public revenue stats, a 501 admin placeholder) — all closed with
   negative tests that fail when the guard is removed.
5. **Science is honest about itself**: 13 models validated with reference
   evidence, 57 explicitly triaged, and the Numba speedup claim **reproduced
   (218× combined, 54–247× per loop) and re-scoped** in the docs.

### 1.3 Weaknesses (ranked, with evidence and owner)

| # | Weakness | Evidence | Severity |
|---|---|---|---|
| W-1 | **57 of 70 models are unvalidated** — the engine's authority is partial | `ENGINE-MODEL-TRIAGE-2026-10-11.md` | high (science credibility) |
| W-2 | **SQLite runtime 3.49.1 < the WAL-reset fix (3.51.3; backports 3.44.6/3.50.7)** — a multi-connection WAL deployment can corrupt | `sqlite.org/wal.html` §11 (fetched 2026-10-11), `database/hub.py::sqlite_wal_deployment_safe()` | high (data integrity) |
| W-3 | **D-03 pilot data is a shape, not law** — requirement text must be replaced by real sources | `tools/seed_compliance_pilot.py` header | high (compliance liability) |
| W-4 | **Playwright browser is geo-blocked**; e2e runs on the system Chrome here | install log (403 from cdn.playwright.dev) | medium (CI coverage) |
| W-5 | **Offline tiers are queue+cache; Background Sync registration and replay conflict semantics missing** | `frontend/src/offline/queue.ts` | medium |
| W-6 | **No HTTP submit endpoint for engine jobs** (the bridge + tests exist; the route does not) | `services/jobs/engine_bridge.py` | medium |
| W-7 | **ruff 768 vs baseline 769** — the debt is lint, not code, but it masks real findings in CI noise | gate output | low-medium |
| W-8 | **EcoCoin frozen 503 everywhere** — the decision is made, the product choice is not | `services/api_gateway/routers/blockchain.py` | product risk |
| W-9 | **The gateway catalog plane and the DB marketplace plane coexist** (KN-24) | P6 report | medium |
| W-10 | **Single-tenant performance envelope unknown** — one latency baseline, no load test at scale | P13 harness | medium (scale) |

### 1.4 External references actually used (fetched this session)

* **GSTC Standards** (gstcouncil.org, fetched 2026-10-11): four pillars — sustainable
  management, socioeconomic, cultural, environmental impacts; six standards (Hotel,
  Tour Operator, Destination, MICE, Attraction, F&B); built on the ISEAL Code of
  Good Practice; free for non-commercial use, commercial use is licensed. **Program
  consequence:** the tourism module may map to the Tour Operator standard as a
  *design reference* (the API never claims certification — W-3 and eco.md P-08 both
  forbid it), and any commercial reuse of the criteria text must be licensed.
* **SQLite WAL** (sqlite.org/wal.html, fetched 2026-10-11): the WAL-reset bug affected
  all versions 3.7.0–3.51.2, fixed in 3.51.3, backported to 3.44.6 and 3.50.7; it
  requires ≥2 connections racing on checkpoint; WAL does not work on network
  filesystems; checkpoint starvation grows the WAL unbounded. **Program consequence:**
  upgrade SQLite to ≥3.51.3 (or qualify a backport ≥3.50.7 and record it as a decision),
  run one writer per file, and add a WAL-size monitor to P15's alerting.
* Repository-pinned references (already in the codebase, not re-fetched): FAO-56
  (crop water), USDA texture/soil taxonomy and RUSLE, WMO climate normals,
  OWASP session-management and ASVS checks (the webhook/HMAC test suite).

---

## 2. Development program (the roadmap)

Sequenced so that every entry condition is something the audit can verify. Waves
assume one agent per phase with the file-ownership map from `DEPENDENCY_MAP.md`.

### Wave A — close the integrity gaps (4 weeks)

| Release | Scope | Entry | Exit (verifiable) |
|---|---|---|---|
| R-1 (W-2 fix) | Upgrade SQLite to ≥3.51.3 (or record the backport decision); add the WAL-size + single-writer monitor; pin `sqlite_wal_deployment_safe()` in the release gate | current tree | `alembic upgrade head` on staging WAL + a load test with 2 connections; no hub ERROR |
| R-2 (engine-job HTTP) | `POST /api/v1/jobs/engine` (202 + job id) and a worker loop entry point; rate-limited; idempotent submit | P13 bridge | e2e: submit → poll → result recorded; the P14 sweep extended |
| R-3 (offline completion) | Background Sync registration, replay backoff + conflict rules (last-write-wins for drafts only, server-authoritative on conflict) | tiers 1–3 shipped | e2e offline→online replay test with an injected conflict |
| R-4 (compliance pilot → real) | Replace the pilot requirement text with the real sources for the chosen jurisdiction; a reviewer sign-off per source | D-03 pilot shape | every requirement row carries the source URL + citation date |

### Wave B — scientific credibility (8 weeks)

| Release | Scope | Exit |
|---|---|---|
| R-5 (validation backlog I) | Validate the soil/hydrology cluster first (highest downstream use: RUSLE, CEC, PTF, FAO-56) against published references; each model must carry reference, tolerance, and the runner's record | models move `unvalidated → validated` in the registry, with the evidence file per model |
| R-6 (catalog/DB unification, KN-24) | One marketplace plane: catalog-plane orders persist `marketplace_orders` rows via the finance contract | the golden path leaves rows in both planes consistent (a reconciliation test) |

### Wave C — surface completion (8 weeks)

| Release | Scope | Exit |
|---|---|---|
| R-7 (frontend breadth) | Village page on real governance endpoints, dashboard with the cross-ledger report, MapLibre boundary map (private until published — the governance rule), bundle budgets in CI, Playwright with the bundled browser in CI | a11y (axe) green on the three journeys; bundle ≤ budget |
| R-8 (tourism breadth) | EcoCoin decision executed (governed ledger or removal), refund settlement wired to the finance reversal, incident workflow surfaced | refund e2e through a compensating journal entry |
| R-9 (operations) | Postgres pilot (one service plane), tracing on (OTLP), the DR drill in CI, the load test at 10× pilot traffic | every RELEASE-RUNBOOK section executed once on staging |

---

## 3. Validation program

### 3.1 The invariant gates (already automated — keep them red-line)

1. `ruff check .` ≤ committed baseline (769 today) · `mypy engine` 0 ·
   `tools/detect_imports.py` 0 violations · `check_service_boundaries.py` 0 stale.
2. `pytest engine/strict_tests` · `pytest services/ -n 6` · `pytest engine/ -n 6`
   (one suite per shell).
3. `tests/test_p14_guard_sweep.py` — the P14 sweep: deleting any delivered guard
   fails a test.
4. `app.openapi()` route count is deliberate (115 today) and the API contract
   version status is stated for every change.

### 3.2 Per-release gates (new)

| Gate | What proves it |
|---|---|
| **Migration rehearsal** | every revision: fresh upgrade → re-run no-op → downgrade → re-upgrade (the P4/P7/P8/P9 pattern, now standard) |
| **Access detox** | for every scoped route: steal the token, mutate the path, and the request must 403/404 (the P3 matrix, extended per new surface) |
| **Money detox** | for every money route: replay with the same Idempotency-Key (200 + cached), different body (422), and a compensating entry must balance (the P5 property suites) |
| **Science protocol** | a model is `validated` only with: reference citation, input range, tolerance, the runner record, and an uncertainty statement (the `publication_stamp` must show `publishable_without_caveat`) |
| **E2E** | the four Playwright journeys + the offline replay + the engine-job lifecycle; in CI with the bundled browser |
| **Performance** | the P13 harness result vs the previous release's (a regression >30% p95 blocks) |
| **DR** | snapshot → verify (sha256) → restore → row-count, on a schedule and before every release |

### 3.3 Independent acceptance (P14 continuation)

Quarterly: a reviewer who delivered none of the phases sweeps security (OWASP
ASVS L2 for the authz/money/upload surfaces), money (the five-ledger
reconciliation on real data), science (re-derive 5 validated models by hand),
legal (credential expiry + brand/trademark separation), and accessibility
(WCAG 2.2 AA + RTL) — and any critical finding re-opens the release.

---

## 4. Economic justification

All currency-less: figures are **planning estimates in person-months and
relative cost units (CU)**, explicitly labelled, so the approver can rebase them.

### 4.1 Cost model (per year, CU)

| Item | Basis | Estimate |
|---|---|---|
| Engineering (2.5 FTE: backend, frontend, science-validation) | market seniority | 150 CU |
| Science validation (57 models ÷ ~6/week with a domain reviewer) | backlog triage | 40 CU one-off, 15 CU/yr after |
| Infrastructure (pilot: 1 app + 1 Postgres + object storage + monitoring) | R-9 sizing | 25 CU/yr |
| Compliance/legal review (pilot jurisdiction, credential workflow) | D-03 | 20 CU one-off |
| Security audit + DR drills (quarterly) | P14/P15 | 12 CU/yr |
| **Year-1 total** | | **~247 CU** (of which 60 one-off) |

### 4.2 Value model (what the platform monetises, per the ratified design)

| Stream | Mechanism (already in the code) | Planning assumption |
|---|---|---|
| Marketplace | platform fee on `com_orders` settlement (the 800/200/200 bps split is implemented and tested) | the commission rate × order value; the platform fee is a code constant today — a pricing decision |
| Tourism | the same fee split on tour bookings; operator-side SaaS fee possible later | bookings × fee |
| Village fund | the 200 bps landscape share accrues to governance-validated villages (the fund ledger exists) | network effect, not direct revenue |
| EcoCoin | frozen (D-04); optionality only — internal points/transfer/removal, decided | 0 until decided |
| Science advisory | decision-support (tasmimyar) with explainability — the contract exists | post-validation, per-seat or per-run |

### 4.3 Justification arithmetic (labelled, so it can be re-based)

* **Cost of delay**: every month without R-1 (SQLite) risks corruption on the money
  ledger — the expected loss is not a line item, it is a *risk transfer*; the fix is
  days of work against unbounded downside. Same reasoning for W-3 (compliance text):
  a wrong regulatory string is a liability, not a bug.
* **Break-even for Wave A (integrity)**: R-1..R-4 ≈ 8 person-weeks. The value is
  avoided-loss (corruption, wrong-compliance, fabricated money moves) plus
  unblocking every revenue stream that needs the money plane to be trusted.
* **Break-even for Wave B (science)**: 55 person-weeks one-off. Value = the
  advisory stream + GSTC-aligned tourism credibility (design reference) — i.e. it
  converts "13 validated models" into a sellable claim. Until then, the platform
  must **not** advertise scientific authority (the `publication_stamp` enforces it).
* **TCO 3-year**: Year 1 ~247 CU (60 one-off), Year 2 ~187 CU, Year 3 ~170 CU
  (validation debt retired after Wave B) → **~604 CU**; revenue needs only ~15 CU
  of monthly gross platform fees to clear the run-rate.
* **Sensitivity**: the two assumptions that move the answer are (a) the commission
  rate on marketplace orders and (b) the science-validation throughput. The plan is
  deliberately ordered so the integrity work (A) is independent of both.

### 4.4 The honest bottom line

The program's engineering core is built and honest: the money plane is ratified,
access control is closed and guarded, the scientific registry reports its own
maturity, and the frontend is real. The remaining spend buys **three things only**:
data integrity (R-1), scientific credibility (R-5/R-6), and surface breadth (R-7/R-8).
Until Wave B lands, the platform is sellable on marketplace + tourism + village
governance mechanics, and must present science as *in progress* — the code already
refuses to let it do otherwise.

---

## 5. Immediate next actions (this week)

1. **R-1**: upgrade SQLite in `D:\eco_nojin` to ≥3.51.3 (or record the backport
   decision) and re-run the WAL gate; add the WAL-size monitor to the runbook.
2. **R-2**: mount the engine-job submit + worker (bridge and tests are ready).
3. **W-4**: switch Playwright to the bundled Chromium in CI (`PLAYWRIGHT_CHROME_CHANNEL`
   unset) so the geo-block does not hide coverage.
4. **W-3**: commission the real requirement text for the pilot jurisdiction.
5. Keep the gates red-lined; every step lands with its migration rehearsal and its
   P14 guard.
