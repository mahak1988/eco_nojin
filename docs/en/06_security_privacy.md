# 06. Security and Privacy

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. Principles

- **Data sovereignty:** farmers own their data; the platform is a custodian.
- **Anonymization:** aggregated data is anonymized before any external use.
- **Minimization:** collect only what is needed for the service requested.
- **Post-quantum readiness:** interfaces reserve NIST-approved PQC algorithms
  (ML-KEM for KEM, ML-DSA for signatures) for future ledger and API security.

## 2. Current State (honest)

| Area | Status |
|---|---|
| Transport security | Not configured yet (dev mode, HTTP) — TLS required for any deployment |
| Authentication / authorization | **Not implemented** (auth service is a placeholder) |
| CORS | `allow_origins=["*"]` with `allow_credentials=True` — invalid combination; must be replaced with an explicit origin allowlist |
| Secrets | `.env.example` uses `change_me`; `docker-compose.yml` contains a literal `***` password placeholder — real secrets must go to a vault |
| Input validation | Pydantic schemas on API boundaries (good) |
| Dependency policy | `requirements.txt` uses unpinned versions — pin and audit before release |
| Data at rest | SQLite research DB unencrypted; production PostGIS encryption/backup policy required |
| MRV integrity | Hashing of MRV records planned for the ledger layer (Phase 5) |

## 3. Threat Model Highlights

- **Unsecured API exposure:** deploying the gateway today would expose
  unauthenticated write endpoints (marketplace orders, carbon project
  registration, sync) — acceptable only in trusted research networks.
- **Simulated satellite data:** must never be presented as real observations
  to external stakeholders (data-integrity risk, see `02_hydroma_engine.md`).
- **Carbon verification endpoint:** internal demo only; presenting its output
  as certified credits would be a regulatory/fraud risk.

## 4. Target Controls (roadmap)

1. AuthN/AuthZ service (OAuth2/OIDC, roles: farmer, cooperative, NGO, admin).
2. Explicit CORS allowlist; HTTPS everywhere; HSTS.
3. Secret management (env vault / cloud secret manager).
4. Pinned, audited dependencies; dependency scanning in CI.
5. Per-tenant data separation and consent records for data sharing.
6. PQC-ready key management in the ledger layer (ML-KEM/ML-DSA interfaces).
7. Audit logging of MRV data with cryptographic hashing (tamper evidence).

## 5. Privacy by Design

- Location data (geolocation hooks in the frontend) is used only for the
  requested analysis and is not shared by default.
- USSD/SMS flows minimize data exchange; phone numbers are treated as
  personal data.
- Impact investors see only anonymized, aggregated metrics.

## 6. Incident Response (planned)

A runbook (severity levels, contacts, data-breach notification obligations
per applicable jurisdiction) is to be drafted before the first public pilot.
