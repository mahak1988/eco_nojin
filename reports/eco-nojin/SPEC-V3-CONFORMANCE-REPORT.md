# SPEC v3.0 CONFORMANCE REPORT — Eco Nojin + Hydroma

Document id: `ECO-V3-CONFORMANCE` · Date: 2026-10-10 · Compared: `ECO_NOJIN_HYDROMA_MASTER_v3.0.html` (status "نهایی‌شده برای اجرا", ref commit `d6fac05`) vs the live tree and every measurement in `GAP-REGISTER.md`, `FORMULA-VALIDATION-REGISTER.md`, `EXTERNAL-ALIGNMENT-PLAN.md`.
Method: every claim below is either (a) measured live today, or (b) cited to a file:line. Nothing is inferred from the document's own assertions.

## 1. Requirements v3.0 states that are ALREADY CLOSED (with evidence)

| v3.0 requirement | Live evidence | Verdict |
|---|---|---|
| **SB-09 / AR-import guard** — `detect_imports.py` PASS | measured today: **PASS, 0 violations** (1051 files) | ✅ |
| **Quick Scan floors** — engine ≥1700, services ≥528 | measured today: **engine 2559 passed / 0 failed**, **services 1052 passed / 0 failed** | ✅ exceeded |
| **SB-07 / AR-03 equation immutability** | no engine equation changed at any point in this programme (PHASES explicitly refused three such edits and recorded them) | ✅ upheld |
| **AR-02 ports / SQLite schema §5.1 (8 tables)** | `adapters/persistence/sqlite_persistence.py` implements the spec §4.5 ABC + the 8-table DDL with 11 tests | ✅ implemented (not yet the production path — see §2) |
| **AR-09 provenance** | `tools/run_e2e_demo.py` emits `provenance.json` with all §5.2 keys; `ECON_06`/ECO-16 report exists | ✅ for the E2E path |
| **AR-10 positive/negative tests per rule** | `engine/tests/test_architecture_rules.py`: **48 tests — 24 negative (3 per INV rule) + 12 positive controls** | ✅ |
| **ECO-02 (۱۷ مسیر Gateway) / ECO-03 (D-18 exponent)** — the *historical* fixes these sections describe | commit `6e7b8b4` wired real dispatch (~75 paths); the source exponent is 0.5 (`et_calculator.py:116`) | ✅ as history — but see §2 (binary) |

## 2. Requirements PARTIALLY closed (v3.0 asserts them as done; the measurement disagrees)

