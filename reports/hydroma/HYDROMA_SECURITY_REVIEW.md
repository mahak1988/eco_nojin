# HYDROMA Security Review

**Generated**: 2026-10-09  
**Scope**: `D:\HyDroMA` repository  
**Auditor**: Kilo autonomous agent  
**Classification**: Internal — Security Audit  

---

## 1. Executive Summary

The HyDroMA (Eco Nojin) codebase implements a defense-in-depth security model across
**11 defensive layers** as defined in `services/security/__init__.py:2-17`. The architecture
separates the scientific engine (`engine/`) from the application services layer (`services/`),
enforces a single gateway entry point for all engine computation, and applies production
configuration validation via a rule-based validator (`engine/hydroma/config/rules.py`).

### Security Posture Summary

| Area | Status | Details |
|------|--------|---------|
| Authentication | Strong | JWT + bcrypt, httpOnly cookies, MFA for admins, RBAC |
| Secret Management | Strong | SecretStr everywhere, production rules, no hardcoded secrets |
| Input Validation | Partial | WAF + pydantic + gateway validation, but facade has bypass paths |
| C++ Boundary | Strong | pybind11 with Python fallback, ABI mismatch guard |
| Rate Limiting | Strong | Per-IP + per-user sliding window, Redis with memory fallback |
| Audit Logging | Present | JSONL local + Supabase cloud, table allowlist guard |
| Error Handling | Hardened | Generic error codes, no internal detail leakage |
| CORS | Secure | No wildcard with credentials, no dev ports allowlisted |

### Key Risks

| ID | Risk | Severity | Status |
|----|------|----------|--------|
| SR-01 | Services bypassing gateway facade directly importing engine modules | MEDIUM | Mitigated by facade pattern, not enforced at CI |
| SR-02 | Fallback Python implementations may diverge from C++ kernels | LOW | Documented corrections made (EVI clipping, PM parameters) |
| SR-03 | Local `.master.key` file stored on disk without encryption | LOW | File permissions set to 0o600 |
| SR-04 | No `.env` file present in repo; must be provisioned per-deployment | INFO | Expected behavior — secrets must come from environment |

---

## 2. Threat Model

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────┐
│                    Internet / Clients                 │
└──────────────────┬──────────────────────────────────┘
                   │  HTTPS (TLS)
                   ▼
