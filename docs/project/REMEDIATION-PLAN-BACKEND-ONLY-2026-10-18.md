# REMEDIATION PLAN — Backend / Database / Infrastructure Only

**Status:** Draft · **Opened:** 2026-10-18 · **Owner:** A00 (program)  
**Scope constraint (user instruction, binding):** **NO FRONTEND.** This plan covers only the
backend (engine + services), the database (models + Alembic), and infrastructure (CI, tooling,
runtime, observability, deploy). `D-01` (frontend removed) stays closed; `D-18` (React/Vite
reactivation) is **out of scope** and is not resumed by any phase here. The product surface is
the HTTP API (OpenAPI) + engine; any future client is a separate decision row.

**Source of truth for gaps:** `reports/PROJECT-SHORTCOMINGS-2026-10-18.md` (12 sections).  
**Execution contract:** inherited from `docs/project/PHASE_PLAN.md §1` and `SECURITY-REMEDIATION-PLAN.md §1`
(env, one suite per shell, guarded/idempotent migrations, no test weakened, no new balance writes
outside finance, secrets never committed).

**Out of scope (explicit):** any `frontend/**`, UI components, a11y/RTL, browser E2E, bundle
audits, npm/pnpm lockfiles, and anything requiring a chosen frontend stack.

---

## 0. Program rules (binding on every phase)

1. **Backend-only.** No phase may create, restore, or depend on a frontend tree. API changes are
   judged by OpenAPI shape + contract tests, not by a client.
2. **One suite per shell.** `pytest services/ -n 6` and `pytest engine/ -n 6` never run
   concurrently. Always `-p no:cacheprovider`. Heavy RAG/torch tests run in their own shard.
3. **Money stays `Decimal`.** No new balance writes outside `services.finance` (D-09/D-11).
4. **Every schema change** ships a guarded/idempotent Alembic revision + `upgrade head --sql`
   proof + rollback note in the docstring + scratch-DB apply.
5. **No test weakened/deleted** to go green (eco.md §1.6). Closure needs evidence (command + output).
6. **Status vocabulary:** `READY_FOR_REVIEW | BLOCKED | PARTIALLY_COMPLETE`.
7. **Tracker (§9) updated by the integrator only.**
8. **Open decisions** are never closed by an agent — only by the named approver with
   reason + date + consequences (`OPEN_DECISIONS.md`).

---

## 1. Wave schedule (backend-only)

| Wave | Phases | Parallel? | Entry gate |
|---|---|---|---|
| W0 stabilize | B0 (hygiene) | serial | G0 (baseline reproducible) |
| W1 security | B1 (remaining SEC) | serial after B0 | G1 |
| W2 data | B2 (registry/migrations) | serial after B1 | G2 |
| W3 engine | B3 (maturity/provenance) | parallel with B4 after B2 | G2 |
| W4 API | B4 (contract hardening) | parallel with B3 | G3 |
| W5 tests | B5 (coverage) | after B4 (stable routes) | G4 |
| W6 infra | B6 (infra/ops) | parallel with B5 prep | G4 |
| W7 release | B7 (acceptance+release) | serial | G5 (B5+B6+decisions) |

---

## Phase B0 — Code-hygiene & collection repair (A01)

**Entry:** G0. **Scope:** repo-wide Python hygiene; no business logic.

**Tasks**
1. Remove BOM (U+FEFF) from 13 files (`database/hub.py`, `services/knowledge/service.py`,
   `services/compliance/__init__.py`+tests, `services/api_gateway/routers/admin_content.py`,
   `admin_security.py`, `services/api_gateway/tests/test_frontend_contract.py`,
   `test_p6_golden_path.py`, `services/finance/tests/test_p5_money_invariants.py`,
   `services/land/tests/test_land_registry.py`, `services/tourism/tests/test_p8_scope.py`,
   `engine/tests/test_stage25_field_validation.py`, `tmp/dump_openapi.py`).
   Verify with `python -c` BOM scan = 0.
