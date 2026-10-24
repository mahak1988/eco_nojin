# EXTERNAL ALIGNMENT PLAN v1 — closing weaknesses by linking the right platforms

Document id: `ECO-XPLAN-v1` · Date: 2026-10-10 · Companion to `DEVELOPMENT-PLAN-v2.md` (Waves 5–8) and `FORMULA-VALIDATION-REGISTER.md`
Principle: **a "link" must not become a runtime dependency of the scientific core.** Every item below is either (A) wiring a platform that is *already installed and measured unused*, (B) a **dev/test-only** reference package (never imported by `engine/` at runtime; tests skip with a clear reason when absent), or (C) a **CI-only** platform job. ZED §2.2 is preserved in all three cases; the core stays offline at runtime.

---

## 1. Measured inventory (this host, 2026-10-10 — no assumptions)

| Measurement | Result | Consequence for this plan |
|---|---|---|
| `pint` installed (0.26.1) | **0 imports in the whole engine** | the spec's ECO-05 DoD ("واحدها با pint/UnitRegistry چک می‌شوند") is unmet *while the tool is installed* — the cheapest gap in the project |
| Distinct unit strings in `engine/` | **16** (10 parse in pint; 6 need domain definitions: `kg/m3`, `FTE`, `fraction of TAW`, `curve number points`, `kg per person per year`, `fraction of consumption`) | pint integration is *small and completable*, not a rewrite |
| Gateway unit path | `engine/gateway/__init__.py:2008-2022` multiplies scalars by a hand-written `UnitSpec.si_equivalent`; no dimensional check anywhere | exactly the boundary where unit-class defects (m/cm, %/m·m⁻¹, MJ vs W·m⁻², °C vs K) should be caught structurally |
| Geo-package stack installed | **geopandas 1.1.4, shapely 2.1.2, pyproj 3.7.2, fiona 1.10.1 — 0 engine imports**; rasterio (4) and xarray (5) *are* used | §4.3 "SQLite + GeoPackage" is satisfiable with zero new dependencies |
| sklearn | 1 engine import (`plant_neuro/voc.py`) | available for PTF fitting + uncertainty intervals (ECO-11) |
| `pyRothC` installed | an **empty namespace package** — the "real model" link is broken | a false link that must be retired, not another dependency |

---

## 2. Tier A — wire what is already installed (no new dependency, fully offline)

| ID | Weakness (gap) | Platform | Design (behaviour-preserving) | Evidence produced | Gaps closed |
|---|---|---|---|---|---|
| **X-1** | whole unit-defect class: `SOIL_AMENDMENT` m/cm (100×), Kirpich %/metric, three eq.-52 copies missing 0.408 (+145 %), Ra vs Rs/W·m⁻² substitutions, curvature 1/m + 1/m² | **pint** | new `engine/gateway/pint_audit.py`: a `UnitRegistry` with the 6 domain definitions, `parse_unit(s)`, `check(name, value, unit_str, expected_str) -> problems`, `convert(...)`; wired **inside `_normalize_units` as an audit that records problems without changing the multiplication path** (unit behaviour identical — brake 2 respected; conversion adoption is a later, mandated step) | `engine/tests/test_pint_unit_gate.py`: round-trips (mm↔m, W·m⁻²↔MJ·m⁻²·day⁻¹, %↔m/m, °C↔K), deliberate incompatibility cases reproducing the four audit defects as *caught* problems, and a **coverage test that every unit string in the engine parses or is declared** | G-Z5, G-H3 (prevention), G-H8, G-H11 |
| **X-2** | GeoPackage/spatial (§4.3), raster SCS-CN unvalidated | **geopandas + shapely + pyproj + fiona** (all installed) | `adapters/persistence/geopackage_adapter.py` writing the spec's SQLite schema + a GeoPackage mirror for spatial datasets; CRS-validated reads in the ingestion path | round-trip test vector/raster + CRS mismatch rejection | G-D1/G-D2 (spatial half), G-S1 |
| **X-3** | pedotransfer regression coefficients unvalidated; ks_cm_per_day 4.1e38 | **scikit-learn** + the **published Saxton & Rawls AWC table already pinned in `engine/strict_tests/conftest.py:87`** | fit θ/θs/AWC regressions to the published table (cross-validated), ship as a frozen artifact with provenance; retire or quarantine the unattributed log-linear Ks | a fit-vs-published test (R², residual bands) replacing "no test reads it" | G-H4, G-S6 (PTF part) |
| **X-4** | uncertainty is `NOT_ESTIMATED` by default (ECO-11) | **scikit-learn (quantile/GBR) + numpy** | `engine/hydroma/uncertainty/`: prediction intervals for the fitted PTF and regression-based indicators, emitted into the gateway's existing `UncertaintySpec` | a closed-form test case (Gaussian CI) plus the PTF interval test | G-S7 |
| **X-5** | output QC / pipeline artefacts | **xarray + netCDF4 + cf_xarray** | CF-convention validation on pipeline outputs (names/units/CRS), NetCDF/GPKG export in `data/processed` per the §4.2 layout | a QC test that rejects a mislabelled unit | G-Z4 (partially), G-D4 |

