# Commit Plan — 2026-10-10

Repository: `D:\HyDroMA` (master @ `d6fac05`, 4 commits).
Scope of this plan: the ~330 paths currently changed/untracked, grouped into
themed commits, plus the two owner decisions and the hygiene items that must
**not** be committed.

## 0. Read this first — the tree is live

This plan is a **snapshot**, not a live view. While the audit was running, a
concurrent process kept writing to the working tree:

| evidence | time |
| --- | --- |
| `data/reports/report_b453d238-*.json` created | 09:11 |
| `reports/hydroma/HYDROMA_REFERENCE_DATA_CATALOG.md` modified | 09:12 |
| `data/rag/hydroma_scientific_corpus.json` rewritten | 09:06 |
| `reports/hydroma/HYDROMA_SCIENTIFIC_CRITERIA.md` modified | 09:14 |
| stray zero-byte root file `file` (re)created | 09:14 |
| `services/marketplace/tests/test_event_emission.py` modified | 09:13 |
| `tools/check_security.py` created (28 KB) | 09:17 |
| `tools/check_venv_integrity.py` modified | 09:19 |
| `services/finance/tests/test_chart_of_accounts.py` created | 09:20 |
| `engine/hydroma/data_assimilation/assimilation.py` (tracked) modified | 09:29 |
| `tools/check_security.py` modified again after creation | 09:2x |

Snapshot numbers, all measured during this audit:

* `git status --short` **before** the `.gitignore` change: **360** entries
  (228 modified, 131 untracked, 1 deleted).
* `git status --short` **after**: **360** entries at the time of writing
  (231 modified, 126 untracked, 1 deleted). The `.gitignore` change removed
  exactly **5** runtime entries; 5 entries appeared in the same window — three
  from the concurrent writer, one modified again, and `reports/release/` from
  this plan itself.

**Action:** re-run `git status --short` immediately before executing the
sequence below, and re-check any path whose content changed after this plan was
written (notably `tools/check_security.py`, the two `reports/hydroma/*.md`
catalogs, and `services/finance/tests/test_chart_of_accounts.py`, none of which
existed in their current form when this plan was drafted).

**Late-arrival rule.** Any path that appears in `git status` but is *not* named
in this plan was written after the snapshot. Assign it by the same prefix rules
used here — `engine/**` → commit 1 (scientific core) unless it names a
scenario/data-pipeline/validation subject, `tools/check_*` → commit 9, etc. Two
late arrivals are already known:

* `engine/hydroma/data_assimilation/assimilation.py` (tracked, modified 09:29)
  → add to **commit 1** (engine scientific core).
* `tools/check_security.py` (created 09:17, still being modified) → add to
  **commit 9** (CI/security) only once the writer has gone quiet.

Nothing in this plan mutates git state. Every command is either read-only
(`git status`, `git ls-files`, `git check-ignore`, `git diff`) or a proposed
`git add` that the owner runs. No `git commit`, no `git rm`, no `git add` was
executed by the audit.

---

## 1. Runtime-artifact audit (what must never be committed)

"Tracked" = present in `git ls-files`. "Ignored" = matched by an ignore rule
(`git check-ignore --no-index`), before vs after this change.

| Path | What it is | Tracked before | Covered before | Covered after |
| --- | --- | --- | --- | --- |
| `data/security/audit.jsonl` | append-only security audit log, **21.6 MB**, grown during this session's test runs (`services/security/audit.py` `_LOCAL_FILE`) | **YES** | NO | YES — `.gitignore:42 data/security/` |
| `data/cache/` | GBIF + connector response cache (6 files) | no | NO | YES |
| `data/copernicus_cache/` | satellite CDS cache dir (empty; `services/data_sources/copernicus_cds.py` `CACHE_DIR`) | no | NO | YES |
| `data/motors/` | scientific-motor chain cache dir (empty; `services/scientific_motors/base.py` defaults `data/motors/cache`) | no | NO | YES |
| `data/maps/` | map-engine output dir (empty) | no | NO | YES |
| `data/master/` | **built** DuckDB `eco_nojin_master.duckdb` (2.8 MB; `tools/build_master_duckdb.py` `DEFAULT_OUTPUT`) | no | NO | YES |
| `data/rag/` | generated RAG fallback corpus (745 KB, vectors; `services/ai/hydroma_rag.py` writes it when qdrant is absent) | no | NO | YES |
| `data/reports/` | session report JSON (95 files, UUID names) | no | NO | YES |
| `data/food_security.duckdb` | **built** DuckDB (`tools/build_food_security_table.py` output) | no | NO | YES — via `*.duckdb` |
| `__pycache__/` | bytecode | no (0 tracked) | YES (pre-existing rule) | YES |
| `.pytest_cache/` | pytest cache | no (0 tracked) | YES (pre-existing rule) | YES |
| `.mypy_cache/` | mypy cache | no (0 tracked) | YES (pre-existing rule) | YES |
| `.ruff_cache/` | ruff cache | no (0 tracked) | YES (pre-existing rule) | YES |

