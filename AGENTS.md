# AGENTS.md — instructions for coding agents in this repository

> **This file is the authoritative source for how to work in this repository.**
> Anything not written here is not a rule. Where a document and the code disagree,
> the code wins and the document is history.

Read this before proposing a plan, running a command, or writing code.

---

## What this repository is

A **backend-only** Python monorepo. A FastAPI gateway in front of a scientific
modelling engine for soil, water, climate, erosion, carbon and MRV.

| Path | What it is |
|---|---|
| `engine/` | The scientific core — 290 Python modules |
| `services/api_gateway/` | The FastAPI app — 85 routers, 751 endpoints |
| `services/models/` | Model registry and model implementations |
| `database/`, `alembic/` | SQLAlchemy 2.0 models and migrations |
| `tests/` | 185 Python test files |
| `contracts/` | OpenAPI and interface contracts |

**There is no frontend.** A Next.js application under `apps/web`, a workspace
package `packages/ui`, and `docs/frontend/` were removed on 2026-09-30 at the
owner's direction. Do not create a web client, a design system, a PWA, a
translation bundle, or a component library. Do not add a Node build step.

`packages/api-client`, `packages/config` and `packages/types` are Python-adjacent
workspace packages and remain. The generated Orval client under
`packages/api-client` is **not regenerated** — the generator was part of the
frontend toolchain and is gone.

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # ruff, mypy, pre-commit
```

Configuration is a single source of truth:
`engine/hydroma/config/settings.py` — pydantic-settings v2, loaded from the
environment. `SECRET_KEY`, `JWT_SECRET` and `DATABASE_URL` have no safe defaults
and the app will not start without them.

`.env` is gitignored. **Never commit it.**

## Run

```bash
.venv\Scripts\python.exe -m alembic upgrade heads
.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000
```

Health: `GET /health`, `GET /ready`.

## Test and lint

```bash
.venv\Scripts\python.exe -m pytest -q
ruff check .
ruff format --check .
mypy --strict engine/hydroma/config/settings.py services/api_gateway/
pre-commit run --all-files
```

**On PowerShell 5.1** use `; if ($?) { … }` — `&&` does not exist in that shell.
Every command block in this file is written for it.

---

## The coverage floor is 36, not 80

`pyproject.toml` sets `[tool.coverage.report] fail_under = 36`, and
`tests/contract/test_g3_g4_coverage_and_deadcode.py:33` asserts the value is a
rung on `{36, 60, 70, 80}` and that it has never been lowered. An earlier version
of this file asserted ≥80% and that assertion was never true of any
configuration in the repository. The test at that path exists **because** the
claim was wrong.

Do not write `--cov-fail-under=80`. To raise the floor, add tests.

## Two CI jobs report and cannot fail

- The broad `schemathesis run --checks=all` step in `ci-cd.yml` ends in
  `|| true`. The narrower `pytest tests/test_contract.py` job is the enforced one.
- `mutmut` runs in CI and its step also ends in `|| true`, against
  `engine/hydroma/{models,soil,climate_adaptation}` only.

Treat both as **not enforced**. Do not describe them as gates.

## `tests/test_contract.py` is broken for CI

Lines 12 and 22 hardcode `D:/eco_nojin`. That is a relative path on any
non-Windows runner, so the file cannot pass in CI as written. Fix it before
relying on it.

---

## Deployment is not available

Staging and production are **disabled**. There is no immutable artifact promotion
and no reviewer gate.

A Helm chart exists at `helm/eco-nojin/` and is **not applied** — `deploy/k8s/`
holds only `.gitkeep` and there are no staging or production namespaces. A
chance that a manifest is written does not mean an environment exists. Do not
describe intent as status.

External Secrets Operator is **not wired**: 0 references under `deploy/`. Treat
it as unimplemented, not as configured-but-idle.

---

## How to work

1. **Branch** `feature/{ticket}-{desc}` from `main`.
2. **Commit** Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
3. **PR** targets `main`; CI green and one review. Squash merge, delete the branch.
4. **Release** an immutable `vX.Y.Z` tag → GitHub Release.

### Rules that are not negotiable

- **Never commit `.env`.** It is in `.gitignore`.
- **Never hardcode a secret.** Go through `get_settings()`.
- **Gate new behaviour behind a feature flag** — the `ENABLE_*` settings.
- **Add a correlation id to logs** — read `X-Request-ID` from the request.
- **Write contract tests for new endpoints** — `tests/test_contract.py`.
- **Update the OpenAPI schema after an API change** —
  `python scripts/generate_openapi_schema.py`.
- **Write an ADR for an architectural decision** — `docs/adr/NNNN-title.md`.
- **Prefer composition over inheritance** — inject through FastAPI `Depends`.
- **Use structured logging** — `logger.info("event", extra={"key": value})`.
- **Handle errors explicitly** — custom exceptions carrying an error code.

### The measurement rule

**Every figure in a document needs a command that reproduces it.** A number you
cannot regenerate is an assertion, not a finding. Derive it from the source of
truth, or mark it `NOT VERIFIED` and say why.

Label every figure `measured` (taken from a primary source) or `estimated` (an
assumption). Never present an estimate as a measurement. Cite a primary source
with a retrieval date.

**A report describes the repository on its date.** When a report and the code
disagree, the code wins and the report is history. Never cite a dated report as
current state.

**Record negative results.** "Could not verify" is required output. Do not delete
a failed lookup to make a document look clean.

### The standard rule

**A standard is only real if a test enforces it.** Every rule under
`docs/standards/` names the test that blocks its violation. A rule with no test
is a wish. If you add a rule, add the test in the same change.

---

## Conventions that were removed, and why

These were true on 2026-09-29 and are no longer true of this tree. Do not
reintroduce them, and do not write code as if they hold:

- **Zustand** — never existed in this project. The frontend used `useState` plus
  React context. There is no frontend now.
- **React Hook Form** — declared in the frontend `package.json` and imported in
  zero files. The frontend is gone.
- **Zod client-side validation** — did not exist. Zod was used server-side only.
- **GraphQL / gRPC** — there is no GraphQL layer. `strawberry`, `graphene` and
  `graphql` have 0 references in the gateway. The single `grpc` hit is
  `services/api_gateway/tracing.py:39`, an OpenTelemetry OTLP **trace exporter**
  import, not a server.
- **`services/api_gateway/security/`, `cache/`, `resilience/` directories** — never
  existed. `security` is the module `services/api_gateway/security.py`; cache and
  resilience are the settings `enable_cache` and `enable_retry`.
- **Chao Mesh, External Secrets** — 0 references under `deploy/`.
- **Workbox** — the PWA used Serwist, a Workbox fork. Both are gone with the app.

`docs/ENGINEERING_INDEX_FA.md` previously carried a claim about 20 of 20 broken
links in this file. That is history, not a current gap.

---

## A trap in this repository

Routes in the deleted frontend lived under directories literally named
`[locale]`, and PowerShell treats `[...]` as a character class. `Select-String
-Path` **silently skipped every such file and still exited 0**. A zero survived
that mistake; a positive count did not. If you ever recreate a bracketed
directory, use `Select-String -LiteralPath` or read the file directly.

The same trap exists in **regex-based extraction**: a non-greedy pattern scoped to
one rule can run past its closing brace into the next one. Prefer a parser over a
regex when the structure matters.