## 3. Tier B — dev/test-only external references (skipped when absent, never runtime)

| ID | Weakness (gap) | Platform (candidate — availability verified in §6) | Integration | Evidence produced | Gaps closed |
|---|---|---|---|---|---|
| **X-6** | the whole non-PM ET0 family is **method-only**: Priestley–Taylor, Blaney–Criddle, Turc, Makkink, and the *individual* Rnl/Rn terms | **PyETo (`pyet` 1.5.0, MIT)** — an independent implementation of FAO-56 eq. 6/52/35 + PT/Makkink/BC/Turc whose own suite pins Example 18 = 3.9 | `requirements-dev` extra `ref`; tests import it *inside* the test function and `pytest.importorskip("pyet")`; feed the Example 18 + Example 20 rows from the existing CSV (**inputs must be `pandas.Series`; latitude in radians**) and assert within tolerance | one parity suite turning ~8 "PARTIAL/UNVALIDATED" entries into `VALIDATED_METHOD_CONFORMANCE` with a *third-party* (not in-repo) reference | G-S1, climate section of the register, G-H8 (clamp deviation measured against PyETo too). Pan evaporation and eq. 47 remain ours to implement |
| **X-7** | SPI/WB/WP have no benchmark beyond in-repo checks (last ECO-10 weakness) | **`climate_indices`** (CDAC; independent SPI/SPEI with gamma + zero term; published NOAA-NCEI/SPEIbase fixtures) | parity test at fixed scales on labelled synthetic series; agreement band documented and published in the register | `VALIDATED_METHOD_CONFORMANCE` **+ cross-implementation agreement** (honest upgrade, still not a published table). **Method difference is explicit: their gamma fit is method-of-moments on calendar-month subsets with ±3.09 clipping vs our MLE over the whole record with ±6.36 — so a tolerance band, never equality. Pin `<3.0.0`** |
| **X-8** | VG parameters + PTF rest on withdrawn attribution | **`rosetta-soil`** v0.3.2 (USDA-ARS; CC0; numpy-only; bundles the trained Rosetta 1/2/3 ANN weights) | reference comparison for the 12 USDA textures + the Saxton-Rawls AWC path with class-level tolerances and bootstrap ensembles | replaces `design_assumption` rows with a Rosetta-referenced comparison (a PTF *comparison*, still not a soil-specific calibration) | G-S6 (VG table), G-H4 |
| **X-9** | texture classification: 782/5151 compositions fall through to an undocumented `loam` | **`soiltexture`** **v1.0.4, GPL-3.0** — point-in-polygon USDA/FAO/ISSS triangle (dev-only; legal sign-off required) | cross-check `classify_texture` over the full 5151-integer grid; disagreements pinned as a table with both tie-break rules documented | a corrected, cited lookup table with a boundary test | G-S6 (texture) |
| **X-10** | model cards carry **fabricated citations** | **doi.org HEAD resolution via `requests`** (no new install; CI-only network; covers Crossref *and* DataCite/Zenodo — a Crossref-only checker false-negatives Zenodo) | `tools/check_citations.py`: extract DOIs from `engine/models/cards/*.md` + `indicators/*.yaml`, resolve each by `HEAD https://doi.org/{doi}` (302 = exists, 404 = unresolvable), print unresolved; ISBNs reported as *unverifiable*, never gating | a CI gate that fails on an unresolvable citation — this class of error becomes structurally impossible. **Already earned: it flags the dead `10.5281/zenodo.4725384` cited in our cards** | G-H1, G-H12 |

