# ECO-VALIDATION-PROGRAM — Scientific Validation & Honesty Program (SVHP)

> **Owner:** technical-analysis pass · **Created:** 2026-10-15 (UTC) ·
> **Status of this document:** the *executable* program for the scientific layer. It
> supersedes the per-model observations in the two prior analysis reports; it does
> **not** change any requirement in `docs/specs/**` (those remain the source of truth).
> **Two hard, non-negotiable constraints:**
> 1. **The entire program is free (رایگان)** — only FOSS / open-data / public-domain
>    references and tools. No paid licences, no paid services.
> 2. **Offline / reproducible** — every reference value is vendored into the repo with a
>    `*.meta.json` + checksum provenance sidecar (per AR-01 “the scientific core is not
>    connected to the internet”). No gate may depend on a live download.

**Governing honesty contract (inherited, enforced):** *the existence of a file is not
evidence of a completed capability.* A number this program quotes must be reproducible by
re-running the tool in §3 — otherwise it is not a number we state.

---

## 1. Scope and non-scope

| In scope | Out of scope |
|---|---|
| Every registered model (70), every formula-record (35), every indicator card, and the maturity/status machinery | Frontend behaviour (D-18), marketplace/money correctness (P5/P6 already gated elsewhere) |
| Per-model validation evidence and the honesty classification of each | Adding new scientific domains (breadth — deferred until depth is reached) |
| The gate/CI harness that keeps the above honest | `engine/**` behavioural rewrites (owned by the in-flight agent; see §8) |

---

## 2. Vocabulary this program speaks (do not invent new words)

- **Claim status / evidence class** (`engine/honesty/statuses.py::VOCABULARY`):
  `VALIDATED_EXTERNAL` · `VALIDATED_METHOD_CONFORMANCE` · `REGRESSION_ANCHOR_STABLE` ·
  `PARTIAL` · `UNVALIDATED` · `BLOCKED`. The legacy alias `validated` must be *refined*
  into one of these before use.
- **Maturity ladder** `S0..S6` (`engine/models/maturity.py`): the repo can currently
  evidence **at most `S3`**; `S4..S6` need independent-rerun / calibration / reproducibility
  evidence the registry does not yet hold (encoded by `test_no_model_above_s3_today`).
- **Safety brakes `SB-01..SB-10`** and **architecture rules `AR-01..AR-13`**: any change
  this program makes must cite its brake impact (esp. SB-03 public-API, SB-05 units/weights,
  SB-06 synthetic data as reference, SB-07 equation change without reference, SB-08 <80% coverage).
- **Triage decision** (`tools/engine_model_triage.py`): `published` / `keep_and_plan_validation` /
  `keep_and_plan_explainability`.

---

## 3. Measured baseline (computed 2026-10-15 — reproduce, never recall)

