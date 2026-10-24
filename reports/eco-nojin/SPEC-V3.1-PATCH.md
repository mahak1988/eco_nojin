# SPEC v3.1 PATCH — line-by-line corrections for `ECO_NOJIN_HYDROMA_MASTER_v3.0.html`

Document id: `ECO-V3-PATCH` · Date: 2026-10-10 · Basis: `SPEC-V3-CONFORMANCE-REPORT.md` (all numbers below measured live on this date)
How to apply: each Patch row is a literal text replacement in the HTML (or a follow-up task). Nothing in this patch changes the document's intent — it converts six *claims* into *measured statements/targets*, repairs two citations, resolves one identifier collision, and repairs five phantom paths.

## P-01 §2.1 Capability map — "۱۸ مدل علمی تأییدشده (سطح ۳)"
- **Current:** `<li>۱۸ مدل علمی تأییدشده (سطح ۳)</li>`
- **Replace with:** `<li>۷ مدل ثبت‌شده در سطح ۳ (ریشه: ۹.۹٪ از ۷۰ مدل)، که ۳ مدل آن لنگر مرجع بیرونی دارند — هدف ۹۰ روزه: ۱۵ مدل سطح ۳</li>`
- **Evidence:** `engine/models/maturity.py` summary measured 2026-10-10: S0 14 · S1 47 · S2 2 · S3 7; external anchors: CANON-001 (FAO-56 Ex. 18), CANON-002 (Ex. 20), CANON-004 (NEH/TR-55). Gap G-V3-03.

## P-02 §2.1 Capability map — "Unit Registry (pint)"
- **Current:** `<li>Unit Registry (pint)</li>`
- **Replace with:** `<li>Unit Registry (pint) — ممیزی واحد پیاده و در حال اتخاذ؛ تبدیل واحد در Gateway هنوز در انتظار تصمیم (G-V3-01)</li>`
- **Evidence:** `engine/gateway/pint_audit.py` (16 unit strings, 6 domain units, 6 tests) exists; `engine/gateway/__init__.py:2008-2022` still multiplies by hand-written `si_equivalent`.

## P-03 §2.1/§3.3 — "Local Data Mirror (CHIRPS, ERA5, SoilGrids)"
- **Current:** `<li>Local Data Mirror (CHIRPS, ERA5, SoilGrids)</li>`
- **Replace with:** `<li>Local Data Mirror — وضعیت: BLOCKED_ENVIRONMENT؛ هیچ آینه‌ای موجود نیست (EO-16). پیش‌نیاز: تصمیم ingestion (STAC/منبع هر داده) + sidecar معتبر §۴.۲ (G-V3-08)</li>`
- **Evidence:** `reports/eco-nojin/ECO-16-E2E-REPORT.md` status BLOCKED_ENVIRONMENT; `tools/run_e2e_demo.py` exits 2 on the absent mirror.

## P-04 §3.1 — CANON-006 reference and threshold
- **Current:** `<tr><td>CANON-006</td><td>van Genuchten soil</td><td>Carsel & Parrish 1988</td><td>rel=1e-12</td></tr>`
- **Replace with:** `<tr><td>CANON-006</td><td>van Genuchten soil</td><td>van Genuchten 1980 + Mualem 1976 (مولف: WRR 12:513)<br>جدول پارامترها: design_assumption — استناد Carsel &amp; Parrish کنارگذاشته شد (ورودت WRR 24:755-769؛ مقایسه با Rosetta 3 ثبت شده)</td><td>rel=1e-12 (فرم)؛ جدول: PARTIAL (α تا ۳.۸×)</td></tr>`
- **Evidence:** `FORMULA-VALIDATION-REGISTER.md` §5; `engine/tests/test_rosetta_ptf_reference.py` (12 textures measured); `engine/data/soil_vg_table.csv` provenance rows.

