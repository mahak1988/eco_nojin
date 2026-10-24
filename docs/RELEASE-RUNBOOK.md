# RELEASE RUNBOOK — ECO Nojin / HyDroMA

* **Status:** Active · **Opened:** 2026-10-11 (P15, A15) · **Program:** `docs/project/PHASE_PLAN.md`
* **Principle:** every stage is reversible, every migration is rehearsed, every
  critical path is measured and alerting before traffic reaches it.

## 0. Pre-flight (every release)

1. `git status` clean on the release commit; the working tree has no untracked
   files other than the ones this program's rules allow (see AGENTS.md).
2. Gates green **on the committed tree** (the live-tree rule of `BASELINE.md`):
   `pytest engine/ -n 6 -p no:cacheprovider` · `pytest services/ -n 6
   -p no:cacheprovider` · `pytest engine/strict_tests -p no:cacheprovider` ·
   `ruff check .` ≤ committed baseline · `mypy engine --ignore-missing-imports`
   = 0 · `tools/detect_imports.py --root .` = 0 ·
   `tools/check_service_boundaries.py` = 0 stale · `app.openapi()` boots and the
    route count is the deliberate one (116 on the working tree as of
    2026-10-11; the P1 engine-job router mount accounts for exactly +1 of
    that. `AGENTS.md` records 113 as the committed baseline — the rest is
    other phases' in-flight work, which is why a new increment is recorded
    per phase rather than against that number.)
3. `alembic heads` is single; `alembic upgrade head --sql` renders.
4. `pytest tests/test_p14_guard_sweep.py` green — the P14 guards are in place.
5. Environment variables set and documented: `SECRET_KEY`, `PYTHONPATH`,
   `BANK_WEBHOOK_SECRET` (fail-closed: unset ⇒ 503), and the rate-limit knobs.
6. The SQLite WAL gate of §3 is resolved for the target host (upgrade, drop-in,
   or a non-WAL decision), and the engine-job worker has somewhere to run: the
   route only *submits* work, so a deployment without
   `python -m services.jobs.worker` ships a surface that never completes a job.

## 1. Stage order (dev → CI → staging → E2E → rehearsal → pilot → gradual)

| Stage | What happens | Rollback |
|---|---|---|
| dev | full gates + `pytest services/*/tests` | n/a |
| CI | the engine job + the P1/P7/P9 contract suites (`.github/workflows/ci.yml`) | the job fails, nothing ships |
| staging | migrate + smoke: `alembic upgrade head` on staging, then the golden paths (login, marketplace order, tourism booking, governance advance, compliance assess) | staging DB is disposable |
| rehearsal | **the migration is run twice** on a copy: `upgrade head` → `downgrade <prev>` → `upgrade head`; the guarded revisions must be a no-op on re-run (the P4/P7/P8/P9/P10 pattern) | the copy is discarded |
| restore drill | `runtime/backup.snapshot` → `verify` (sha256) → `restore` → row-count check (the P4 drill pattern) | from the snapshot |
| limited pilot | one village, one seller cohort, one jurisdiction; monitoring on | pilot flag off |
| gradual | 5% → 25% → 100% with the alert budget below | the previous version |

## 2. Monitoring & alerting (before traffic)

* **Structured logs** with the request id / trace id chain (`X-Request-ID`,
  gateway `trace_id`, the evidence chain of `engine/evidence`).
* **Error tracking** on the `EcoNojinException` code vocabulary — every
  `code` is a page or a ticket, never an anonymous 500.
* **Health checks**: `/health` on every service plane; the finance
  reconciliation endpoints wired to a scheduled run.
* **Finance alerts**: unbalanced batch (must never happen — the invariant),
  escrow release without a verified payment, wallet-vs-ledger drift above zero,
  duplicate-`Idempotency-Key` 422 rate (a client bug signal).
* **Credential/assessment expiry sweep** (`ComplianceService.sweep_expired`)
  on a schedule, alerting on credentials expiring within 7 days.
* **Queue monitoring** for the eventbus outbox (`services/integration/outbox_worker.py`):
  depth and age; a stalled outbox is a data-integrity incident.
* **Queue monitoring** for the engine-job worker
  (`services/jobs/worker.py`): a non-empty `compute_jobs` queue in state
  `pending`/`queued` means no worker is draining it. The route answers 202
  immediately, so the failure mode is silent without this check — jobs are
  accepted, never run, and only a `compute_jobs` age metric exposes it.

## 3. The SQLite WAL gate (D-16, KN-09)

