
# برنامه دقیق فازبندی توسعه HyDroMA (اکو نوژین)

**تاریخ:** ۲۰۲۶-۱۰-۲۱  
**مبنای:** وضعیت سنجش‌شده پروژه + PHASE_PLAN.md + KNOWN_ISSUES.md + گزارش تحلیلی  
**افق برنامه‌ریزی:** ۱۳ هفته (۹۱ روز)  
**قاعده بنیادین:** هر فاز فقط زمانی ورود می‌کند که gate ورودش سبز باشد. خود‌گزارش‌دهی completion درخواست است نه وضعیت.

---

## ۰. وضعیت فعلی فازها (خط‌مبنای ۲۰۲۶-۱۰-۲۱)

| فاز | وضعیت | درصد تکمیل |
|---|---|---|
| P0 record | ✅ بسته | ۱۰۰٪ |
| P1 honesty/quality | ✅ بسته | ۱۰۰٪ |
| P2 contracts | ✅ بسته | ۱۰۰٪ |
| P3 identity | ✅ بسته | ۱۰۰٪ |
| P4 data/migrations | ✅ بسته | ۱۰۰٪ |
| P5 money truth | ✅ بسته | ۱۰۰٪ |
| P6 marketplace | ✅ بسته | ۱۰۰٪ |
| P7 governance | ⚠️ بخشی | ~۷۰٪ |
| P8 tourism | ⚠️ بخشی | ~۶۵٪ |
| P9 compliance | ⚠️ بخشی | ~۶۰٪ |
| P10 engine maturity | ✅ بسته | ۱۰۰٪ |
| P11 daneshyar/decision | ⚠️ بخشی | ~۵۰٪ |
| P12 frontend | ❌ بازنشده | ۰٪ |
| P13 perf/offline | ⚠️ بخشی | ~۳۰٪ |
| P14 acceptance | ⚠️ بخشی | ~۴۰٪ |
| P15 release | ❌ باز | ۰٪ |

---

## ۱. فازبندی جدید — ۶ فاز اجرایی

فازهای بازنشده بر اساس اولویت‌بندی و وابستگی‌ها بازسازماندهی شده‌اند. هر فاز شامل:
- **مدت:** تخمین هفته
- ** gate ورود:** پیش‌نیازها
- **دامنه فایل:** محدوده مجاز تغییر
- **تسک‌ها:** کارهای مشخص با معیار پذیرش
- ** gate خروج:** شرط تکمیل
- **تحویل‌ها:** خروجی ملموس

---

## فاز A — تثبیت و رفع نقص‌های بحرانی (هفته ۱-۲)

**اولویت:** 🔴 P0 — بحرانی  
**مدت:** ۲ هفته  
** gate ورود:** وضعیت فعلی (همیشه آماده)

### دامنه فایل
- `engine/gateway/model_dispatcher.py` + فایل‌های dispatcher جدید
- `engine/hydroma/quantity.py`
- `engine/tests/test_architecture_rules.py`
- `services/_gateway_facade_adapters/`
- `tools/import_guard_policy.json`
- `architecture/dependency-graph.md`

### تسک‌ها

| # | تسک | معیار پذیرش | تلاس |
|---|---|---|---|
| A1 | **شکستن model_dispatcher.py** (۲۶۱۹→<۸۰۰ خط): استخراج domain dispatchers (hydrology, soil, climate, carbon, economics, groundwater) با registry pattern | هر فایل ≤۸۰۰ خط؛ `pytest engine/` سبز؛ `test_structure_ceilings` PASS | بالا |
| A2 | **ادغام pint در quantity.py**: جایگزینی stub با `pint.UnitRegistry` واقعی؛ تبدیل در Gateway | `quantity.py` از pint استفاده می‌کند؛ AR-06 رعایت شده؛ `pytest engine/strict_tests` سبز | متوسط |
| A3 | **رفع مسیر اسناد سخت‌کد**: `test_architecture_rules.py:34` → `docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md` | تست دیگر FileNotFoundError نمی‌دهد | کم |
| A4 | **بستن تخلف‌های import guard**: کوچ ۶ bypass در `_gateway_facade_adapters/` از طریق `EngineGateway` | `tools/detect_imports.py --root .` = ۰ | متوسط |
| A5 | **بازتولید dependency-graph**: `python tools/dependency_graph.py --out architecture/dependency-graph.md` + ratchet به ۱۴۰ | گراف به‌روز؛ `check_service_boundaries` PASS | کم |
| A6 | **ارتقای SQLite به 3.51.3**: بستن KN-09/D-16 — WAL ایمن | `sqlite_wal_deployment_safe()` = True | کم |

