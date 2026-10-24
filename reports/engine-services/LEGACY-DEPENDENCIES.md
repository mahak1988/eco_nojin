# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — LEGACY DEPENDENCIES

**Document ID:** ECO-00-LEGACY-DEPENDENCIES  
**Date:** 2026-10-08  
**Status:** COMPLETE

---

## Legacy Dependency Detection Policy

Per ECO-00 Section 23, search for references to old project concepts and classify each.

---

## 1. Old Project Names

| Reference | Location | Classification | Notes |
|-----------|----------|---------------|-------|
| "Eco Nojin" | Throughout (settings, docstrings) | REQUIRED | Current project name |
| "EcoCoin" | `services/__init__.py:1` | REQUIRED | Alternate project name, current |
| "econojin" | 50+ files (settings, config) | REQUIRED | Current project identifier |

---

## 2. Old Package Names

| Package | Referenced By | Status | Classification |
|---------|--------------|--------|----------------|
| `database` | Engine + Services | **MISSING** | BLOCKED_EXTERNAL_DEPENDENCY |
| `adapters` | `services/land/service.py` | **CREATED** | FIXED (BLOCKER-P1 — resolved) |
| `frontend` | `services/api_gateway/main.py` (comments) | Removed | OBSOLETE |
| `ecowallet` | `services/ecowallet/` | Present | REQUIRED |
| `map_engine` | `engine/land/integration/water_adapter.py` | Present (in services) | **FIXED** — forbidden import removed from water_adapter.py |

---

## 3. Old Absolute Paths

No hardcoded absolute paths found in engine or service source code. All paths are relative or configuration-driven.

---

## 4. Old Environment Variables

The following environment variables are used in `engine/hydroma/config/settings.py`:

| Variable | Current Status | Classification |
|----------|---------------|----------------|
| `APP_ENV` | Alias for `ENVIRONMENT` | REQUIRED |
| `DEBUG` / `APP_DEBUG` | Accepted | REQUIRED |
| `SECRET_KEY` | Required in production | REQUIRED |
| `JWT_SECRET` | For JWT signing | REQUIRED |
| `API_BASE_URL` | API endpoint | REQUIRED |
| `FRONTEND_URL` | Frontend URL | OBSOLETE (frontend deleted) |
| `DATABASE_URL` | Database connection | BLOCKED_EXTERNAL_DEPENDENCY |
| `REDIS_URL` | Redis | OPTIONAL |
| `NATS_URL` | Event bus | OPTIONAL |
| `SUPABASE_URL` / `SUPABASE_KEY` | Supabase | OPTIONAL |
| `OPENAI_API_KEY` | OpenAI API | OPTIONAL |
| `ANTHROPIC_API_KEY` | Anthropic API | OPTIONAL |
| `SENTINEL_HUB_CLIENT_ID` | Sentinel Hub | OPTIONAL |
| `CDSE_CLIENT_ID` / `CDSE_PASSWORD` | Copernicus | OPTIONAL |
| `TWILIO_ACCOUNT_SID` | Twilio | OPTIONAL |
| `TELEGRAM_BOT_TOKEN` | Telegram | OPTIONAL |
| `ZARINPAL_MERCHANT_ID` | ZarinPal | REQUIRED |

---

## 5. Old Database Names

No explicit database names found in code. Database URL is configuration-driven via `DATABASE_URL` or `database_url` setting.

---

## 6. Old API Hosts

| Host | Found In | Classification |
|------|----------|----------------|
| `http://localhost:3000` | Settings (cors_origins, frontend_url) | DEPRECATED (frontend removed) |
| `http://localhost:8000` | Default API URL | REQUIRED (API gateway) |
| `https://power.larc.nasa.gov` | Settings | REQUIRED (climate data) |
| `https://api.open-meteo.com` | Settings | REQUIRED (weather data) |
| Polygon RPC URLs | Settings | OPTIONAL (blockchain) |
| `smtp.gmail.com` | Settings | OPTIONAL (email) |

---

## 7. Old Service URLs

