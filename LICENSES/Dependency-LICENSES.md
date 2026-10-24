# Dependency License & ZED Compliance Audit

> **Task:** W1-2 (License & ZED audit, ZED §د.5) · **Agent:** A-LICENSES · **Date:** 2026-10-10
> **Spec:** `docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md` (ECO-MASTER-v2.0-ZED-UNIFIED) — §2.2ب
> (approved stack), §2.2الف (forbidden categories), §2.2ج (data/download rules), §2.2د (Python
> dependency rules, item 5 = documentation in `LICENSES/`).
> **Method:** declarations audited from `pyproject.toml` (`[project] dependencies` +
> `optional-dependencies`), `requirements.txt`, `requirements-dev.txt`; runtime-only packages
> verified from `D:\eco_nojin\.venv\Lib\site-packages\*.dist-info` (shipped `METADATA` license
> fields + shipped `LICENSE*` files, resolved via `importlib.metadata`).
> **Verification policy:** a license is recorded only when verified from a LICENSE file shipped in
> installed package metadata; everything else reads **UNVERIFIED — verify before publishing**.
> **Legend:** see `LICENSES/README.md` (ZED-APPROVED / ZED-OPTIONAL / ZED-VIOLATION).

## Audit table

| Package | Declared version spec | Source (pyproject line / requirements line / venv runtime) | OSI license | ZED status | Note |
|---------|----------------------|------------------------------------------------------------|-------------|------------|------|
| numpy | >=1.26 | pyproject.toml:26; requirements.txt:6 | BSD-3-Clause (verified, shipped LICENSE.txt) | ZED-APPROVED | §2.2ب lists NumPy/SciPy/pandas (BSD) as mandatory compute layer. Runtime: 2.3.5. |
| scipy | >=1.11 | pyproject.toml:27; requirements.txt:7 | BSD-3-Clause (verified, shipped LICENSE.txt) | ZED-APPROVED | §2.2ب mandatory compute layer. Runtime: 1.16.3. |
| pandas | >=2.0 | pyproject.toml:28; requirements.txt:8 | BSD-3-Clause (verified, shipped LICENSE) | ZED-APPROVED | §2.2ب mandatory compute layer. Runtime: 2.3.3. |
| pydantic | >=2.0 | pyproject.toml:33; requirements.txt:13 | MIT (verified, shipped LICENSE) | ZED-APPROVED | Marked approved per task table decision; not literally enumerated in §2.2ب — MIT, works offline, sits in the approved MIT stack layer. Runtime: 2.13.4. |
| duckdb | >=0.10 | pyproject.toml:29; requirements.txt:9 | MIT (verified, shipped LICENSE) | ZED-VIOLATION | server/cloud DB category forbidden by spec §2.2الف; removal is Wave 3 decision (the MIT license itself is compliant; the objection is the category). Runtime: 1.5.5. |
| supabase | >=2.0 | pyproject.toml:30; requirements.txt:10 | MIT (verified, shipped LICENSE) | ZED-VIOLATION | server/cloud DB category forbidden by spec §2.2الف; removal is Wave 3 decision (the MIT license itself is compliant; the objection is the category). Runtime: 2.31.0. |
| requests | >=2.31 | pyproject.toml:31; requirements.txt:11 | Apache-2.0 (verified, shipped LICENSE + NOTICE) | ZED-OPTIONAL | HTTP client is not itself in §2.2ب; acceptable only on gated, non-core paths per §2.2ج.3 — engine core must stay HTTP-framework free per AR-03. Runtime: 2.34.2. |
| httpx | >=0.25 | pyproject.toml:32; requirements.txt:12 | BSD-3-Clause (verified, shipped LICENSE.md) | ZED-OPTIONAL | Same class as `requests`: offline-capable client, confined to non-core paths per §2.2ج.3 / AR-03. Runtime: 0.28.1. |
| loguru | >=0.7 | pyproject.toml:34; requirements.txt:14 | UNVERIFIED — verify before publishing | ZED-OPTIONAL | Core-declared logging dependency, but NOT installed in the audited venv (`importlib.metadata`: PackageNotFoundError), so no shipped metadata exists to verify from. Confirm license plus §2.2د.3 offline behaviour before publishing. |
| cryptography | >=41.0 | requirements.txt:15 (not declared in pyproject.toml) | Apache-2.0 OR BSD-3-Clause, dual-licensed (verified, shipped LICENSE + LICENSE.APACHE + LICENSE.BSD) | ZED-OPTIONAL | Dual license, recipient's choice; offline-capable. Missing from `pyproject.toml` → §2.2د.4 registration gap. Runtime: 50.0.0. |
| pytest | >=7.4 | pyproject.toml:39; requirements.txt:18 | MIT (verified, shipped LICENSE) | ZED-APPROVED | §2.2ب lists pytest (MIT) in the development/test layer. Runtime: 9.1.1. |
| hypothesis | >=6.0 | requirements.txt:36; requirements-dev.txt:8 (not declared in pyproject.toml) | MPL-2.0 (verified, shipped LICENSE.txt) | ZED-APPROVED | §2.2ب lists hypothesis in the test layer, but the spec table states MIT while the installed wheel ships MPL-2.0 — both OSI-approved, file-level copyleft, acceptable for a test-only tool; discrepancy flagged. Missing from pyproject → §2.2د.4 registration gap. Runtime: 6.168.0. |
| pytest-cov | >=4.1 | pyproject.toml:40; requirements.txt:19 | MIT (verified, shipped LICENSE) | ZED-OPTIONAL | Dev/test tooling; not enumerated in §2.2ب but in no §2.2الف forbidden category. Runtime: 6.0.0. |
| pytest-asyncio | >=0.21 | pyproject.toml:41; requirements.txt:20 | Apache-2.0 (verified, shipped LICENSE) | ZED-OPTIONAL | Dev/test tooling; not enumerated in §2.2ب but in no §2.2الف forbidden category. Runtime: 1.4.0. |
| mypy | >=1.5 | pyproject.toml:42; requirements.txt:21 | MIT (verified, shipped LICENSE) | ZED-OPTIONAL | Dev/type-check tooling; not enumerated in §2.2ب but in no §2.2الف forbidden category. Runtime: 1.13.0. |
| ruff | >=0.1.0 | pyproject.toml:43; requirements.txt:22 | MIT (verified, shipped LICENSE) | ZED-OPTIONAL | Dev/lint tooling; not enumerated in §2.2ب but in no §2.2الف forbidden category. Runtime: 0.11.2 (a stale 0.16.4 dist-info directory is also present in the venv). |
| pybind11 | >=2.11 | pyproject.toml:46; requirements.txt:25 | BSD-3-Clause (verified, shipped LICENSE) | ZED-OPTIONAL | §2.2ب C++ Build layer lists CMake/pybind11 as optional (pybind11 itself is BSD, the GPL in that row refers to GCC/Clang). Runtime: 3.1.0. |
| ninja | >=1.11 | pyproject.toml:47; requirements.txt:26 | UNVERIFIED — verify before publishing | ZED-OPTIONAL | Build tool; not installed in the audited venv, no shipped metadata to verify from. |
| cmake | >=7.0 | pyproject.toml:48; requirements.txt:27 | UNVERIFIED — verify before publishing | ZED-OPTIONAL | §2.2ب explicitly lists CMake in the optional C++ Build layer; not installed in the audited venv, no shipped metadata to verify from. |
| torch | >=2.0 | pyproject.toml:51; requirements.txt:30 | Apache-2.0 (primary) plus bundled Apache-2.0/LLVM-exception, BSD-2-Clause, BSD-3-Clause, MIT and BSL-1.0 components (verified, shipped LICENSE) | ZED-OPTIONAL | ML extra; the §2.2ب ML row lists scikit-learn, torch is not enumerated there but is not a §2.2الف forbidden category either — local, offline-capable, very heavy dependency worth a Wave 3 review. Runtime: 2.13.0+cpu. |
| transformers | >=4.33 | pyproject.toml:52; requirements.txt:31 | Apache-2.0 (verified, shipped LICENSE) | ZED-OPTIONAL | Same class as torch: local ML extra, no forbidden category. Runtime: 5.16.1. |
| sentence-transformers | >=2.2 | pyproject.toml:53; requirements.txt:32 | Apache-2.0 (verified, shipped LICENSE + NOTICE) | ZED-OPTIONAL | Same class as torch: local ML extra, no forbidden category. Runtime: 6.0.0. |
| qdrant-client | >=1.6 | pyproject.toml:54; requirements.txt:33 | Apache-2.0 (verified, shipped LICENSE) | ZED-VIOLATION | Client for Qdrant, a server-side vector database — same server-DB category as duckdb/supabase under §2.2الف; the Apache-2.0 license itself is compliant, the category is the objection. Confirm the Wave 3 decision (it parallels the duckdb/supabase ruling). Runtime: 1.19.1. |
| python-telegram-bot | >=21.0 | pyproject.toml:57 (telegram extra; not in requirements files) | UNVERIFIED — verify before publishing | ZED-VIOLATION | Talks to the Telegram Bot API, a cloud service requiring a bot token and internet — §2.2الف cloud-API category and conflicts with §2.2د.2 (must work without API key). License unverified: not installed in the audited venv. |
| pytest-xdist | >=3.5 | requirements-dev.txt:9 (not declared in pyproject.toml) | MIT (verified, shipped LICENSE) | ZED-OPTIONAL | Dev/test tooling; not enumerated in §2.2ب but in no §2.2الف forbidden category. Missing from pyproject → §2.2د.4 registration gap. Runtime: 3.8.0. |
| pytest-html | >=4.0 | requirements-dev.txt:10 (not declared in pyproject.toml) | UNVERIFIED — verify before publishing | ZED-OPTIONAL | Dev/reporting tooling; not installed in the audited venv, no shipped metadata to verify from. |
| types-requests | >=2.31 | requirements-dev.txt:13 (not declared in pyproject.toml) | Apache-2.0 (verified, shipped LICENSE — typeshed project) | ZED-OPTIONAL | Type stubs only, no runtime code. Missing from pyproject → §2.2د.4 registration gap. Runtime: 2.33.0.20260712. |
| types-pyyaml | >=6.0 | requirements-dev.txt:14 (not declared in pyproject.toml) | UNVERIFIED — verify before publishing | ZED-OPTIONAL | Type stubs only; not installed in the audited venv, no shipped metadata to verify from. |
| pint | UNDECLARED — absent from pyproject.toml and requirements*.txt | venv runtime (D:\eco_nojin\.venv) | BSD-3-Clause (verified, shipped LICENSE) | ZED-OPTIONAL | §2.2ب lists pint (BSD) as recommended-optional. **UNDECLARED-DEPENDENCY debt.** Not imported anywhere in the repository (grep for `import pint` / `from pint`: 0 matches) — installed runtime-only. Runtime: 0.26.1. |
| sqlalchemy | UNDECLARED — absent from pyproject.toml and requirements*.txt | venv runtime (D:\eco_nojin\.venv) | MIT (verified, shipped LICENSE) | ZED-OPTIONAL | §2.2ب lists SQLAlchemy 2.x (MIT) as optional ORM/DB layer. **UNDECLARED-DEPENDENCY debt.** Active runtime dependency: imported across `database/`, `services/*`, `alembic/` and `engine/ports/persistence.py` without any declaration. Runtime: 2.0.52. |
| numba | UNDECLARED — absent from pyproject.toml and requirements*.txt | venv runtime (D:\eco_nojin\.venv) | BSD (2-Clause text as shipped; metadata `License: BSD`) — verified, shipped LICENSE | ZED-OPTIONAL | §2.2ب lists numba (BSD) as optional speed layer. **UNDECLARED-DEPENDENCY debt** (additional finding beyond the two named in the task brief): imported by `engine/hydroma/cpp_bridge/{indices,soil,hydrology}_{fast,fallback}.py` and `engine/hydroma/cpp_bridge/tests/test_benchmarks.py` (7 files). Runtime: 0.62.1. |