Evidence for the "tracked" column:

* `git ls-files data/` → exactly two tracked files:
  `data/model_registry.json` (genuine source) and `data/security/audit.jsonl`
  (runtime log — decision A below).
* `git ls-files "*.duckdb"` → **0** files, so the `*.duckdb` rule cannot
  untrack anything.
* `git ls-files` filtered on `__pycache__` / `*_cache` → **0** files.
* `git check-ignore --no-index --stdin -z -v` over all 1,589 tracked files
  matches **exactly one** tracked path — `data/security/audit.jsonl` — i.e. no
  source file is swallowed by the new rules.

---

## 2. `.gitignore` change

The working tree already carried an **uncommitted** secrets block
(`.env`, `.env.*`, `!.env.example`, `*.key`, `*.pem`, `privacy_vault/`) from
the earlier repair session. That block is included in this commit; the audit
only *added* the second block below.

```diff
--- a/.gitignore
+++ b/.gitignore
@@ -1,6 +1,14 @@
 # Virtual environment (2.2 GB — never commit)
 .venv+

+# Local secrets — never commit. .env.example is the committed template.
+.env
+.env.*
+!.env.example
+*.key
+*.pem
+privacy_vault/
+
 # Caches and generated artifacts
 __pycache__/
 *.py[cod]
@@ -17,6 +25,22 @@
 temp_imports*.json
 openapi.json

+# Runtime data (regenerated by tools/tests — never commit; see
+# reports/release/COMMIT-PLAN-2026-10-10.md)
+data/cache/
+data/copernicus_cache/
+data/motors/
+data/maps/
+data/master/
+data/rag/
+data/reports/
+*.duckdb
+# NOTE: data/security/audit.jsonl is *still tracked* (runtime security log,
+# ~21.6 MB) — ignore rules never untrack files, so it stays in the index until
+# the owner runs `git rm --cached data/security/audit.jsonl`. The rule below
+# only takes effect once that decision is executed.
+data/security/
+
 # OS / editor
 .vscode/
 .DS_Store
```

Deliberately **not** ignored, because these are genuine source: `data/links/`
(the links catalog), `data/model_registry.json` (registry), `tools/import_guard_policy.json`
(policy data committed at HEAD), and every `*.py` file.

Guard test for these rules (new, untracked):
`tools/tests/test_gitignore_covers_runtime_data.py` — parses `.gitignore` with
a small pure-Python matcher, cross-checks against
`git check-ignore --no-index`, pins both directions (runtime ignored, source
not) and the "no tracked file matches a rule except the documented
`data/security/audit.jsonl`" invariant. Offline, no sleeps, ~7 s.

---

## 3. Proposed commit sequence

Ordering rationale: the ignore rules go in first so every later `git add` is
protected; then the scientific core and its layers; services land after the
gateway wiring they mount through; documentation and compliance last. Each
commit's `git add` block is complete and non-overlapping — every changed path
appears exactly once across the whole sequence.

Bucket sizes (status entries): 38 / 17 / 20 / 13 / 42 / 99 / 59 / 25 / 27 / 11 / 3.

### Commit 0 — safety net (repo hygiene)

```bash
git add .gitignore
git add tools/tests/test_gitignore_covers_runtime_data.py
git add reports/release/COMMIT-PLAN-2026-10-10.md
```

Suggested message: `chore: ignore runtime data artifacts + guard test for the rules`