2. Fix latent undefined names (F821):
   - `services/api_gateway/main.py:321` — import `DbOrderRepo` from `services.marketplace.db_repos`
     (or remove the dead wiring block) — must not leave a `NameError` path.
   - `services/finance/routers/finance.py` — import `ComPaymentIntent` from `database.models`
     (bank webhook path is money-critical).
   - `services/marketplace/hub_service.py:2098` — import `MarketplaceCommissionRule` (or remove
     the dead method).
   - `services/tourism/models/festival.py` — import `UTC` from `datetime`.
   - `engine/gateway/input_validator.py:305` — import `numpy as np` (or remove annotation).
3. Fix invalid-syntax PEP 695 (Python 3.12-only) in `services/_contracts/status.py`,
   `services/api_gateway/base_router.py`, `services/api_gateway/eventbus/retry.py` — rewrite
   with `TypeVar`/`Generic` compatible with Python 3.11 (project target), or raise the
   declared target to 3.12 in `pyproject.toml` + CI + AGENTS.md (decision required; default:
   keep 3.11, rewrite).
4. Add missing `__init__.py` to `services/territory/` and `services/wallet/`.
5. Re-run collection: `pytest services/ engine/ --collect-only -q` must report **0 errors**.
6. Ruff: reduce 1139 → ≤ 769 baseline. Priority order: F821 (0), invalid-syntax (0),
   F811 (≤ 20), F401 (≤ 60), E402 (≤ 80), E501 (≤ 400) in this phase; the rest scheduled
   in B5. Record new baseline in `tools/lint_baseline.json` + AGENTS.md.
7. Break `engine/gateway/model_dispatcher.py` (2554 lines) below the 800-line ceiling in
   `test_structure_ceilings.py` — split into sub-dispatchers by domain prefix; keep the public
   `dispatch(model_id, ...)` signature stable (API contract).

**Gate (B0):**
- `pytest services/ engine/ --collect-only -q` → 0 errors.
- `ruff check .` ≤ 769 (or recorded new lower baseline).
- `tools/detect_imports.py --root .` = 0.
- `mypy engine --ignore-missing-imports` = 0 (run with 300s+ timeout).
- `from services.api_gateway.main import app; app.openapi()` boots.
- `engine/tests/test_structure_ceilings.py` green.

**Exit:** collection green, lint at/below baseline, no undefined-name paths in money/science
routes, dispatcher split merged.

---

## Phase B1 — Security closure (remaining SEC) (A03 + A04)

**Entry:** G1 (B0). **Scope:** `services/api_gateway/**`, `services/auth/**`,
`services/security/**`, `services/backup/**`, `services/business_modules/iot/**`,
`services/business_modules/voice/**`, `database/hub.py`, `adapters/persistence/**`.

**Tasks**
1. SEC-05 (HIGH): add authz (`require_user`/`require_admin`/`require_api_key`) to voice
   (tts/stt/ask/ivr-call/ivr-sms), mrv (8 POSTs), sync/trigger, insurance, science; validate
   Twilio DTMF signature (`twilio_ivr.py`) + escape TwiML. Negative tests per endpoint.
2. SEC-06 (HIGH, latent): either (a) add authz + `storage_path` validation (allow-listed
   root, no traversal) to backup router, or (b) delete the router + its tests and record the
   removal. Decision: **(a) only if backup is a committed capability (D-17); else (b).**
   Default (b) until D-17 closes.
3. SEC-07: remove JWT-from-query-string acceptance in `supabase_proxy.py` and `auth_supabase.py`;
   require header only.
4. SEC-09/10/11: DB credentials out of argv (env/pipe), WAL fail-closed on buggy SQLite
   (raise, do not log-and-continue), `0600` file mode + at-rest encryption note for SQLite
   stores; `prune_workspace.py` + `cleanup.py` refuse tracked files even on git error
   (fail-closed).
5. SEC-13: remove CSRF exemptions on `refresh`/`logout`/`reset-password` (coordinate with
   cookie auth; lands with double-submit) — or document the residual risk + compensating
   control.
6. SEC-15: CORS `allow_headers` add `X-TOTP-Code`, `X-Step-Up-Token`, `x-csrf-token`,
   `Idempotency-Key`, `X-API-Key`.
