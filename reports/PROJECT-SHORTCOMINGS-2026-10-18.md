# کمبودها و نقص‌های پروژه HyDroMA (Eco Nojin)

**تاریخ تحلیل:** 2026-10-18  
**مبنای تحلیل:** کد زنده مخزن `D:\HyDroMA` (HEAD `2cb974e`، working tree کثیف/در حال کار) + مستندات `docs/project/*` (BASELINE, KNOWN_ISSUES, OPEN_DECISIONS, CAPABILITY_MATRIX, PHASE_PLAN, DEPENDENCY_MAP) + AGENTS.md.  
**روش:** مطالعه ساختار، اجرای گیت‌های کیفیت (ruff, pytest collect, import guard, app boot)، و استخراج نقص‌های باز از مستندات برنامه.

---

## 1. خلاصه اجرایی

پروژه یک موتور علمی آب-انرژی-کشاورزی (engine/) را با یک پلتفرم خدمات FastAPI (services/) ترکیب می‌کند. معماری دو-نیمه با مرز سخت (import guard) و قرارداد صداقت (هیچ فایلی به‌تنهایی قابلیت نیست) خوب تعریف شده و بخش بزرگی از برنامه 28-ماده‌ای بسته شده است. اما با وجود گیت‌های سبز روی کاغذ، **کمبودهای ساختاری و عملیاتی قابل توجهی** باقی مانده که مانع "محصول قابل ارائه" شدن آن است:

| شاخص | مقدار اندازه‌گیری‌شده |
|---|---|
| فایل‌های Python (بدون venv) | ~1388 |
| دامنه‌های سرویس | 75 (فقط 36 دارای تست) |
| مدل‌های موتور | 72 (۱۷ validated، ۵۵ unvalidated) |
| route ثبت‌شده در app | 118 (pin قدیمی 113، drift) |
| مسیرهای OpenAPI | 702 |
| خطاهای ruff | **1139** (baseline متعهد 769 → +370) |
| خطاهای collection pytest | 1 (BOM در `test_stage25_field_validation.py`) |
| مسائل باز KNOWN_ISSUES | ~27 |
| تصمیمات باز OPEN_DECISIONS | ~13 (D-03,D-04,D-05,D-06,D-07,D-08,D-12,D-13,D-14,D-15,D-16,D-17,D-18) |
| فازهای "partially closed" | P7, P8, P9, P11, P13, P14, P15 |
| فرانت‌اند | **حذف شده** (D-01) — محصول فقط بک‌اند |

---

## 2. کیفیت کد و نگهداری

### 2.1 بدهی lint (ruff 1139 vs baseline 769)
- `E501` (line-too-long): **602** — mayorیت فایل‌ها از حد طول خط تجاوز می‌کنند.
- `E402` (import not at top): **159** — importهای lazy/داخل تابع که ممکن است نشان‌دهنده وابستگی‌های شرطی/چرخه‌ای باشد.
- `F401` (unused import): **111** — کد مرده/واردات اضافی.
- `F811` (redefined while unused): **71** — تعریف تکراری (مثلاً `services/blockchain/service.py` دو بار `get_balance`).
- `invalid-syntax`: **48** — بخشی از آن PEP 695 (type parameter lists, Python 3.12) در `services/_contracts/status.py`, `services/api_gateway/base_router.py`, `services/api_gateway/eventbus/retry.py` با `target-version=py311`.
- `F821` (undefined name): **38** — نام‌های تعریف‌نشده که در برخی مسیرها `NameError` ایجاد می‌کنند.

### 2.2 BOM (U+FEFF) در 13 فایل
فایل‌های زیر با BOM ذخیره شده‌اند (شامل `database/hub.py` هستهٔ پایگاه داده):  
`database/hub.py`, `services/compliance/__init__.py`, `services/compliance/tests/__init__.py`, `services/knowledge/service.py`, `services/api_gateway/routers/admin_content.py`, `services/api_gateway/routers/admin_security.py`, `services/api_gateway/tests/test_frontend_contract.py`, `services/api_gateway/tests/test_p6_golden_path.py`, `services/finance/tests/test_p5_money_invariants.py`, `services/land/tests/test_land_registry.py`, `services/tourism/tests/test_p8_scope.py`, `engine/tests/test_stage25_field_validation.py`, `tmp/dump_openapi.py`.

**پیامد:** `ast.parse` روی `engine/tests/test_stage25_field_validation.py` با `SyntaxError: invalid non-printable character U+FEFF` شکست می‌خورد و collection کل `engine/` را می‌شکند (۳۴۳۷ تست جمع‌آوری‌شده + ۱ خطا، متوقف). این یک **نقص واقعی P0/P3** است که گیت "0 failed" را غیرقابل تأیید می‌کند.

