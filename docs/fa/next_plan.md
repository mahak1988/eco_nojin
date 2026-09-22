# برنامه پیشرو — اقدامات بعدی اکو نوژین/هیدروما

> **تاریخ:** ۱۸ سپتامبر ۲۰۲۶
> **وضعیت:** P0 — کامل | P1 — کامل | P2 — در حال انجام

---

## وضعیت فعلی (به‌روز شده از ۱۸ سپتامبر ۲۰۲۶)

| حوزه | وضعیت | جزئیات |
|---|---|---|
| P0-1: چرخاندن سرکت‌ها | ✅ کامل | `settings.py:322-360` — اعتبارسنجی سکرت در startup |
| P0-2: خطاهای سینتکسی | ✅ کامل | BOM از `village_hub.py` حذف شد؛ همه فایل‌ها `py_compile` موفق |
| P0-3: ایمپورت تست خراب | ✅ کامل | `PROTECTED_PREFIXES` موجود در `idempotency.py:21-27` |
| P0-4: SQL Injection در Audit | ✅ بررسی شد | `ALLOWED_TABLES` چک می‌شود قبل از f-string در `audit.py:29-31` |
| P0-5: اعتبارسناجی سکرت در استارت | ✅ کامل | `@model_validator` در `settings.py` |
| P1-4: حذف localhost از SSRF | ✅ کامل | `localhost`/`127.0.0.1` از `ALLOWED_DOMAINS` حذف شد در `ssrf.py` |
| P2-1: مهاجرت print() به structlog | ✅ انجام شده | `bots/main.py`, `carbon/compliance/generate.py` — print()های محصول حذف شد |
| **تست‌ها** | ⚠️ ۲ fail | `test_list_profiles` (pre-existing isolation) + `test_confirm_payment` (pre-existing SQLite type) |
| **کل تست‌ها** | ۲۶۹ pass / ۲ fail | +۳۹ تست plant_neuro، +۲۲ تست finance (قبلاً شکست خورده)

---

## برنامه فاز P2 — بهینه‌سازی (۱ تا ۴ هفته)

### ✅ P2-1: مهاجرت `print()` به `structlog` — تکمیل شده

| فایل | وضعیت | جزئیات |
|---|---|---|
| `services/bots/main.py` | ✅ کامل | ۲ print() حذف شد؛ `import sys` حذف شد |
| `services/carbon/compliance/generate.py` | ✅ کامل | `print("init.py done")` → `logger.info(...)` |
| `services/ai/admin_assistant.py` | ✅ بررسی شد | هیچ print() در این فایل نیست |
| `services/bots/handlers/farm.py` | ✅ بررسی شد | هیچ print() در این فایل نیست |
| `engine/memory_monitor.py` | ✅ بررسی شد | print در docstring (خط ۱۵) — نه کد واقعی |

**نتیجه:** همه `print()`های محصول/سرویس در `services/` و `engine/` حذف شده‌اند

### P2-2: بهینه‌سازی عملکرد C++ هسته

| فایل | اقدام |
|---|---|
| `engine/cpp_core/` | پروفایل با `gprof`/`perf` |
| `engine/cpp_core/src/numerics/` | بررسی SIMD/parallelization برای runoff و physics |
| `engine/cpp_core/src/models/` | بهینه‌سازی HBV/SCS-CN برای batch processing |

**هدف:** ۲x سرعت محاسبات نسبت به Numba

### P2-3: بهینه‌سازی کش و Cache Hit Rate

| فایل | اقدام |
|---|---|
| `services/satellite/sentinel2_provider.py` | بررسی cache hit rate، افزودن cache warming برای bounding boxes متداول |
| `services/map_engine/orchestrator.py` | افزودن cache versioning برای bust کش هنگام تغییر پارامترها |
| `services/ai/rag.py` | بهینه‌سازی BM25 retrieval با caching برای_queries تکراری |

### ✅ P2-4: بهبود پوشش تست (Test Coverage) — تکمیل شده

| حوزه | قبل | بعد | اقدام |
|---|---|---|---|
| plant_neuro | ۰ | ۳۹ | تست‌های واحد جامع برای signals.py, voc.py, engine.py |
| commerce/idempotency | ۰ (broken) | ۱۸ | `PROTECTED_PREFIXES` و `FinIdempotencyKey` اضافه شد |
| finance | ۰ (broken) | ۲۲ | `DailyEarnings` model اضافه شد به `database/models.py` |
| **کل تست‌ها** | ۱۸ (قبل از P1) | ۲۶۹ pass | ۳۹ جدید plant_neuro + ۴۰ بازیابی شده |