### Commit 1 — engine scientific core (38 entries)

```bash
git add engine/cpp_core
git add engine/hydroma/analyses
git add engine/hydroma/biofertilizer
git add engine/hydroma/calibration
git add engine/hydroma/climate
git add engine/hydroma/config
git add engine/hydroma/core
git add engine/hydroma/cpp_bridge
git add engine/hydroma/crop
git add engine/hydroma/examples
git add engine/hydroma/formulas
git add engine/hydroma/groundwater
git add engine/hydroma/hybrid_ml
git add engine/hydroma/mrv
git add engine/hydroma/plant_neuro
git add engine/hydroma/satellite
git add engine/hydroma/simulation
git add engine/hydroma/simulation_env
git add engine/hydroma/soil
git add engine/hydroma/utils
git add engine/hydroma/watershed
git add engine/land/integration
git add engine/hydroma/alembic_graph.py
git add engine/hydroma/cpp_bindings.py
git add engine/hydroma/data_assimilation/assimilation.py
git add engine/hydroma/models/hyrue.py
git add engine/hydroma/quantity.py
git add engine/hydroma/wrapper.py
git add engine/land/drainage.py
git add engine/tests/test_groundwater_extended.py
```

Suggested message: `engine: scientific-core updates (climate, soil, groundwater, plant neuro, watershed, ROTHC runner)`

### Commit 2 — scenario layer (17 entries)

```bash
git add scenario/
git add engine/hydroma/scenarios
git add engine/hydroma/scenario_composite/
git add engine/hydroma/spi_calculator.py
git add engine/hydroma/water_balance.py
git add engine/hydroma/water_productivity.py
git add adapters/engine_adapter.py
git add adapters/hydroma_adapter.py
git add engine/tests/test_scenario_layer.py
git add engine/tests/test_scenario_manager.py
git add engine/tests/test_composite_scenario_engine.py
git add engine/tests/test_spi_calculator.py
git add engine/tests/test_water_balance.py
git add engine/tests/test_water_productivity.py
git add services/analysis/drought_agent.py
git add services/analysis/scenario_agent.py
git add services/analysis/tests/
```

Suggested message: `scenario: composite scenario engine, SPI/water-balance/productivity indicators and adapters`

### Commit 3 — knowledge / decision bridge (20 entries)

```bash
git add decision/
git add engine/knowledge/__init__.py
git add engine/tasmimyar/__init__.py
git add engine/tasmimyar/weights_loader.py
git add engine/hydroma/decision_support/dss.py
git add engine/hydroma/risk/
git add engine/hydroma/economics/analysis.py
git add engine/hydroma/economics/integration.py
git add engine/tests/test_decision_economic_criteria.py
git add engine/tests/test_tasmimyar_weights.py
git add engine/tests/test_knowledge_engine.py
git add services/ai/embedding_service.py
git add services/ai/unified_rag.py
git add services/ai/hydroma_rag.py
git add services/ai/tests/
git add services/knowledge/service.py
git add services/knowledge/tests/
git add services/scientific_motors/registry.py
git add services/scientific_motors/tests/
git add services/tasmimyar/tests/
```

Suggested message: `knowledge: DSS/economics bridge, tasmimyar weights, scientific-motor registry, RAG services`

### Commit 4 — data layer + DuckDB (13 entries)

```bash
git add engine/data_connector.py
git add engine/hydroma/data_pipeline/pipeline.py
git add engine/hydroma/data_pipeline/download_gate.py
git add engine/hydroma/data_pipeline/README-ZED.md
git add engine/hydroma/data_pipeline/connectors/
git add engine/hydroma/data_pipeline/tests/test_master_duckdb_build.py
git add engine/tests/test_download_gate.py
git add tools/build_master_duckdb.py
git add tools/build_food_security_table.py
git add tools/tests/test_build_food_security_table.py
git add tools/tests/fixtures/live_exchange_2026-10-10.json
git add services/data_manual/loader.py
git add services/data_manual/tests/
```

Suggested message: `data: master/food-security DuckDB builders, data-pipeline download gate, connectors package`

**Excluded from this commit (now ignored):** `data/master/`.
Decision A below covers `data/security/audit.jsonl`.