### 2.3 باگ‌های نهفته (F821) — مسیرهای مرده/شکننده
- `services/api_gateway/main.py:321` — `DbOrderRepo` وارد نشده (فقط `DbProductRepo, DbSellerRepo`) → مسیر wiring marketplace به DB در صورت اجرا `NameError`.
- `services/finance/routers/finance.py:962,1014` — `ComPaymentIntent` وارد نشده → webhook بانکی (مسیر مالی حساس) در صورت اجرا `NameError`.
- `services/marketplace/hub_service.py:2098` — `MarketplaceCommissionRule` وارد نشده.
- `services/tourism/models/festival.py` — `UTC` وارد نشده (چندین `datetime.now(UTC)`).
- `engine/gateway/input_validator.py:305` — `np` وارد نشده.

اینها ممکن است "مسیرهای مرده" باشند، اما در یک پروژه مالی/علمی نباید کد غیرقابل اجرا در مسیرهای حساس وجود داشته باشد.

### 2.4 فایل‌های بیش از حد بزرگ
- `engine/gateway/model_dispatcher.py`: **2554 خط** (سقف تعریف‌شده در `test_structure_ceilings.py` = 800) → KN-22. نگهداری و بازبینی آن بسیار سخت است.
- `services/api_gateway/main.py`: assembly monolitیک با 100+ router.

### 2.5 39 دامنهٔ سرویس بدون تست
دامنه‌های بدون پکیج `tests/`: `alerting, audit, auth_legacy, backup, business_modules, content, contracts, data, data_sources, design_engine, dispute_resolution, ecosystem, ecowallet, field_monitoring, integration, legal, logistics, mobile_monitoring, models, mrv, nojin, observability, ogc, oracle, organization, privacy, provenance, quality, quality_assurance, rangeland, reliability, science, supabase, territory, wallet, workers` (و چند internal).  
**پیامد:** قابلیت‌های مهم (backup, legal, rangeland, mrv, privacy, provenance) بدون پوشش تستی — ناقض "tested/validated".

### 2.6 `__init__.py` گم‌شده
- `services/territory/` و `services/wallet/` فاقد `__init__.py` (همان کلاس نقص KN-44 که قبلاً برای `knowledge` و `blockchain` رخ داده بود). در pytest با import-mode پیش‌فرض `prepend` می‌تواند collection را بشکند.

---

## 3. امنیت

برنامهٔ امنیتی (SECURITY-REMEDIATION-PLAN) بخش بزرگی را بسته است (SEC-01..04, SEC-13 partially, SEC-14, SEC-27, SEC-28, SEC-38). اما **باز باقی مانده:**

- **SEC-05 (P1):** endpointهای بدون احراز هویت برای هزینه/محاسبه: `voice` (tts/stt/ask/ivr-call/ivr-sms با تماس واقعی Twilio)، `mrv` (۸ POST)، `sync/trigger`, `insurance`, `science`; webhook Twilio DTMF بدون اعتبارسنجی امضا.
- **SEC-06 (P1/P2, latent):** backup router با 16 endpoint بدون authz و `storage_path` بدون اعتبارسنجی (نوشتن فایل دلخواه / overwrite DB). فعلاً mount نشده اما یک `include_router` آن را فعال می‌کند — ریسک بالا.
- **SEC-07..12:** JWT در query string، supply chain فرانت (الان فرانت حذف شده ولی CI), credentials در argv pg_dump, WAL fail-open, عدم file-mode/encryption-at-rest, `prune_workspace.py` حذف فایل‌های tracked.
- **SEC-13 (MED):** CSRF exemptions روی routeهای state-changing auth (`refresh`, `logout`, `reset-password`).
- **SEC-15/16/17/18/19/20/21/22/23/24/25:** CORS headers ناقص، enumeration، 2FA بدون TOTP، JWT بدون aud/iss، step-up replay در پردازش، rate-limit per-process، bind 0.0.0.0، dead `security_legacy.py`، password policy ضعیف، demo creds، passkey localhost.
- **KN-35..KN-42:** بسیاری بسته شده، اما S3-B/S4 follow-ups باز (SEC-13, SEC-16, SEC-17, SEC-19, SEC-23, SEC-08 lockfile).
- **rate limiting per-process:** فرض single-worker مستند نشده؛ XFF چپ‌ترین hop از هر proxy مورد اعتماد گرفته می‌شود.
- **`/metrics` و `/redoc`** وضعیت امنیتی نامشخص در برخی manifests.

