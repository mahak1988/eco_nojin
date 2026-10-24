# LICENSES/

Dependency license and ZED-compliance documentation for Eco Nojin / HyDroMA.

## Purpose

This directory implements **ZED rule §2.2د item 5**: every Python dependency must be
documented in `LICENSES/`. The source spec is
`docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md` (ECO-MASTER-v2.0-ZED-UNIFIED):

- **§2.2ب** — approved FOSS stack (what is allowed, and at which layer).
- **§2.2الف** — forbidden categories (paid / cloud / server-DB / SaaS).
- **§2.2د** — Python dependency rules (1. OSI license, 2. no API key, 3. offline after install,
  4. registered in `pyproject.toml`, 5. documented in `LICENSES/`).
- **§2.2ج** — data rules (no live downloads in the scientific core; downloads only gated and
  outside the core).

It fulfils task **W1-2 (License & ZED audit, ZED §د.5)** of
`reports/eco-nojin/EXECUTION-PLAN-v1.md:20`. This is a documentation-only deliverable: no code,
`pyproject.toml`, or `requirements*.txt` was modified.

## Contents

| File | Purpose |
|------|---------|
| `README.md` | This file: purpose, method, legend. |
| `Dependency-LICENSES.md` | Per-package audit table (package, declared version spec, declaration source, OSI license, ZED status, notes) plus findings. |

(The execution plan names the second file `DEPENDENCY-LICENSES.md`; the delivered file is
`Dependency-LICENSES.md`, same content and location `LICENSES/`.)

## Method (source of truth)

1. **Declared dependencies** were taken from, in order of authority:
   - `pyproject.toml` — `[project] dependencies` (lines 26–34) and
     `[project.optional-dependencies]` (lines 37–58: `dev`, `cpp`, `ml`, `telegram`);
   - `requirements.txt`;
   - `requirements-dev.txt`.
2. **Runtime-only packages** (installed but not declared) were verified from the audited virtual
   environment `D:\eco_nojin\.venv` — specifically
   `D:\eco_nojin\.venv\Lib\site-packages\*.dist-info`, using the shipped `METADATA`
   (`License`, `License-Expression`, `License ::` classifiers) **and** the shipped
   `LICENSE*` / `licenses/` files, plus `importlib.metadata` for resolved runtime versions.
3. **Verification policy (fail-closed):** a license is stated only when it can be verified from a
   LICENSE file shipped in the installed package metadata. Any license claim that could **not** be
   verified this way is written as **UNVERIFIED — verify before publishing**. Nothing is guessed.

## Legend — ZED status column of `Dependency-LICENSES.md`

| Status | Meaning |
|--------|---------|
| **ZED-APPROVED** | The dependency is listed in the approved stack, spec §2.2ب (e.g. Python/NumPy/SciPy/pandas — BSD, mandatory compute layer; pytest/hypothesis — development/testing layer). |
| **ZED-OPTIONAL** | Allowed as an extra/optional package per spec §2.2ب (GIS row, SQLAlchemy ORM row, C++ Build row, scikit-learn/numba/Matplotlib/pint rows), or dev-only tooling that belongs to none of the §2.2الف forbidden categories. |
| **ZED-VIOLATION** | Falls in a forbidden category of spec §2.2الف (paid / cloud / server-DB / SaaS): server databases, cloud APIs that need a key or the internet, commercial software, commercial compilers, SaaS services. |

## Audit record

- **Agent:** A-LICENSES · **Date:** 2026-10-10 · **Scope:** documentation only (no code changes).
- **Coverage:** 31 packages = every declared dependency (pyproject + requirements.txt +
  requirements-dev.txt) plus runtime-only undeclared packages found installed in
  `D:\eco_nojin\.venv`.
- **Out-of-scope:** transitive dependencies of the declared packages (e.g. `urllib3`, `certifi`,
  `packaging`) are not individually enumerated here; they inherit the obligations of the direct
  dependency that pulled them in.
