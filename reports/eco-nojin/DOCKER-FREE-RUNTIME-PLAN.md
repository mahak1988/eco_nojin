# DOCKER-FREE RUNTIME PLAN — قرارداد DP-2

Document id: `ECO-DP2-RUNTIME` · Date: 2026-10-10 · Owner decision: remove Docker from the plan; use a lightweight, internal, free, fast-start runtime.

## 1. Measured footprint (this host, today)

| Location | What it is | Docker dependency |
|---|---|---|
| `Dockerfile*`, `docker-compose*`, `infra/`, `.dockerignore` | **do not exist** | none — nothing to remove on disk |
| `engine/hydroma/production/deployment.py` | generates a **Kubernetes/Helm descriptor** (`postgresql.auth.existingSecret`, `host: postgresql, port: 5432`) | a container-era artifact; the real Docker-era code |
| `engine/hydroma/config/rules.py:213,352-354` | production rule **mandating PostgreSQL** | the operational consequence |
| `database/base.py` | SQLAlchemy `JSONB` → SQLite `JSON` compile shim | dialect work for the two-tier story |
| `engine/hydroma/models/cache.py` | already documents "SQLite without Docker or a server" | precedent for the local tier |
| `.github/workflows/ci.yml` | 6 jobs, **none uses Docker** | nothing to change |
| `ECO-NOJIN_MASTER_v3.1_UNIFIED.md` | now carries **DP-2** (this decision) | the plan-level removal the owner asked for |

## 2. Target architecture — "Hydroma Runtime" (internal, free, fast)

```
python -m runtime.supervise up      # start everything (default: this host, seconds)
python -m runtime.supervise status  # health per process
python -m runtime.supervise down    # graceful stop
python -m runtime.backup            # file snapshot + sha256, restorable
```

| Concern | Design |
|---|---|
| **Process model** | one Python supervisor process that starts each FastAPI service as a `uvicorn` worker in its own subprocess, plus the scheduler and a `/healthz` endpoint; no container, no orchestrator, no service mesh |
| **Configuration** | `runtime/services.yaml` — one entry per service: module, host, port, workers, health path, dependencies; pure YAML, human-readable |
| **Storage** | two tiers selected by `HYDROMA_STORAGE_TIER`: `local` (default) = **SQLite + WAL**, file-based, zero install; `scaled` = PostgreSQL, opt-in |
| **Secrets** | `.env`/environment only (no cluster secrets, no vault) |
| **Backup/restore** | `runtime/backup.py`: WAL checkpoint → file copy → sha256 manifest → `restore` |
| **Observability** | per-process logs under `data/logs/`, `/healthz` per service, status table on the CLI |
| **Scale escape hatch** | the same `services.yaml` is the spec for a future `systemd`/single-box deployment; the PostgreSQL tier exists and is exercised by the existing SQLAlchemy models |

## 3. Why this satisfies the owner's constraint
- **سبک و داخلی**: the runtime is ~3 files of pure Python + one YAML; it lives in this repo and needs nothing external.
- **رایگان**: no licence, no cloud account, no image registry — SQLite + Python stdlib.
- **راه‌اندازی سریع**: `up` is a subprocess start, not an image build; the engine suite starts in ~2 minutes, the app tier in seconds.
- **رفتار حفظ**: nothing in the scientific core changes (ZED §2.2ج; brake 7); layer-3 wiring only.

## 4. Implementation (three subagents, disjoint files)

| Agent | Files | Task |
|---|---|---|
| **R-A** | NEW `runtime/__init__.py`, `runtime/services.yaml`, `runtime/supervise.py`, `runtime/tests/test_supervise.py` | the supervisor: YAML-driven up/down/status, per-process health, port allocation, log files; tests with a stub service (no network binding conflicts) |
| **R-B** | EDIT `engine/hydroma/config/rules.py`, NEW `engine/hydroma/production/runtime_deployment.py`, NEW `engine/hydroma/tests/test_storage_tier.py` | tier-aware storage rule (`HYDROMA_STORAGE_TIER=local|scaled`) replacing the unconditional PostgreSQL mandate; a runtime descriptor replacing the K8s/Helm one; tests pinning both tiers |
| **R-C** | NEW `runtime/backup.py`, `runtime/tests/test_backup.py` | WAL-checkpoint snapshot + sha256 manifest + restore + retention; tests on a temp SQLite DB |

## 5. Risks and controls
| Risk | Control |
|---|---|
| A worker process dies silently | supervisor restarts it and records the exit code in `status` |
| Port conflicts with existing services | the YAML pins ports and `up` fails fast with a named conflict |
| SQLite WAL growth | backup checkpoints + retention policy in `backup.py` |
| The "local" tier being mistaken for production scale | the tier is explicit in settings and logged on every boot; the constitution says the scaled tier is opt-in, not required |
| Deleting the old K8s path breaks callers | `deployment.py` keeps generating the old descriptor only when the tier is `scaled` (documented), so no caller breaks |

## 6. Definition of done
1. `python -m runtime.supervise up` starts the listed services and `/healthz` is green; `down` stops them.
2. `HYDROMA_STORAGE_TIER=local` boots with **no PostgreSQL** and no Docker; the previous "Production requires PostgreSQL" rule no longer fires in that tier.
3. `python -m runtime.backup` produces a checksummed snapshot that `restore` accepts.
4. `pytest engine/`, `pytest services/`, `tools/detect_imports.py --root .` remain green.
5. `ECO-NOJIN_MASTER_v3.1_UNIFIED.md` carries DP-2 (done) and lists `runtime/` in its appendix.