| v3.0 requirement | Reality (measured) | Gap id |
|---|---|---|
| **AR-06 / ZED item 4: "هیچ تغییر واحد بدون pint/UnitRegistry"**; capability map claims **"Unit Registry (pint)"** | pint is installed and audited (`engine/gateway/pint_audit.py`, 16 unit strings, 6 domain units) but the **gateway still multiplies by a hand-written `si_equivalent`** (`engine/gateway/__init__.py:2008-2022`) and `engine/hydroma/quantity.py` is a **10-line stub**. The audit caught 4 real unit-defect classes (incl. the 100× `SOIL_AMENDMENT`) that pint would structurally prevent | G-V3-01 |
| **KPI: reference data ۱۰۰٪ for CANON-001..006**; appendix path **`data/reference_data/`** | published anchors exist for **CANON-001** (FAO-56 Ex. 18, 3.9), **CANON-002** (Ex. 20, 5.0), **CANON-004** (NEH/TR-55). **CANON-005 has no published value** (and its card printed 0.018 m vs the measured 0.3062 m), **CANON-006 is a Rosetta *comparison*** — the table itself is unreconciled (α up to 3.8×). Also the location is `tests/reference_data/`, not `data/reference_data/` | G-V3-02 |
| **§2.1 "۱۸ مدل علمی تأییدشده (سطح ۳)"** + KPI "Scientific Validation Coverage ≥ ۸۰٪" | registry maturity measured: **S0 14 · S1 47 · S2 2 · S3 7** of 70 = **۹.۹٪**, and only **CANON-001 + 004** (plus 002 via Example 20) have *external* anchors. The 80 % KPI would need **56 S3 models**; 9 exist | G-V3-03 |
| **§3.1 CANON-006 reference = "Carsel & Parrish 1988"** | that attribution is **withdrawn/fabricated**: the real paper is WRR 24:755-769, `engine/data/soil_vg_table.csv` marks the rows `design_assumption`/`design_assumption_disputed`, and the gateway still answers with the withdrawn attribution | G-V3-04 (= G-H4/G-S6, re-cited in v3.0) |
| **§3.1 CANON-005 reference = "scipy.special.expi"** | a library call is not a scientific reference; the model has **no published drawdown value** anywhere in the tree | G-V3-05 |
| **§3.1 thresholds "۰.۰۰۰٪" for CANON-001/002** | the engine deviates from FAO-56's printed text by the `Rs/Rso ≥ 0.3` clamp (G-H8, measured −1.44 MJ/m²/day Rn) and an uncited `dtr_floor` (+124 % at ΔT=0.02). Agreement with PyETo is exact, but agreement with the *published equations as printed* is not 0.000 % | G-V3-06 |
| **§4 ECO-03 "اصلاح Hargreaves exponent (D-18)"** | source fixed (**0.5**) and the public checker fixed (PHASES), **but the shipped `.pyd` still computes 0.48** (−4.5 %, G-H9) — silently passed by `scientific_verification:298` under a 10 % tolerance | G-V3-07 |
| **§2.1/§3.3 "Local Data Mirror (CHIRPS, ERA5, SoilGrids)"** and appendix **`data/mirror/`** | **no mirror exists**; the E2E chain is `BLOCKED_ENVIRONMENT` (ECO-16 report); ZED forbids live download; the STAC decision is **not confirmed** by the owner | G-V3-08 |
| **§2.1 "SQLite (cache)" at layer 2 + DP-1 no direct cross-DB access** | the in-memory `engine/ports/persistence.py` protocol is the production path; the spec-conformant SQLite adapter is not wired to the gateway/evidence/knowledge/decision writes (G-D3) | G-V3-09 |
| **ZED item 3: synthetic data must be labelled `# FIXTURE`** | our tests label `synthetic_test_data: true` inside JSON/meta and the E2E gating docstring; the **literal `# FIXTURE` convention required by v3.0 is not used anywhere** | G-V3-10 |

## 3. NEW requirements in v3.0 with no implementation found (new gap class)

§3.2 defines **ten novel indices**, each with a stated role in the business layer. None of them exists in the tree (the formula audits F-HYDRO/F-SOIL/F-ECO/F-CLIMATE covered every scientific module and found none):

| Index | v3.0 role | Implementation | Gap id |
|---|---|---|---|
| **FDII** Flash Drought Intensity Index | early warning in H2 | absent | G-V3-11 |
| **CDHE** Compound Drought-Heat Index | crop risk / insurance in H1 | absent | G-V3-12 |
| **CMSI** Crop Multi-Stress Index | supplier ranking H1/H7 | absent | G-V3-13 |
| **WSNI** Water-Soil Nexus Index | supplier sustainability H5 | absent | G-V3-14 |
| **RRI** Restoration Readiness Index | H7 service prioritisation | absent | G-V3-15 |
| **IWEq** Intergenerational Water Equity | ESG reporting H4 | absent | G-V3-16 |
| **WAI** Water Access Index | irrigation priority regions | absent | G-V3-17 |
| **WVI** Water Vulnerability Index | supply-chain risk H2 | absent | G-V3-18 |
| **PSI** Production Stability Index | supplier ranking | absent | G-V3-19 |
| **CW** Cost of Water | product pricing H6 | absent (adjacent: `water_productivity` + economics exist) | G-V3-20 |
| **Canary Dispatch (۵٪)** — model A/B comparison (ECO-11) | model version governance | absent | G-V3-21 |

Each of these needs a **published definition + reference + validation anchor** before implementation, exactly as FAO-56 Example 18 became the template for `ENO_ET0_FAO56_001`. Inventing them without citations would violate v3.0's own AR-03/SB-07 and the honesty contract's first rule.

## 4. Internal inconsistencies and unsupported claims inside v3.0 itself