## 4. Tier C — platform links in CI and at the boundary

| ID | Weakness | Platform | Design | Effect |
|---|---|---|---|---|
| **X-11** | shipped `.pyd` still uses Hargreaves exponent **0.48** (−4.5 %) while source uses 0.5 | **GitHub Actions + cmake/ninja** (both already in the `cpp` extra) | CI job: configure/build `engine/cpp_core` on `windows-latest`, run the C++ unit tests, **compare the freshly built kernel against the shipped `.pyd`** and fail on divergence; until a release pipeline exists, this is the authoritative parity gate | G-H9 closed by construction (the divergence can no longer ship silently). **Prerequisites: commit `.github/`, fix the `cmake>=7.0` pin (latest is 4.4.4), forbid the `setup.py` `cpp_nojin` path, correct the `.so`→`.pyd` copy instruction** |
| **X-12** | no local raw mirrors → E2E blocked | **Microsoft Planetary Computer STAC (`pystac-client`)**, keyless | ingestion-side only (outside the engine, behind the `--allow-download` flag from Wave 3), writing `data/raw/**` + `.meta.json` sidecars per §4.2 | unblocks ECO-16 without violating ZED §2.2ج |
| **X-13** | provenance of every dependency and model | **PyPI/DOI metadata snapshots** into `LICENSES/` (already scaffolded) | extend the license bill of materials with the new `ref` extra and a DOI list | G-Z6, and the "no undeclared dependency" contract |

## 5. Retire the broken links (honesty first)

| Link | Reality | Action |
|---|---|---|
| `services/scientific_motors/rothc_real.py:125-127` "real model" | the installed `pyRothC` is an **empty namespace package** | remove the claim from the response/docstring, mark RothC `BLOCKED_NO_REFERENCE_IMPLEMENTATION`, and record it in `EQUATION-DIVERGENCE-REGISTER.md` |
| `CANON-006` Mualem 1976 / Carsel & Parrish 1988 | wrong volume/pages and, for the embedded table, a **withdrawn** attribution | corrected by the PHASES agent's card edits; permanently guarded by X-10 |
| `formula_checks.py:211` "FAO publishes 0.48" | FAO publishes 0.5 | PHASES fixed; guarded by the pipeline in X-6 (PyETo pins the same constant) |

## 6. Sequencing and gates

| Wave | Items | Exit gate |
|---|---|---|
| **W9 — unit & spatial wiring** | X-1, X-2 | pint audit lands with all 16 unit strings covered; GPKG round-trip; `_normalize_units` behaviour unchanged (full engine suite green); unit-defect fixtures now *rejected* |
| **W10 — reference packages (dev-only)** | X-6, X-7, X-9 | `pip install -e ".[ref]"`; parity suites pass; every parkinson test skips-with-reason when the package is absent; register re-classes the affected families |
| **W11 — PTF & uncertainty** | X-3, X-4, X-8 | fitted-PTF-vs-published test passes; uncertainty module produces a real estimate for at least one indicator with a closed-form test |
| **W-12 — CI platforms & provenance** | X-5, X-10, X-11, X-12, X-13 | citation checker green; C++ parity gate green (or the divergence documented and quarantined); license register extended; ingestion behind the flag documented |

Metrics to move: `UNPARSED_UNIT_STRINGS 6 → 0` · `families with VALIDATED_EXTERNAL 9 → ≥17` · `phantoms 57 → (X-10 keeps it at 0-new)` · `unit-class defects 5 → 0 structurally` · `CI gates: +3` (citations, C++ parity, GPKG).