### gate خروج
```
✅ pytest engine/ -q -n 6        → 0 failed
✅ pytest engine/strict_tests -q → 0 failed
✅ tools/detect_imports.py       → 0 violations
✅ model_dispatcher.py           → ≤800 lines
✅ quantity.py                   → uses pint (not stub)
✅ sqlite_wal_deployment_safe()  → True
```

### تحویل‌ها
- ۶ domain dispatcher فایل جدید
- `quantity.py` مبتنی بر pint
- dependency-graph بازتولیدشده
- گزارش فاز A در `reports/PHASE-A-*.md`

---

## فاز B — تکمیل فازهای بخشی و بستن شکاف‌های امنیتی (هفته ۳-۵)

**اولویت:** 🟠 P1 — مهم  
**مدت:** ۳ هفته  
** gate ورود:** gate خروج فاز A سبز

### دامنه فایل
- `services/village/**` (P7 تکمیل)
- `services/tourism/**` (P8 تکمیل)
- `services/compliance/**` (P9 تکمیل)
- `services/knowledge/**`, `services/tasmimyar/**` (P11 تکمیل)
- `services/auth/**`, `services/api_gateway/middleware/**` (امنیت)
- `services/blockchain/**` (KN-02/KN-19 رفع)

### تسک‌ها

| # | تسک | معیار پذیرش | تلاس |
|---|---|---|---|
| B1 | **P7 تکمیل**: HTTP router حکمرانی روستایی + cross-village negative tests + legacy 18-table migration audit | workflow E2E سبز؛ cross-village tampering fail | بالا |
| B2 | **P8 تکمیل**: refund/incident entities (9-entity model) + capacity overbooking test + GSTC criteria doc | booking→payment→refund E2E سبز | متوسط |
| B3 | **P9 تکمیل**: pilot jurisdiction data seeds + expiry review workflow + no-verdict-without-assessment test | compliance workflow E2E سبز | متوسط |
| B4 | **P11 تکمیل**: learning-program flow + restoration MVP + RAG shard (KN-15) | courses/decision flows integration-tested | بالا |
| B5 | **SEC-05 بستن**: authz روی cost/compute endpoints (voice, mrv, science, sync) | هر endpoint بدون token → 401/403 | متوسط |
| B6 | **SEC-06 بستن**: backup router guard — authz + storage_path validation | unauthorized → 403; path traversal → 400 | متوسط |
| B7 | **SEC-13/16/17/19 بستن**: CSRF protection, enumeration guard, 2FA+TOTP, password policy | detox tests سبز | بالا |
| B8 | **KN-02/KN-19 رفع**: Ecocoin — یا ledger واقعی + migration یا hard-disable صادقانه | fabrication وجود ندارد؛ هر پاسخ honest است | متوسط |

### gate خروج
```
✅ pytest services/ -q -n 6      → 0 failed
✅ P7/P8/P9/P11                  → تمام workflow tests سبز
✅ SEC-05/06/13/16/17/19         → detox tests سبز
✅ KN-02/KN-19                   → بسته
✅ app.openapi()                 → boots
```

### تحویل‌ها
- ۴ فاز بخشی تکمیل‌شده (P7, P8, P9, P11)
- شکاف‌های امنیتی P1 بسته‌شده
- گزارش فاز B در `reports/PHASE-B-*.md`

---

## فاز C — اعتبارسنجی علمی و شاخص‌های نوین (هفته ۶-۸)

**اولویت:** 🟠 P1 — مهم (هسته ارزش‌آفرینی)  
**مدت:** ۳ هفته  
** gate ورود:** gate خروج فاز B سبز