### Commit 5 — registry / gateway wiring (42 entries)

```bash
git add database/
git add engine/data/meta_contract.py
git add engine/errors.py
git add engine/gateway/__init__.py
git add engine/gateway/pint_audit.py
git add engine/models/registry.py
git add engine/models/maturity.py
git add engine/ports/persistence.py
git add engine/ports/persistence_impl.py
git add engine/ports/persistence_port.py
git add adapters/persistence/
git add data/model_registry.json
git add services/_gateway_facade.py
git add services/api_gateway/main.py
git add services/api_gateway/routers/
git add services/api_gateway/tests/
git add services/models/land_models.py
git add services/models/registry.py
git add tools/migrate_services_to_gateway.py
git add tools/run_e2e_demo.py
git add engine/tests/test_registry_status.py
git add engine/tests/test_unwired_model_wiring.py
git add engine/tests/test_meta_contract.py
git add engine/tests/test_error_contract.py
git add engine/tests/test_maturity_mapping.py
git add engine/tests/test_persistence_port_contract.py
git add engine/tests/test_persistence_spec_contract.py
git add engine/tests/test_architecture_rules.py
git add engine/tests/test_e2e_chain_gating.py
git add engine/tests/test_pint_unit_gate.py
```

Suggested message: `gateway: dispatch wiring, persistence ports/bridge and model-registry contracts`

### Commit 6 — services domain layer (99 entries; added theme)

Not in the original ten themes, but the remaining 99 `services/**` paths need a
home. It sits here because these services mount through the gateway wired in
commit 5.

```bash
git add services/admin
git add services/analytics
git add services/auth
git add services/auth_legacy
git add services/backup
git add services/bots
git add services/business_modules/carbon
git add services/business_modules/voice
git add services/carbon
git add services/commerce
git add services/content
git add services/contracts
git add services/dispute_resolution
git add services/ecowallet
git add services/field_monitoring
git add services/finance
git add services/integration
git add services/inventory
git add services/jobs
git add services/land
git add services/landscape
git add services/ledger
git add services/livestock
git add services/logistics
git add services/marketplace
git add services/mobile_monitoring
git add services/nojin
git add services/notification
git add services/oracle
git add services/organization
git add services/rangeland
git add services/reporting
git add services/simulation
git add services/sponsors
git add services/telegram_bot
git add services/territory
git add services/tourism
git add services/workflow
```

Suggested message: `services: domain-layer modules and their test suites (finance, commerce, marketplace, tourism, landscape)`

### Commit 7 — validation corpus (59 entries)

```bash
git add conftest.py
git add tests/
git add indicators/
git add engine/baseline/R18.json
git add engine/honesty/
git add engine/scientific_verification/__init__.py
git add engine/strict_tests/
git add engine/models/cards/
git add engine/hydroma/models/validation/
git add engine/land/tests/test_kirpich_agreement.py
git add services/conftest.py
git add services/validation/formula_checks.py
git add services/validation/tests/
git add engine/tests/test_validation_corpus.py
git add engine/tests/test_card_code_agreement.py
git add engine/tests/test_machine_evidence_consistency.py
git add engine/tests/test_no_phantom_test_paths.py
git add engine/tests/test_evidence_chain.py
git add engine/tests/test_citation_links.py
git add engine/tests/test_fao56_example18.py
git add engine/tests/test_fao56_example20_missing_data.py
git add engine/tests/test_rosetta_ptf_reference.py
git add engine/tests/test_climate_indices_spi_parity.py
git add engine/tests/test_pyet_parity.py
git add engine/tests/test_mutation_sensitivity.py
git add engine/tests/test_honesty_contracts.py
git add engine/tests/test_baseline_manager.py
```

Suggested message: `validation: canon cards, strict-test suite s01-s23, FAO56/ROSETTA/pyet parity corpora`

### Commit 8 — connectors (25 entries)

