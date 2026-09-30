# Eco Nojin

A green-economy and agricultural-science platform: an ecological modelling engine
behind a FastAPI gateway.

**This repository is currently backend-only.** The Next.js frontend that used to
live in `apps/web` has been removed. There is no web client, no design system, no
PWA, and no i18n bundle in the tree. If you were looking for the UI, it is not
here. See [Removed](#removed) for what went and how to bring it back.

---

## What is here

| Area | Measured |
|---|---|
| Gateway routers | **85** modules under `services/api_gateway/routers/` |
| HTTP endpoints | **751** `@router` / `@app` decorators across `services/` |
| Scientific engine | **290** Python modules under `engine/` |
| Python tests | **185** files under `tests/` |
| Python | 3.12.10 · FastAPI 0.141.1 |

Everything below is stated from the tree as it is on 2026-09-30. Reproduce any
figure with the command in its row.

### The four subsystems

| Path | What it is |
|---|---|
| `engine/` | The scientific core — soil, hydrology, climate, erosion, carbon, MRV |
| `services/api_gateway/` | FastAPI app, 85 routers, auth, middleware, observability |
| `services/models/` | Model registry and scientific model implementations |
| `database/`, `alembic/` | SQLAlchemy 2.0 models and migrations |

The gateway is the only supported entry point. It is what the deleted frontend
called, and it is what anything new should call.

---

## Requirements

- Python 3.12 (`pyproject.toml`, `[project] requires-python`)
- PostgreSQL for anything beyond SQLite development
- `pip` / `uv` — there is no Node requirement for the backend

---

## Local development

```bash
# 1. environment
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# 2. configuration
#    copy .env.example to .env and fill it in. SECRET_KEY, JWT_SECRET and
#    DATABASE_URL have no safe defaults and the app refuses to start without them.
#    .env is gitignored and must never be committed.

# 3. database
.venv\Scripts\python.exe -m alembic upgrade heads

# 4. run
.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000
```

Health probes: `GET /health` and `GET /ready`.

> **On PowerShell 5.1** use `; if ($?) { … }` rather than `&&`. The shell in this
> repository's documented commands is Windows PowerShell 5.1 and does not
> support `&&`.

---

## Testing

```bash
.venv\Scripts\python.exe -m pytest tests/unit -q
.venv\Scripts\python.exe -m pytest tests/integration -q
.venv\Scripts\python.exe -m pytest -q            # everything
```

**The coverage floor is 36%, not 80%.** `pyproject.toml` sets
`[tool.coverage.report] fail_under = 36`, and
`tests/contract/test_g3_g4_coverage_and_deadcode.py:33` asserts that value is a
rung on `{36, 60, 70, 80}` and has never been lowered. An earlier revision of the
README claimed ≥80% — that claim was never enforced by any configuration in the
repository. Do not write `--cov-fail-under=80`.

`tests/test_contract.py` is known to be broken in CI: it hardcodes `D:/eco_nojin`
at lines 12 and 22, which is a relative path on a non-Windows runner.

---

## Quality gates

```bash
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # ruff, mypy, pre-commit

ruff check .
ruff format --check .
mypy --strict engine/hydroma/config/settings.py services/api_gateway/
pre-commit run --all-files
```

`ruff` is configured in `pyproject.toml` and replaces flake8/isort/black. Ruff,
mypy and pre-commit live in `requirements-dev.txt` and are **not** installed by
`requirements.txt` alone.

The frontend gates that used to sit alongside these are gone with the frontend:
`check:site-url`, `check:messages`, `check:locales`, `check:locale-encoding`,
`check:page-meta`, `check:font-coverage`, `check:ui-kit`,
`check:orphan-components`, `i18n:compile`, `test:coverage`, `test:e2e`,
`lighthouse`, and `check-scenery` / `scenery-contrast`. Their scripts survive
under `scripts/` but nothing invokes them.

---

## Deployment

**Staging and production are disabled.** No immutable artifact promotion and no
reviewer gates are configured. Do not assume a deploy path exists.

- Containers: multi-stage Dockerfiles for the gateway under `deploy/`
- Orchestration: a Helm chart exists at `helm/eco-nojin/` and **is not applied** —
  `deploy/k8s/` holds only `.gitkeep`, and there are no staging or production
  namespaces to deploy into
- Secrets: External Secrets Operator is **not wired**. 0 references under
  `deploy/`. Treat it as unimplemented.

The frontend deployment manifests (`k8s/base/frontend-*.yaml`,
`helm/eco-nojin/templates/*-frontend.yaml`) were removed with the frontend.

---

## Removed

The Next.js 15 / React 19 application under `apps/web`, its workspace package
`packages/ui`, and `docs/frontend/` were deleted on 2026-09-30 at the repository
owner's direction. Also removed with them: the Lighthouse and Core Web Vitals
budget files, the design-system and page-template gates, the 14-locale
message bundle, the Playwright and Storybook suites, and the CI workflows that
existed only to run them (`i18n-ci.yml`, `nightly-e2e.yml`).

**This deletion is reversible for everything git tracks.** 1,105 files were
committed before the removal, so:

```bash
git checkout -- apps packages/ui docs/frontend
```

and re-add the `apps/*` line to `pnpm-workspace.yaml`, the frontend jobs to
`.github/workflows/ci.yml`, the `frontend` job to `ci-cd.yml`, the
`apps/web/**` entry to `biome.json`, and the frontend scripts to the root
`package.json`.

Seventeen files that were never committed — `ModelCard.tsx`, `Scenery.tsx`,
`lib/i18n/format.ts` and related tests — have no git copy. They were preserved
outside the repository at
`C:\Users\hp\AppData\Local\Temp\eco-nojin-frontend-untracked-20260930`.

---

## Conventions

1. **Branch** `feature/{ticket}-{desc}` from `main`.
2. **Commit** Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
3. **PR** targets `main`, needs CI green and one review. Squash merge, delete branch.
4. **Release** an immutable `vX.Y.Z` tag.

- **Never commit `.env`.** It is gitignored.
- **Never hardcode a secret.** Read configuration through
  `engine/hydroma/config/settings.py` (`get_settings()`), which is pydantic-settings
  and loads from the environment.
- **Gate new behaviour behind a feature flag** — the `ENABLE_*` settings.
- **Add a correlation id to logs** — read `X-Request-ID` from the request headers.
- **Custom exceptions with error codes** for anything a client can hit.
- **Every figure in a document needs a reproduction command.** A number you cannot
  regenerate is an assertion, not a finding. Derive it from the source of truth or
  mark it `NOT VERIFIED` and say why. A document that states a status is not a
  report of one; when the two disagree, the code wins and the document is history.
- **A standard is only real if a test enforces it.** Name the test that blocks a
  violation. A rule with no test is a wish.
- **Record negative results.** "Could not verify" is required output, not a gap to
  quietly delete.

---

## Known gaps

These are measured defects, not a backlog of wishes.

| Gap | Evidence |
|---|---|
| `tests/test_contract.py` cannot pass in CI | hardcodes `D:/eco_nojin` at lines 12, 22 |
| Contract suite is not enforced | the `schemathesis run` step in `ci-cd.yml` ends in `\|\| true`, so it reports and cannot fail a build |
| Mutation testing is not enforced | the `mutmut` step ends in `\|\| true` and targets a narrow path list |
| Staging and production are unreachable | no artifact promotion, no namespaces |
| External Secrets Operator is not wired | 0 references under `deploy/` |
| Coverage ratchet has ~0 headroom | floor 36 against a measured value close to it; raising it needs new tests, not a new number |
| `load` requires a manual host flag | `locust` is not in any requirements file; only in `ci-cd.yml` |

---

## License

See the repository's licence file. Third-party licences for the scientific
methods are recorded in `docs/`.