### دامنه فایل
- `engine/hydroma/**` (اعتبارسنجی مدل‌ها)
- `engine/indicators/**` (شاخص‌های نوین)
- `engine/evidence/**`, `engine/knowledge/**` (provenance)
- `engine/strict_tests/**` (تست‌های اعتبارسنجی جدید)
- `tests/reference_data/**` (داده مرجع جدید)
- `data/mirror/` (ایجاد جدید)

### تسک‌ها

| # | تسک | معیار پذیرش | تلاس |
|---|---|---|---|
| C1 | **اعتبارسنجی ۱۰ مدل اولویت‌بالا**: van Genuchten (CANON-006), RothC کامل، SPI کامل, water_balance, water_productivity, runoff advanced, crop water, irrigation, salinity, NDVI/EVI — هرکدام با لنگر مرجع مستقل | S3 از ۱۸.۶٪ به ≥۲۵٪ (۱۷+/۷۰) | بسیار بالا |
| C2 | **پیاده‌سازی ۳ شاخص نوین**: FDII (Farm Diversification), CDHE (Crop Diversity), CMSI (Climate Margin) — هرکدام با تعریف چاپ‌شده + لنگر مرجع + strict test | ۳ شاخص با وضعیت IMPLEMENTED+TESTED | بالا |
| C3 | **ایجاد data/mirror/**: ساختار raw/processed/indices/model_runs/evidence/scenarios/decisions + CHIRPS/ERA5-land/SoilGrids ingestion pipeline (flag-gated) | E2E ingestion سبز؛ `data/mirror/` وجود دارد | بالا |
| C4 | **Provenance روی هر payload علمی**: model version + data version + assumptions + limits + uncertainty | هر نتیجه علمی provenance دارد | متوسط |
| C5 | **CANON-005 تکمیل**: Theis — مقدار مرجع چاپ‌شده در درخت + validation corpus | VALIDATED_EXTERNAL | کم |
| C6 | **Publication bar (D-13)**: فقط مدل‌های validated در مسیرهای user-facing منتشر می‌شوند | `publication_stamp` فعال؛ unvalidated → 503 | متوسط |

### gate خروج
```
✅ pytest engine/strict_tests -q  → 0 failed
✅ S3/total                       → ≥۲۵٪ (≥۱۷ validated)
✅ ۳ شاخص نوین                    → IMPLEMENTED+TESTED
✅ data/mirror/                   → وجود دارد + ingestion سبز
✅ provenance                     → روی هر scientific payload
✅ D-13                           → تصمیم بسته
```

### تحویل‌ها
- ۱۰ مدل جدید validated
- ۳ شاخص نوین پیاده‌شده
- `data/mirror/` با ingestion pipeline
- Provenance فعال روی همه payload‌ها
- گزارش فاز C در `reports/PHASE-C-*.md`

---

## فاز D — بهبود کیفیت و بستن تصمیمات باز (هفته ۹-۱۰)

**اولویت:** 🟡 P2 — مطلوب  
**مدت:** ۲ هفته  
** gate ورود:** gate خروج فاز C سبز

### دامنه فایل
- کل درخت (lint cleanup — behaviour-preserving)
- `database/models.py` (مهاجرت جداول خارج registry)
- `alembic/versions/` (مهاجرت‌های جدید)
- `services/api_gateway/main.py` (refactor assembly)
- `docs/project/OPEN_DECISIONS.md`

### تسک‌ها

| # | تسک | معیار پذیرش | تلاس |
|---|---|---|---|
| D1 | **کاهش ruff به baseline**: رفع E501 (line-too-long), F401 (unused import), F811 (redefined), F821 (undefined name) — behaviour-preserving | `ruff check .` ≤ ۷۶۹ | مکانیکی |
| D2 | **مهاجرت ecocoin به registry**: ecocoin_balances/transactions → ORM model + Alembic migration (یا حذف اگر D-04 = remove) | جداول خارج registry = ۰ (جز adapters) | متوسط |
| D3 | **مهاجرت village tables**: ~۱۸ جدول باقی‌مانده → guarded migration | `alembic upgrade head` سبز؛ single head | متوسط |
| D4 | **شکستن main.py assembly**: auto-registration router + plugin pattern (از ۱۱۷۸→<۴۰۰ خط) | `app.openapi()` = همان route count؛ boot سبز | متوسط |
| D5 | **بستن D-04** (Eco Coin): تصمیم نهایی — ledger واقعی یا حذف کامل | OPEN_DECISIONS: D-04 = closed | تصمیم |
| D6 | **بستن D-07** (payment providers): انتخاب و pin provider | OPEN_DECISIONS: D-07 = closed | تصمیم |
| D7 | **بستن D-15** (hosting): تصمیم استقرار — monolith vs microservice | OPEN_DECISIONS: D-15 = closed | تصمیم |
| D8 | **Named Enum parity** (KN-06): pre-pass برای تمام Enum ستون‌ها | SQLite/Postgres parity test سبز | متوسط |

### gate خروج
```
✅ ruff check .                   → ≤۷۶۹
✅ جداول خارج registry            → ۰ (جز adapters)
✅ alembic upgrade head --sql     → renders clean
✅ main.py                        → <۴۰۰ خط
✅ D-04, D-07, D-15               → closed
✅ pytest services/ engine/       → 0 failed
```

### تحویل‌ها
- بدهی lint کاهش‌یافته
- تمام جداول در registry
- `main.py` refactor شده
- ۳ تصمیم باز بسته‌شده
- گزارش فاز D در `reports/PHASE-D-*.md`

---

## فاز E — عملیات، پرفورمنس و پذیرش مستقل (هفته ۱۱-۱۲)

**اولویت:** 🟡 P2 — مطلوب  
**مدت:** ۲ هفته  
** gate ورود:** gate خروج فاز D سبز

### دامنه فایل
- `runtime/**` (supervisor بهبود)
- `tools/performance_baseline.py` (به‌روزرسانی)
- `tools/backup_restore_drill.py` (شواهد اجرا)
- تست‌های پذیرش (فقط خواندن — نه تغییر کد)
- `services/api_gateway/middleware/**` (caching, rate-limit tuning)

### تسک‌ها

| # | تسک | معیار پذیرش | تلاس |
|---|---|---|---|
| E1 | **P13 تکمیل**: API latency p95 per critical route + index review + top offenders fix | latency report با اعداد سنجش‌شده | متوسط |
| E2 | **Heavy compute isolation**: engine jobs از طریق worker queue (D-15 dependent) | request path ≠ compute path | بالا |
| E3 | **Offline sync (D-12)**: public content + drafts + server-authoritative sensitive ops + conflict semantics | offline queue tests سبز | بالا |
| E4 | **RAG shard در CI**: جدا کردن torch/sentence-transformers در job جداگانه | CI سبز؛ بدون xdist crash | کم |
| E5 | **Backup/restore drill با شواهد**: اجرای واقعی در staging + row-count verification | drill log در reports/ | متوسط |
| E6 | **P14 تکمیل — independent acceptance**: security sweep + money sweep + scientific sweep + legal sweep + detox | هر critical finding = severity+owner+fix phase | بالا |
| E7 | **OTel tracing فعال**: config-gated + OTLP endpoint + structured logs | traces در observability dashboard | متوسط |
| E8 | **Performance baseline refresh**: p50/p95/p99 per route با load test | `reports/performance-baseline-*.json` به‌روز | متوسط |

### gate خروج
```
✅ P13                            → تکمیل
✅ P14                            → acceptance report signed
✅ latency report                 → موجود با اعداد واقعی
✅ backup/restore drill           → شواهد اجرا
✅ RAG shard                      → CI سبز
✅ OTel                           → config-gated + فعال
```

### تحویل‌ها
- P13 و P14 تکمیل‌شده
- Performance baseline به‌روز
- Backup drill با شواهد
- OTel فعال
- گزارش فاز E در `reports/PHASE-E-*.md`

---

## فاز F — آماده‌سازی Release و فرانت‌اند MVP (هفته ۱۳)

**اولویت:** 🟢 P3 — بلندمدت  
**مدت:** ۱ هفته  
** gate ورود:** gate خروج فاز E سبز + D-15/D-16/D-17 closed

### دامنه فایل
- `frontend/` (ایجاد جدید — React/Vite)
- `tools/export_openapi.py` (بهبود)
- release tooling + runbooks
- `docs/project/**` (به‌روزرسانی)

### تسک‌ها

| # | تسک | معیار پذیرش | تلاس |
|---|---|---|---|
| F1 | **فرانت‌اند MVP (D-18)**: React + Vite + TypeScript + OpenAPI client generation + ۵ صفحه کلیدی (dashboard, marketplace, village, tourism, admin) | app boots؛ ۵ صفحه render؛ API contract drift gate در CI | بسیار بالا |
| F2 | **E2E journey tests**: ۵ golden path (browse→cart→order→payment→confirmation + village registration + tourism booking + carbon project + admin workflow) | هر journey سبز در CI | بالا |
| F3 | **Release runbook**: dev → CI → staging → E2E → migration dry-run → backup drill → limited pilot → monitoring → gradual rollout → post-release review | runbook مستند | متوسط |
| F4 | **Deployment version registry**: نسخه‌گذاری ساختاریافته + incident response + rollback procedure | version در هر deploy ثبت می‌شود | متوسط |
| F5 | **i18n اولیه**: ۳ locale (fa, en, ar) — RTL support | فرانت‌اند در ۳ زبان render می‌شود | متوسط |
| F6 | **P15 تکمیل**: تمام معیارهای release | MVP-1 آماده | تصمیم |

### gate خروج
```
✅ فرانت‌اند                      → boots + ۵ صفحه + API contract
✅ E2E journeys                   → ۵/۵ سبز
✅ release runbook                → مستند
✅ P15                            → تکمیل
✅ D-18                           → closed
✅ MVP-1                          → آماده release
```

### تحویل‌ها
- فرانت‌اند MVP
- E2E journey tests
- Release runbook
- MVP-1 آماده

---

## ۲. نمودار وابستگی فازها

```
فاز A (تثبیت)          هفته ۱-۲
    │
    ▼
فاز B (تکمیل + امنیت)  هفته ۳-۵
    │
    ▼
فاز C (اعتبارسنجی)      هفته ۶-۸    ← هسته ارزش‌آفرینی
    │
    ▼
فاز D (کیفیت + تصمیمات) هفته ۹-۱۰
    │
    ▼
فاز E (عملیات + پذیرش)  هفته ۱۱-۱۲
    │
    ▼
فاز F (Release + UI)    هفته ۱۳
```

**نکته:** فازها **سری** هستند زیرا هرکدام به خروجی قبلی وابسته‌اند. تنها استثنا:
- در فاز B، تسک‌های B1-B4 (تکمیل فازهای بخشی) می‌توانند **موازی** اجرا شوند (disjoint file trees)
- در فاز C، تسک‌های C1 و C2 می‌توانند **موازی** اجرا شوند (مدل‌ها ≠ شاخص‌ها)

---

## ۳. زمان‌بندی دقیق

| هفته | فاز | تسک‌های فعال | تحویل‌های کلیدی |
|---|---|---|---|
| ۱ | A | A1 (شکستن dispatcher), A2 (pint), A3 (مسیر اسناد) | dispatcher فایل‌های جدید |
| ۲ | A | A4 (import guard), A5 (dependency graph), A6 (SQLite) | gate A سبز |
| ۳ | B | B1 (P7 تکمیل) ∥ B2 (P8 تکمیل) ∥ B5 (SEC-05) | village/tourism router |
| ۴ | B | B3 (P9 تکمیل) ∥ B4 (P11 تکمیل) ∥ B6 (SEC-06) | compliance/knowledge |
| ۵ | B | B7 (SEC-13/16/17/19) ∥ B8 (KN-02/19) | امنیت کامل |
| ۶ | C | C1 (۱۰ مدل validated — دسته ۱: ۵ مدل) | ۵ مدل جدید S3 |
| ۷ | C | C1 (دسته ۲: ۵ مدل) ∥ C2 (۳ شاخص نوین) | S3 ≥ ۲۵٪ |
| ۸ | C | C3 (data/mirror) ∥ C4 (provenance) ∥ C5 (CANON-005) ∥ C6 (D-13) | mirror + provenance |
| ۹ | D | D1 (lint cleanup) ∥ D2 (ecocoin migration) ∥ D3 (village migration) | lint ≤ ۷۶۹ |
| ۱۰ | D | D4 (main.py refactor) ∥ D5-D7 (تصمیمات) ∥ D8 (Enum parity) | تصمیمات بسته |
| ۱۱ | E | E1 (latency) ∥ E2 (worker queue) ∥ E3 (offline) ∥ E4 (RAG shard) | P13 تکمیل |
| ۱۲ | E | E5 (backup drill) ∥ E6 (acceptance) ∥ E7 (OTel) ∥ E8 (perf baseline) | P14 تکمیل |
| ۱۳ | F | F1 (frontend) ∥ F2 (E2E) ∥ F3-F6 (release) | MVP-1 آماده |

---

## ۴. تخصیص منابع

| فاز | تعداد تسک | تلاس کل (نسبی) | ریسک | عامل بحرانی |
|---|---|---|---|---|
| A | ۶ | ۱۶ | متوسط | A1 (شکستن dispatcher) — اگر شکست، کل برنامه متوقف |
| B | ۸ | ۲۴ | بالا | B7 (امنیت) — ممکن است نیاز به redesign داشته باشد |
| C | ۶ | ۲۸ | بالا | C1 (اعتبارسنجی) — ممکن است مدل‌ها نیاز به بازنویسی داشته باشند |
| D | ۸ | ۱۸ | کم | D1 (lint) — مکانیکی اما حجم بالا |
| E | ۸ | ۲۲ | متوسط | E6 (acceptance) — ممکن است finding‌های جدید کشف کند |
| F | ۶ | ۲۴ | بالا | F1 (frontend) — بزرگترین تحویل |

---

## ۵. معیارهای پیشرفت (KPI)

| شاخص | خط‌مبنای امروز | هدف فاز A | هدف فاز C | هدف فاز F |
|---|---|---|---|---|
| S3/total (مدل‌های validated) | ۱۸.۶٪ | ۱۸.۶٪ | ≥۲۵٪ | ≥۳۰٪ |
| ruff findings | ~۸۱۵ | ~۸۱۵ | ~۸۱۵ | ≤۷۶۹ |
| تست‌ها | ~۶۵۷۲ | ~۶۶۰۰ | ~۶۸۰۰ | ~۷۰۰۰ |
| import guard violations | ۰ | ۰ | ۰ | ۰ |
| شکاف‌های امنیتی P1 | ۶ | ۶ | ۰ | ۰ |
| تصمیمات باز | ۱۳ | ۱۳ | ۱۰ | ≤۳ |
| شاخص‌های نوین پیاده | ۰ | ۰ | ۳ | ۵ |
| provenance coverage | partial | partial | کامل | کامل |
| فرانت‌اند | ❌ | ❌ | ❌ | ✅ MVP |

---

## ۶. ریسک‌ها و کاهش

| ریسک | احتمال | اثر | کاهش |
|---|---|---|---|
| شکستن dispatcher رفتار را تغییر دهد | متوسط | بالا | byte-identical public surface test قبل/بعد |
| اعتبارسنجی مدل‌ها نیاز به بازنویسی دارد | بالا | بالا | triage اولیه: keep/rewrite/remove |
| فرانت‌اند دیرتر از ۱ هفته | بالا | متوسط | MVP محدود به ۵ صفحه؛ OpenAPI contract اول |
| تصمیمات باز بسته نمی‌شوند | متوسط | بالا | fallback: تصمیم → defer با ریسک مستند |
| RAG shard در CI شکست بخورد | کم | متوسط | fallback: skip heavy tests در CI |
| امنیت redesign نیاز دارد | متوسط | بالا | فاز B بافر ۳ هفته‌ای دارد |

---

## ۷. تعریف Done (برای هر تسک)

تسک فقط زمانی done است که:
1. ✅ کد نوشته/تغییر شده و commit شده
2. ✅ تست‌های جدید نوشته شده و سبز هستند
3. ✅ تست‌های موجود هنوز سبز هستند (no regression)
4. ✅ gate خروج فاز سبز است
5. ✅ گزارش تحویل در `reports/` ثبت شده
6. ✅ مستندات به‌روز شده (`docs/project/*`, `AGENTS.md` اگر لازم)
7. ✅ lint/typecheck سبز
8. ✅ هیچ تستی حذف یا تضعیف نشده

---

*این برنامه توسط CodeGeeX AI بر اساس تحلیل عمیق وضعیت فعلی پروژه و مستندات برنامه‌ریزی موجود تهیه شده است.*