---

## 4. داده، مدل و مهاجرت

- **Alembic single head** (`20261013_120000_p8_departure_cancel_reason`)، 13 revision روی دیسک — خوب.
- **جداول خارج از registry:** جفت raw-SQL `ecocoin_balances`/`ecocoin_transactions` (KN-02) هنوز در هیچ migration/مدل ORM نیست؛ `adapters/persistence` صفحهٔ جدا (عمداً)؛ DuckDB artifacts.
- **Village ~18 جدول** بدون migration (KN-12) — فقط 6 `gov_*` جدول migrated.
- **Marketplace carts in-memory** (`OrderManager._carts`) — KN-23؛ cart پایدار برای buyer لاگین‌شده P12.
- **دو صفحهٔ catalog/order:** in-memory `ProductCatalog`/`OrderManager._orders` در کنار DB marketplace — KN-24 (تصمیم داده‌ای حل‌نشده).
- **Named Enum:** فقط یکی (`carbon_credit_records.state`); pre-pass plan ثبت شده اما اجرا نشده.
- **SQLite 3.49.1 < 3.51.3** (WAL-safe) — gate استقرار؛ باید قبل از WAL upgrade شود (KN-09, D-16).
- **adjust movements `abs(qty)`** — KN-07 بسته شده (reconcile folds via prefixes) اما reconciliation کماکان quantity/value-blind به mispostingهای ledger.
- **per-user attribution across 5 ledgers** — D-10 بسته شده (`users.id` shared key) اما historical NULLs باقی می‌مانند.
- **backup/restore drill** (D-17) مستند شده اما شواهد اجرا نیست.

---

## 5. موتور علمی (engine)

- **72 مدل، فقط ۱۷ validated، ۵۵ unvalidated** — KN-16 triaged اما backlog باز.
- **provenance/uncertainty** فقط partial؛ روی هر payload علمی wire نشده (P10).
- **scenarios/apply** مدل ثبت نشده → 500 `Model APPLY_SCENARIO not registered` (KN-29).
- **nojin endpoints:** 422/500 (db field required, soil analyze UnboundLocalError, rangeland IntegrityError, groundwater type not subscriptable) — KN-27.
- **Numba claim 124–244×** — گزارش شده، بازتولید مستقل انجام نشده (KN-16).
- **heavy RAG tests** (torch/sentence-transformers) تحت xdist crash می‌کنند (KN-15) — sharding لازم.
- **model_dispatcher.py 2554 خط** — ceiling نقض.
- **BOM** در `engine/tests/test_stage25_field_validation.py` collection را می‌شکند.

---

## 6. تست و کیفیت

- **services:** 2102 تست جمع‌آوری، 0 خطا collection.
- **engine:** 3437 تست + 1 خطا collection (BOM).
- **strict_tests:** 1390 collected.
- **39 دامنه بدون تست** (§2.5).
- **heavy RAG tests** crash تحت xdist (KN-15).
- **route-count pin** (113) drift کرده به 118 بدون به‌روزرسانی مستندات/تست.
- **مایپای:** گزارش 0 errors اما اجرای کامل timeout می‌خورد (120s) — قابلیت اطمینان پایین در CI.

---

## 7. API و قرارداد

- **`/api/v1/rules` و `/api/v1/units`** → 503 (duckdb store unavailable) — KN-43 resolved به 503 (قبلاً 500).
- **`/api/v1/sync/*`** disabled stub (KN-28) — `/merge` همیشه `client_wins` برمی‌گرداند.
- **`/api/tasmimyar`** prefix غیراستاندارد (KN-29).
- **`/lms/*`** نیازمند env vars (503-ready).
- **`/api/nojin/*`** 422/500 (KN-27).
- **marketplace stats** aggregate across all sellers (KN-21) — per-seller scoping نیست.
- **`/dashboard/public/*`** بخشی fabrication داشت (KN-46 resolved: carbon/projects/weather به no_data).
- **marketplace hierarchy** (marketplace→bazaar→shop→product) — سطح bazaar هنوز در کد نیست (CAPABILITY_MATRIX: partial).
- **tourism** partially closed — refund/incident entities باقی (P8).

---

## 8. تصمیمات باز (OPEN_DECISIONS)

بسته‌شده: D-01 (frontend removed), D-09, D-10, D-11.  
**باز:** D-03 (pilot jurisdiction), D-04 (Eco Coin nature), D-05 (blockchain), D-06 (NATS), D-07 (payment providers), D-08 (session model), D-12 (offline scope), D-13 (model release bar), D-14 (local brand/village validation), D-15 (hosting), D-16 (WAL/SQLite), D-17 (backup RPO/RTO), D-18 (reactivating frontend — architecture review pending).  
**پیامد:** فازهای P5/P6/P7/P8/P9/P11/P13/P15 بلوکه یا "partially closed" باقی مانده‌اند.