## 7. What no link can fix (must stay on the mandate list)
supabase/duckdb removal and SQLite master migration · `_gateway_facade` completion · Gateway public-API migration · real CHIRPS/ERA5/SoilGrids *content* (a platform gives access, not permission to download silently) · the Guttman-1999 SPI *table* (a reference *implementation* is not a published table, and the labels must say so).

## 8. ZED & honesty assurance
- No Tier B package enters `engine/` imports: enforced by extending `tools/detect_imports.py` with an `ENGINE_NO_TEST_REFERENCE_PACKAGES` rule and a CI negative test.
- Every parity test that skips must print the missing package and the gap it would close.
- No status promotion happens "because a package agrees": the register's E/R/I/N classes are updated by a human decision recorded in the gap register, exactly as with the FAO-56 Example-18 anchor.

## 9. Verified availability (research executed 2026-10-10 against PyPI/GitHub/Crossref/DataCite/doi.org and the runner images)

| Candidate | Verified facts (license · deps · offline · installs here) | Method match to our audit items | Verdict for this plan |
|---|---|---|---|
| **`rosetta-soil` v0.3.2** (USDA-ARS, Todd Skaggs) | **CC0 1.0** — the cleanest licence of all candidates · pure Python, numpy only, bundles trained ANN weights, no compiler/network · installs here as-is | implements **Rosetta 1/2/3** (Schaap et al. 2001 JH 251:163-176; Schaap/Nemes/vG 2004 VZJ; Zhang & Schaap 2017 JH 547:39-53), models 2–5, 7 outputs θr/θs/α/n/Ks/K0/L + bootstrap ensembles | **RANK 1 (X-8)** — exact oracle for `SOIL_PARAMETERS_VG` and the Saxton-Rawls path. Beware: the `rosetta` PyPI name is an unrelated BSD toolkit and `pyrosetta` is absent; the real one is `rosetta-soil` |
| **PyETo 1.5.0** (`pyet-org/pyet`, GMD 17:7083-2024) | **MIT** · pure Python · deps numpy/xarray/pandas **all already installed** · zero new install | `pm_fao56` (eq. 6 verbatim), `hargreaves` (eq. 52), `priestley_taylor` (α=1.26), `makkink`, `blaney_criddle` (3 variants), `turc`, `calc_rad_sol_in` (Ångström eq. 35). **Its own test suite pins FAO-56 Example 18 = 3.9 mm/day — independent corroboration of our anchor.** **Missing: pan evaporation and the eq. 47 wind conversion (we must implement those ourselves)** | **RANK 2 (X-6)** — gotchas: inputs must be `pandas.Series`, latitude in **radians** |
| **DOI checker (requests-only)** | zero new installs (`requests` already core) · network **CI-only** | empirically resolves DOIs via `HEAD https://doi.org/{doi}` (302 = exists) — covers Crossref **and** DataCite/Zenodo; Crossref-only would false-negative every Zenodo DOI | **RANK 3 (X-10)** — and it already earned its cost: it found a **genuinely dead DOI in our own model cards: `10.5281/zenodo.4725384`** (404 on Crossref, DataCite and doi.org). ISBNs are *unverifiable* offline → report, don't gate |
| **`soiltexture` v1.0.4** | **GPL-3.0** · pure Python, matplotlib only (already installed) | independent USDA/FAO/ISSS triangle via point-in-polygon (gmassei/SoilTexture tables) | **RANK 4 (X-9)** — uniquely suited to characterise our 782/5151 unclassified gap over the exhaustive grid, but: **legal sign-off before any use beyond local dev/CI** (test-only does not link GPL into the MIT engine), and its own tie-break is *first polygon wins* — undocumented, so disagreements must be pinned as a table, never silently "fixed" |
| **`climate_indices` v2.4.0** (CDAC/NOAA) | BSD-3-Clause + NOAA public-domain notice · pure Python (no numba needed) · deps satisfied **except `h5netcdf`** | SPI/SPEI with gamma **and** the zero term — **but the gamma fit is method-of-moments, not MLE**, fitted **per calendar month**, output clipped **±3.09** (ours: MLE, whole record, ±6.36) | **RANK 5 (X-7)** — parity is a **documented tolerance band**, not equality (state this in the register). **Pin <3.0.0** (3.0.0 unreleased, adds a compiled Rust backend and changes values). Value: published fixtures `ncei_spi`, `speibase`, `noaa-eddi-*`, `pet_literature` |
| **pint 0.26.1** | BSD-3 · **already installed** · pandas/xarray bridges exist (`pint-pandas`, `pint-xarray`) | the only dimensional-algebra interop for our raster/xarray pipeline; astropy pulls `astropy-iers-data` (first-use **download** → ZED would reject) and unyt pulls sympy | **confirmed choice (X-1)**, but note: **pint ≥0.26 requires Python ≥3.12 while `pyproject.toml` declares `requires-python >=3.11`** → either pin `pint<0.26` or raise the floor (a configuration decision, recorded) |
| **Windows `.pyd` CI job** | `windows-latest` = Windows Server 2025 with **MSVC 17.14, CMake 3.31.6, Ninja 1.13.2, Python 3.12.10**; `engine/cpp_core/CMakeLists.txt` needs 3.22 + C++20 + OpenMP + pybind11 (pip-installable, sets `pybind11_DIR`) | can build `hydroma_core.cp312-win_amd64.pyd` and run the 20 C++ parity tests the strict suite currently skips | **feasible but sequenced last (X-11)** — four blockers first: (a) `.github/workflows/` is **untracked** and every job is `ubuntu-latest`; (b) **`pyproject.toml`'s `cpp` extra pins `cmake>=7.0` while the newest cmake on PyPI is 4.4.4 → `pip install .[cpp]` is unsatisfiable** (a real defect to file); (c) `engine/cpp_core/setup.py` is a second, divergent build path (`cpp_nojin`, C++17, only `bindings.cpp` + `nojin_calculator.cpp`) that must not be used for parity; (d) the strict-suite skip reason tells developers to copy a `.so` — on Windows that must be `.pyd` |