7. SEC-16/17/18/19/20/21/22/23/24/25: enumeration hardening (constant-time, generic
   messages), 2FA provisioning route (`generate_totp_secret` callers), JWT aud/iss/required
   claims, step-up JTI in Redis (or document single-worker limit), rate-limit trust of XFF
   (rightmost trusted hop), bind entrypoints to `127.0.0.1` by default (configurable),
   delete dead `security_legacy.py`, password policy + breach check on live path (min 12,
   complexity), remove demo creds / gate behind explicit seed flag, passkey RP_ID/ORIGIN from
   settings.
8. SEC-31 (scanner gate): wire `tools/check_security.py` into CI as blocking on HIGH
   (already 0 findings / 1251 files).
9. Add detox tests: revert each guard → a test fails (A14 owns the sweep, but guards land here).

**Gate (B1):**
- Security test suites green (incl. `services/security/tests/test_security_remediation.py`).
- `tools/check_security.py` = 0 findings (HIGH blocking in CI).
- No unauthenticated route in the cost/compute set (verified by a route-audit test).
- `ruff check .` ≤ baseline; import guard 0.

**Exit:** no HIGH/CRIT finding open; SEC plan S3-B/S4 closed or explicitly deferred with
owner + reason in `KNOWN_ISSUES.md`.

---

## Phase B2 — Data model & migration completion (A04)

**Entry:** G2 (B1). **Scope:** `database/models.py`, `database/hub.py`, `alembic/**`.

**Tasks**
1. EcoCoin (KN-02, D-04): decide in this phase — either (a) migrate `ecocoin_balances`/
   `ecocoin_transactions` into the ORM registry + a guarded Alembic revision + wire
   `EcocoinLedgerService` behind the router (KN-19), or (b) remove the router and service
   and document removal. **Default (b) until D-04 closes; if D-04 stays open, keep the
   write-freeze and remove the fabricated router payloads (return 503 feature-disabled).**
2. Village (KN-12): guarded migration for the remaining ~12 village tables (beyond the 6
   `gov_*`); HTTP router surface for governance workflow; cross-village negative tests over
   live endpoints; conflict-of-interest attestation.
3. Marketplace carts (KN-23): persistent DB-backed cart for logged-in buyers (new table
   `mkt_carts`/`mkt_cart_items`, guarded revision, idempotent).
4. Catalog/order plane unification decision (KN-24): document in `DEPENDENCY_MAP.md` (dated)
   whether in-memory `ProductCatalog`/`OrderManager._orders` are retired in favor of the DB
   plane; if retired, remove dead code; if kept, mark explicitly as cache with invalidation
   contract.
5. `marketplace_order_items.order_id` FK verification on a scratch DB (KN-04 sibling) +
   any remaining deferred FKs.
6. Named Enum pre-pass (KN-06): parity test asserting Python members vs DB check constraints
   on SQLite; `ALTER TYPE ... ADD VALUE` rule documented for the next enum change.
7. SQLite WAL gate (KN-09, D-16): document upgrade requirement before any WAL deployment;
   `sqlite_wal_deployment_safe()` stays the gate; add a startup check that refuses to boot in
   WAL mode on < 3.51.3.
8. Restore drill (D-17): backup → restore → row-count check, evidence in report.
9. `adjust` reconciliation (KN-07): extend `reconcile_inventory` to surface unrecognized
   adjustment formats as drift (already partially); add a test.

**Gate (B2):**
- `alembic upgrade head --sql` renders; `alembic heads` single; `alembic upgrade head` applies
  on a scratch DB; restore-drill log in report.
- No off-registry money table without a documented decision.
- `pytest services/inventory/tests services/marketplace/tests services/village/tests -n 4` green.

**Exit:** ecocoin resolved (migrated or honestly disabled), village migrated + routed,
carts persistent, catalog decision recorded, restore drill evidenced.

---

## Phase B3 — Engine maturity & provenance (A10)

**Entry:** G2 (B2 may run in parallel for independent parts). **Scope:** `engine/**`.

**Tasks**
1. Triage the 55 unvalidated models (KN-16): per model → keep-and-plan / stub-only / remove;
   dated table in `docs/project/ENGINE-MODEL-TRIAGE-*.md`; `publication_stamp` attaches
   status/caveat to every scientific payload (D-13 bar = S3).
2. Provenance & uncertainty on every scientific payload: model version, data version,
   assumptions, limits (currently partial). Wire into all scientific routes via the gateway
   facade.