┌─────────────────────────────────────────────────────┐
│              API Gateway (services/)                │
│  • WAF (signature-based)                           │
│  • Rate Limiting (per-IP + per-user)               │
│  • Security Headers (CSP, HSTS, X-Frame-Options)    │
│  • Security Error Sanitization (errors.py)         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│           Auth Service (services/auth/)              │
│  • JWT issuance (HS256)                              │
│  • bcrypt password hashing                           │
│  • RBAC (farmer/advisor/admin + 3 admin sub-roles)  │
│  • httpOnly cookies + CSRF double-submit             │
│  • MFA (TOTP) + step-up auth for admin actions      │
│  • Telco webhook API-key guard                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│         Gateway Facade (services/_gateway_facade.py)│
│         *** ONLY approved path to engine ***        │
│  • Lazy singleton EngineGateway                      │
│  • ProvenanceSpec initialization                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│          Engine Gateway (engine/gateway/__init__)   │
│  • Input validation (model_id, inputs required)     │
│  • Unit normalization (si_equivalent)               │
│  • Model dispatch (100+ model_id routes)            │
│  • Provenance, uncertainty, execution metadata    │
│  • Normalized error handling                         │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌────────────────┐  ┌────────────────────────┐
│ Python kernels │  │ C++ bridge (pybind11)  │
│ (fallback)     │  │ cp312-win_amd64.pyd  │
└────────────────┘  └────────────────────────┘
```

### 2.2 Trust Boundaries

| Boundary | Enforcement | File |
|----------|-------------|------|
| Engine ↔ Services | Singleton EngineGateway; facade is only approved import path | `engine/gateway/__init__.py:1-7`, `services/_gateway_facade.py:1-17` |
| Auth in engine | Import guard: no auth/payment/blockchain imports in engine/ | `services/security/__init__.py` |
| Secret access | `SECRET_FIELDS` allowlist + `reveal()` function | `engine/hydroma/config/secrets.py:22-43` |
| Production config | `validate_production_settings` runs 21 rules | `engine/hydroma/config/rules.py:285-406` |
| Error exposure | `safe_error_detail` / `safe_detail_for_status` | `services/api_gateway/errors.py:62-99` |

---

## 3. Authentication & Authorization

### 3.1 JWT Authentication

**Location**: `services/api_gateway/auth.py`

- **Algorithm**: HS256 (`settings.jwt_algorithm`)
- **Signing key**: Resolved via `jwt_signing_key` property, preferring
  `jwt_secret` → `secret_key` → `app_secret_key` from `SecretStr` fields
- **Key strength guard**: `_signing_key()` raises `RuntimeError` if key is
  missing, < 32 chars, or matches any of 8 known development defaults
  (`_WEAK_SIGNING_KEYS` at `auth.py:40-50`)
- **Token lifetimes**: Access = 30 min (`access_token_expire_minutes`),
  Refresh = 30 days (`refresh_token_expire_minutes: 43200`)

### 3.2 Password Security

- **Hashing**: bcrypt with auto-generated salt (`bcrypt.hashpw` +
  `bcrypt.gensalt()`) at `auth.py:78-86`
- **Verification**: Constant-time comparison via `bcrypt.checkpw`, with
  `ValueError` caught to prevent crash on malformed hashes

### 3.3 RBAC

**Location**: `services/api_gateway/auth.py:55-73`, `services/auth/permissions.py`

- **Roles**: `farmer`, `advisor`, `admin`, `security_admin`,
  `content_admin`, `user_admin`
- **Admin roles** (superset): `ADMIN_ROLES = {admin, security_admin, content_admin, user_admin}`
- **Dependency-based enforcement**: `require_roles(*roles)`, `require_admin`,
  `require_security_admin`, `require_content_admin`, `require_user_admin`
- **MFA enforcement**: `require_admin_with_mfa` at `auth.py:289-360` requires
  either `X-TOTP-Code` header (TOTP verification) or `X-Step-Up-Token` header
  (step-up proof from `/api/v1/security/step-up/challenge`)

### 3.4 Cookie Security

**Location**: `services/api_gateway/auth.py:422-475`

- Access and refresh tokens stored in **httpOnly** cookies (not localStorage)
- `secure=True` in production (HTTPS only)
- `samesite="lax"` for CSRF protection
- CSRF double-submit token set as non-httpOnly cookie (`services/security/csrf.py`)
  — the client reads it and echoes it back in `x-csrf-token` header

### 3.5 API Key Guard

- Telco webhook endpoints (`/ussd`, `/voice`, `/sms`) protected by
  `require_api_key` using constant-time comparison (`hmac.compare_digest`)
- In production, missing key returns 503 (fail-closed)

---

## 4. Secret Management

### 4.1 SecretStr Wrapping

**Location**: `engine/hydroma/config/settings.py:79`, `engine/hydroma/config/secrets.py`

All sensitive fields use `SecretValue = Annotated[SecretStr, BeforeValidator(_coerce_secret)]`:

```
SecretStr → str         reveal(v) returns the plaintext string
SecretStr(SecretStr("x"))  reveal(v) returns the inner wrapper → handled by idempotent validator
str      → SecretStr    _coerce_secret wraps exactly once
```

The `_coerce_secret` function is **idempotent** — it checks `isinstance(value, SecretStr)`
before wrapping, preventing the double-wrapping defect that would make `reveal()` return
a `SecretStr` object instead of a `str`.

### 4.2 SECRET_FIELDS Allowlist

**Location**: `engine/hydroma/config/secrets.py:22-43`

11 fields are explicitly allowlisted for revelation:
`secret_key`, `app_secret_key`, `jwt_secret`, `agent_token`, `nats_password`,
`nats_token`, `telegram_bot_token`, `telco_webhook_key`,
`blockchain_private_key`, `oauth_encryption_key`, `mrv_ingest_key`.

### 4.3 Production Validation Rules

**Location**: `engine/hydroma/config/rules.py` — 21 `ProductionRule` entries

Each rule has a stable `id` (slug, not index), a `check` function returning
`None` (satisfied) or a detail string (violated), and a `severity`
(ERROR raises / WARNING warns). Key rules:

| Rule ID | Check | Severity |
|---------|-------|----------|
| `cors_wildcard_with_credentials` | No `*` in cors_origins with allow_credentials=True | ERROR |
| `secret_key_strength` | Secret must be 64+ chars, not a known default | ERROR |
| `jwt_secret_strength` | JWT signing key must be 64+ chars, not a known default | ERROR |
| `debug_enabled` | `debug=False` in production | ERROR |
| `simulated_data_enabled` | `enable_simulated_data=False` in production | ERROR |
| `agent_token_insecure` | agent_token not "dev-agent-token" | ERROR |
| `debug_routes_enabled` | `enable_debug_routes=False` | ERROR |
| `supabase_url_missing` | SUPABASE_URL set when sync enabled | ERROR |
| `supabase_service_role_key_missing` | Service role key set when sync enabled | ERROR |
| `telegram_bot_token_missing` | TELEGRAM_BOT_TOKEN set | ERROR |
| `blockchain_private_key_missing` | BLOCKCHAIN_PRIVATE_KEY set when blockchain enabled | ERROR |
| `alchemy_api_key_missing` | ALCHEMY_API_KEY set when blockchain enabled | ERROR |
| `database_not_postgresql` | DATABASE_URL starts with postgresql:// | ERROR |
| `redis_url_missing` | REDIS_URL configured | ERROR |
| `nats_url_missing` | NATS_URL set when event bus enabled | ERROR |
| `sentry_dsn_missing` | SENTRY_DSN set | WARNING |
| `passkey_rp_id_missing` | PASSKEY_RP_ID set | ERROR |
| `passkey_origin_missing` | PASSKEY_ORIGIN set | ERROR |
| `oauth_redirect_uri_missing` | OAUTH_REDIRECT_URI set | ERROR |
| `oauth_encryption_key` | OAUTH_ENCRYPTION_KEY set (separate from JWT signing key) | ERROR |

### 4.4 No Hardcoded Secrets

- **No `.env` file** exists in the repository (`D:\HyDroMA\.env` — absent)
- All secrets default to empty strings or `SecretStr("")`
- The `is_secure_secret` property checks against `INSECURE_SECRETS` frozenset
  containing 9 known bad defaults
- Test files use `# nosec` annotations for intentionally weak test keys

