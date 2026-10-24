# SECURITY REMEDIATION PLAN — executable program

* **Status:** Active · **Opened:** 2026-10-12 · **Companion to:** `PHASE_PLAN.md` (this plan
  supersedes nothing; it schedules the security findings of the 2026-10-12 vulnerability audit and
  runs under the same execution contract). **Source audit:** the findings table in §2 (verified
  against the live tree on 2026-10-12; every file:line re-checked by hand or by a sub-agent).
* **Inputs (required reading for every agent):** `BASELINE.md`, `KNOWN_ISSUES.md`,
  `OPEN_DECISIONS.md`, `DEPENDENCY_MAP.md`, `PHASE_PLAN.md`, `AGENTS.md`, and this file.
* **Rule (same as PHASE_PLAN §1):** a work item is *done* only when its gate commands pass on a
  committed tree. Self-reported completion is a request, not a status. No issue is closed by
  deleting or weakening a test — closure requires evidence (command + output).

## 1. Execution contract (inherited, restated because it bites)

1. Env in every shell: `$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"`; `$env:SECRET_KEY="test-secret-key"`;
   interpreter `& "D:\eco_nojin\.venv\Scripts\python.exe"` (bare `python` is not on PATH).
2. **One test suite per shell.** `pytest services/ -n 6` and `pytest engine/ -n 6` never run
   concurrently (kills xdist). Always `-p no:cacheprovider`. Heavy RAG tests stay in their own shard.
3. No new schema change without a **guarded/idempotent Alembic revision** + `upgrade head --sql`
   proof + rollback note in the docstring. (SEC-02 needs one.)
4. Every fix carries a **negative regression test that fails if the fix is reverted** (detox); the
   test names the finding id (e.g. `test_sec01_role_not_self_assignable`).
5. Route-count pin stays **113** unless a phase deliberately changes it and records the delta.
6. Lint must not grow past the committed baseline (769). `mypy engine --ignore-missing-imports`
   stays 0. `tools/detect_imports.py --root .` stays 0. App still boots (`app.openapi()`).
7. Money stays `Decimal`; nothing in this plan touches settlement math.
8. Secrets: never printed, never committed; `.env` stays git-ignored (verified 2026-10-12:
   `git ls-files -- .env` empty, no history entry).

## 2. Findings → work items

Severity from the audit; every citation was re-verified against the live tree on 2026-10-12.