3. Scenario contract (KN-29): register `APPLY_SCENARIO` model or remove the endpoint honestly
   (503 with error code, never a 500). Partial-failure state, never silently averaged.
4. Reproduce the Numba 124–244× claim: hardware, dataset, versions, parity — or downgrade the
   claim in docs (separate heavy compute from request path via queue/worker).
5. Fix nojin backend defects (KN-27): `GET /api/nojin/*` session dependency (not query param),
   `POST /soil/analyze` UnboundLocalError, `POST /rangerangeland/` IntegrityError,
   `POST /hydroma/water/groundwater-service/run` AquiferType subscriptability, `GET /auth/me`
   403 proof_of_work, `/auth/login|register` db-dependency defect.
6. Groundwater type fix, soil analyze fix, rangeland fix — all server-side, with tests.
7. Heavy RAG/torch tests (KN-15): split into a separate shard (`-n 2` or single-process)
   in CI; document in `tools/coverage_gate.py`-adjacent tooling. No change to test logic.

**Gate (B3):**
- `pytest engine/ -q -n 6 -p no:cacheprovider` green (0 failed, 0 collection errors).
- `pytest engine/strict_tests -q -p no:cacheprovider` green.
- Provenance fields present on all scientific routes (contract test).
- Benchmark note reproducible by a second engineer (or claim downgraded).

**Exit:** registry truth = published truth; no 500 on documented scientific routes; heavy tests
sharded.

---

## Phase B4 — API contract hardening (A06/A07/A08/A11)

**Entry:** G3 (B2+B3). **Scope:** `services/api_gateway/routers/**`,
`services/marketplace/**`, `services/commerce/**`, `services/tourism/**`,
`services/tasmimyar/**`, `services/knowledge/**`, `services/village/**`,
`services/rangeland/**`.

**Tasks**
1. Sync (KN-28): either implement server side of `/sync/*` (status/pending/trigger/merge with
   real server state) or remove the routes honestly. Default: remove unless a backend consumer
   needs offline sync (D-12). Record decision.
2. Tasmimyar (KN-29): mount `POST /api/tasmimyar/advice` under `/api/v1` (or document the
   unversioned prefix as intentional); add tests.
3. Marketplace (KN-21): per-seller scoping on `GET /api/v1/marketplace/stats`; document
   `/opportunities` village search as public-by-design.
4. Marketplace hierarchy (CAPABILITY_MATRIX): define contract marketplace→bazaar→shop→product
   with separate states for seller membership/verification/brand usage/legal trademark/product
   certification (eco.md §6); state test per distinction. (No frontend; OpenAPI shape only.)
5. Tourism (P8): resolve KN-01 fully (no `requires_setup` ever); entity decision 3 vs 9
   recorded with scope test; capacity/cancellation/refund/complaint tests; booking→payment→
   refund E2E through finance contract.
6. Village/rangeland (P7): access tiers (migration routes, water sources, sacred sites,
   ownership) default private; versioned charter; working group with decision history; sensitive
   data never leaked in public endpoints.
7. Compliance (P9): registry + workflow (classify→jurisdiction→requirements→documents→
   verification→status); expiry review; no "fully compliant" claim without assessment record;
   pilot jurisdiction data seeds load (D-03 gated).
8. Knowledge/Daneshyar (P11): programs/courses/groups/enrollment; content ownership +
   publication rights; decision support explainability (goal, inputs, criteria, scenarios,
   assumptions, uncertainty, limits, version, accountable decision-maker); advice never
   auto-applied; Eco Coin hook only after D-04.
9. LMS (KN-29): 503-ready stays; if env vars are provisioned, document in runbook.
10. Nojin data (DEPENDENCY_MAP §6): provision `MATERIALS` registry + `NojinMaterial`/
    `NojinRecipe`/`NojinSoilType` from an authoritative source — no fabrication; currently
    empty `{}`. Or honestly disable the catalog endpoints.

**Gate (B4):**
- All listed endpoints return documented shapes (OpenAPI) with contract tests.
- No 500 on documented routes; no fabricated success payloads.
- `app.openapi()` boots; route count recorded (no pin, but delta documented).
- Commerce + marketplace + tourism + village suites green.