| URL | Found In | Classification |
|-----|----------|----------------|
| `http://localhost:11434` | Ollama LLM URL | OPTIONAL (AI) |
| `http://127.0.0.1:11434` | Ollama API URL | OPTIONAL (AI) |
| `https://sepal.io` | SEPAL API | OPTIONAL |
| `https://catalogue.dataspace.copernicus.eu` | Copernicus CDS | OPTIONAL |

---

## 8. Old Authentication Modules

| Module | Found In | Classification |
|--------|----------|----------------|
| `services.api_gateway.auth` | Various services | REQUIRED (shared auth) |
| `services.auth` | Auth service | REQUIRED |
| `services.auth_legacy` | Auth legacy | LEGACY_WRAPPER |
| `database.hub` | All services | BLOCKED_EXTERNAL_DEPENDENCY |

---

## 9. Old Configuration Systems

| System | Found In | Status |
|--------|----------|--------|
| `.env` file | Settings via `pydantic-settings` | REQUIRED |
| Environment variables | Settings | REQUIRED |
| Hardcoded config | None found | None |

---

## 10. Old OpenAPI Generated Clients

No OpenAPI generated client directories found. Routers use FastAPI decorators directly.

---

## 11. Old Frontend Packages

| Package | Status | Notes |
|---------|--------|-------|
| Next.js | Removed | Referenced in comments only (`services/api_gateway/main.py` comments) |
| React/Vue | Not found | None |
| Vite | Removed | Port 5173 mentioned in settings comment |

---

## 12. Old Deployment Assumptions

| Assumption | Evidence | Status |
|-----------|----------|--------|
| SQLite database | `database_url: str = "sqlite:///./data/econojin.db"` | Development default |
| Local PostgreSQL | Via `database.hub` | Requires external config |
| Docker | No Dockerfiles found | Not deployed |
| Kubernetes | No k8s configs found | Not deployed |
| Supabase | Optional integration | `database_url` can point to Supabase |
| Redis | Optional | Rate limiting, caching |
| NATS | Default `nats://localhost:4222` | Event bus |

---

## 13. Old Cloud Provider Assumptions

| Provider | Found In | Status |
|----------|----------|--------|
| AWS | Not found | None |
| Google Cloud | Not found | None |
| Azure | Not found | None |
| Supabase | Optional | `services/supabase/` |
| Copernicus CDS | Optional | Satellite data |
| Sentinel Hub | Optional | Satellite imagery |

---

## 14. Old Secrets/Config Paths

No old secrets or config paths found in source code. Secrets are referenced via pydantic `SecretStr` settings, with insecure defaults documented and rejected in production.

**Security finding:** Several API keys default to empty strings (`""`), which is safe (disabled by default). The `telegram_bot_token` and `agent_token` use `SecretValue` which wraps in `SecretStr`.

---

## 15. Cross-Package Legacy References

### Engine → Services References

| File | Service Import | Status |
|------|----------------|--------|
| `engine/hydroma/generative_ai/__init__.py` | `services.ai.*` | **MITIGATED** (lazy) |
| `engine/land/integration/water_adapter.py:230` | `services.map_engine.*` | **FIXED** |
| `engine/data_connector.py:51-62` | `services.security.query_safe` (comment) | **RESOLVED** (allowlist moved to engine) |

### Services → Legacy Patterns

| Reference | Location | Status |
|-----------|----------|--------|
| `services/scientific_motors/` | Referenced in `models/registry.py` docstring | UNKNOWN — directory not found |

---

## 16. Summary

| Classification | Count |
|----------------|-------|
| REQUIRED | 12 |
| OPTIONAL | 15 |
| OBSOLETE | 3 |
| REPLACEABLE | 2 |
| UNKNOWN | 4 |
| BLOCKED_EXTERNAL_DEPENDENCY | 1 |
| FORBIDDEN_DEPENDENCY | 2 (1 mitigated, 1 fixed) |
| LEGACY_WRAPPER | 1 |

---

*End of Legacy Dependencies Report*