1. **The fabricated Carsel & Parrish citation is carried into the new spec** (§3.1) — the very class of defect our audit corrected in six cards and 20 DOI tokens. v3.0 should cite WRR 24:755-769 and mark the embedded table `design_assumption`.
2. **"۱۸ مدل سطح ۳" is contradicted by the repo's own registry** (7) and by the 80 % KPI (needs 56). The claim is either aspirational or counts models the register marks `blocked`/`unvalidated`.
3. **AR-01..AR-10 and SB-01..SB-10 use the same identifiers with different meanings** than the earlier spec: v2.0's AR-05 meant "services must not call engine internals", v3.0's AR-05 means "evidence-based decision". Our `architecture/rules.yaml`, the 48 negative tests and the honesty module encode the v2.0 numbering. **The vocabulary collision must be resolved before v3.0 becomes the constitution**, or a reviewer will validate the wrong rule.
4. **The brake set changed** (v2.0's 7 → v3.0's 10, adding SB-02 100-line deletion, SB-08 coverage < 80 %, SB-09 guard, SB-10 fix-log). `engine/honesty/statuses.py::BRAKES` still holds 7.
5. **Phantom paths in §10**: `ECO-NOJIN_ZED_Scientific_Appendix_v2.md`, `ECO-NOJIN_MASTER_v3.0_UNIFIED.md`, `engine/strict_tests/test_s17_gateway_fixes.py`, `data/reference_data/`, `data/mirror/` do not exist — the same class as the 57 phantom test paths now tracked as G-H5.
6. **Quick Scan floors are stale** (1700/528 vs the measured 2559/1052) — harmless but should be updated so the gate cannot silently regress.
7. **DP-1 relaxes ZED to layer 1 only**, which changes the *meaning* of earlier gaps: G-Z1 (duckdb/supabase) becomes a layer-1 concern only — our `legacy-bridge` extra already matches this, but the register should re-cite DP-1.

## 5. What must change in our registers (consequence of v3.0)

| Register | Change |
|---|---|
| `GAP-REGISTER.md` | add G-V3-01..G-V3-21 (§2 partials + §3 new indices); re-cite G-Z1 under DP-1; re-cite G-H5 (phantom paths) to include the five phantom paths of v3.0 §10 |
| `engine/honesty/statuses.py` | `BRAKES` 7 → 10 (SB-01..SB-10) |
| `architecture/rules.yaml` + `test_architecture_rules.py` | add a v3.0 AR-01..AR-10 column alongside the INV rules so both vocabularies are asserted without collision |
| `EXTERNAL-ALIGNMENT-PLAN.md` | the ten novel indices become a new workstream (§17) with a published-definition precondition; `data/mirror/` and `data/reference_data/` locations reconciled with `tests/reference_data/` |
| `RESUME-STATE.md` | pending list gains the v3.0 reconciliation workstream |

## 6. Recommended order (all additive, no equation/API change)
1. **Vocabulary first** (G-V3 §4 items 3–4): reconcile AR/SB identifiers across the two specs; extend `BRAKES` to 10. Cheap, prevents misdirected validation.
2. **Adopt pint at the gateway boundary** (G-V3-01) — the audit module already exists; wiring is the behaviour-preserving insertion the plan designed.
3. **Reference anchors for CANON-005/006** (G-V3-02/05): official reference for Theis (FAO-56 has none; Geoscience literature) and the **USDA public-domain** texture/hydraulic table transcription for the VG table — the same route already used for FAO-56 and McKee, no GPL.
4. **Rebuild the C++ kernel in CI** (G-V3-07) — blocked only on the `.github/` commit decision.
5. **Novel indices** (G-V3-11..21): one index at a time, each with a published definition first; none before its reference exists.
6. **Mirror + ingestion** (G-V3-08): requires the owner's STAC/dataset decisions (still unconfirmed).

Bottom line: v3.0 is a *governance and integration* constitution, and most of its non-negotiable claims are either already true (guard, tests, immutability) or measurable-and-false today (18 S3 models, 0.000 % error, the mirror, the unit registry, ten indices). Applying it without correction would enshrine six over-claims; applying it with §6 repairs it becomes the strongest instrument the project has had.