## 11. Executability — demonstrated, not asserted (2026-10-10)

| Item | Execution evidence | Outcome |
|---|---|---|
| **X-10 DOI checker** | `tools/check_citations.py` written, 5 offline extraction tests green, then run live | **23 DOIs scanned, 21 DEAD, 2 OK** → immediately produced gap **G-H17** (a P0 fabrication class) |
| **G-H14 (cmake pin)** | `pyproject.toml` `cpp` extra: `cmake>=7.0` → `cmake>=3.22` | **CLOSED** — the extra is installable again; `pip install -e ".[ref,units]"` verified on this host (with `--no-build-isolation`, since PyPI DNS is blocked here) |
| **reference extras** | `pyproject.toml` gains `ref = [pyet>=1.5, climate_indices>=2.4,<3.0, rosetta-soil>=0.3]` and `units = [pint …]`; the three packages are **installed in D:\eco_nojin\.venv** and import cleanly | the parity suites can run locally as well as in CI |
| **CI** | `.github/workflows/ci.yml` gains a `parity` job (three suites, `continue-on-error` while bands are calibrated) and a citation-check step (non-blocking until G-H17 clears); YAML validated (6 jobs) | gates exist; blocking flips are explicit, documented conditions |
| **X-10 remainder + X-1 + X-6/X-7/X-8** | four subagents dispatched in parallel with disjoint file ownership (see dispatch table in §12) | in progress |
| **W5–W7 (PHASES subagent)** | 6 cards corrected; `SOIL_AMENDMENT` 100 → 10 000 kg/ha; checker exponent 0.48 → 0.5 (endpoint now green); three eq.-52 copies routed to the engine (7.05 → 3.97 mm/day); Kirpich duplicate delegates to canonical (23.44 min); pedotransfer Ks gated `UNCONFIRMED` | verified: engine/tests 533 passed · strict 1309 passed · services 792 passed · import-guard 0 violations; **no engine equation changed** |