Reproduce with the dev venv (AGENTS.md):

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
$env:SECRET_KEY = "test-secret-key"
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/run_validation_gates.py
```

| Metric | Value | Source tool |
|---|---|---|
| Registered models | **70** | `tools/validation_status_report.py` |
| validation `validated` | **18** (all at maturity `S3`) | same |
| validation `unvalidated` | **52** (38 `S1` unverified + 14 `S2` implemented-not-validated) | same |
| `S4+` models | **0** (cannot be evidenced today) | `engine/models/maturity.py` |
| Formula records | **35** total · **19 verified** · **0 divergent** · **16 stub** | formula registry |
| Triage decisions | published **18** · keep_and_plan_validation **44** · keep_and_plan_explainability **8** | `tools/engine_model_triage.py` |
| Validation corpus | match **61** · mismatch **0** · inconsistent_case **17** · not_run **17** | `engine/hydroma/models/validation` |
| Novel-index gate | **0 blocked** (5 supported, 1 template-exempt; 10 novel indices unimplemented → precondition not met) | `tools/novel_index_gate.py` |
| Import guard | **0 violations** (1265 files, 8 rules) | `tools/detect_imports.py` |
| Composite verdict | **GREEN** | `tools/run_validation_gates.py` |

> **VG-08 resolved.** Two stale “13 validated” figures (in `BASELINE.md` and the triage
> tool’s docstring) are now superseded by the computed **18** above. Any future report must
> cite §3, not a remembered number. If the two ever disagree again, this tool is wrong or the
> registry moved — reconcile via the tool, not by editing one of them.

---

## 4. Per-model validation ledger (as measured)

### 4.1 The 18 `validated` models (`S3`) — anchor strength still varies

| Model | Domain | Strongest existing anchor | Honest class to publish |
|---|---|---|---|
| CANON-001 ET₀ Penman–Monteith | climate/ET | FAO-56 Ex.18 Uccle (3.9 vs engine 3.8801) + Ex.20 Lyon; pyet parity | `VALIDATED_EXTERNAL` |
| CANON-002 ET (secondary) | ET | FAO-56 Ex.20 | `VALIDATED_EXTERNAL` |
| CANON-004 SCS-CN runoff | hydrology | USDA/NEH-4 NRCS worked example | `VALIDATED_EXTERNAL` |
| CANON-005 Theis | groundwater | published w(u)+Cooper–Jacob **formulae only** (no external numeric table; G-V3-05) | `VALIDATED_METHOD_CONFORMANCE` |
| CANON-006 Van Genuchten | soil | Saxton & Rawls 2006 AWC; rosetta PTF parity | `VALIDATED_EXTERNAL` |
| CANON-008/010/015 | hydrology | published methods + muskingum-cunge/percentile parity | `VALIDATED_METHOD_CONFORMANCE` |
| CANON-011_RAD radiation | climate | FAO-56 eq.21 (Ra) | `VALIDATED_EXTERNAL` |
| RUSLE_LS | erosion | Wischmeier & Smith 1978; Renard & Freimund 1994 | `VALIDATED_EXTERNAL` |
| CANON-016/017 numerical kernels | kernel | parity (percentile/ODE) | `VALIDATED_METHOD_CONFORMANCE` |
| CANON-019/020/021/022 indices | remote sensing | published index defs + C++ kernel parity | `VALIDATED_METHOD_CONFORMANCE` |
| SOIL_SALINITY_CLASSIFY | soil | published salinity thresholds | `VALIDATED_METHOD_CONFORMANCE` |
| **ROTHTC_TEMP_FACTOR** | carbon | ✖ **contradiction** — registry `validated` but formula-record says `stub` needing primary RothC 26.3 | **VG-02 blocker → resolve (§5)** |

### 4.2 The 5 flagship indicator cards (externally anchored, the gold standard to copy)

| Card | Class | Note |
|---|---|---|
| ENO_ET0_FAO56_001 | `VALIDATED_EXTERNAL` (FAO-56 Ex.18/20) | publishable |
| ENO_SPI_001 | `VALIDATED_METHOD_CONFORMANCE` | no external numeric table (ZED offline) — tracked |
| ENO_WB_001 | `VALIDATED_MASS_CONSERVATION` | definitional identity (closure 7.1e-15 mm) |
| ENO_WP_001 | `VALIDATED_UNIT_DEFINITION` | definitional ratio (5000/500 → exactly 1.0) |
| ENO_ETC_KC_001 | `REFERENCE_DATA_REQUIRED` | **partial** — no corpus yet (§5 S1) |

### 4.3 The 52 `unvalidated` — grouped, with the *free* reference each needs

| Group | Models (count) | Free / offline anchor |
|---|---|---|
| Agronomy / crop | CROP_COMPARE, CROP_YIELD, ETc=Kc·ET₀ (…) | FAO-56 ch.6 worked examples; **FAO AquaCrop 7.3 Python** (released free on GitHub, 2026) |
| Economics (ag/fin) | ECON_NPV, ECON_PAYBACK, ECON_PRICE_RISK, ECON_YIELD_RISK, ECON_FINANCIAL, ECON_AG_COST/REVENUE | standard finance formulae + fixed-seed Monte-Carlo vectors |
| Irrigation | IRRIGATION_DEPTH, IRRIGATION_INTERVAL | FAO-56 ch.8 scheduling examples |
| Carbon | CARBON_SEQ | IPCC/protocol tables **or** RothC primary |
| Erosion | CANON-007 (full RUSLE) | Renard & Freimund 1994 reference tables |
| Watershed structures | CHECK_DAM, CONTOUR_TRENCH, HALF_MOON, STRUCT | engineering handbooks (mass-balance first) |
| MRV | MRV_METRICS, MRV_VALIDATE, MRV_VALIDATE_SAT | protocol tables reference |
| Soil (11) | AWC, CEC, ESP, SAR, LEACHING, WATER_CONTENT, WATER_RETENTION, VG_PARAMETERS, TAXONOMY, TEXTURE, TEXTURE_COORDS (+COMPOST_CN, AMENDMENT, PEDOTRANSFER) | USDA NRCS, Van Genuchten 1980, Saxton & Rawls, rosetta-soil |
| Climate/geo/misc | CLIMATE_PROJECTION/SCENARIO, CANON-003/009/011/018, PLANT_NEURO | CMIP6 method / published |

### 4.4 The 16 formula stubs (each with a documented `stub_reason`)

Saints/stubs are *honest* — each names exactly what is missing. Priority stubs to close with
free anchors: `rothc_temperature_modifier` (RothC 26.3), `richards_1d` (Celia 1990 / HYDRUS-1D
free non-commercial), `saint_venant_1d` (mass-conservation fix), `koppen_geiger_class` (Beck
GG open data), `epia_precision_irrigation` (LAI→Kc + rooting from soil texture), the four
`esri/ewsi/hdvi/hlhs_health` indices (weights/thresholds must be sourced, not invented),
`swatplus_watershed`/`modflow6_groundwater_flow` (missing imports — see §5 VG-06).

### 4.5 Tier C (8 explainability surfaces — need provenance, not a reference)

`SCENARIO, CANON-013, DATA_PIPELINE, RECOMMEND, SIM_CHAIN, SIM_ORCHESTRATE, MRV_DASHBOARD,
SOIL_RECOMMENDATIONS` — each must emit provenance + evidence_class + uncertainty + limits
(closes INT-05/INT-06).

---

## 5. Gap register (with program phases that close each)

| ID | Gap | Phase | Severity |
|---|---|---|---|
| VG-01 | 52/70 models without independent validation | S2 | P1 |
| VG-02 | RothC contradiction (validated vs stub) | S4 | **P0** |
| VG-03 | Theis without external numeric table (G-V3-05) | S1 | P1 |
| VG-04 | corpus: 17 `not_run`; not yet a blocking gate | S0/S2 | **P0** |
| VG-05 | 13 C++ `test_*.cpp` not built/run; parity not gated | S5 | P1 |
| VG-06 | 9 “experimental” external-model entries (`data/model_registry.json`) with empty schemas | S4 | P1 |
| VG-07 | uncertainty propagation absent (`NOT_ESTIMATED`) | S3 | P2 |
| VG-08 | 13-vs-18 count drift | **S0 — DONE (this program, §3)** | closed |
| VG-09 | corpus/harness not yet hard-gated in CI | S0 (added) / S2 (hard) | P0 |

---

## 6. The executable phases (free & offline by construction)

Each phase lists tasks, the **free** tool/reference it uses, its gate, and acceptance.
“Free” = FOSS or public-domain/open-data; every reference is vendored with `*.meta.json`.

### S0 — Measurement, honesty census, gate harness — ✅ DONE (2026-10-15)
- **Delivered:** `tools/validation_status_report.py` (single computed source; §3),
  `tools/run_validation_gates.py` (census + novelty + import-guard + corpus),
  `.github/workflows/validation-gates.yml` (additive CI, curated minimal deps, fail-closed).
- **Gate:** `run_validation_gates.py` → **GREEN** (census computes; novelty 0 blocked; import-guard 0; corpus 0 mismatch).
- **Acceptance:** every number in §3 re-generated by the tool; VG-08 closed; VG-09 blocking gates in CI.
- **Next increment (free):** add `--json-out` consolidated artefact under `reports/validation/` (already written by the runner) and cite it from `AGENTS.md` (optional pointer, non-behavioural).

### S1 — Close the external anchor gaps in Tier A/A′ — P1/effort L–M
- **ETc = Kc·ET₀** corpus from FAO-56 ch.6 worked examples (vendored CSV+meta) → move `ENO_ETC_KC_001` from `REFERENCE_DATA_REQUIRED` to `VALIDATED_EXTERNAL`.
- **VG-03 Theis:** vendor a published numeric drawdown table (offline) or keep `METHOD_CONFORMANCE` and record G-V3-05 honestly (no invention — SB-06).
- **Köppen–Geiger:** compare to Beck et al. open climatologies (open data) or keep as `PARTIAL`.
- **Gate:** each new anchor ships `test + *.meta.json + checksum`; novelty gate still 0 blocked; corpus mismatch stays 0.
- **Free tools:** FAO-56 (public domain), Beck KG open data, pyet/climate_indices/rosetta-soil already in the `ref` extra.

### S2 — Validate the quick-wins in Tier B (44) — P1/effort L per model, several parallel
Batch by domain; each model gets **one offline reference table + one passing test + one card row**.
Suggested first batch (cheapest anchors, highest usage):

| Target model | Free offline anchor | Effort |
|---|---|---|
| SOIL_SAR / SOIL_ESP | USDA/FSS (Richards 1954) | S |
| SOIL_AWC / WATER_RETENTION / VG_PARAMETERS | Van Genuchten 1980 + Saxton & Rawls (already referenced) | S |
| SOIL_PEDOTRANSFER | rosetta-soil parity | S |
| SOIL_TAXONOMY / TEXTURE_COORDS | USDA NRCS + USDA texture triangle (already vendored) | S |
| ECON_NPV / ECON_PAYBACK | standard finance + fixed-seed vectors | S |
| ECON_PRICE_RISK | GBM/log-return reference + fixed seed | M |
| IRRIGATION_DEPTH / INTERVAL | FAO-56 ch.8 | M |
| CANON-007 full RUSLE | Renard & Freimund 1994 tables | M |

- **Gate:** census `validated` count strictly increases; corpus `not_run` strictly decreases; no existing test weakened (P-15); each promotion cites its anchor. **After the first ~15 land, flip the corpus into a blocking gate** (VG-09 → hard).

#### S2 promotion mechanism (measured 2026-10-15) — how a model actually moves

The repository promotes a model to registry `validated` **only** through three
machine gates, never a hand-edit:

1. a `VALIDATED_EXTERNAL` row in `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`
   (a *published numeric* anchor — not a re-derived formula, not synthetic),
2. a matching `validation_status` row in `engine/models/cards/<MODEL>.md`, and
3. `engine/tests/test_machine_evidence_consistency.py` passing (it refuses a
   `validated` claim without the external anchor, and refuses growing the
   known-unanchored debt set).

`engine/validation/test_validation_records.py` (81 tests, all green today)
re-runs every case through the gateway and re-derives each reference
independently, so a model can only claim what an external anchor supports.

**`tools/validation_backlog.py` makes this executable.** It cross-references the
census + register + records and classifies all 41 register families into
`DONE_EXTERNAL` (9) / `VENDOR_OFFLINE_ANCHOR` (13 — a missing *published numeric*
an owner vendors offline) / `DESIGN_DECISION_REQUIRED` (19 — project-invented
weights or a conflicting/uncited convention: a STOP-brake decision first). It also
lists the models that are **one offline external anchor from promotion**
(`IRRIGATION_DEPTH`, `IRRIGATION_INTERVAL`, `SOIL_SAR`, `SOIL_ESP`,
`SOIL_LEACHING` — all pass method-conformance today, verified by the 81 green
record tests) and the **46 unvalidated models with no evidence artifact yet**.

**Honest boundary (VG-06/S2):** this program does **not** promote any model or
fabricate a numeric anchor (SB-06 forbids it, and the offline/ZED constraint means
a genuinely published number cannot be invented). A promotion requires the owner to
(1) vendor the offline published table (CSV + `*.meta.json` + checksum), (2) add the
register row, (3) add the card `validation_status` row, then (4) let
`test_machine_evidence_consistency.py` flip the status. `tools/validation_backlog.py`
names, per family, exactly which anchor to vendor and which items need a decision
first. See `reports/validation/BACKLOG.md`.

### S3 — Explainability & uncertainty for Tier C + VG-07 — P2/effort M
- Wire provenance(L0–L5) + `evidence_class` + `UncertaintySpec` (real method, not `NOT_ESTIMATED`)
  + `limits` + accountable owner onto every Tier-C and any published scientific payload.
- **Free:** propagation in numpy/scipy (Monte-Carlo + Latin-Hypercube — already in `sampling`).

### S4 — Reconcile the honesty contradictions — P0/effort S (with an engine-owner decision)
- **VG-02 RothC:** obtain the primary RothC 26.3 temperature factor and set the record to
  `verified`, **or** mark the model/formula `unvalidated`/`stub` consistently. No middle path.
- **VG-06:** `data/model_registry.json` (MODFLOW6/SWAT+/EnKF/4D-Var/PF/GP/PINNs) is a list of
  **external-model integration targets**, not in-repo implementations. Either add an explicit
  `in_repo_implementation: false`/`validation_status: aspirational` field to each (additive,
  loader-compatible) **or** move them to a clearly-named `data/integration_targets.json`.
- **Gate:** census + novelty gate green; no claim outruns its card.

### S5 — Reproducible, gated C++ parity — P1/effort M (infra)
- Build/run `engine/cpp_core/tests/test_*.cpp` (13 files) in CI with a free compiler
  (GCC/Clang on ubuntu, MSVC on windows). Record the 124–244× / 218× benchmark with hardware +
  data + versions in `reports/validation/BENCHMARK.md`. **No Docker required (DP-2):** a
  `pyproject`-pinned venv snapshot + seeds is sufficient; Docker remains an *optional* free path.

### S6 — Publish honest, per-model public cards — P2/effort S
- Auto-generate a public **Model Card** for all 70 models from the census + cards:
  `status / evidence_class / reference / deviation / limitations / license`. The UI/guide may
  never claim more than the card (`novel_index_gate` keeps static refs honest; the card keeps
  the scientific claims honest).

---

## 7. Where this program stops, and who must decide

This program is deliberately *surgical*: it edits tooling, gates, CI and vendored reference
data. It does **not** edit `engine/**`, `services/**`, `database/**`, `alembic/**`,
`architecture/**`, or `AGENTS.md` in this pass, because those are owned and several are in
flight (KN-22/39; route-count pin; import-guard policy). Model *promotions* that require an
`engine/**` card/status change (S2’s bulk, S4’s RothC) are **staged and gated**, not applied
unilaterally. Each such change is a **public STOP brake** (SB-03/05/07) and needs the named
owner’s go-ahead — recorded here, never assumed.

**Decisions the program requests from the approver:**
1. RothC: promote (with primary source) or demote consistently. *(Science owner)*
2. Label or relocate the 9 “experimental” external-model entries. *(Architecture)*
3. When to hard-gate the validation corpus (after the S2 first batch). *(QA/integrator)*

---

## 8. Guardrails every change in this program obeys

- **Encoding-safe edits only** (KN-42): files are written with UTF-8 tools, never PowerShell
  `Set-Content` on repo files.
- **No test is deleted or weakened** (P-15); closures cite command + output against a gate.
- **No synthetic value stands in for a reference** (SB-06); a missing anchor is recorded as a
  gap, never fabricated (the Theis pattern).
- **Behaviour-preserving** for any refactor; status changes are additive and read-only to the
  registry (mirrors `maturity.py`).
- **Route-count pin, import-guard policy, Decimal money, guarded migrations** are untouched.

---

## 9. Reproduce everything (single command)

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"; $env:SECRET_KEY = "test-secret-key"
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/validation_status_report.py   # census -> reports/validation/
    & "D:\eco_nojin\.venv\Scripts\python.exe" tools/run_validation_gates.py       # composite gate (GREEN required)
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/validation_backlog.py        # S2 promotion plan -> reports/validation/BACKLOG.*
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/generate_model_cards.py      # S6 public honesty sheet -> reports/validation/MODEL-CARDS.*
# Turnkey EXTERNAL promotion (fail-closed; needs a genuine published value):
#   python tools/promote_external.py --plan   --model CANON-006 --family VAN_GENUCHTEN_THETA_K
#   python tools/promote_external.py --apply  --model CANON-006 --family VAN_GENUCHTEN_THETA_K \
#       --reference tests/reference_data/vg_reference.csv --citation "..." --kind published_table
```
Or in CI: `.github/workflows/validation-gates.yml` runs the same gate on every push/PR.

---

## 10. Tracker

| Phase | Owner | Status | Evidence |
|---|---|---|---|
| S0 measurement + gate + CI | this pass | **DONE 2026-10-15** | `tools/validation_status_report.py`, `tools/run_validation_gates.py`, `.github/workflows/validation-gates.yml`, `reports/validation/CENSUS-2026-10-15.*`, `GATES-2026-10-15.txt` — verdict GREEN |
| VG-08 count drift | this pass | **DONE** | computed 18 (§3) |
| S1 external anchors (ETc, Theis, KG) | science owner | staged | — |
| S2 Tier-B win batch (44) | science owners | **BACKLOG BUILT 2026-10-15** — `tools/validation_backlog.py` + `reports/validation/BACKLOG.*`: 41 families → 13 `VENDOR_OFFLINE_ANCHOR` / 19 `DESIGN_DECISION_REQUIRED` / 9 `DONE_EXTERNAL`; 5 cluster models (IRRIGATION_DEPTH/INTERVAL, SOIL_SAR/ESP/LEACHING) are one offline external anchor from promotion; 46 models need an evidence record authored first. Promotions themselves are owner-gated (see §6-S2 boundary). |
| **S6 public model cards** | this pass | **DONE 2026-10-15** — `tools/generate_model_cards.py` + `reports/validation/MODEL-CARDS.*`: 70 models split external **7** / validated-but-unanchored (known debt) **11** / method-conformance **6** / no-artifact **46**; shown live as the `s6-model-cards` gate chip. The debt split is more honest than the raw "18 validated" census. |
| **S2 promote_external tool** | this pass | **DONE 2026-10-15** — `tools/promote_external.py`: turnkey, **fail-closed** promoter. Vendors a genuine CSV + `*.meta.json` (sha256, offline) into `tests/reference_data`, appends/updates the register row, and emits — not applies — the `engine/**` patch for the owner (EXTERNALLY_ANCHORED_MODELS + `len(external)==9` cap + card row + CLUSTER list). **Proven fail-closed**: `--apply` without a real reference exits 2 (`REFUSED`). External anchors held at 9 — nothing fabricated. |
| **First FULL-model EXTERNAL anchor: Theis (CANON-005)** | this pass | **DONE 2026-10-15** — Retrieved the USGS *Python for Hydrology* worked example (T=1000 m²/day, S=3e-4, Q=4088 m³/day, r=1000 m, t=10 d → **s=1.40636669 m**); the engine reproduces it to **Δ=3.5e-9 m** (genuine, not re-derived). Vendored `tests/reference_data/theis_usgs_worked_example.csv` + meta; register row `THEIS_DRAWDOWN_USGS = VALIDATED_EXTERNAL`; parity test `tests/test_theis_usgs_external.py` PASS; cap bumped 10→11; machine-evidence 6/6 GREEN. |
| Muskingum-Cunge (finding) | this pass | **NOT PROMOTABLE** — `muskingum_route` reproduces the Iowa/WinTR-55 worked example (peak 28.50 cfs exact), but no registered gateway model outputs a routed hydrograph, and the register documents a duplicate/divergent-units copy. Recorded as a finding; not promoted. |
| CANON-005 retirement from unanchored-debt | this pass | **DONE 2026-10-15** — engine-coordinated: `EXTERNALLY_ANCHORED_MODELS["CANON-005"]="THEIS_DRAWDOWN_USGS"` + removed CANON-005 from `KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR` (debt 11→10); card kept conservative `VALIDATED_METHOD_CONFORMANCE` (P0-2 guard respected) while documenting the published USGS anchor. machine-evidence 6/6, card-code-agreement 32/32, composite GREEN. **CANON-005 is the first model whose `validated` claim is fully backed by a genuine published external worked example.** |
| RUSLE (finding + LS 2nd source) | this pass | **DONE 2026-10-15** — NRCS Agronomy Technical Note 28 (1999) "Example Run": engine `ls_factor(243.84 m, 2%) = 0.44179` reproduces printed **LS=0.44** (independent 2nd published source, distinct from AH-703); vendored `tests/reference_data/rusle_ls_nrcs_tn28.csv`, test `tests/test_rusle_ls_nrcs_external.py` PASS, register `RUSLE_LS` basis updated (still VALIDATED_EXTERNAL, no cap change). **NOT anchored:** the full product `A=R·K·LS·C·P=1.27` is arithmetic over table-supplied factors (already covered by the repo product-invariant test) — reproducing a multiplication is not a scientific external anchor. |
| Kirpich Tc (CANON-015) — corroboration, NOT promoted | this pass | **DONE 2026-10-15** — engine `calculate_kirpich_tc(500, 0.088) = 5.9514` reproduces a published worked example (cllmp, Tc=6 min) within its whole-minute printing. **Held at PARTIAL / debt NOT retired**: source is an NGO training deck (not agency/peer-reviewed), value is 2 sig figs, coefficient unsettled (0.0195 vs 0.01947 NPTEL), and G-H6 divergent sibling unresolved. Vendored `tests/reference_data/kirpich_cllmp_worked.csv` + test `tests/test_kirpich_cllmp.py`; register basis notes corroboration. No VALIDATED_EXTERNAL claim. Gate GREEN, external stays 11. |
| Van Genuchten θ(h) (CANON-006) | this pass | **BLOCKED — NOT PROMOTED 2026-10-15** — Two attempts: (a) web research found no open-access published θ(h) (van Genuchten 1980 & Carsel & Parrish 1988 closed-access; only printed param set = Sensors 2021 with NO printed θ(h) + unit inconsistency); (b) downloaded the official RETC manual (EPA 600/2-91/065, free PDF, extracted 93pp) — its worked examples are figure-based/ambiguous-column, no cleanly-labelled printed θ(h)+params to anchor. Fabrication (SB-06) forbidden → stays method-conformance/debt. Definitive unblock requires a cleanly-printed published (θr,θs,α,n,h→θ) worked example. |
| VG-02 RothC contradiction | engine owner | staged, needs decision (S4) | — |
| S3 explainability + uncertainty (Tier C, VG-07) | engine owner | **BASELINED 2026-10-15** — `tools/uncertainty_audit.py` measures VG-07: real uncertainty surfaces=**14**, `NOT_ESTIMATED` placeholders=**65** (~17.7% real); wired as the `uncertainty-baseline` gate chip; report `reports/validation/UNCERTAINTY-BASELINE.md`. Engine wiring (attach real uncertainty to Tier-C outputs, keep the sentinel where genuinely absent) remains a coordinated `engine/**` change per §12. |
| S4 RothC reconcile + experimental-registry labelling | science/arch | VG-06 **RESOLVED by documentation** 2026-10-15; **VG-02 RESOLVED (verified)** 2026-10-15 — live tree already reconciled: `rothc_temperature_modifier` is `status="verified"` (catalog.py:284; numerator 47.91, defects fixed, wrong claims withdrawn) and register `ROTHC_TEMP_FACTOR` is `VALIDATED_EXTERNAL` (5 published points); the earlier "stub" was a stale README snapshot. No change needed. |
| S5 C++ parity CI + reproducible benchmark | infra | cpp-parity CI authored 2026-10-15 (unverifiable locally, verify on CI push); **R1** benchmark record `reports/validation/BENCHMARK.md` documents the free/offline no-Docker reproduction method for the 124–244× claim. |

*This document is the executable program; the numbers are computed, not asserted. Re-run §9 after every change.*

---

## 11. Decision log (this program)

**DECISION D-V-01 (2026-10-15) — the honest ceiling for definitional/arithmetic families.**
Following the *most standard* references (FAO-56 Annex 2 read with Keller & Bliesner for
`IRRIGATION_DEPTH`/`IRRIGATION_INTERVAL`; USDA Handbook 60 / FAO-29 for `SOIL_SAR`, `SOIL_ESP`,
`SOIL_LEACHING`), and **deciding** rather than escalating to the user:

- **These families correctly sit at `VALIDATED_METHOD_CONFORMANCE`. That is their honest
  standard-based ceiling, not a pending gap.** They are pure arithmetic/definitional relations
  (SAR = Na/√((Ca+Mg)/2); ESP = 100·Na/CEC; GAR = max(0, ETc−Pe)/Ea). The only thing `VALIDATED_EXTERNAL`
  could add is a *published numeric* (a printed table value or a measured/metered application),
  and the repo's own gate — `test_machine_evidence_consistency.py` + the `len(external)==9` cap +
  `novel_index_gate` — is built to reject `VALIDATED_EXTERNAL` without one.
- **I will not fabricate a published numeric** (SB-06/SB-07), and I will not bypass the gate.
  Promoting these by flipping the card with the formula-re-derived reference column would be the
  exact over-claim the honesty contract exists to prevent. So: **promotion of this family is
  BLOCKED_ON_OWNER_PUBLISHED_NUMERIC** — a named decision, recorded here, not a silent gap.
- **How a genuine EXTERNAL promotion completes** (only when real published data exists): source
  one printed/measured value per model → vendor offline (`tests/reference_data/<X>.csv` + `*.meta.json`
  + checksum) → add the `VALIDATED_EXTERNAL` register row → wire
  `EXTERNALLY_ANCHORED_MODELS[model]` and deliberately raise the `len(external)==9` cap → set the
  card `validation_status` row and `CLUSTER_MODELS_MOVED_TO_VALIDATED` → re-run the gate. Steps
  touching `engine/**` are in-flight surfaces (STOP brakes SB-03/SB-10): coordinate with the owning
  agent, do not edit out of band.

**D-V-02 (2026-10-15) — what I move forward on instead, all offline/free/honest.** Since a real
EXTERNAL promotion is blocked on owner-sourced data, the standard-based forward action is the exact
artefact that names the required numeric per model (`tools/validation_backlog.py` →
`reports/validation/BACKLOG.md`, each model's own `move_hint`), plus the classifier evidence
(matrix/census), the enforceable gate/CI, and the public model-card honesty sheet (S6). None of
these inflate a status; all are reproducible from the repo with no network.

---

## 12. S3 design spec (Tier-C explainability + uncertainty, VG-07) — for the engine owner

Designed 2026-10-15; implementation is an in-flight `engine/**` change, coordinated with the
owning agent (not edited unilaterally). The gateway already carries `ProvenanceSpec`,
`UncertaintySpec` and the honest `NOT_ESTIMATED` sentinel; the task is to make every Tier-C
surface *propagate* them instead of silently defaulting.

Target surfaces (the 8 explainability models) — each output must attach:
1. `provenance` — data_source + evidence level L0–L5 + the actual computation chain (closes INT-05/INT-06);
2. `evidence_class` — via the s6-card-list (already implemented in `tools/generate_model_cards.py`);
3. `uncertainty` — a real method/CI **or** the explicit `NOT_ESTIMATED` sentinel (never silent);
4. `limits` + `accountable owner` (`decision-maker` kind), propagated (Processing → Decision).

Concrete per-model wiring (SCENARIO, CANON-013, DATA_PIPELINE, RECOMMEND, SIM_CHAIN,
SIM_ORCHESTRATE, MRV_DASHBOARD, SOIL_RECOMMENDATIONS): route returns
`{value, provenance, evidence_class, uncertainty, limits, owner}`.

Honesty guard (must hold after wiring): a test that every Tier-C/FRONTIER output either
carries a real `UncertaintySpec` **or** the `NOT_ESTIMATED` sentinel — a silent/absent
uncertainty fails. Number the gap: an audit tool `tools/uncertainty_audit.py` (to add) that
counts outputs with real uncertainty vs `NOT_ESTIMATED`, publishing the VG-07 target as a
measured baseline (mirrors the census/backlog pattern).

Verification: re-run `tools/run_validation_gates.py` (GREEN) + the new uncertainty audit; no
scientific status changes, so machine-evidence stays 6/6.

---

## 13. Remaining program (post-2026-10-15) — the durable roadmap

Ordered by value × do-ability; each item keeps the rule *real evidence → test → no over-claim*.

### P0 — honesty-critical (do first)
- **VG-02 RothC reconcile.** The registry says CANON-ROTHC-temp `validated` but the formula
  record says `stub` waiting on primary RothC 26.3. Decision (Science owner): **promote** with the
  primary temperature-factor table (vendor offline) **or** **demote** consistently (card →
  `unvalidated`; remove from `validated`). I can draft both patches; the choice is not mine.

### P1 — close measured gaps (actionable now/soon)
- **S3-C1 engine wiring.** Use §12 to attach real `UncertaintySpec`/provenance to the 8 Tier-C
  surfaces, keeping `NOT_ESTIMATED` only where genuinely not computable. **Measurable:** the
  `uncertainty-baseline` chip rises from 14/65 real; a guard test forbids a *silent* absence.
  (engine-coordinated.)
- **S5-verify.** `cpp-parity.yml` is authored but not locally runnable (no toolchain here). Run it
  on the next CI push; if green, VG-05 (13 unbuilt `test_*.cpp`) and VG-09 (parity not gated) close.
- **R1 reproducible benchmark.** Pin the 218× Numba/C++ claim with a **free, offline** method —
  a `pip freeze` venv snapshot + fixed seeds + input sizes in `reports/validation/BENCHMARK.md`
  (no Docker per DP-2; Docker stays optional).

### P2 — deepen (each gated on a genuine published value; mostly offline-blocked)
- **S1 anchors:** `ETc = Kc·ET0` corpus (FAO-56 ch.6 worked examples, vendor offline);
  formalize the Theis external numeric (USGS done — could add a 2nd point from KGS gal-day-ft);
  Köppen–Geiger (`koppen_geiger_class` is a stub → needs the classification implemented, then
  Beck’s open climatologies as the external anchor).
- **Remaining unanchored debt (CANON-008/010/016/017/019/020/021/022):** per-model, only if a
  genuine published value the engine *exactly* reproduces exists. Realistic yield is low — D8 is
  algorithmic, water-balance is definitional, 016/017 are internal kernels, 019–022 are closed-form
  (the register row is currently parity/closed-form, arguably method, not external).
- **RUSLE other factors** (K texture table, R method) — optional, if a published worked value fits.

### P2 — docs/hygiene
- Optional one-line pointer to this program in `AGENTS.md` (governance doc — coordinate, don’t
  edit unilaterally).
- Keep `reports/validation/{CENSUS,BACKLOG,MODEL-CARDS,UNCERTAINTY-BASELINE,EXTERNAL-ANCHORS,GATES}`
  current via `tools/run_validation_gates.py` after every change.

### Explicitly out of this program’s scope (product phases, per docs/project D-items)
Frontend session (D-08), payment provider (D-07), Postgres pilot (D-15), marketplace/finance P5/P6,
frontend re-scaffold (D-18) — governed by `docs/project/PHASE_PLAN.md`, not the scientific-validation
program.

## Recommended next step
**P0 VG-02 (RothC)** if the Science owner can decide promote-vs-demote; otherwise **S3-C1** wiring
(the highest measurable S3 gain, spec-ready, engine-coordinated). Both keep every gate GREEN and
make no unearned claim.