**Exit:** every public endpoint is either implemented+tested or honestly disabled (503/feature
flag) with an error code; no stub returns success-shaped data.

---

## Phase B5 — Test coverage expansion (A14)

**Entry:** G4 (B4). **Scope:** `services/**/tests/**`, `engine/tests/**`,
`engine/strict_tests/**`, `tests/**`.

**Tasks**
1. Add a `tests/` package (or a shared `tests/test_<domain>.py`) to the 39 untested domains:
   priority order: `backup, legal, rangeland, mrv, privacy, provenance, security, auth_legacy,
   backup, ecosystem, wallet, reliability, observability, quality, quality_assurance, audit,
   dispute_resolution, logistics, organization, field_monitoring, mobile_monitoring, science,
   integration, content, models, data, data_sources, design_engine, ogc, oracle, supabase,
   workers, territory, alerting, analytics` (the list from the shortcomings report).
   Each domain gets at least: import smoke, one happy path, one authz-negative path where
   applicable.
2. Cross-tenant negative matrix (P3): user↔user, shop↔shop, village↔village,
   seller↔other-seller ledger; each test fails if the scope guard is removed (detox).
3. Money detox (P14): revert each authz/money guard → a test fails; duplicate-webhook,
   retry, refund, rounding at cent level; ledger reconciliation pairwise diff.
4. Scientific detox: units, provenance, reproducibility; revert provenance → test fails.
5. Heavy RAG/torch shard (KN-15): separate CI job with `-n 2` (or single process) +
   timeout; document memory requirement.
6. Collection stability: BOM scan + `__init__.py` presence added to CI (a pre-commit/CI
   check) so regressions fail fast.
7. Lint ratchet: reduce ruff further toward 0 on touched files; update baseline.
8. Property-based money tests: extend the 73 existing tests to new settlement paths.

**Gate (B5):**
- Every service domain has ≥ 1 test file (or an explicit "no test, reason" entry in
  `CAPABILITY_MATRIX.md`).
- Cross-tenant matrix + money detox green.
- `pytest services/ -q -n 6 -p no:cacheprovider` green (0 failed, 0 collection errors).
- `pytest engine/ -q -n 6 -p no:cacheprovider` green.
- `pytest engine/strict_tests -q -p no:cacheprovider` green.

**Exit:** coverage breadth ≥ 90% of service domains; detox evidence recorded.

---

## Phase B6 — Infrastructure, observability & operations (A13/A15)

**Entry:** G4 (B5 prep may start in parallel). **Scope:** `tools/**`, `.github/workflows/**`,
`runtime/**`, `database/hub.py`, `services/observability/**`, `docs/RELEASE-RUNBOOK.md`.

**Tasks**
1. SQLite upgrade plan (D-16): CI installs SQLite ≥ 3.51.3 (or documents the system
   requirement); `sqlite_wal_deployment_safe()` gate enforced at startup in WAL mode;
   runbook step added.
2. Backup/restore drill (D-17): scheduled job + evidence; RPO/RTO documented.
3. Observability: enable OTel tracing when `OTLP_ENDPOINT` is set (config-gated, default off);
   structured logs already present; health checks `/health`, `/ready`; Prometheus `/metrics`
   auth-gated (SEC-14).
4. Heavy compute isolation: engine jobs through a worker queue (feeds D-15); request path
   stays fast; document queue monitoring.
5. CI gates (backend-only): import guard, service boundaries, ruff baseline ratchet, mypy
   engine, security scan (HIGH blocking), collection stability (BOM + `__init__.py`),
   Alembic `upgrade head --sql` render, app boot. Remove any leftover frontend job references.
6. Performance baseline (P13): p95 per critical route, DB query counts, index review; record
   numbers; fix top offenders with measured justification. No speculative optimization.
7. Runtime supervisor (DP-2, no Docker): document single-deployable + staged rollout
   (dev→CI→staging→E2E→migration dry-run→backup/restore drill→limited pilot→monitoring→
   gradual rollout→post-release review) in `docs/RELEASE-RUNBOOK.md`.
8. Alembic discipline: every revision idempotent + `--sql` proof + rollback note; `alembic
   upgrade head` on scratch DB in CI.