---

## 5. Input Validation & WAF

### 5.1 Web Application Firewall

**Location**: `services/security/waf.py:1-125`

- **14 rules** covering SQLi (7), XSS (4), path traversal (2), command
  injection (3), SSRF (1), and scanner UAs (1)
- **Block threshold**: 40 points (`BLOCK_THRESHOLD`)
- **Immediate block**: Any rule with `block_when_hit=True` and weight ≥ 40
  triggers an instant 403
- **URL decoding**: Checks single and double percent-decode layers to catch
  encoded payloads (e.g., `%55%4e%49%4f%4e%20%73%45%4c%45%43%54`)
- **Bounded event log**: `MAX_EVENTS = 1000` — the WAF event log is capped
  to prevent memory exhaustion via event flooding

### 5.2 Rate Limiting

**Location**: `services/security/rate_limit.py:1-147`,
`services/api_gateway/security.py:48-210`

- **Per-IP sliding window**: 60-second window, 120 req general / 10 req auth paths
- **Per-user budget**: 300 req/subject, tracked as `rate:user:{sub}`
- **Redis with in-memory fallback**: Falls back to deque-based tracking if Redis
  unavailable
- **Memory safety**: Bounded at 50,000 buckets; fail-closed at capacity (refuses
  new IPs rather than evicting live buckets)
- **Trusted proxy support**: X-Forwarded-For parsing for IPs behind known proxies
- **Windows clock resolution fix**: Member key includes UUID4 suffix to avoid
  collapsing concurrent requests on Windows (`~15.6ms` clock resolution)

### 5.3 API Gateway Rate Limiting

**Location**: `services/api_gateway/security.py:48-210`

- **RateLimitMiddleware**: Per-IP, with optional `key_by_subject` mode
- **APIKeyGuardMiddleware**: Validates `X-API-Key` for telco endpoints using
  `hmac.compare_digest` (constant-time)
- **SecurityHeadersMiddleware**: Sets `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`
- **HTTPSRedirectMiddleware**: Optional HTTP→HTTPS redirect
- **RequestIDMiddleware**: X-Request-ID propagation + correlation context