```bash
git add engine/hydroma/data_pipeline/tests/test_era5_connector.py
git add engine/hydroma/data_pipeline/tests/test_cds_connector.py
git add engine/hydroma/data_pipeline/tests/test_wapor_connector.py
git add engine/hydroma/data_pipeline/tests/test_grdc_connector.py
git add engine/hydroma/data_pipeline/tests/test_igrac_connector.py
git add engine/hydroma/data_pipeline/tests/test_usgs_nwis_connector.py
git add engine/hydroma/data_pipeline/tests/test_data_connector_errors.py
git add services/satellite/
git add services/map_engine/
git add services/mrv/kobo.py
git add services/business_modules/iot/device_connector.py
```

Suggested message: `connectors: ERA5/CDS/WAPoR/GRDC/IGRAC/USGS suites, satellite fetchers and map-engine pipelines`

### Commit 9 — CI / security (27 entries)

```bash
git add .github/
git add pyproject.toml
git add requirements.txt
git add tools/detect_imports.py
git add tools/_analyze_imports.py
git add tools/check_citations.py
git add tools/check_security.py
git add tools/check_venv_integrity.py
git add tools/phantom_path_check.py
git add tools/eco04_comprehensive_scan.py
git add tools/tests/test_check_security_env_scan.py
git add services/security/
git add services/alerting/models.py
git add services/provenance/
git add services/blockchain/service.py
git add services/quality_assurance/routers/quality.py
git add services/territory_audit.py
git add services/tests/
git add reports/security/
git add reports/quality/
git add reports/lint/
```

Suggested message: `ci: import-guard tooling, security scan/checks, security and provenance services`

### Commit 10 — reports / docs (11 entries)

```bash
git add AGENTS.md
git add HYDROMA-MASTER-TESTING.md
git add "ECO-NOJIN MASTER EXECUTION SPECIFICATION.md"
git add architecture/
git add reports/HYDROMA-PROJECT-REPORT-FA-2026-10-09.md
git add reports/HYDROMA-STAGE1-DIAGNOSTIC-2026-10-09.md
git add reports/HYDROMA-STAGE2-FIX-REPORT-2026-10-09.md
git add reports/eco-nojin/
git add reports/hydroma/
```

`reports/baseline_engine.txt` is **deliberately excluded** — see observation
O-1 below. Note that `reports/hydroma/` was modified by the concurrent writer
at 09:12/09:14; review those two files before committing them.

Suggested message: `docs: stage-1/stage-2 diagnostics, project report and architecture records`

### Commit 11 — `.env.example` + links catalog (3 entries)

```bash
git add .env.example
git add data/links/
git add LICENSES/
```

Suggested message: `config: env template, external links catalog and license bundle`

---

## 4. Owner decisions (do not execute without the owner)

### Decision A — `data/security/audit.jsonl` is a tracked runtime log

Current state (measured):

* Tracked: **yes** — `git ls-files` lists it, and `git status` shows
  ` M data/security/audit.jsonl`.
* Size: **~21.6 MB**, still growing — `services/security/audit.py` appends to
  `data/security/audit.jsonl` (`_LOCAL_FILE`) during test runs, so it is pure
  runtime state, not source.
* The new rule `data/security/` (`.gitignore:42`) **does not untrack it** —
  ignore rules never affect the index. Until the decision is executed, the file
  keeps showing as modified and *can* still be committed.

No `git rm --cached` was run. If the owner decides to untrack it, the proposed
command is:

```bash
git rm --cached data/security/audit.jsonl          # keep the local file on disk
git commit -m "chore: untrack runtime security audit log"
```

Add it back only if the owner decides the log is evidence that belongs in
history — in which case it should be rotated and trimmed first, not carried at
current size.

### Decision B — the 5-agent orphan test files

**63 untracked test files** exist. Static checks run during the audit: all 63
parse (`py_compile`), every `engine`/`services` import in them resolves, all 63
are collected by `pytest --collect-only -q engine services`, and none contains
`TODO`/`FIXME`/stub bodies. So none is obviously broken — but the owner asked
which are complete, and only the owner can confirm that each file's checks were
actually run green.

Full list, oldest first (last-modified local time, 2026-10-10, with size):