| ID | Sev | Finding | Evidence (file:line) | Work item |
|---|---|---|---|---|
| SEC-01 | **CRIT** | Registration on `services/auth/main.py` accepts a client-supplied `role`; the user row commits **before** token minting crashes on non-existent settings fields (`jwt_secret_key`, `jwt_access_token_minutes`), so an `admin` account survives the 500 and can then log in through the working gateway router | `services/auth/main.py:55,135-147`; `services/auth/compat.py:32-33`; `runtime/services.yaml:33` | S0 |
| SEC-02 | **CRIT** | No account lockout / rate limit on the login path that is actually mounted (`AuthService` lockout binds to the unmounted `AuthUser` model; gateway `AuthRateLimitMiddleware` covers only the gateway's own `/api/v1/auth/*` paths) | `services/auth/main.py:150-160`; `services/auth/service.py:47-55` | S0 |
| SEC-03 | **HIGH** | IoT cross-tenant read + IDOR: `list_devices` ignores its `user_id` argument; `platform_id` comes from the `X-Tenant-Id`/`X-Platform-Id` header; device mutations have no ownership check | `services/business_modules/iot/device_manager.py:105-148`; `routers/iot_devices.py:51,60,97,210-212` | S0 |
| SEC-04 | **HIGH** | SSRF + unauth info disclosure: `POST /api/v1/security/anti-phishing` fetches an arbitrary URL server-side (`urllib`, `file://` included); `/security/status` and `/security/events` are unauthenticated | `routers/security_router.py:243-255,126,258`; `services/security/anti_phishing.py:92-97` | S1-A |
| SEC-05 | **HIGH** | Unauthenticated cost/compute endpoints: `voice` tts/stt/ask/ivr-call/ivr-sms (real Twilio calls when credentials exist), `mrv` (8 POSTs), `sync/trigger`, `insurance`, `science`; the Twilio DTMF webhook validates no signature and builds TwiML without escaping | `routers/voice.py:128-248,390-422`; `business_modules/voice/twilio_ivr.py:51-53` | S1-B |
| SEC-06 | **HIGH (latent)** | Backup router: 16 endpoints, zero authz, unvalidated `storage_path` → arbitrary file write; restore overwrites the live DB. **Not mounted today** — one `include_router` activates it | `services/backup/router.py:49-254`; `schemas.py:55,98`; `service.py:523-529,715` | S1-C |
| SEC-07 | **HIGH** | JWTs accepted as URL query parameters (logs, history, `Referer`) | `routers/supabase_proxy.py:197,227,248,276,294,311`; `routers/auth_supabase.py:450` | S2 |
| SEC-08 | **HIGH** | Frontend supply chain: every lockfile `resolved` points at `registry.npmmirror.com`; GitHub Actions unpinned (mutable tags); production source maps on; `npm ci --no-audit`; bundle audit not wired into CI | `frontend/package-lock.json`; `.github/workflows/ci.yml:66-67,212-236`; `frontend/vite.config.ts:161` | S2 |
| SEC-09 | MED | DB credentials leak into `pg_dump`/`pg_restore` argv despite the in-code comment | `services/backup/service.py:591-596,734-735` | S1-C |
| SEC-10 | MED | WAL is installed on a WAL-reset–buggy SQLite (runtime 3.49.1 < 3.51.3): detected, logged, still fail-open | `database/hub.py:113,496-505` | S1-C |
| SEC-11 | MED | No `0600` file mode and no encryption-at-rest for SQLite stores; snapshots are plaintext | `adapters/persistence/sqlite_persistence.py:410-414`; `database/config.py` | S1-C |
| SEC-12 | MED | `prune_workspace.py` deletes **tracked** working-tree files (no git guard); `cleanup.py`'s tracked-file guard fails open on any git error | `tools/prune_workspace.py:197-214` (call site 250); `tools/cleanup.py:71-79` | S1-C |
| SEC-13 | MED | CSRF exemption list covers state-changing auth routes (`refresh`, `logout`, `reset-password`); `samesite=lax` does not block cross-site POST | `services/security/csrf.py:33-56` | S3-A |
| SEC-14 | MED | No CSP header is sent at all; `/metrics` is unauthenticated | `services/api_gateway/security.py:213-224`; `services/api_gateway/main.py:330` | S1-A |
| SEC-15 | MED | CORS `allow_headers` omits `X-TOTP-Code`, `X-Step-Up-Token`, `x-csrf-token`, `Idempotency-Key`, `X-API-Key` — credentialed browser clients cannot send them | `services/api_gateway/main.py:388` | S3-A |
| SEC-16 | MED | Email/username enumeration on register+login, plus a timing oracle (bcrypt skipped for unknown users); reset token leaked in dev default | `routers/auth.py:220-221,300-304`; `services/auth_legacy/service.py:139-141` | S3-B |
| SEC-17 | MED | 2FA toggle needs no TOTP code; no route ever provisions `two_factor_secret` (`generate_totp_secret` has zero callers) ⇒ the MFA gate reduces to a self-granted flag | `routers/auth.py:574-583`; `services/two_factor.py:15-17`; `api_gateway/auth.py:307-324` | S3-B |
| SEC-18 | MED | JWT decode pins no `aud`/`iss`/required claims; refresh/step-up separation is hand-written only | `services/api_gateway/auth.py:108-135`; `services/auth/main.py:94` | S3-A |
| SEC-19 | MED | Step-up proofs replay across workers (in-process JTI set); `verify_step_up` checks `auth_time` but not the proof's own `exp` | `services/security/step_up.py:96-116,213,220-228` | S3-A |
| SEC-20 | MED | Rate limiting is per-process (single-worker assumption undocumented); XFF takes the leftmost hop from any trusted proxy | `middleware/rate_limit.py:118-177`; `services/api_gateway/security.py:96-120` | S3-A |
| SEC-21 | MED | Standalone service entrypoints bind `0.0.0.0` | `services/auth/main.py:178`; `services/ledger/main.py:171`; `services/workflow/main.py:216` | S3-B |
| SEC-22 | MED | `security_legacy.py` is unimported dead code carrying the exact zadd-collision bug that `security.py` fixed | `services/api_gateway/security_legacy.py:148` | S3-A |
| SEC-23 | MED | Password policy: min-length 8 only, no complexity/breach check on the live path; bcrypt rounds unpinned; `auth_supabase` allows 6 | `routers/auth.py:59`; `api_gateway/auth.py:79`; `auth_supabase.py:90` | S3-B |
| SEC-24 | MED | Demo credentials in source; `eco_nojin_allow_seed` defaults to allow | `services/auth_legacy/service.py:119-125`; `engine/hydroma/config/settings.py:439` | S3-B |
| SEC-25 | MED | Passkey `RP_ID`/`ORIGIN` hardcoded to localhost despite the settings fields and production rules | `routers/passkey_router.py:34-35`; `engine/hydroma/config/rules.py:456-465` | S3-B |
| SEC-26 | MED | Logout does not revoke access tokens; `revoke_all_sessions` reads an attribute nothing ever sets | `routers/auth.py:418-431,619-626` | S3-B |
| SEC-27 | MED | API-key comparison is not constant-time (the codebase already has `compare_digest` elsewhere) | `api_gateway/auth.py:378`; `services/auth/main.py:122` | S3-A (auth.py) / S0 (auth/main.py) |
| SEC-28 | LOW | WAF false-positive rules (`sqli-comment` weight 15) and trivially bypassed scanner-UA blocklist; anti-bot challenge store is per-process | `services/security/waf.py:19`; `middleware.py:117-122` | S1-A |
| SEC-29 | LOW | `.env` holds live-format dev secrets on disk (git-ignored, never committed); no secret-scanning gate in CI | `.env:21-22`; `.gitignore:5-7` | S4 |
| SEC-30 | LOW | Docs surface: `/docs`, `/openapi.json`, `/redoc`, `/debug/routes` (flag) are public; honeypot exempts them by design | `services/api_gateway/main.py:743-928` | S4 (document; gate by network policy) |
| SEC-31 | **process** | CI does not run `tools/check_security.py`, `tools/detect_imports.py` as gates, `npm audit`, or the bundle audit; no regression/detox harness for the fixes above | `.github/workflows/ci.yml` | S4 |
| SEC-32 | **process** | No external penetration test on the public surface before release; KN rows for SEC-01…SEC-30 not yet recorded | `docs/project/KNOWN_ISSUES.md` | S4 |

## 3. Wave schedule

| Wave | Work items | Parallel? | Entry gate |
|---|---|---|---|
| **W-S0** | S0 (SEC-01, SEC-02, SEC-03) | **serial — blocks everything** | this plan accepted |
| **W-S1** | S1-A ∥ S1-B ∥ S1-C (SEC-04, 05, 06, 09–12, 14, 28) | three agents, disjoint file trees (§4) | G-S0 |
| **W-S2** | S2 (SEC-07, SEC-08) | one agent (`frontend/**`, `.github/**`, `tools/frontend_bundle_audit.*`) | G-S0 |
| **W-S3** | S3-A ∥ S3-B (SEC-13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27) | two agents, disjoint trees | G-S0 (S1/S2 may still run) |
| **W-S4** | S4 (SEC-29…SEC-32) | integrator + QA agent | G-S1 ∧ G-S2 ∧ G-S3 |

## 4. Phase cards

### S0 — Privilege escalation & tenant isolation (owner: A-S0, serial)

* **Entry:** this plan accepted. **Scope:** `services/auth/main.py`, `services/auth/service.py`,
  `services/auth/schemas.py`, `services/api_gateway/routers/auth.py`,
  `services/api_gateway/routers/iot_devices.py`, `services/business_modules/iot/device_manager.py`,
  `database/models.py` (one column), one new guarded Alembic revision, new tests.
* **Tasks**
  1. **SEC-01:** remove `role` from `UserCreate` (accept only the self-assignable default) or
     validate it against `ALLOWED_ROLES`/`settings`; mint the token **before** committing the user
     row, or fix the field names to `jwt_signing_key` / `access_token_expire_minutes` so the path
     works. Regression test: `POST /register` with `role="admin"` must not create an admin
     (assert the row's role, not just the status code).
  2. **SEC-02:** add `failed_login_attempts` + `locked_until` to `User` (guarded, idempotent,
     backfill-safe revision) and enforce lockout on **both** the gateway login path and
     `services/auth/main.py`; wire the existing `AuthService` lockout or port it. Keep the
     per-IP `AuthRateLimitMiddleware`; the lockout is per-account.
  3. **SEC-03:** derive `platform_id` from the token (`get_current_user_with_tenant` /
     `request.state.tenant_id`), never from headers; add `AND user_id = :caller` to
     `list_devices`; add ownership checks to `update_device_status` / `deregister`.
  4. **SEC-27 (auth/main.py half):** `hmac.compare_digest` for the API-key comparison.
  5. Add tests: role-escalation negative, lockout after N failures, cross-tenant device read
     (must fail if the scope guard is removed — detox).
* **Gate:** `pytest services/auth/tests services/api_gateway/tests -q -n 4 -p no:cacheprovider`
  green; `alembic upgrade head --sql` renders and applies on a scratch DB; `ruff check .` ≤ 769;
  `mypy engine --ignore-missing-imports` = 0; `detect_imports` = 0; app boots with 113 routes.
  **Exit:** no privilege is obtainable from a request body or header; lockout enforced on every
  mounted login path.

### S1-A — Security service surface (owner: A-S1a)

* **Entry:** G-S0. **Scope:** `services/security/**` (except `csrf.py`, `step_up.py` and
  `services/security/rate_limit.py` — S3-A owns those), `services/api_gateway/routers/security_router.py`.
* **Tasks**
  1. **SEC-04:** in `anti-phishing`, allow only `https`, resolve the host and reject
     private/loopback/link-local/multicast ranges, cap redirects (or disable), cap response size,
     and require an admin dependency on all three `/security/*` routes. Keep the honest
     `requires_network` response shape.
  2. **SEC-14:** add a real CSP header to the mounted `SecurityHeadersMiddleware` (report-only
     first if the frontend needs a baseline) and gate `/metrics` behind an auth dependency or a
     documented network policy; keep the `/security/status` self-check truthful afterwards.
  3. **SEC-28:** drop or down-weight the `sqli-comment` rule that false-positives on Persian text
     and em-dashes; document the scanner-UA rule as friction, not defence; note the per-process
     challenge store in the middleware docstring (already partly done).
* **Gate:** SSRF regression tests (private IP, `file://`, redirect, DNS-rebinding-ish host),
  CSP present on responses (test asserts the header), `/metrics` 401/403 unauthenticated;
  `pytest services/security/tests services/api_gateway/tests -q -n 4`; ruff/mypy/guard unchanged;
  113 routes. **Exit:** the security endpoints are no longer an attack surface of their own.

### S1-B — Unauthenticated cost & compute endpoints (owner: A-S1b)

* **Entry:** G-S0. **Scope:** `services/api_gateway/routers/voice.py`, `routers/mrv.py`,
  `routers/sync.py`, `routers/insurance.py`, `routers/science.py`,
  `services/business_modules/voice/**`, `services/business_modules/ussd/**`.
* **Tasks**
  1. **SEC-05:** require auth (or `require_api_key` where the telco aggregator is the caller) on
     every endpoint that spends money or heavy CPU: `voice/tts`, `voice/stt`, `voice/ask`,
     `voice/ivr/call`, `voice/ivr/sms`, `sync/trigger`; leave the stateless read/compute
     catalogues public by design but document them. Validate the Twilio webhook signature
     (`X-Twilio-Signature` HMAC over the raw body + auth token) and escape TwiML content.
  2. Add per-route rate limits where the global limiter is too coarse (configuration, not code
     constants, wherever the repo already reads env).
  3. Tests: unauthenticated call → 401/403; forged Twilio webhook → 401; TwiML escaping test.
* **Gate:** targeted router suites green; route behaviour tests pin the new status codes;
  ruff/mypy/guard unchanged; 113 routes. **Exit:** no unauthenticated request can cost money or
  unbounded CPU.

### S1-C — Backup, persistence & tooling safety (owner: A-S1c)

* **Entry:** G-S0. **Scope:** `services/backup/**`, `database/hub.py`, `database/config.py`,
  `adapters/persistence/sqlite_persistence.py`, `tools/prune_workspace.py`, `tools/cleanup.py`.
* **Tasks**
  1. **SEC-06:** add an admin role dependency to every backup route, confine `storage_path` to an
     allowlisted base directory, and put restore behind an explicit typed confirmation. Add a
     **guard test asserting the backup router is not mounted** on the gateway app (it is not
     today) so an accidental mount fails CI.
  2. **SEC-09:** pass discrete connection parameters + `PGPASSWORD` to `pg_dump`/`pg_restore`;
     never embed the URL with credentials in argv.
  3. **SEC-10:** make the WAL gate fail-closed — refuse WAL (or abort startup) when
     `sqlite_wal_deployment_safe()` is false on a file engine, instead of logging and continuing;
     keep the in-memory/no-op path. Record the decision in `KNOWN_ISSUES.md` (KN-09 family).
  4. **SEC-11:** create SQLite files with mode `0600`; document the encryption-at-rest option
     (SQLCipher/FS) as an open decision (**D-SEC-03**) — do not implement it unilaterally.
  5. **SEC-12:** gate `prune_workspace.py` deletions on the `git ls-files` set (report-and-skip
     tracked files, like `cleanup.py`); make `cleanup.py`'s tracked-file lookup **fail closed**
     (abort when git fails) and confine `--paths` under ROOT.
* **Gate:** backup authz tests (non-admin → 403; path escape → 400); WAL refusal test on a
  simulated old SQLite (monkeypatched version tuple); prune/cleanup tests with a tracked fixture
  file; `pytest tests/test_sqlite_wal_gate.py tests/test_p14_guard_sweep.py tools/tests -q -n 4`;
  alembic untouched (no schema change here); ruff/mypy/guard unchanged. **Exit:** the data plane
  cannot be written, wiped, or leaked through its own tooling.

### S2 — Frontend & CI supply chain (owner: A-S2)

* **Entry:** G-S0. **Scope:** `frontend/**`, `.github/workflows/**`, `tools/frontend_bundle_audit.*`.
* **Tasks**
  1. **SEC-07:** stop accepting JWTs from query strings in `supabase_proxy` / `auth_supabase`
     (header or `__Host-` cookie only); add tests that a `?token=` request is rejected.
  2. **SEC-08:** regenerate `package-lock.json` from the official npm registry (verify a sample of
     `resolved` URLs afterwards); pin every GitHub Action to a full commit SHA; disable
     production source maps (or serve them only to authenticated hosts); remove `--no-audit` and
     add a blocking `npm audit --audit-level=high`; add `npm run audit:bundle` as a CI step after
     build.
  3. Keep `tools/check_frontend_layering.py` green (cross-slice imports stay 0).
* **Gate:** `npm ci` from the official registry succeeds and `npm test` + `npm run build` pass;
  CI workflow diff reviewed; the frontend job runs the new audit steps; no route-count or backend
  change. **Exit:** the browser plane ships no token in URLs and installs from a verified registry.

### S3-A — Session, tokens & middleware hardening (owner: A-S3a)

* **Entry:** G-S0. **Scope:** `services/security/csrf.py`, `services/security/step_up.py`,
  `services/api_gateway/security.py`, `services/api_gateway/auth.py`,
  `services/api_gateway/middleware/rate_limit.py`, `services/api_gateway/middleware/identity.py`,
  `services/api_gateway/security_legacy.py` (deletion), `services/api_gateway/main.py` (CORS only).
* **Tasks**
  1. **SEC-13:** remove `/api/v1/auth/refresh`, `/logout`, `/reset-password`, `/change-password`
     from `EXEMPT_PREFIXES`; keep bearer clients exempt by design (document it).
  2. **SEC-15:** add the auth/CSRF/idempotency headers to CORS `allow_headers`.
  3. **SEC-18:** emit and require `iss`/`aud` on access tokens; decode with
     `options={"require": ["exp", "iss", "aud", "sub"]}`; keep the algorithm pin.
  4. **SEC-19:** move the consumed-JTI set to Redis when `REDIS_URL` is configured (with the
     in-memory fallback documented as single-worker-only) and verify the proof's own `exp`.
  5. **SEC-20:** document the single-worker assumption as a hard deployment constraint in
     `runtime/services.yaml` comments **or** back the buckets with Redis (decision **D-SEC-02**);
     fix XFF handling to walk from the rightmost hop.
  6. **SEC-22:** delete `security_legacy.py` after proving zero importers (grep + the import
     contract test suite).
  7. **SEC-27 (gateway half):** constant-time API-key comparison.
* **Gate:** CSRF regression tests (cross-site POST with cookies → 403 on refresh/logout); JWT
  claim tests (missing `aud` → 401; refresh token rejected at `decode_token` call sites that
  require an access token); step-up replay test with the Redis path when available;
  `pytest services/security/tests services/api_gateway/tests -q -n 4`; ruff/mypy/guard unchanged;
  boot with **113 + 1 recorded route delta** — the SEC-17 enrollment route is a deliberate
  addition under contract item 5 (record it in the delivery report, do not treat the pin as a
  failure). **Exit:** ambient-authority requests are challenge-bound and tokens are tightly
  scoped.

### S3-B — Account lifecycle & information disclosure (owner: A-S3b)

* **Entry:** G-S0. **Scope:** `services/api_gateway/routers/auth.py`,
  `services/auth_legacy/service.py`, `services/auth/schemas.py`, `services/two_factor.py`,
  `services/api_gateway/routers/passkey_router.py`, `services/api_gateway/routers/auth_supabase.py`.
* **Tasks**
  1. **SEC-16:** identical generic responses for register/login success+failure; run a bcrypt
     verify against a dummy hash when the user is unknown (kill the timing oracle); make
     forgot-password fail closed (`is_production` must be explicitly false **and** the env var
     explicitly set — never default to dev).
  2. **SEC-17:** 2FA enrollment route that provisions `two_factor_secret` (QR + recovery codes,
     codes stored hashed, constant-time compare) and a toggle that requires a valid TOTP code;
     keep the manual-DB write and the ORM flag in one transaction.
  3. **SEC-23:** shared password validator (length + complexity + breach-list check) applied at
     every schema, including `auth_supabase`; pin `bcrypt.gensalt(rounds=...)`.
  4. **SEC-24:** remove demo credentials from source (seed from env/CI secrets only) and flip
     `eco_nojin_allow_seed` default to 0.
  5. **SEC-25:** read passkey `RP_ID`/`ORIGIN` from settings at construction; fail closed when
     unset in production (the production rules already exist).
  6. **SEC-26:** revoke the access token on logout (short denylist or short TTL + forced refresh)
     and set `_request_token_jti` in `get_current_user` so `revoke_all_sessions` works.
  7. **SEC-21:** default standalone entrypoints to `127.0.0.1`.
* **Gate:** enumeration tests (same status+body for known/unknown email; timing parity),
  2FA enrollment + toggle tests, passkey origin test, logout revocation test;
  `pytest services/auth/tests services/api_gateway/tests -q -n 4`; ruff/mypy/guard unchanged;
  113 routes. **Exit:** account lifecycle discloses nothing and MFA is real.

### S4 — Verification, gates & closure (owner: integrator + A-S4 QA)

* **Entry:** G-S1 ∧ G-S2 ∧ G-S3. **Scope:** `.github/workflows/**`, `tools/check_security.py`
  wiring, `docs/project/**`, `reports/security/**` (new), test plans.
* **Tasks**
  1. **SEC-31:** add CI gates — `tools/check_security.py --fail-on HIGH` (with the
     gateway-bypass-import rule reconciled against `detect_imports.py`'s sanctioned list so the
     existing 28 "HIGH" architecture findings do not mask real ones), `detect_imports.py`,
     `npm audit`, bundle audit, and the new SEC regression tests as their own shard.
  2. **SEC-32:** add KN-30… rows to `KNOWN_ISSUES.md` (one per finding, owner phase, evidence),
     update `BASELINE.md` gates, and commission an **external penetration test** on the public
     surface (authz, injection, SSRF, rate-limit, secrets, audit — the P14 sweep scope) before any
     production release; every critical must have severity + owner + fix phase.
  3. **SEC-29:** rotate the dev secrets in `.env` (they were never committed — verified), add a
     pre-commit/CI secret scan, and document that production secrets are injected, never filed.
  4. **SEC-30:** document the docs/debug surface; gate `/docs`, `/openapi.json`, `/redoc` behind a
     network policy in production (environment/config, recorded in the release runbook).
  5. Full gates on a committed tree: `pytest services/ -q -n 6 -p no:cacheprovider` **and**
     `pytest engine/ -q -n 6 -p no:cacheprovider` (separate shells), `pytest engine/strict_tests`,
     `ruff check .`, `mypy engine --ignore-missing-imports`, `detect_imports`, `app.openapi()`,
     `alembic heads` single + `upgrade head --sql` clean.
* **Gate:** all SEC regression tests green in CI; external pentest report has no unresolved
  critical/high; the full gate block above reproduced and pasted into
  `reports/security/SECURITY-REMEDIATION-2026-10-12.md`. **Exit:** the audit findings are closed
  with evidence, or carried as KN rows with owner + due phase.

## 5. Risk & rollback (per wave)

* **S0** touches auth: deploy behind the feature flags where possible; the lockout migration is
  additive and guarded; rollback = revert the commit (the new columns are nullable/backfilled, the
  old behaviour restores). Keep the gateway router working at every commit — never land the
  `services/auth/main.py` change and a gateway change in the same commit if the gateway change
  depends on it.
* **S1-A/S1-B** only tighten status codes (401/403) and add checks: low regression risk; the
  Twilio-signature change must ship with the aggregator's signing config or their webhooks start
  failing — coordinate before merge (documented as an integration need).
* **S1-C** fail-closed WAL changes boot behaviour on file engines: test on a scratch DB first;
  the prune/cleanup guard changes are operator-tooling only.
* **S2** lockfile regeneration may move transitive versions: run the full frontend test set and
  record the diff; actions pinning is mechanical.
* **S3** CSRF/CORS tightening can break existing browser clients: land with the frontend in the
  same wave or keep a documented grace period; every status-code change is pinned by a test.
* **S4** CI gates may go red on the first day from pre-existing findings: ratchet from the
  committed baseline like the lint rule (fail on *new* findings first).

## 6. Open decisions for the approver (agents never close these)

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| D-SEC-01 | `services/auth/main.py`: fix or remove? | (a) fix fail-closed (S0 default, keeps `test_import_contracts.py` green); (b) remove from `runtime/services.yaml` + delete module + update the two referencing tests | (a) now; (b) in the auth-consolidation follow-up |
| D-SEC-02 | Redis for rate-limit buckets + step-up JTI set | (a) keep in-memory, document single-worker as a hard constraint; (b) Redis when `REDIS_URL` is set | (b) if Redis is part of the deployment; else (a) with the constraint in `runtime/services.yaml` |
| D-SEC-03 | Encryption at rest for SQLite stores | (a) `0600` + FS encryption only; (b) SQLCipher | (a) now; (b) with the D-15 Postgres pilot |
| D-SEC-04 | Mount the backup router at all | (a) never mount, keep it a library + the guard test; (b) mount with admin authz after S1-C | (a) until a real backup/restore feature is scheduled |

## 7. Tracker (integrator-maintained)

| Item | Wave | Owner | Status | Gate evidence |
|---|---|---|---|---|
| S0 privilege/isolation | W-S0 | A-S0 | **done 2026-10-12** (SEC-01/02/03) | `services/security/tests` 196 passed; alembic head `20261012_140000_sec_user_lockout` renders + guarded double-upgrade verified on scratch DB; mypy 0; guard 0 |
| S1-A security surface | W-S1 | A-S1a | **done 2026-10-12** (SEC-04/14/28) | `services/security/tests` 196 passed incl. 57 regression tests; CSP header + metrics gate verified on the live app |
| S1-B cost endpoints | W-S1 | A-S1b | **done 2026-10-13** (SEC-05) | voice/mrv/sync/science write+compute endpoints authenticated; Twilio signature + TwiML escaping tested |
| S1-C backup/persistence/tooling | W-S1 | A-S1c | **done 2026-10-13** (SEC-06/09/10/11/12) | backup router admin-gated + path-contained + confirm-gated; pg argv hygiene; WAL fail-closed; 0600 files; prune/cleanup guards — all with regression tests |
| S2 frontend/CI supply chain | W-S2 | A-S2 | **done 2026-10-13** (SEC-07/08 + SEC-31 gate) | token from Authorization header; sourcemaps dev-only; npm audit + bundle audit in CI; scanner reconciled (0 findings/1251 files) and blocking on HIGH in CI. Deferred: lockfile registry + action SHAs (need network) |
| S3-A session/tokens/middleware | W-S3 | A-S3a | **mostly done 2026-10-13** (SEC-15/18/20/22/25/26/27) | CORS headers; iss claim; XFF rightmost; legacy module deleted; passkey from settings; revoke-all excludes caller. Deferred: SEC-13 (CSRF, needs frontend wave), SEC-19 (Redis, D-SEC-02) |
| S3-B account lifecycle | W-S3 | A-S3b | **partial 2026-10-13** (SEC-24) | demo-seed credentials env-only + allow_seed default 0. Remaining: SEC-16 enumeration, SEC-17 2FA enrollment, SEC-23 password policy |
| S4 verification & closure | W-S4 | integrator | **partial 2026-10-13** (SEC-31/32) | scanner gate + regression suite in CI; KN rows + report sections. Remaining: external pentest, final full-suite run before release |
| Review addendum (15 findings R1–R15) | W-S1 | A-S1 + QA | **done 2026-10-13** | 41→57 regression tests; security 196 / gateway 320 / auth+root 76+2s green; mypy 0; guard PASS; ruff delta 0 |

*Report template per agent (PHASE_PLAN §5): summary, files, decisions taken/open, commands +
real outputs, remaining debt, risks, API/schema changes, integration needs, reproduction steps,
per-criterion status, final status ∈ {`READY_FOR_REVIEW`, `BLOCKED`, `PARTIALLY_COMPLETE`}.
Deliverables land in `reports/security/`; the integrator links this plan from `PHASE_PLAN.md` and
records the KN rows in `KNOWN_ISSUES.md` at S0 start.*