`database/hub.py` exposes `sqlite_wal_deployment_safe()` (`version >= (3,51,3)`).
The runtime in this environment is **3.49.1 — below the fix**. A WAL deployment
**must upgrade SQLite first**; the release checklist refuses to proceed while
`sqlite_wal_deployment_safe()` is False on a file engine.

### 3.1 The upgrade decision

The gate is a *build* check, so the release decision is a build decision, not a
code change. In order of preference:

1. **Upgrade SQLite to ≥ 3.51.3** (or to a 3.44.6 / 3.50.7 backport). This fixes
   the stdlib `sqlite3` module, the async plane (`sqlite+aiosqlite`, which uses
   the stdlib module and therefore cannot be helped by anything else), and
   every other consumer at once. This is the preferred resolution.
2. **Install the `pysqlite3` drop-in** when the too-old library is the *system*
   one and upgrading it is not available: the wheel bundles its own
   libsqlite3. `sqlite_engine_in_use()` reports whether that is in play, and
   `wal_safe_sqlite_url()` moves a *file* engine onto
   `sqlite+pysqlite3://` only when the drop-in is actually a fix.
3. If neither is possible, **do not deploy a WAL database** on that host. The
   gate is not advisory: `sqlite_wal_deployment_safe()` is False, and
   `install_sqlite_pragmas()` logs the requirement on the error channel with the
   engine it resolved.

The resolution is a report, not a silent repair — the report is the artefact to
paste into a release note:

```python
from database.hub import sqlite_engine_in_use, sqlite_wal_deployment_safe

print(sqlite_wal_deployment_safe())
print(sqlite_engine_in_use().reason)
# → 'bundled sqlite3 3.49.1 is affected by the WAL-reset bug (fixed in 3.51.3)
#    and the pysqlite3 drop-in is not installed; upgrade SQLite before a WAL
#    deployment'   ← this build, today
```

The async plane is never rewritten onto the drop-in: aiosqlite talks to the
standard-library module, so an affected build there must be fixed by upgrading.

### 3.2 The WAL-size monitor (starvation)

A growing WAL is not a busy database: SQLite checkpoints automatically after
1000 committed pages, so a file past that point means the checkpoint is *not
running* — a long-lived reader is pinning the tail (or
`PRAGMA wal_autocheckpoint` was disabled). Every other reader then pays for a
file that only grows, and the checkpoint backlog turns into a very slow start
when it finally runs.

`wal_size_report(db_path)` measures the sibling `<db>-wal` file and raises the
warning:

```python
from database.hub import wal_size_report

report = wal_size_report("data/hydroma.db")
# report.starved        → True past 1000 pages / ~4 MB
# report.page_count, report.size_bytes
# report.message        → the operator sentence, including what to look for
```

Two properties worth knowing before wiring it into a monitor:

* It is a **live** measurement. Closing the last connection checkpoints the log
  back into the database and unlinks the file, so a quiescent database always
  reports `exists=False`. Sample while the application is running; a report
  taken afterwards says nothing about what happened.
* It is **pure filesystem inspection** — no connection is opened, so it is safe
  to run from a monitoring job while the writer is live.

Alert on `starved`, and on `size_bytes` growth over consecutive samples. The fix
is to close the long-running reader transaction (or restore
`wal_autocheckpoint`), not to delete the WAL file: deleting a live WAL is how a
database gets corrupted, which is the same failure the version gate prevents.

### 3.3 Tests

`tests/test_sqlite_wal_gate.py` covers the gate on both paths: the version
resolution (bundled, missing drop-in, a drop-in that is a genuine fix, and a
drop-in that is also affected) and the WAL size (no log, a short log, a real
starved log pinned by an open writer, a truncated header, and the in-memory
case where no log can exist). The in-memory case is the reason `wal_supported`
is a separate field from `exists`.

## 4. Rollback

* Code: redeploy the previous image; the route surface and the API contract are
  versioned (`API-CONTRACT-v1.md`), so an old client meets an old-compatible
  server.
* Database: every schema change since the last release is a separate guarded
  revision with a downgrade; **downgrades are destructive on a `create_all`
  database** (they remove what `create_all` created) — prefer the
  roll-forward (a new compensating revision) over a downgrade in production.
* Feature flags: EcoCoin (`HYDROMA_ECOCOIN_WRITES_ENABLED`, default frozen),
  eventbus/NATS (optional import), auth rate limiting.

## 5. Post-release review (within 48 h)

* Compare the P13 latency report against the baseline taken at P13.
* The reconciliation suite on production data; any drift is an incident.
* Pilot feedback on the village governance and tourism booking flows.
* The register (`docs/project/KNOWN_ISSUES.md`) is updated: what the release
  changed, what it exposed, what stays open.