```text
03:03    6727  engine/hydroma/data_pipeline/tests/test_data_connector_errors.py
03:03    9570  engine/hydroma/data_pipeline/tests/test_era5_connector.py
03:03  35323   engine/strict_tests/test_s16_gateway_strict_contracts.py
03:12  14345   engine/strict_tests/test_s21_recommendation_validation.py
03:33    9236  engine/hydroma/data_pipeline/tests/test_master_duckdb_build.py
03:33  10271   engine/hydroma/data_pipeline/tests/test_cds_connector.py
03:33    9401  engine/hydroma/data_pipeline/tests/test_wapor_connector.py
04:45    2110  engine/tests/test_error_contract.py
04:46    3018  engine/tests/test_maturity_mapping.py
04:59    3175  engine/tests/test_download_gate.py
05:00    4393  engine/tests/test_tasmimyar_weights.py
05:01    2575  engine/tests/test_water_productivity.py
05:01  18556   engine/tests/test_architecture_rules.py
05:02    5475  engine/tests/test_meta_contract.py
05:03  12240   engine/tests/test_persistence_spec_contract.py
05:05  10261   engine/tests/test_baseline_manager.py
05:20    3466  engine/tests/test_water_balance.py
05:24    5347  engine/tests/test_persistence_port_contract.py
05:28  43085   engine/strict_tests/test_s19_plant_neuro_validation.py
05:28  17279   engine/tests/test_scenario_layer.py
05:28  31329   engine/strict_tests/test_s17_gateway_route_repair.py
05:30  38483   engine/tests/test_decision_economic_criteria.py
05:38  16336   engine/strict_tests/test_s18_scientific_validation.py
05:38  34963   engine/strict_tests/test_s20_simulation_validation.py
05:38  17379   engine/strict_tests/test_s23_decision_engine_validation.py
05:44  10750   engine/tests/test_groundwater_extended.py
05:46  15206   engine/hydroma/data_pipeline/tests/test_usgs_nwis_connector.py
05:51  17670   engine/hydroma/data_pipeline/tests/test_igrac_connector.py
05:55  10056   engine/hydroma/data_pipeline/tests/test_grdc_connector.py
06:04  19341   engine/tests/test_scenario_manager.py
06:09    5143  services/finance/tests/test_finance_router_wallet.py
06:13    3917  services/finance/tests/test_wallet_batch_posting.py
06:13    2278  services/commerce/tests/test_settlement_posting.py
06:14  15847   services/finance/tests/test_reconciliation.py
06:21  12505   engine/tests/test_composite_scenario_engine.py
06:23    6704  engine/tests/test_e2e_chain_gating.py
06:23  10654   services/finance/tests/test_consolidation.py
06:36  17842   engine/tests/test_spi_calculator.py
06:56  10198   services/marketplace/tests/test_order_items.py
07:05  17201   services/tourism/tests/test_api_router.py
07:19    3744  engine/tests/test_validation_corpus.py
07:31  25886   engine/tests/test_registry_status.py
07:31  46023   engine/tests/test_unwired_model_wiring.py
07:38    4576  engine/land/tests/test_kirpich_agreement.py
07:45  13468   services/inventory/tests/test_p0_3_http500_repair.py
07:54    5253  engine/tests/test_fao56_example20_missing_data.py
07:55    8370  engine/tests/test_fao56_example18.py
07:56    2390  engine/tests/test_honesty_contracts.py
08:00    7160  engine/tests/test_mutation_sensitivity.py
08:00  13424   services/commerce/tests/test_landscape_fund_crediting.py
08:04  14729   services/marketplace/tests/test_payment_order_flow.py
08:05    4413  engine/tests/test_no_phantom_test_paths.py
08:06    7722  engine/tests/test_machine_evidence_consistency.py
08:09  21122   services/inventory/tests/test_p2_18_concurrency_integrity.py
08:25  25471   engine/tests/test_card_code_agreement.py
08:36    2728  engine/tests/test_citation_links.py
08:54  20508   engine/tests/test_pyet_parity.py
08:56    3892  engine/tests/test_pint_unit_gate.py
09:02    7133  services/commerce/tests/test_event_emission.py
09:02  19217   engine/tests/test_rosetta_ptf_reference.py
09:03  19189   engine/tests/test_climate_indices_spi_parity.py
09:13  18018   services/marketplace/tests/test_event_emission.py
09:20  19317   services/finance/tests/test_chart_of_accounts.py
```

The **last five written** — the most likely agent output still in flight, and
the ones to confirm first:

```text
09:02    7133  services/commerce/tests/test_event_emission.py
09:02  19217   engine/tests/test_rosetta_ptf_reference.py
09:03  19189   engine/tests/test_climate_indices_spi_parity.py
09:13  18018   services/marketplace/tests/test_event_emission.py
09:20  19317   services/finance/tests/test_chart_of_accounts.py
```

Watch item: the only duplicate basename pair in the whole set is
`test_event_emission.py` in both `services/commerce/tests/` and
`services/marketplace/tests/` (written 09:02 and 09:13, i.e. by two different
writes 11 minutes apart). If both were meant to be one file, one of them is an
orphan.

Recommended pre-commit gate for whichever files the owner blesses:

```bash
python -m pytest engine/ services/ -q -p no:cacheprovider
```

---

## 5. Additional observations for the owner

These are **not** part of decisions A and B; each needs a yes/no from the owner
before the related path is committed.

**O-1 — `reports/baseline_engine.txt` is a captured pytest log, not a document.**
It ends with `35 failed, 2091 passed, 29 skipped, 44 xfailed ... in 262.01s`.
Either it is the pre-repair baseline evidence (then keep it, and say so in the
commit), or it is a stale run log (then delete it). It is excluded from commit
10 above; it is also currently untracked.

**O-2 — generated scan outputs are already tracked in `tools/`.**
`tools/detect_imports_output.json`, `tools/detect_imports_output_v2.json`,
`tools/detect_imports_summary_v2.json` and `tools/eco04_comprehensive_scan.json`
are tracked run outputs (pre-existing debt). Suggested, if the owner agrees:

```bash
git rm --cached tools/detect_imports_output.json tools/detect_imports_output_v2.json tools/detect_imports_summary_v2.json tools/eco04_comprehensive_scan.json
printf '%s\n' 'tools/detect_imports_output*.json' 'tools/eco04_comprehensive_scan.json' >> .gitignore
```

**O-3 — stray files at the repository root.** `file` is a zero-byte file being
recreated roughly every minute by the concurrent process; `temp_probe_gateway.py`
(7 KB) and `_scratch_validation/` (18 scratch scripts) are session leftovers;
`temp_fix_vr.py` is **tracked but deleted from disk** (` D temp_fix_vr.py`), so
it needs an index removal, not an ignore rule. Suggested:

```bash
git rm temp_fix_vr.py                 # tracked deletion; keeps history clean
Remove-Item file, temp_probe_gateway.py
Remove-Item -Recurse _scratch_validation
```

**O-4 — the working tree is being written by another actor.** See section 0.
Pick a quiet window, re-run `git status --short`, and re-read this plan before
executing. A `git stash` was also present on 2026-10-10
(`stash@{0}: WIP on master: ...`) — irrelevant to this plan, but worth a look
before any rebasing.

---

## 6. Verification performed by this audit

| Check | Result |
| --- | --- |
| `git status --short` before / after the `.gitignore` change | 360 → 360 (exactly 5 runtime entries removed; 5 entries added in the same window by the concurrent writer and by this plan) |
| Runtime entries removed from status | `data/cache/`, `data/master/`, `data/rag/`, `data/reports/`, `data/food_security.duckdb` |
| Runtime paths still visible in `git status` after the change | none (`data/cache/`, `data/copernicus_cache/`, `data/motors/`, `data/maps/`, `data/master/`, `data/rag/`, `data/reports/`, `*.duckdb` all ignored) |
| Tracked files that match any ignore rule | exactly **1** — `data/security/audit.jsonl` (decision A) |
| `python tools/detect_imports.py --root .` | **PASS** — 0 violations |
| `pytest tools/tests -q -p no:cacheprovider` | **passed** — 47 passed (26 pre-existing + 16 concurrent `test_check_security_env_scan.py` + 5 new gitignore-guard tests) |
| `ruff check tools/tests/test_gitignore_covers_runtime_data.py` | All checks passed |
| `mypy tools/tests/test_gitignore_covers_runtime_data.py --ignore-missing-imports` | Success: no issues found |
| Mutating git commands executed by this audit | none (no `git add`, `git commit`, `git rm`, `git stash`) |