### P2-5: مهاجرت `requirements.txt` به `pyproject.toml`/`uv`

| اقدام | جزئیات |
|---|---|
| `requirements.txt` | به `pyproject.toml` مهاجرت (در حال حاضر خالی) |
| `requirements-research.txt` | ادغام یا لایه‌بندی واضح |
| `.venv` sync | `uv sync` برای lockfile ثابت |

---

## برنامه فاز P3 — ویژگی‌های جدید (۴ تا ۸ هفته)

### ✅ P3-1: ماژول Plant Neuro — تکمیل شده

| زیرماژول | وضعیت |
|---|---|
| `signals.py` | ✅ کامل (12 تست) |
| `voc.py` | ✅ کامل (11 تست) |
| `engine.py` | ✅ کامل (16 تست) |
| **تست‌ها** | ✅ ۳۹ تست واحد — همه قبول |

**باقی‌مانده:**
- ⬜ `POST /api/v1/neuro/stress-analysis` اندپوینت در gateway
- ⬜ یکپارچگی با `services/satellite/sentinel2_provider.py` برای VOC از طریق spectral analysis

### P3-2: یکپارچگی Map Engine

| پایپ‌لاین | وضعیت |
|---|---|
| `TopographicPipeline (M-TOP)` | ✅ کامل |
| `RUSLEPipeline (M-ERS)` | ✅ کامل |
| `VegetationPipeline (M-VEG)` | ✅ کامل |
| `RunoffPipeline (M-RUN)` | ✅ کامل |
| `SlopeAspectPipeline (M-SLP)` | ✅ جدید (ایجاد شد) |

**باقی‌مانده:**
- ✅ M-SLP در orchestrator ثبت شد (به صورت try/except — قابل بهبود)
- ⬜ افزودن MapType.M_AGC (agrochemical), M_IRR (irrigation), M_CARB (carbon) به base.py

### ✅ P3-3: کامل کردن Design Engine

| سرویس | وضعیت |
|---|---|
| `irrigation_design_service.py` | ✅ Drip, Sprinkler, Furrow |
| `water_structure_design_service.py` | ✅ Check Dam, Contour Trench, Half Moon, Retention Pond |
| **API اندپوینت‌ها** | ⬜ `POST /api/v1/design/irrigation`, `/api/v1/design/structure` نیاز به افزودن به gateway

### P3-4: تکمیل سرویس‌های placeholder (W-004)

| سرویس | وضعیت |
|---|---|
| `services/auth` | ⚠️ بخشی کامل |
| `services/ledger` | ⚠️ ۱۶۴ خط — double-entry حلقه شواهد |
| `services/notification` | ⬜ placeholder |
| `services/reporting` | ⬜ placeholder |
| `services/workflow` | ⚠️ ۲۰۰+ خط — workflow main.py |

**اولویت:** auth → ledger → reporting → workflow → notification

---

## برنامه اجرایی — اقدامات بعدی (۷۲ ساعت آینده)

| # | وظیفه | اولویت | زمان تخمینی |
|---|---|---|---|
| 1 | نوشتن تست‌های واحد برای `plant_neuro/signals.py` | بالا | ۴ ساعت |
| 2 | نوشتن تست‌های واحد برای `plant_neuro/voc.py` | بالا | ۴ ساعت |
| 3 | نوشتن تست‌های واحد برای `plant_neuro/engine.py` | بالا | ۳ ساعت |
| 4 | مهاجرت `print()`ها به `structlog` در ۵ فایل باقی‌مانده | متوسط | ۲ ساعت |
| 5 | افزودن `MapType`های جدید به `base.py` | متوسط | ۲ ساعت |
| 6 | ثبت `SlopeAspectPipeline` مستقیم در orchestrator | پایین | ۲۵ دقیقه |
| 7 | بهینه‌سازی C++ core با پروفایل | کم | ۶ ساعت |
| 8 | افزودن `backend-test` job به CI | متوسط | ۱ ساعت |

---

## خلاصه

- **P0** کامل شد (همه موارد بررسی شد یا اصلاح شد)
- **P1** کامل شد (backend-only changes — plant_neuro, map_engine, design_engine)
- **P2** آماده — تمرکز بر تست‌ها، بهینه‌سازی، و structlog migration
- **P3** زیرساخت‌ها آماده‌اند — فقط تکمیل سرویس‌های placeholder و افزودن endpointهای API باقی مانده است