So the plan is executable: two cheapest items ran in minutes and each produced a measurable improvement (one closed a live unit defect, the other exposed a new P0). The remaining items are gated by the named blockers below — and those gates are *decisions*, not technical obstacles:

1. **`cmake>=7.0` pin** (G-H14) → **CLOSED** in this session.
2. **`.github/` untracked** (G-H16) → a commit decision; no gate runs until then.
3. **`soiltexture` GPL-3.0** → legal sign-off for anything beyond local dev/CI.
4. **pint adoption** → pin/pyversion decision recorded in the `units` extra; the audit wiring stays behaviour-preserving either way.
5. **sklearn PTF / uncertainty** and **STAC ingestion** → user mandate (they change scientific outputs and data provenance respectively).
6. **Everything that touches an equation or a public API** → already recorded in the mandate list (G-H14…H17 style), unchanged by this plan.

## 12. Parallel dispatch (coordination contract)

Four subagents, disjoint file ownership, one common rules block (env, additive-only, no equation/API change, re-read before edit because a concurrent worker edits this tree):

| Agent | Owns | Deliverables |
|---|---|---|
| **A-PINT** (X-1) | NEW `engine/gateway/pint_audit.py`, NEW `engine/tests/test_pint_unit_gate.py` | pint audit with the six alias/domain units; catches the four audit defect classes; **no existing file edited** |
| **A-PYET** (X-6) | NEW `engine/tests/test_pyet_parity.py` | engine vs PyETo for Examples 18/20, Hargreaves, PT/Blaney–Criddle/Turc/Makkink, Ångström; measured deltas reported |
| **A-SOILPKG** (X-7/X-8) | NEW `engine/tests/test_climate_indices_spi_parity.py`, NEW `engine/tests/test_rosetta_ptf_reference.py` | SPI cross-implementation with the documented MOMME-vs-MLE band; VG table vs Rosetta-3 |
| **A-DOIFIX** (G-H17) | the two legacy reference docs (DOI tokens only) + NEW `reports/eco-nojin/CITATION-CORRECTIONS.md` | verify each dead DOI against primary sources; correct or mark `CITATION-UNVERIFIED`; never invent a DOI |
| **main agent** | `pyproject.toml`, `.github/workflows/ci.yml`, venv installs, registers | extras, CI jobs, package installs, register updates, final gate |

Rule that makes the parallelism safe: nobody edits another agent's files, and the final gate (engine + services + guard + ruff + the new suites) is run only after every agent reports.

## 13. Final gate after the four-agent run (2026-10-10, all green)

| Gate | Result | Previous (Wave-3 gate) |
|---|---|---|
| `pytest engine/` | **2517 passed, 30 skipped, 42 xfailed, 0 failed** | 2126 passed |
| `pytest services/` | **916 passed, 9 skipped, 0 failed** | 627 passed |
| `tools/detect_imports.py --root .` | **PASS — 0 violations** | 0 violations |
| `ruff check .` | **1497 errors** (down from 1943; the concurrent worker is also cleaning lint) | 1943 |
| `tools/phantom_path_check.py` | 57 missing paths tracked (CI job added; debt G-H5) | — |
| `tools/check_citations.py` | **dead = 0**, error = 2 (both verified real via Crossref by A-DOIFIX; network-blocked from this host) | **dead = 21** |
| new suites | pint 6 · PyETo 3 (+1 skip) · climate_indices/Rosetta 7 · citation 5 · honesty/phantom 9 · machine-evidence 6 · mutation 2 | — |

**Outcome per dispatch item:** A-PINT delivered the pint audit for all 16 unit strings with the four defect classes now detectable (no existing file edited). A-PYET proved exact agreement with an independent FAO-56 implementation on Examples 18/20 and near-exact on Hargreaves/PT/Makkink/Turc, and documented two *variant* gaps. A-SOILPKG established SPI cross-implementation agreement (corr 0.96–0.99, sign 0.95–0.99) and measured every VG row against Rosetta 3, quantifying G-S6/G-H4. A-DOIFIX replaced 20 DOI tokens with verified DOIs (15 distinct) and marked 6 `CITATION-UNVERIFIED` instead of inventing any. Two defects in the plan's own tooling were found and fixed during the run (HEAD→GET resolution; the "dead vs publisher-403" rule).