## P-05 §3.1 — CANON-005 reference and threshold
- **Current:** `<tr><td>CANON-005</td><td>Theis groundwater</td><td>scipy.special.expi</td><td>دقیق</td></tr>`
- **Replace with:** `<tr><td>CANON-005</td><td>Theis groundwater</td><td>Theis, C.V. (1935) — مرجع: تابع exponentially integral (پیاده‌سازی مرجع: scipy.special.expi). <b>مقدار مرجع چپشده در درخت نیست</b>؛ حالت مرجع اندازه‌گیری‌شده: ۰.۳۰۶ m (کارت PREV از ۰.۰۱۸ اصلاح شد)</td><td>VALIDATED_METHOD_CONFORMANCE (بدون لنگر چپشده)</td></tr>`
- **Evidence:** `models/cards/CANON-005_theis_solution.md` (corrected by PHASES); `test_groundwater_extended.py`; G-V3-05.

## P-06 §3.1 — the "۰.۰۰۰٪" thresholds for CANON-001/002
- **Current:** `<tr><td>CANON-001</td>…<td>۰.۰۰۰٪</td></tr>` and `<tr><td>CANON-002</td>…<td>۰.۰۰۰٪</td></tr>`
- **Replace with:** `≤۰.۰۰۵ mm/day در مقابل پیاده‌سازی مستقل (PyETo: Δ=0.000000 برای مثال‌های ۱۸/۲۰) — با انحراف مستند از متن چپشدهٔ FAO (DEV-01 کلمپ Rs/Rso، DEV-02 dtr_floor)`
- **Evidence:** `engine/tests/test_pyet_parity.py` (3.880092 = 3.880092; 4.567920 = 4.567920); `reports/eco-nojin/DEVIATION-REGISTER.md` D-01/D-02.

## P-07 §4 ECO-03 — "اصلاح Hargreaves exponent (D-18)"
- **Current:** `<li>ECO-03: اصلاح Hargreaves exponent (D-18) + S11/S02/S16/S17 به‌روزرسانی</li>`
- **Replace with:** `<li>ECO-03: اصلاح Hargreaves exponent (D-18) — <b>منبع اصلاح شد (۰.۵)، باینری آن‌سایت هنوز ۰.۴۸ است</b>؛ چکر عمومی اصلاح شد. پیش‌نیاز: بازسازی C++ در CI (G-V3-07)</li>`
- **Evidence:** `engine/cpp_core/src/climate.cpp:44-59` xfail + `scientific_verification:298` tolerance; `services/validation/formula_checks.py` fixed by PHASES.

## P-08 §6.1 KPI — "Scientific Validation Coverage ≥ ۸۰٪"
- **Current:** `<tr><td>Scientific Validation Coverage</td><td>تعداد مدل‌های سطح ۳ / کل مدل‌ها</td><td>≥ ۸۰٪</td></tr>`
- **Replace with:** `<tr><td>Scientific Validation Coverage</td><td>تعداد مدل‌های سطح ۳ / کل مدل‌ها</td><td>خط‌مبنای امروز ۹.۹٪ — هدف ۹۰ روزه ≥ ۲۵٪، هدف بلندمدت ≥ ۸۰٪ (با لنگر بیرونی برای هر ارتقا)</td></tr>`
- **Evidence:** measured maturity 7/70; G-V3-03. An 80 % target over 70 models without anchors would re-create exactly the "validated while blocked" class the audit removed.

## P-09 §6.1 KPI — "Reference Data Availability … ۱۰۰٪ برای CANON-001 تا CANON-006"
- **Current:** `<tr><td>Reference Data Availability</td><td>فایل‌های مرجع در tests/reference_data/</td><td>۱۰۰٪ برای CANON-001 تا CANON-006</td></tr>`
- **Replace with:** `<tr><td>Reference Data Availability</td><td>فایل‌های مرجع در tests/reference_data/</td><td>امروز ۳ از ۶ (CANON-001/002/004). شکاف: CANON-005 (بدون مقدار چپشده)، CANON-006 (فقط مقایسهٔ Rosetta)</td></tr>`
- **Evidence:** `tests/reference_data/fao56_examples.csv` + `test_fao56_example18/20`; corpus `scs_cn` NEH anchor; G-V3-02.

