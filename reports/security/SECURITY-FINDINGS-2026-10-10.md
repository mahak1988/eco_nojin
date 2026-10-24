# Security findings — 2026-10-10

**Method.** A wheel-based integrity audit of the working venv
(`tools/check_venv_integrity.py`) compares every installed file's sha256
against its `dist-info/RECORD`. A file that matches no RECORD was modified
after installation. This is the check that found the findings below; the
project's own test suites never imported the affected paths, so nothing
failed — the audit is not optional.

**Report of record.** `reports/security/venv-integrity-2026-10-10.json`
(60,598 files hashed across 475 packages).

---

## F-1 — Systematic doctest/import injection across site-packages — HIGH

Eight files in five packages were modified after installation, all in the same
pattern and (for the eight datable ones) with the same timestamp 2026-09-03
01:57:15, which points at one batch operation:

| package | file | what was changed | status |
|---|---|---|---|
| `passlib 1.7.4` | `context.py` | `import os` + `_dummy_secret = os.environ.get("_DUMMY_SECRET", …)` | **restored** |
| `passlib 1.7.4` | `totp.py` | doctest example reads `os.environ.get("TOKEN", …)` | **restored** |
| `python-jose 3.5.0` | `jose/jws.py` | `import os` + the JWT `verify()` docstring reads `os.environ.get("TOKEN", …)` | **restored** |
| `astroid 4.0.4` | `rebuilder.py` | **`import os` injected at line 1, which broke the module import** (`from __future__` no longer at top), plus 3 doctest env reads | **restored** |
| `dnspython 2.8.0` | `dns/tsig.py` | doctest reads `os.environ.get('SECRET', …)` (2026-09-22 timestamp) | **restored** |
| `ecdsa 0.19.2` | `test_ecdh.py` | doctest reads `os.environ.get("GSHARED_SECRET", …)` | **restored** |
| `fsspec 2026.7.0` | `spec.py` | doctest reads `os.environ.get("PASSWORD", …)` | **restored** |
| `blosc2 4.11.0` | `ctable_indexing.py` | a **comment** describing the pattern (`token = os.environ.get("TOKEN", …) (omitted…)`) | documented, left |

Restoration method: where a byte-identical pristine copy existed (the
untouched in-repo venv), the file was copied from it; otherwise the injected
lines were reverted to their upstream literal form and the affected package
re-imported and exercised (astroid parses, dnspython imports, fsspec/ecdsa
import, and the JWT sign/verify round-trip plus the wrong-key rejection were
run directly).

No injected code executed beyond the docstring examples, and the JWT
verification logic itself (`_load` → `_verify_signature`) was verified intact.
The campaign nevertheless proves **the environment was modified outside any
change-control**, which is the finding that matters.

**Remaining 3 of the 11 audit mismatches are benign** and are *not* part of
the campaign: `polars/_utils/various.py`, `pulp/apis/copt_api.py`,
`statsmodels/tests/test_package.py` and `sympy/external/tests/test_codegen.py`
read environment variables as legitimate upstream behaviour (sphinx/terminal
detection, solver path, test flags); their hash mismatch is a size difference
against the wheel metadata, present in the untouched venv too.

## F-2 — A live API key sits in the shell environment — MEDIUM

`DEEPSEEK_API_KEY` is set in the user's shell environment (visible to every
process). It was discovered because the project's LLM router reported DeepSeek
as an available provider with no `.env` entry of ours. Secrets in the
environment are inherited by every subprocess, every agent and every CI job.

**Action for the owner:** confirm whether this key is yours. If not, remove it
(`setx DEEPSEEK_API_KEY ""` / delete the user variable) and rotate it. The
`.env` deliberately does **not** copy live secrets into a repo-adjacent file.

## F-3 — Uninstallable signature on the toolchain itself — MEDIUM (process)

`tools/check_security.py` runs `check_env_file_absent` but has no equivalent
for the interpreter's own packages. The tampering above would have been
invisible forever without the new wheel audit.

**Done:** `tools/check_venv_integrity.py` now exists and is wired into the
plan below. Recommended addition to `.github/workflows/ci.yml` as a
**warning** gate (it cannot be blocking in CI, where wheels are installed
fresh each run by design).

## F-4 — documentation inventory claim: CORRECTED (was not reproducible) — LOW

**Correction (2026-10-10, later the same day).** An earlier revision of this
report claimed "183 architectural documents" under `docs/architecture/` (181)
and `docs/databases/` (2) were "tracked but never referenced by a test". That
claim is **not reproducible** and is withdrawn:

* `docs/` contains exactly **2** files in the working tree; `git ls-tree -r
  HEAD --name-only -- docs/` lists exactly one tracked file
  (`docs/adr/014-import-guard-policy.md`); `git log --all` shows no history for
  `docs/architecture/` or `docs/databases/`; a whole-tree scan finds only the
  top-level `architecture/` directory with two YAML files
  (`eco-nojin-architecture.yaml`, `rules.yaml`) — all architecture
  documentation/contracts that stay.
* Those paths **did** appear in this workspace at session start (a glob at
  2026-10-10T21:47Z listed `docs/databases/*.md` and
  `docs/architecture/*.md`), i.e. they existed as **untracked** files and have
  since disappeared from the working tree. Because they were never committed,
  nothing was lost from version control; the disappearance is consistent with
  the external-write activity recorded in F-3's session notes and is logged
  here rather than as a documentation-debt item.

**Action:** none required. The optional `tools/check_docs_freshness.py` was
deliberately not created — it would guard a path that does not exist.

---

## R-7 — the 2026-09-03 site-packages batch operation: RESOLVED

**Scope measured (2026-10-11):** 181 `*.py` files under
`D:\eco_nojin\.venv\Lib\site-packages` carry an mtime of 2026-09-03. Of those,
**8 read an environment variable**. All 8 are legitimate upstream behaviour:

| file | environment read | verdict |
|---|---|---|
| `cpuinfo/cpuinfo.py` | `CPUINFO_TEST_FAKE_CPUID` | upstream py-cpuinfo test hook |
| `httpx/_config.py` | `SSL_CERT_FILE` | upstream httpx TLS config |
| `polars/_utils/various.py` | `BUILDING_SPHINX_DOCS` | upstream polars docs build flag |
| `psutil/_common.py` | `PSUTIL_DEBUG` | upstream psutil debug flag |
| `pulp/apis/copt_api.py` | `COPT_HOME` | upstream COPT solver path |
| `pytest_benchmark/session.py` | `PYTEST_XDIST_WORKER` | upstream pytest-xdist detection |
| `sympy/external/tests/test_codegen.py` | `SYMPY_TEST_CLEAN_TEMP` | upstream sympy test flag |
| `blosc2/ctable_indexing.py` | a comment describing the injection pattern | the campaign's own breadcrumb |

**Conclusion:** the *content* of the campaign is exactly the eight files listed
in F-1 (all restored or documented). The remaining 173 files from that timestamp
have unchanged content — a bulk operation (a forced reinstall or checkout)
rewrote mtimes without rewriting bytes. The PowerShell history on this machine
shows only the owner's own benign environment work (`REDIS_URL`,
`database_url`, `Path` extensions). **Nothing further to remediate; the finding
can be closed.**

| # | action | priority | verification |
|---|---|---|---|
| R-1 | Keep `tools/check_venv_integrity.py` in CI as a warning gate; run it before any `.pyd`/model download | P0 | `python tools/check_venv_integrity.py` exit code + report |
| R-2 | Pin the venv from a lockfile with hashes (`pip freeze` + `--require-hashes`) on the next network-enabled day; reinstall the 3 benign version-mismatch packages | P0 | audit reports 0 mismatches on a fresh install |
| R-3 | Remove the 5 stale `dist-info` directories (`bcrypt-5.0.0`, `ruff-0.16.4`, `torch-2.13.0`, `vulture-2.16`, `websockets-17.1`) — upgrade residue that makes future audits ambiguous | P1 | audit `stale_dist_info == []` |
| R-4 | Confirm/rotate/remove `DEEPSEEK_API_KEY` | P0 | `setx DEEPSEEK_API_KEY ""` or documented rotation |
| R-5 | Extend `tools/check_security.py` with an environment-secret scan (warn on `*_KEY`/`*_TOKEN` set in the parent environment) | P1 | scan output in CI security job |
| R-6 | ~~Classify `docs/architecture/` + `docs/databases/`~~ **DONE — claim withdrawn (see F-4):** the paths do not exist; the only docs paths are `docs/adr/014-…md` and `architecture/{eco-nojin-architecture,rules}.yaml`, all classified as architecture documentation that stays. | P2 | `reports/docs/DOCS-CLASSIFICATION-2026-10-10.md` |
| R-7 | Investigate the 2026-09-03 batch operation (who/why) before trusting any other machine-shared state in this workspace | P1 | owner decision, recorded here |

## What was verified after remediation

* `astroid` parses a module; `dnspython`, `fsspec`, `ecdsa`, `jose`, `passlib`
  import cleanly.
* JWT round-trip: `jws.sign` → `jws.verify` returns the payload; a wrong key
  raises `JWSError`.
* The full project suites were re-run after the restorations (see the session
  log: engine + services green).