## 14. Decisions recorded (user mandate, 2026-10-10)

| Item | Decision | Constraints imposed | Implementation (in progress) |
|---|---|---|---|
| **X-9 texture oracle** | **Reject the GPL-3.0 package**; use the free public-domain route | no GPL code anywhere; no legal approval needed; no new dependency | `tools/characterize_texture_classifier.py` characterizes the engine's own classifier over the full 5151-composition grid (fallback count, overlap bands, corner behaviour) and writes `reports/eco-nojin/TEXTURE-CLASSIFIER-AUDIT.md`. The corrected table will be **transcribed USDA public-domain boundaries**, cited like the FAO-56/McKee reference data in `tests/reference_data/` |
| **X-3/X-8 PTF** | **Adopt Rosetta (CC0, USDA-ARS) as the reference PTF** | "رایگان و حجم بالا نبر" | a **frozen 12-row JSON artifact** (`engine/hydroma/soil/ptf_reference.json`, < 20 KB) generated by `tools/regenerate_ptf_reference.py` with the installed CC0 package, plus a **dependency-free loader** (`ptf_reference.py`: stdlib `json`/`math` only). The engine table is **not replaced** — G-S6 stays open as a decision; the artifact supplies the reference comparison and the uncertainty bands |
| **X-4 uncertainty** | approved as part of the PTF decision | same "small and free" constraint | the bands come from Rosetta's own ensemble spread, frozen in the same artifact → an `UncertaintyEstimate` can be produced **without any new runtime dependency** |
| **X-12 STAC** | **not confirmed** (user message truncated) | — | deferred until confirmed |
| **X-11 C++ parity** | **not confirmed** | — | deferred until confirmed |

Net effect: items 1 and 2 are executable with **zero new runtime dependencies**, no GPL, and a measured artifact under 20 KB — the "don't bloat, keep it free" constraint is met by freezing once and regenerating on demand.

## 16. Final gate after resume (2026-10-10 19:5x, all green)

| Gate | Result | Gate before resume (18:0x) |
|---|---|---|
| `pytest engine/` | **2559 passed, 30 skipped, 42 xfailed, 0 failed** (721 s) | 2517 passed |
| `pytest services/` | **1052 passed, 9 skipped, 0 failed** (637 s) | 916 passed |
| `tools/detect_imports.py --root .` | **PASS — 0 violations** | 0 violations |
| `ruff check .` | **883 errors** (down from 1497) | 1497 |
| `tools/phantom_path_check.py` | 57 missing paths tracked (G-H5) | 57 |
| `tools/check_citations.py` | **dead = 0** (2 network ERRORs, both verified real via Crossref) | dead = 0 |
| new suites (13 files) | **55 passed, 1 skipped, 0 failed** | — |

**User-approved items delivered.** Item 1 (texture, GPL-free): `TEXTURE-CLASSIFIER-AUDIT.md` — full 5151-composition characterization, 84.8 % classified, **782 fallback** via `taxonomy.py:246 return "loam"`, 555 overlap; 4 tests pin the counts. Item 2 (PTF, Rosetta/CC0, small): `ptf_reference.json` **8354 bytes / 12 textures**, dependency-free loader (mypy-clean), regeneration drift guard (`MATCH`, sha256 f92ef4f9…), 6 tests; the engine table is unchanged and G-S6 stays open by design.

**Transient-failure note (honesty).** One services run mid-resume reported 29 failures, all in `services/finance/`. Re-runs proved them **transient**: `test_finance_router_wallet.py` alone 23/23, chart+wallet together 41/41, `services/finance` alone 102/102, and the full services suite 1052/0. The cause was an in-flight concurrent edit to `database/models.py` (modified at 19:22, during that run) plus a finance-layer state-isolation sensitivity; nothing in this programme touches `database/` or `services/finance/`. Recorded as **G-H19**.
