# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — SECURITY FINDINGS

**Document ID:** ECO-00-SECURITY-FINDINGS  
**Date:** 2026-10-08  
**Status:** COMPLETE  
**Auditor:** Kilo autonomous agent

---

## Security Finding Format

Per ECO-00 Section 36, findings use:
- SECURITY-ID
- Severity
- Location
- Finding
- Evidence
- Impact
- Recommended remediation
- Status

---

## SECURITY-001: Broken Import — Missing adapters Package

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-001 |
| **Severity** | HIGH (availability) |
| **Location** | `services/land/service.py:12` |
| **Finding** | Import of non-existent `adapters.engine_adapter.EngineAdapter` |
| **Evidence** | `from adapters.engine_adapter import EngineAdapter` — `adapters/` directory did not exist at project root |
| **Impact** | `LandService` cannot be loaded, causing potential DoS of land service endpoints |
| **Remediation Applied** | Created `adapters/engine_adapter.py` and `adapters/hydroma_adapter.py` at project root |
| **Status** | **FIXED** |

---

## SECURITY-002: Secret Handling in Settings

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-002 |
| **Severity** | INFORMATIONAL |
| **Location** | `engine/hydroma/config/settings.py` |
| **Finding** | Settings model with proper SecretStr handling |
| **Evidence** | `SecretValue = Annotated[SecretStr, BeforeValidator(_coerce_secret)]`, `is_secure_secret` property, `jwt_signing_key` resolution |
| **Impact** | Secrets properly redacted in repr; production validation enforced |
| **Recommended Remediation** | None required — this is a positive finding |
| **Status** | **VERIFIED SAFE** |

---

## SECURITY-003: OAuth Encryption Key Derivation

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-003 |
| **Severity** | MEDIUM (key reuse) |
| **Location** | `engine/hydroma/config/settings.py:547-562` |
| **Finding** | OAuth encryption key was previously missing, derived from SECRET_KEY (documented and fixed) |
| **Evidence** | Comment documents that `oauth_encryption_key` was read via `getattr(settings, "oauth_encryption_key", None)` returning None, with fallback deriving Fernet key from first 32 bytes of SECRET_KEY |
| **Impact** | Previous: JWT signing key reused for OAuth encryption; short SECRET_KEY produced low-entropy key |
| **Recommended Remediation** | **FIXED** — Added `oauth_encryption_key` field as SecretValue |
| **Status** | **FIXED** |

---

## SECURITY-004: CORS Configuration

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-004 |
| **Severity** | LOW |
| **Location** | `engine/hydroma/config/settings.py:190-191` |
| **Finding** | CORS now properly configured; removed insecure defaults |
| **Evidence** | `cors_origins: list[str] = ["http://localhost:8000"]` (removed 3000/3001), `allow_credentials: bool = True` |
| **Impact** | Removed credentialed cross-origin hole that existed when dev frontend ports were allowlisted |
| **Recommended Remediation** | None required — this is a positive finding |
| **Status** | **VERIFIED SAFE** |

---

## SECURITY-005: Local OAuth Fallback Flag

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-005 |
| **Severity** | MEDIUM |
| **Location** | `engine/hydroma/config/settings.py:151` |
| **Finding** | `enable_local_oauth_fallback` defaults to False and is refused in production |
| **Evidence** | Comment: "anyone who can reach the callback can create an account without proving anything" |
| **Impact** | Development-only affordance; disabled in production |
| **Recommended Remediation** | None required — properly guarded |
| **Status** | **VERIFIED SAFE** |

---

## SECURITY-006: WebAuthn Passkey Configuration

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-006 |
| **Severity** | MEDIUM |
| **Location** | `engine/hydroma/config/settings.py:541-542` |
| **Finding** | WebAuthn RP_ID and Origin are configurable, with production guard |
| **Evidence** | Empty defaults mean "passkeys not available"; CHECK 16 refuses production start if unset |
| **Impact** | Prevents localhost-scoped passkey ceremonies |
| **Recommended Remediation** | None required — properly guarded |
| **Status** | **VERIFIED SAFE** |

---

## SECURITY-007: B3 MRV Ingest Key

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-007 |
| **Severity** | LOW |
| **Location** | `engine/hydroma/config/settings.py:531` |
| **Finding** | MRV ingest key is separate from telco webhook key with documented justification |
| **Evidence** | Comment explains different trust relationships for LoRaWAN operator webhook vs. field devices |
| **Impact** | Key rotation isolation prevents cross-contamination |
| **Recommended Remediation** | None required |
| **Status** | **VERIFIED SAFE** |

---