---

## 9. فرانت‌اند

- فرانت‌اند کاملاً حذف شده (D-01 closed 2026-10-13): `frontend/`, design/audit/plan docs, tooling, CI job. **محصول فقط بک‌اند است.**
- D-18: یک initiative جدید React/Vite (untracked) با architecture review pending.
- OpenAPI (702 paths) قرارداد عمومی HTTP است؛ هیچ client تایپ‌شده در CI drift gate ندارد.
- **کمبود:** بدون UI، محصول قابل استفاده توسط کاربر نهایی نیست؛ 15 locale ناقص.

---

## 10. عملیات و استقرار

- **SQLite 3.49.1 < 3.51.3** — gate استقرار (D-16).
- **OTel tracing disabled** (no OTLP endpoint).
- **heavy torch/sentence-transformers** تحت xdist crash (KN-15).
- **monolith** (D-15: no microservice split without load evidence) — scaling نامشخص.
- **backup/restore drill** (D-17) شواهد اجرا ندارد.
- **WAL posture** fail-open روی SQLite buggy (SEC-10).
- **.env.example** تغییر یافته (در working tree) — بررسی نیاز.

---

## 11. اولویت‌بندی پیشنهادی (برای بستن کمبودها)

1. **P0 — رفع collection break:** حذف BOM از 13 فایل (به‌ویژه `database/hub.py`, `engine/tests/test_stage25_field_validation.py`) تا `pytest engine/` کامل جمع‌آوری شود. (کم‌هزینه، بالاسری بالا.)
2. **P0 — latent F821:** وارد کردن `DbOrderRepo`, `ComPaymentIntent`, `MarketplaceCommissionRule`, `UTC`, `np` در فایل‌های مربوطه یا حذف مسیرهای مرده. (ریسک مالی/علمی.)
3. **P1 — امنیت باقی‌مانده:** SEC-05 (authz روی cost/compute endpoints), SEC-06 (backup router guard یا حذف), SEC-13/16/17/23 (CSRF, enumeration, 2FA, password policy). Detox tests.
4. **P1 — کاهش ruff به baseline 769:** حداقل E501/E402/F401/F811/F821 و invalid-syntax PEP695. (مکانیکی، behaviour-preserving.)
5. **P2 — اعتبارسنجی مدل‌های موتور:** 55 مدل unvalidated → keep-and-plan/stub-only/remove + provenance روی هر payload (D-13).
6. **P2 — registry/مهاجرت:** ecocoin pair و village tables را یا به registry بیاورید یا صریحاً حذف کنید (KN-02, KN-12). Marketplace carts به DB.
7. **P2 — تست:** اضافه کردن تست به 39 دامنهٔ بدون تست (backup, legal, rangeland, mrv, privacy, provenance, ...).
8. **P3 — تصمیمات باز:** بستن D-04 (Eco Coin), D-07 (payment providers), D-15/16/17 (deploy/WAL/backup) قبل از release.
9. **P3 — فرانت‌اند:** تصمیم D-18 (React/Vite) یا ماندن API-only با OpenAPI به‌عنوان قرارداد.
10. **P4 — monolith hygiene:** شکستن `model_dispatcher.py` (2554→<800) و `main.py` assembly.

---

## 12. نتیجه‌گیری

پروژه **معماری و قراردادهای خوبی** (import guard, money=Decimal, Alembic guarded, honesty contract) دارد و بخش بزرگی از برنامهٔ اجرایی بسته شده است. اما **"وجود فایل = قابلیت"** هنوز در برخی نقاط (ecocoin router با hard-coded literals، nojin endpoints 500، dashboard fabricationهای باقی‌مانده، 55 مدل unvalidated، 39 دامنه بدون تست، collection break) نقض می‌شود. همچنین **بدهی کیفیت کد (ruff +370، BOM، invalid-syntax، F821 latent) و تصمیمات باز (13 تصمیم) و حذف فرانت‌اند** مانع ارائهٔ محصول قابل استفاده هستند. اولویت باید بر **رفع نقص‌های P0 (collection break + latent bugs) و بستن امنیت باقی‌مانده و اعتبارسنجی مدل‌ها** باشد، سپس کاهش بدهی lint و تصمیمات باز.

---

*این گزارش یک تحلیل وضعیت است، نه یک تغییر کد. هیچ فایل کدی تغییر نکرده است.*