9. Environment template: keep `.env.example` accurate; document all operational knobs
   (`HYDROMA_*`, `BANK_WEBHOOK_SECRET`, `SECRET_KEY`).

**Gate (B6):**
- CI pipeline green on a committed tree (backend jobs only).
- Backup/restore drill evidenced.
- Performance report vs targets recorded.
- App boots under the documented env; `/health` and `/ready` return 200.

**Exit:** reproducible, recoverable deploy; monitoring + alerting documented; no frontend job
in CI.

---

## Phase B7 — Independent acceptance & release (A14/A15, backend-only)

**Entry:** G5 (B5+B6+decisions). **Scope:** test plans & reports only — the implementer of a
capability is not its auditor.

**Tasks**
1. Sweep per eco.md §14 (backend scope only): security (authz, injection, uploads,
   rate-limit, secrets, audit), money (replay, webhooks, refunds, rounding, reconciliation),
   scientific (units, provenance, reproducibility), legal (credential expiry, brand,
   complaints), data (migrations, backstops, restore).
2. Detox: revert each authz/money/provenance guard → a test fails (evidence recorded).
3. E2E journeys (API-level, no browser): register→login→order→payment webhook→settlement;
   village onboarding→charter→decision; tourism booking→refund; compliance classify→assess.
4. Acceptance report: every critical finding has severity + owner + fix phase; zero
   unresolved criticals.
5. Release runbook execution (B6) on staging: migration dry-run, restore drill, rollback
   documented.
6. Post-release review template.

**Gate (B7):**
- Acceptance report signed (backend scope).
- Zero unresolved critical findings.
- Release reproducible + recoverable; rollback documented.
- MVP-1 released (backend + DB + infra), MVP-2/3 scheduled.

**Exit:** backend product releasable; frontend explicitly deferred to a future decision row
(D-18) — not part of this release.

---

## 2. Open decisions that must close before/within phases

| Decision | Needed by | Phase | Notes |
|---|---|---|---|
| D-04 (Eco Coin nature) | B2 | B2 | migrate vs. remove; freeze stays until closed |
| D-06 (NATS) | B4 | B4 | optional extra; outbox remains durability |
| D-07 (payment providers) | B4 | B4 | webhook+idempotency contract stays |
| D-03 (pilot jurisdiction) | B4 | B4 | compliance seeds |
| D-13 (model release bar) | B3 | B3 | publish only `validated` |
| D-14 (local brand/village validation) | B4 | B4 | |
| D-15 (hosting) | B6/B7 | B7 | monolith + staged rollout |
| D-16 (WAL/SQLite) | B6 | B6 | upgrade before WAL |
| D-17 (backup RPO/RTO) | B2/B6 | B2 | drill evidence |
| D-18 (frontend) | — | **out of scope** | not resumed here |

Decisions never closed by agents — only by named approvers with reason + date + consequences.

---

## 3. File-ownership map (anti-collision, backend-only)

| Owner | Exclusive write scope | Never touches |
|---|---|---|
| A01 | hygiene (B0): BOM, F821, `__init__.py`, dispatcher split, ruff baseline | business logic |
| A03 | `services/api_gateway/**`, `services/auth/**`, `services/security/**`, `services/backup/**`, `services/business_modules/iot/**`, `voice/**` (B1) | DB models |
| A04 | `database/models.py`, `database/hub.py`, `alembic/**` (B2) | services business logic |
| A05 | `services/finance/**`, `services/wallet/**`, `services/ledger/**`, `services/ecosystem/**` | marketplace, tourism |
| A06 | `services/marketplace/**`, `services/commerce/**` (B4) | finance internals |
| A07 | `services/api_gateway/routers/nojin.py`, `services/nojin/**`, `services/rangeland/**`, `services/village/**`, `services/territory/**` (B4) | finance internals |
| A08 | `services/api_gateway/routers/dashboard.py` (public endpoints), `services/tourism/**` (B4) | finance internals |
| A09 | `services/legal/**`, `services/compliance/**` (B4) | finance internals |
| A10 | `engine/**` (B3) | services, DB models |
| A11 | `services/knowledge/**`, `services/tasmimyar/**` (B4) | engine internals |
| A13 | infra/tooling/CI (B6) | feature code |
| A14 | test plans & acceptance (B5/B7) | feature code |
| A15 | release tooling (B7) | feature code |