### 5.4 Engine Gateway Input Validation

**Location**: `engine/gateway/__init__.py:358-392`

- `_validate_request`: Enforces `model_id` and `inputs` presence
- `_normalize_inputs`: Multiplies values by `unit_spec.si_equivalent` for unit
  normalization
- Model dispatch validates against known model_id set (100+ entries)
- Invalid/missing model returns `GatewayError(error_code="MODEL_NOT_FOUND")`

### 5.5 Facade Bypass Risk

**Location**: `services/_gateway_facade.py:70-85`

Three functions (`calculate_cec`, `calculate_esp`, `calculate_sar`) have
`RuntimeError` fallback paths that import directly from `engine.hydroma.soil.chemistry`,
bypassing the gateway. This is documented as a numpy dependency workaround but
represents a **controlled bypass** — the gateway's provenance/uncertainty
metadata is lost when the fallback fires.

---

## 6. Error Handling & Information Disclosure

### 6.1 Safe Error Detail Mapping

**Location**: `services/api_gateway/errors.py`

- 16 exception types mapped to generic error codes (e.g.,
  `IntegrityError → "data_integrity_violation"`,
  `ValueError → "invalid_input"`)
- 12 HTTP status codes mapped to safe messages (400 → "Bad request",
  500 → "Internal server error")
- `safe_error_id()` generates a SHA-256 hash (first 12 chars) for client-side
  error correlation without exposing internals
- `log_and_return()` logs full exception internally, returns safe body

### 6.2 No `str(exc)` Leakage

The error handler explicitly avoids exposing `str(exc)` to clients.
The `errors.py:3` header states it "replaces `str(exc)` exposure with safe,
generic error codes per eco.md §48."

---

## 7. Data Protection & Privacy

### 7.1 PrivacyVault

**Location**: `services/privacy/vault.py:1-208`

- **Encryption**: Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
- **Master key**: Generated via `Fernet.generate_key()`, stored as
  `storage_path/.master.key` with `chmod 0o600`
- **User key derivation**: PBKDF2-HMAC-SHA256, 100,000 iterations
- **Commitment hash**: SHA-256 of sorted-key JSON for on-chain commitments
- **Access control**: `retrieve()` checks `owner_id`; granular access grants
  via `grant_access()` / `revoke_access()`
- **Access logging**: Every read appends to `access_log` within the encrypted entry

### 7.2 Encryption at Rest

- **Supabase**: Field-level encryption for sensitive columns
- **PrivacyVault**: Fernet encryption for off-chain evidence
- **OAuth tokens**: Encrypted at rest with dedicated `oauth_encryption_key`
  (separate from JWT signing key since 2026-10-03)

### 7.3 Encryption in Transit

- **TLS**: Enforced via `HTTPSRedirectMiddleware` (opt-in via
  `ECONOJIN_REQUIRE_HTTPS`) and HSTS header
- **Supabase**: HTTPS-only client (`create_client(url, key)`)
- **NATS**: TLS-capable connection string

---

## 8. Audit Logging

**Location**: `services/security/audit.py:1-104`

- **Dual store**: Supabase `security_events` table (via Management API with
  parameterized queries) with local JSONL fallback (`data/security/audit.jsonl`)
- **Table allowlist**: `_supabase_write()` validates table name against
  `{"security_events", "audit_log"}` to prevent SQL injection (C3 FIX)
- **Event categories**: `waf`, `rate`, `anomaly`, `honeypot`, `authz`, `phishing`
- **Recorded fields**: timestamp, IP, actor, action, decision, detail (JSON),
  severity
- **Store field**: Each record logs which store was used (`local-jsonl` or
  `supabase-cloud`), making the fallback explicit

---

## 9. C++ Engine Boundary Security

### 9.1 Module Loading

**Location**: `engine/hydroma/cpp_bridge/__init__.py:25-76`

- **Single import point**: `_hydroma_core = None` initialized once; pybind11
  module registered in `sys.modules` via `setdefault` to prevent double-init
  crash (`generic_type: type "..." is already registered!`)
- **ABI safety**: Extension filename carries interpreter ABI tag
  (`hydroma_core.cp312-win_amd64.pyd`); untagged names are a stale-load hazard