## SECURITY-008: Engine → Services Dependency (Architectural Risk)

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-008 |
| **Severity** | MEDIUM |
| **Location** | `engine/hydroma/generative_ai/__init__.py`, `engine/land/integration/water_adapter.py` |
| **Finding** | Engine layer imports from services layer |
| **Evidence** | See DEPENDENCY-MAP.md — two violations of the engine boundary rule |
| **Impact** | Engine cannot be used independently; potential for circular imports; coupling violates security isolation principles (scientific engine should not depend on application infrastructure) |
| **Recommended Remediation** | Remove forbidden imports; move AI compatibility layer to services |
| **Status** | **ACTIVE** (1 mitigated, 1 unmitigated) |

---

## SECURITY-009: Duplicate Secret Declarations

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-009 |
| **Severity** | LOW |
| **Location** | `engine/hydroma/config/settings.py:456-461` |
| **Finding** | Six settings fields were each declared twice in the class body |
| **Evidence** | Comment documents: `bank_transfer_card_number`, `bank_transfer_holder`, `bank_transfer_sheba`, `hydroma_core_dll`, `intl_payment_checkout_url`, `local_rpc_url` |
| **Impact** | Dead text reading as real settings — could cause misconfiguration |
| **Recommended Remediation** | **FIXED** — consolidated to single declaration each |
| **Status** | **FIXED** |

---

## SECURITY-010: Removed Bare Secret Field

| Field | Value |
|-------|-------|
| **Security ID** | SECURITY-010 |
| **Severity** | MEDIUM |
| **Location** | `engine/hydroma/config/settings.py:403-406` |
| **Finding** | Bare `private_key` field was removed (no consumer, shadowed `blockchain_private_key`) |
| **Evidence** | Comment: "an unvalidated escape hatch for the same secret" |
| **Impact** | Prevented accidental use of unvalidated private key |
| **Recommended Remediation** | None required |
| **Status** | **FIXED** |

---

## SCIENTIFIC SECURITY Findings

Per ECO-00 Section 37, the following scientific integrity issues were identified and addressed:

### SCIENTIFIC-001: Silent Unit Conversion Fix

| Field | Value |
|-------|-------|
| **Finding** | Field capacity head was 330.0 cm instead of 33.0 cm |
| **Location** | `engine/hydroma/soil/physics.py:201-202` |
| **Impact** | AWC collapsed; sand reported 0.0006 vs 0.091 published |
| **Status** | **FIXED** |

### SCIENTIFIC-002: Hidden Constant — RUSLE Calibration

| Field | Value |
|-------|-------|
| **Finding** | Three locations applied 0.10 calibration multiplier to RUSLE |
| **Location** | `engine/hydroma/scientific_motors/erosion_rusle.py`, `core/core.py`, `chain_runner.py` |
| **Impact** | 10x reduction of published erosion quantity |
| **Status** | **FIXED** — multiplier removed, made explicit caller argument |

### SCIENTIFIC-003: Unexplained Coefficient — Hargreaves Exponent

| Field | Value |
|-------|-------|
| **Finding** | Hargreaves used exponent 0.50 instead of 0.48 |
| **Location** | `climate/et_calculator.py:113` |
| **Impact** | 3.3% overestimate at 5°C diurnal range, 6.6% at 25°C |
| **Status** | **FIXED** |

### SCIENTIFIC-004: Unseeded Stochastic Behavior

| Field | Value |
|-------|-------|
| **Finding** | Python's `hash()` used in output filenames for spatial runoff |
| **Location** | `engine/hydroma/models/runoff_model.py` |
| **Impact** | Non-reproducible raster filenames across runs |
| **Status** | **DOCUMENTED** in formula catalog (STUB status) |

### SCIENTIFIC-005: Silent Clipping Discrepancy

| Field | Value |
|-------|-------|
| **Finding** | EVI did not clip to [-1,1] in Python fallback |
| **Location** | `engine/hydroma/cpp_bridge/__init__.py:304-306` |
| **Impact** | Python fallback could return values C++ could never produce |
| **Status** | **FIXED** |

---

## Secrets Check Summary

**Scanned:** All files in `engine/` and `services/` for potential secrets

| Finding | Severity | Status |
|---------|----------|--------|
| No hardcoded secrets in source code | — | VERIFIED |
| No credential files in repository | — | VERIFIED |
| No .env files committed | — | VERIFIED |
| Secret fields use SecretStr | — | VERIFIED |
| Production secret validation enforced | — | VERIFIED |
| API keys default to empty strings (safe disabled) | — | VERIFIED |

---

*End of Security Findings Report*