---

## 4. Dependency graph (backend-only)

```
B0 (hygiene) ──► B1 (security) ──► B2 (data) ──┬──► B3 (engine)  ──┐
                                                ├──► B4 (API)      ──┼──► B5 (tests) ──► B7 (release)
                                                └──► B6 (infra)   ──┘
B5 + B6 + (D-04/D-07/D-13/D-15/D-16/D-17 closed) ──► B7
```

Parallel-safe after B2: **B3 ∥ B4** (engine vs services, disjoint trees).  
Serial-required: B0 before everything; B1 before B2 (security on auth/db paths); B2 before B3/B4 where
schema is touched; B5 after B4 (stable routes); B7 after B5+B6+decisions.

---

## 5. Tracker (integrator-maintained)

| Phase | Wave | Owner | Status | Gate evidence |
|---|---|---|---|---|
| B0 hygiene | W0 | A01 | planned | collection 0 errors; ruff ≤ 769; guard 0; mypy 0; boot; ceilings green |
| B1 security | W1 | A03/A04 | planned | security suites green; check_security 0 HIGH; route audit; ruff ≤ baseline |
| B2 data | W2 | A04 | planned | alembic sql renders; single head; scratch apply; restore drill; inventory/marketplace/village green |
| B3 engine | W3 | A10 | planned | engine+strict green; provenance on routes; benchmark or downgrade |
| B4 API | W4 | A06/A07/A08/A09/A11 | planned | contract tests; no 500/fabrication; commerce/marketplace/tourism/village green |
| B5 tests | W5 | A14 | planned | ≥90% domains tested; cross-tenant + money detox green; both big suites green |
| B6 infra | W6 | A13 | planned | CI green (backend-only); restore drill; perf report; health/ready 200 |
| B7 release | W7 | A14/A15 | planned | acceptance signed; zero unresolved criticals; reproducible deploy |

---

## 6. Success criteria (backend-only product)

The program is complete when ALL of the following hold on a committed tree:

1. `pytest services/ engine/ --collect-only -q` → 0 errors.
2. `pytest services/ -q -n 6 -p no:cacheprovider` → 0 failed.
3. `pytest engine/ -q -n 6 -p no:cacheprovider` → 0 failed.
4. `pytest engine/strict_tests -q -p no:cacheprovider` → 0 failed.
5. `ruff check .` ≤ recorded baseline (target 0 on touched files).
6. `mypy engine --ignore-missing-imports` → 0 errors.
7. `tools/detect_imports.py --root .` → 0 violations.
8. `tools/check_service_boundaries.py` → 0 stale.
9. `tools/check_security.py` → 0 HIGH findings (blocking in CI).
10. `alembic upgrade head --sql` renders; `alembic heads` single; scratch-DB apply green.
11. `from services.api_gateway.main import app; app.openapi()` boots; every public route is
    implemented+tested or honestly disabled (503/feature flag) — no fabricated success.
12. Provenance fields present on every scientific payload; only `validated` models published
    (D-13).
13. Money: single source of truth (finance journal), shared user key, reconciliation green,
    detox evidence recorded.
14. ≥ 90% of service domains have tests; cross-tenant + money + scientific detox green.
15. Backup/restore drill evidenced; SQLite WAL gate enforced; OTel config-gated.
16. **No frontend dependency anywhere in CI or runtime** (D-01 stays closed; D-18 not resumed).

---

## 7. What this plan deliberately does NOT do

- Does **not** create, restore, or depend on any frontend tree (D-01 closed, D-18 out of scope).
- Does **not** change the import-guard policy or money contract without a recorded decision.
- Does **not** close any open decision — only the named approver does, with reason + date.
- Does **not** claim a capability from the existence of a file (honesty contract, eco.md P-01).

---

*This plan is a backend/database/infrastructure remediation program. It supersedes nothing; it
complements `PHASE_PLAN.md` and `SECURITY-REMEDIATION-PLAN.md` by re-scoping them to backend-only
and adding the hygiene (B0) and coverage (B5) phases needed to close the shortcomings in
`reports/PROJECT-SHORTCOMINGS-2026-10-18.md`.*