**Coverage: 31 packages.**

## Findings

### (a) Undeclared runtime dependencies (UNDECLARED-DEPENDENCY debt)

- **pint 0.26.1** — installed in `D:\eco_nojin\.venv`, declared nowhere. §2.2ب lists pint (BSD) as
  recommended-optional, so the license is fine; the gap is the missing declaration (§2.2د.4).
  No import sites in the repository — installed runtime-only.
- **sqlalchemy 2.0.52** — installed, declared nowhere, yet actively imported across `database/`,
  `services/*`, `alembic/` and `engine/ports/persistence.py`. §2.2ب lists SQLAlchemy 2.x (MIT) as
  optional, so the license is fine; the declaration gap is the debt.
- **numba 0.62.1** — installed, declared nowhere, imported by `engine/hydroma/cpp_bridge/` fast and
  fallback modules (7 files). §2.2ب lists numba (BSD) as optional; declaration gap is the debt.
  (Flagged additionally to the two packages named in the task brief because engine core files
  import it.)
- Also observed installed-and-imported but undeclared (all in §2.2ب optional rows, not covered by
  this table — recommend a follow-up pass): `pyyaml`, `aiohttp`, `rasterio`, `shapely`,
  `geopandas`, `matplotlib`, `scikit-learn`.

### (b) ZED violations present in the dependency list

- **Core dependencies:** `supabase` (pyproject.toml:30 / requirements.txt:10) and `duckdb`
  (pyproject.toml:29 / requirements.txt:9) — server/cloud DB category forbidden by spec §2.2الف;
  removal is a Wave 3 decision.
- **Optional extras also flagged:** `qdrant-client` (ml extra) — server-side vector DB, same
  server-DB category reasoning as duckdb/supabase; `python-telegram-bot` (telegram extra) — cloud
  API requiring a bot token (§2.2الف cloud-API category, conflicts with §2.2د.2).

### (c) Packages whose license could not be verified

Not installed in the audited venv, so no shipped LICENSE/metadata to verify from — each reads
**UNVERIFIED — verify before publishing**: `loguru` (core dependency), `ninja`, `cmake`,
`pytest-html`, `types-pyyaml`, `python-telegram-bot`.

### (d) Registration gaps against ZED §2.2د.4 (dependencies must be registered in pyproject.toml)

Declared in `requirements*.txt` but missing from `pyproject.toml`: `cryptography`, `hypothesis`,
`pytest-xdist`, `pytest-html`, `types-requests`, `types-pyyaml`. Additional discrepancy: spec
§2.2ب lists hypothesis as MIT while the installed wheel ships MPL-2.0.