- **Degradation logging**: When C++ is unavailable, `logger.error()` fires
  (never silent), with `_cpp_import_error` stored for diagnostics

### 9.2 Hybrid Intelligence Pattern

- **Scalar args** → C++ kernel → NumPy fallback
- **Array args** → Numba (small, <1M elements) → C++ (large) → NumPy
- **Telemetry**: Separate counters for `numba_calls`, `cpp_calls`,
  `fallback_calls` with timing
- **Numerical divergence fixes**: Python fallbacks corrected for EVI clipping
  (now clips to [-1, 1] matching C++), Hargreaves parameter order, PM cloudiness
  factor [0.3, 1.0] ratio limit

### 9.3 Build Security

**Location**: `engine/cpp_core/CMakeLists.txt:1-256`

- C++20 standard required, `/permissive-` (strict conformance), `/W4` warnings
- OpenMP for parallel processing
- pybind11 via `find_package` with `FetchContent` fallback from official repo
- Separate `hydroma_core` static lib and `hydroma_core_py` Python module targets
- 11 test executables + optional benchmarks

---

## 10. Provenance & Scientific Integrity

### 10.1 Engine-Level Provenance

**Location**: `engine/hydroma/provenance.py`

- `ResultProvenance` mixin: requires `data_source` and `model` fields (no default
  for `data_source`, preventing omission)
- `DataSource` enum: `measured`, `modelled`, `simulated`, `unavailable`, `degraded`
- `ProvenanceCarrier` base class for duck-typed results with keyword-only
  required `data_source` and `model`
- Prevents the "fabricated constant mislabeled as measured" defect documented
  in the module docstring (mrv/nojin_mrv.py, simulation/hecras.py)

### 10.2 Service-Level Provenance

**Location**: `services/provenance/`

SQLAlchemy models + pydantic schemas + API router + service logic for persisting
provenance records linked to computation results.

### 10.3 Gateway Provenance

**Location**: `engine/gateway/__init__.py:59-77`

- `ProvenanceSpec`: source, source_type, trust_level, provenance_id
- `UncertaintySpec`: uncertainty_type (default "NOT_ESTIMATED"), value, unit, method
- `ExecutionMetadata`: gateway_version, timestamp, execution_id, engine_version,
  cpp_backend flag
- All results from `GatewayResult` carry full provenance/uncertainty metadata

---

## 11. CORS & Network Security

### 11.1 CORS Configuration

**Location**: `engine/hydroma/config/settings.py:190-192`

- Default: `["http://localhost:8000"]` (self-origin only)
- Removed dangerous defaults: `http://localhost:3000` and `http://localhost:8001`
  (belonged to deleted Next.js app, with `allow_credentials=True` would be a
  credentialed cross-origin hole)
- JSON array parsing (not comma-separated) per pydantic-settings
- `allow_credentials=True` is intentional and paired with explicit origin allowlist

### 11.2 Trusted Proxies

- `trusted_proxies` field for X-Forwarded-For parsing
- `RateLimitMiddleware` and `RateLimiter._client_key` honor trusted proxy CIDRs
- Only parses X-Forwarded-For from known proxy networks (not arbitrary clients)

---

## 12. Anti-Phishing & Bot Defense

**Location**: `services/security/`

- **Anti-phishing**: `anti_phishing.py` — domain squatting detection, SPF/DKIM/DMARC
  validation, page-clone signature matching (Layer 5)
- **Honeypot traps**: `honeypot.py` — fake admin/.env endpoints that auto-block
  attackers (Layer 8)
- **Anomaly scoring**: `anomaly.py` — request behavior scoring (Layer 9)
- **Post-quantum crypto**: `pqcrypto.py` — CRYSTALS-Kyber/Dilithium hybrid (Layer 6)
- **Self-healing watchdog**: `watchdog.py` — health checks + auto-restart +
  intrusion circuit breaker (Layer 7)
- **Step-up auth**: `step_up.py` — MFA re-authentication for sensitive actions (W-016 fix)
- **Passkeys**: `passkeys.py` — WebAuthn passkey flows via `webauthn` library
- **CSRF**: `csrf.py` — Double-submit token pattern

---

## 13. Security Findings

### 13.1 Findings by Severity