## P-10 §7.2 Quick Scan floors
- **Current:** "باید ۱۷۰۰+ passed" / "باید ۵۲۸+ passed"
- **Replace with:** "باید ≥ ۲۵۵۹ passed (خط‌مبنای ۲۰۲۶-۱۰-۱۰) و ۰ failed" / "باید ≥ ۱۰۵۲ passed و ۰ failed"
- **Rationale:** a floor below today's suite lets a regression of hundreds of tests pass unnoticed; floors must be raised as the suite grows, never lowered.

## P-11 §3.2 — the ten novel indices
- **Add after the table:** `<div class="note note-warning"><strong>پیش‌شرط پیاده‌سازی (AR-03/SB-07):</strong> هیچ‌یک از ده شاخص §۳.۲ پیش از وجود <em>تعریف چپشده + لنگر مرجع مستقل</em> پیاده نمی‌شود. الگو: FAO-56 Example 18 برای ENO_ET0_FAO56_001. تا آن زمان هر شاخص تألیفی، نقض SB-06 است.</div>`
- **Evidence:** absence verified by four formula audits; G-V3-11..21.

## P-12 §10 Appendix — five phantom paths
- **Rows to correct:** `ECO-NOJIN_ZED_Scientific_Appendix_v2.md` (does not exist) → mark `[باید نوشته شود]`; `ECO-NOJIN_MASTER_v3.0_UNIFIED.md` → `[باید تولید شود]`; `engine/strict_tests/test_s17_gateway_fixes.py` → the real files are `test_s16_gateway_strict_contracts.py` / `test_s17_*`; `data/reference_data/` → the live location is `tests/reference_data/`; `data/mirror/` → `[وجود ندارد — BLOCKED_ENVIRONMENT]`.
- **Evidence:** verified on disk today; same class as G-H5 (57 phantom test paths).

## P-13 Identifier collision (AR and SB) — adopt v3.0, publish the map
- **Decision proposed:** v3.0's AR-01..AR-10 and SB-01..SB-10 become canonical; the earlier spec's identifiers are re-labelled everywhere (registration YAML, docstrings, tests) with the map below.
- **Mapping (v2.0 meaning → v3.0 identifier):**

| v2.0 requirement (what the repo enforces today) | v3.0 identifier | Note |
|---|---|---|
| AR-01 Separation of Concerns (no network in science) | AR-01 | identical |
| AR-02 Dependency Inversion (Ports) | AR-02 | identical |
| AR-03 Scientific Boundary (CANON model + reference + verification) | AR-03 | v3.0 narrows it to *immutability*; keep both meanings under AR-03 |
| AR-04 no frontend/auth/payment/blockchain in scientific core | **no v3.0 equivalent** | must be kept as a project rule — propose AR-11 |
| AR-05 Services shall not call model internals | **no v3.0 equivalent** | must be kept — propose AR-12 (currently enforced by `SERVICES_NO_ENGINE_INTERNALS`) |
| AR-06 all model calls through Gateway | **no v3.0 equivalent** | must be kept — propose AR-13 |
| AR-07 AI layer shall not change the model | AR-07 | identical intent |
| AR-08 Fail Closed | AR-08 | identical |
| AR-09 no hidden configuration | AR-09 | v3.0 broadens to provenance — compatible |
| AR-10 every model change has reason/result/test/report | AR-10 | v3.0 broadens to positive+negative tests — compatible |

- **Follow-up task (code, not this patch):** extend `engine/honesty/statuses.py::BRAKES` from 7 to 10 (SB-01..SB-10) and add the v3.0 column to `architecture/rules.yaml`; `engine/tests/test_architecture_rules.py` (48 tests) keeps its INV coverage unchanged.

## Patch summary
| Kind | Count |
|---|---|
| Claim → measured statement | 7 (P-01, P-02, P-03, P-08, P-09, P-10, P-11) |
| Citation/reference repair | 2 (P-04, P-05) |
| Threshold honesty | 1 (P-06) |
| Historical-fix honesty | 1 (P-07) |
| Phantom paths | 1 (P-12) |
| Governance decision | 1 (P-13) |
| **Total patches** | **13** |

After these 13 patches, no claim in v3.0 contradicts the measured tree, and the document can be adopted as the project's constitution: every remaining requirement (brakes, boundary contract, schema, Quick Scan, KPIs, roadmap, index preconditions) is already enforceable by tooling that exists today.