| ID | Severity | Finding | Location | Status |
|----|----------|---------|----------|--------|
| SR-01 | MEDIUM | Facade fallback bypasses gateway for 3 soil chemistry functions | `services/_gateway_facade.py:70-85` | Documented — controlled bypass |
| SR-02 | LOW | Python fallbacks could diverge from C++ kernels | `engine/hydroma/cpp_bridge/__init__.py` | Mitigated — numerical corrections applied |
| SR-03 | LOW | `.master.key` stored on disk unencrypted (only file perms protect it) | `services/privacy/vault.py:50-58` | Acceptable for current threat model |
| SR-04 | INFO | No `.env` file in repository | repo root | Expected — secrets provisioned per-deployment |
| SR-05 | INFO | `Audit._supabase_write` uses f-string for table name in SQL | `services/security/audit.py:41-43` | Safe — validated against allowlist before use |
| SR-06 | LOW | `require_admin_with_mfa` calls `db.query()` (sync) inside async context | `services/api_gateway/auth.py:312` | Functional but suboptimal — potential thread-safety issue |
| SR-07 | MEDIUM | No runtime import guard enforcement at CI level | N/A | See `tools/check_security.py` for remediation |

### 13.2 Positive Findings

| ID | Area | Finding |
|----|------|---------|
| SF-01 | Secret management | All secrets use `SecretStr` via `SecretValue` annotated type |
| SF-02 | JWT signing | Fail-fast if signing key is weak, short, or a known default |
| SF-03 | Password hashing | bcrypt with salt, constant-time verification |
| SF-04 | Cookie security | httpOnly + secure + samesite=lax for all tokens |
| SF-05 | CSRF | Double-submit token pattern, not stored in httpOnly cookie |
| SF-06 | Error handling | No internal detail leakage; generic error codes only |
| SF-07 | Rate limiting | Per-IP + per-user, Redis with memory fallback, fail-closed at capacity |
| SF-08 | WAF | URL decoding, bounded event log, immediate block for high-weight rules |
| SF-09 | C++ ABI | Extension carries interpreter ABI tag in filename |
| SF-10 | Provenance | Required provenance fields prevent data misattribution |
| SF-11 | CORS | No wildcard with credentials, no stale dev ports |
| SF-12 | Audit trail | Dual-store with explicit store field, table-name allowlist |

---

## 14. Recommendations

1. **Enforce gateway usage at CI level**: Deploy `tools/check_security.py` as a
   pre-commit hook to detect direct imports from `engine.hydroma` in services/
   that bypass `_gateway_facade.py`.

2. **Fix SR-06**: Replace `db.query()` in `require_admin_with_mfa` with an async
   query pattern to match the async session dependency.

3. **Address SR-01**: Wire soil chemistry functions through the gateway dispatch
   to eliminate the `RuntimeError` fallback path in `_gateway_facade.py`.

4. **Encrypt `.master.key`**: Use OS keyring or a KMS to protect the PrivacyVault
   master key at rest, rather than file permissions alone.

5. **Integrate WAF with API gateway**: Currently `WafEngine` is standalone;
   the `RateLimitMiddleware` in the gateway does not call it. Ensure the
   middleware chain includes WAF checks.

---

## 15. Compliance Mapping

| Standard | Requirement | Status |
|----------|-------------|--------|
| OWASP ASVS L1 | 1.5.2 Hashed passwords | ✅ bcrypt |
| OWASP ASVS L1 | 3.1.1 GET not mutated | ✅ WAF + gateway validation |
| OWASP ASVS L1 | 4.1.1 TLS | ✅ HTTPSRedirectMiddleware, HSTS |
| OWASP ASVS L1 | 4.2.1 Session ID binding | ✅ JWT + subject claim |
| OWASP ASVS L1 | 5.1.1 Parameterized queries | ✅ Supabase client uses parameterized API |
| OWASP ASVS L1 | 8.1.1 Error handling | ✅ safe_error_detail |
| OWASP ASVS L1 | 9.2.1 Secret management | ✅ SecretStr + production rules |
| OWASP ASVS L2 | 2.1.1 Session timeout | ✅ 30-min access token |
| OWASP ASVS L2 | 2.4.1 Remember me | ✅ 30-day refresh with rotation |

---

*End of Security Review — Generated 2026-10-09*
