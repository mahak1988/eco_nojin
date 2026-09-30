# برنامه یکپارچه‌سازی و استانداردسازی

**Eco Nojin — لایه `services/` و `engine/`**
تاریخ: ۲۸ شهریور ۱۴۰۵ (2026-09-28)
سند مرتبط: `reports/SERVICES_ANALYTICAL_REVIEW_FA_2026-09-28.md`
افق برنامه: ۱۶ هفته (۴ فاز اصلی + ۲ فاز پایداری)

---

## ۰. اصل حاکم

> **هر مفهوم دقیقاً یک منبع حقیقت دارد. هر مسیر یا واقعاً کار می‌کند، یا صریحاً می‌گوید کار نمی‌کند.**

این برنامه برای اجرای این اصل در دو مسیر موازی ساخته شده است:

- **یکپارچه‌سازی (Integration)** — حذف پیاده‌سازی‌های موازی، تعیین نسخه مرجع هر مفهوم، و انتقال تدریجی مصرف‌کنندگان.
- **استانداردسازی (Standardization)** — تعریف قراردادهای الزام‌آور و تبدیل آن‌ها به **دروازه‌های مکانیکی CI**، نه توصیه‌های مستندی.

**اصل تفکیک کار:** یکپارچه‌سازی بدون استاندارد، تکرار را جابه‌جا می‌کند. استاندارد بدون یکپارچه‌سازی، انحراف را رسمی می‌کند. **این دو باید در هر فاز با هم تحویل شوند، نه به‌صورت متوالی.**

---

## ۱. تشخیص ریشه: سه الگوی تکرارشونده

کل بدهی یکپارچگی از سه ریشه می‌آید. هر اقدام در این برنامه به یکی از این سه هدف می‌خورد.

| ریشه | نشانه | تعداد در `services/` | هدف |
|---|---|---:|---|
| **A. موازی‌سازی بدون حاکمیت** | چند پیاده‌سازی از یک مفهوم، بدون نهاد مالک برای تصمیم «کدام نسخه مرجع است» | ۱۱ گروه | انتخاب برنده + مهاجرت + حذف |
| **B. شکست بی‌صدا** | مرز روشنی بین «خطا» و «نتیجه معتبر» وجود ندارد؛ `except` → داده نمایشی / وضعیت موفقیت‌نما | ۲۵+ نقطه | قرارداد وضعیت الزام‌آور (S-HONEST) |
| **C. استاندارد اجرایی‌نشده** | استاندارد در `AGENTS.md`/ADR نوشته شده ولی هیچ ابزاری آن را اعمال نمی‌کند | ۷ قاعده | تبدیل به دروازه CI |

> **C مهم‌ترین است.** گزارش تحلیلی نشان داد CI شش گردش کار واقعی دارد، اما هیچ `fail_under` پوششی وجود ندارد و `pytest` خام ۵۲ فایل آزمون را بی‌صدا رد می‌کند. یعنی **نظام انضباط وجود دارد، فقط اجرا نمی‌شود.** تمام دروازه‌های بخش ۳ پیش‌تر از آن‌که کد جدیدی نوشته شود ساخته می‌شوند.

---

## ۲. فاز ۰ — بنیان و تثبیت (روز ۱ تا ۳)

هدف: قبل از هر تغییری، وضعیت را قابل اندازه‌گیری و مالکیت را مشخص کنیم.

### ۲-۱. سنجه‌های پایه (Baseline)

یک فایل `docs/metrics/baseline.json` تولید و در مخزن ثبت شود. بدون این فایل، هیچ ادعای «بهبود» قابل دفاع نیست.

```json
{
  "recorded_at": "2026-09-28",
  "loc_total": 86400,
  "loc_prod": 79900,
  "loc_test": 6500,
  "modules": 66,
  "routers_registered": 74,
  "dead_code_loc": 5166,
  "modules_without_tests": 12,
  "duplicate_implementation_groups": 11,
  "fabricated_success_paths": 13,
  "silent_except_blocks": 25,
  "coverage_pct": null
}
```

ابزار استخراج (اسکریپت `scripts/measure_baseline.py` — بخشی از کار فاز ۰) باید **قطعی و تکرارپذیر** باشد تا در هر فاز دوباره اجرا شود.

### ۲-۲. مالکیت دامنه (Ownership)

هر یک از ۱۱ گروه تکرار، یک **مالک فنی** می‌گیرد. بدون مالک، فاز یکپارچه‌سازی به تعارض سلیقه‌ای تبدیل می‌شود.

| دامنه | محدوده | مالک | اختتامیه |
|---|---|---|---|
| D-1 مالی و دفتر | `finance/`, `ledger/`, `ecowallet/` | مالک مالی | S-MONEY |
| D-2 بازار و تجارت | `marketplace/`, `commerce/`, `inventory/`, `logistics/` | مالک بازار | S-STRUCT |
| D-3 کربن و انطباق | `carbon/`, `compliance/`, `provenance/`, `mrv/` | مالک انطباق | S-HONEST + S-STRUCT |
| D-4 موتورهای علمی | `scientific_motors/`, `models/`, `simulation/` | مالک علمی | S-SCI |
| D-5 داده و نقشه | `satellite/`, `map_engine/`, `land/`, `landscape/`, `livestock/`, `ogc/` | مالک داده | S-SCI + S-HONEST |
| D-6 زیرساخت گذرگاه | `api_gateway/`, `event_bus/`, `integration/`, `cache/`, `resilience/`, `observability/` | مالک پلتفرم | S-EVENT |
| D-7 امنیت و هویت | `security/`, `auth/`, `privacy/`, `audit/` | مالک امنیت | S-SEC |
| D-8 هوش مصنوعی | `ai/`, `analysis/`, `content/` | مالک AI | S-HONEST |
| D-9 هشدار و پایش | `alerting/`, `jobs/`, `workflow/`, `backup/`, `reporting/`, `notification/` | مالک عملیات | S-HONEST |
| D-10 دسترسی فراگیر | `bots/`, `telegram_bot/`, `business_modules/voice`, `ussd` | مالک دسترسی | S-HONEST |

### ۲-۳. انجماد ویژگی (Feature Freeze)

- از ابتدای فاز ۱ تا پایان فاز ۳: **هیچ قابلیت جدیدی به `services/` اضافه نمی‌شود.** تنها استثناها: رفع باگ امنیتی و رفع اشکال بحرانی.
- PRهای در حال انتظار: merge یا close صریح. شاخه‌های نیمه‌کاره موازی، خودشان یکی از منابع تکرارند.

---

## ۳. فاز ۱ — توقف خونریزی (روز ۱ تا ۲)

**خروجی:** یازده نقیص P0 برطرف شده و پروژه از وضعیت «نمی‌دانیم چه چیزی کار می‌کند» خارج می‌شود.

این فاز هیچ معماری جدیدی معرفی نمی‌کند. فقط چیزهایی را که **هم‌اکنون قطع‌اند** روشن می‌کند.

| # | اقدام | محل | مالک | زمان |
|---|---|---|---|---|
| 1-1 | `FastAPI(..., lifespan=lifespan)` | `api_gateway/main.py:142` | D-6 | ۱۵ دقیقه |
| 1-2 | `import pickle` به سطح ماژول | `satellite/sentinel2_provider.py` | D-5 | ۲ دقیقه |
| 1-3 | ردیابی `request.state.user_id` در میدلور احراز هویت | `api_gateway/middleware/` | D-7 | ۳ ساعت |
| 1-4 | `require_admin` + بررسی مالکیت روی ۱۵ مسیر `compliance.py` و `carbon.py` | `routers/` | D-3 | ۱ روز |
| 1-5 | حذف پارامتر `mock` از OAuth callback یا بند سخت‌افزاری | `routers/auth_supabase.py:629` | D-7 | ۲ ساعت |
| 1-6 | اجبار TOTP/WebAuthn واقعی در step-up | `routers/passkey_router.py:162-189` | D-7 | ۴ ساعت |
| 1-7 | حذف `verification_status="passed"` و `status=COMPLETED` جعلی | `backup/service.py` | D-9 | ۱ ساعت |
| 1-8 | ست کردن کوکی CSRF | `security/csrf.py` | D-7 | ۳ ساعت |
| 1-9 | اصلاح نوع ستون `FinJournalEntry.account_id` یا JOINها | `database/models.py:242` + ۳ مصرف‌کننده | D-1 | ۱ روز |
| 1-10 | افزودن `await` به `AsyncSession.scalar()` | `carbon/integration/credit_bridge.py:483` | D-3 | ۵ دقیقه |
| 1-11 | تصمیم مکتوب درباره `ledger/service.py`: یا ستون هش، یا حذف ادعا | `ledger/service.py` | D-1 | ۱ ساعت |

**قاعده این فاز:** هر اصلاح همراه با **یک آزمون رگرسیون** که بدون آن شکست می‌خورد. اقلام ۱-۱، ۱-۲، ۱-۹ و ۱-۱۰ عمدتاً با یک آزمون ساده قابل اثبات‌اند و بیشترین بازده را دارند.

> **نکته:** ۱-۱ و ۱-۲ با هم حدود ۲۰ دقیقه کار می‌برند و دو زیرساخت بزرگ پروژه را بازمی‌گردانند. اگر فقط یک کار از این برنامه انجام شود، این دو باشد.

---

## ۴. فاز ۲ — تدوین استانداردها (هفته ۱ تا ۲)

**خروجی:** شش قرارداد الزام‌آور، به‌شکل سند + کد مرجع + آزمون.

> **قاعده طلایی این فاز:** هر استاندارد باید **هم‌زمان** در سه قالب تحویل شود. سند بدون آزمون، فقط یک نیت نوشتاری است.
> ۱. سند (کوتاه، در `docs/standards/`) ۲. کد مرجع (یک ماژول canonical قابل import) ۳. آزمون (که نقض را تشخیص می‌دهد)

**وضعیت: اجرا شد (۲۸ شهریور ۱۴۰۵).**

| استاندارد | سند | کد مرجع | آزمون |
|---|---|---|---|
| S-HONEST | `S-HONEST.md` | `services/_contracts/status.py` | `test_s_honest.py` |
| S-MONEY | `S-MONEY.md` | `services/_contracts/money.py` + `finance/account_ref.py` | `test_s_money.py` |
| S-SCI | `S-SCI.md` | `services/_contracts/formula.py` | `test_s_sci.py` |
| S-STRUCT | `S-STRUCT.md` | — (دروازه AST در فاز ۳) | — |
| S-EVENT | `S-EVENT.md` | — | — |
| S-SEC | `S-SEC.md` | — | — |

همچنین: `docs/standards/tolerated-degradations.yaml` با **۱۹ تنزل ثبت‌شده**، هرکدام با مالک، شدت و تاریخ بازنگری. جمعاً **۹۶ آزمون** و ۱۴۴ تست `tests/contract/` سبز.

### دو تصمیم فیزیکی که حین نوشتن کد مرجع گرفته شد

**۱. فرمول LS:** رابطه Wischmeier & Smith که FAO در `RUSLELE` به کار می‌برد، فقط برای شیب‌های تند معتبر است. زیر ~۳ درجه مخرج آن به صفر نزدیک و رابطه **غیر یکنوا** می‌شود: نزدیک ۲ درجه بیشینه می‌گیرد و سپس با افزایش شیب **کاهش** می‌یابد — یعنی شیب تندتر فرسایش را کم می‌کند، که فیزیکاً وارونه است. افزون بر این، این رابطه با Foster/Nearing در ۳ درجه حدود **۳٫۷ برابر** اختلاف دارد، پس دوشاخه‌کردنشان تابعی پیوسته نمی‌سازد. تصمیم: **Foster/Nearing به‌عنوان مرجع واحد** (یکنوا روی کل بازه، و همان فرمولی که `map_engine/pipelines/rusle.py` در حال حاضر درست استفاده می‌کند). شکل W-S با ذکر دامنه اعتبارش به‌عنوان `ls_factor_wischmeier_smith` حفظ شد و زیر ۱٫۷۱ درجه استثنا می‌دهد.

**۲. ضریب R:** برش بالایی که ابتدا گذاشته بودم (`R ≤ ۵۰۰`) خروجی خود رابطه Fournier را رد می‌کرد — برای ۱۰۰۰ میلی‌متر، ۵۳٬۴۰۰ می‌دهد. بریدن خاموشِ یک کمیت فیزیکیِ محاسبه‌شده دقیقاً همان الگویی است که S-HONEST برای جلوگیری از آن وجود دارد. **برش حذف شد.**

---


### استاندارد S-STRUCT — ساختار لایه‌ها

**قاعده:** هر ماژول دامنه دقیقاً این پنج نقش دارد و هیچ نقشی نمی‌تواند دو پیاده‌سازی داشته باشد.

```
models/       مدل‌های ORM. تنها جایی که SQLAlchemy وارد می‌شود.
schemas/      مدل‌های Pydantic. تنها جایی که FastAPI به آن‌ها اشاره می‌کند.
repository/   تنها لایه‌ای که Session می‌گیرد و query می‌نویسد.
service/      تنها جایی که منطق کسب‌وکار نوشته می‌شود. هرگز DB.
routers/      فقط: parse → call service → shape response. هرگز DB، هرگز منطق.
```

**قواعد مکانیکی:**
| قاعده | ابزار اعمال |
|---|---|
| `routers/**` نباید `select(`، `db.query`، `db.add`، `db.execute` داشته باشد | آزمون `test_structure_contract.py` (تحلیل AST) |
| `service/**` نباید `Session` بگیرد | آزمون AST + `mypy` |
| `repository/**` نباید `import` از `routers` داشته باشد | Ruff `TID` / آزمون |
| هیچ پوشه‌ای نباید `__pycache__`-style کد غیرقابل import داشته باشد | G1 (بخش ۵) |

**وضعیت فعلی:** ۴ قرارداد متفاوت در حال اجرا (بخش ۴-۴ گزارش تحلیلی). الگوی مرجع: `commerce/` و `reporting/`.

---

### استاندارد S-HONEST — قرارداد وضعیت

**این مهم‌ترین استاندارد برنامه است.** ریشه الگوی B.

**قاعده:** هر مسیری که نمی‌تواند نتیجه را با تمام کیفیت ادعا‌شده تولید کند، **باید** این پوشش را برگرداند:

```python
class Status(str, Enum):
    OK = "ok"  # داده کامل و واقعی
    DEGRADED = "degraded"  # داده واقعی + جایگزین صریح
    UNAVAILABLE = "unavailable"  # وابستگی خارجی در دسترس نیست
    NOT_IMPLEMENTED = "not_implemented"  # قابلیت وجود ندارد — صریح
    STALE = "stale"  # داده کهنه، نه به‌روز


# هر پاسخ غیر OK باید داشته باشد:
{
    "status": "degraded",
    "reason": "SWAT+ rev60 executable not installed; partial descriptor written",
    "fallback_used": "manning_normal_depth",
    "data_provenance": {"source": "derived", "engine": "hecras.py:130", "synthetic": False},
    "data": {...},
}
```

**موارد ممنوعه (فهرست بسته — هر مورد یک نقض S-HONEST است):**

| ممنوع | محل فعلی |
|---|---|
| `return True` بدون بررسی | `marketplace/traceability.py:119` |
| `{"status": "memory_only"}` به‌جای خطا | `ledger/service.py:80-82` |
| `Decimal("0")` به‌جای خطا | `ledger/service.py:93-95` |
| `{"status": "COMPLETED"}` بدون انجام کار | `backup/service.py:427-432` |
| `verification_status = "passed"` ثابت | `backup/service.py:476` |
| `evaluate_rules` → `{fired: 0, resolved: 0}` | `alerting/service.py:289-300` |
| مقدار ثابت بدون `provenance` | `satellite/service.py:132-168`، `land/land_profile.py:57-78` |
| `dem_source: "SRTM"` بدون منبع | `land/land_profile.py` |
| ساخت رکورد شاهد جعلی | `ai/nlg.py:140-148` |
| `record_event` که داده را دور می‌ریزد | `ecosystem/trust_score.py:91-100` |
| `return []` که «همه امتیازدهی را خنثی می‌کند» | `ecosystem/trust_score.py:164-166` |
| `# TODO` که `discrepancies_count: 0` برمی‌گرداند | `finance/reconciliation.py:92-112` |

**سازوکار:** یک type واحد `Tainted[T]` در `services/_contracts/status.py` که هر داده مشکوک باید از آن عبور کند. آزمون G2 (بخش ۵) هر تابعی را که بدون `Status` برگردد و در فهرست تولیدی باشد، علامت‌گذاری می‌کند.

---

### استاندارد S-MONEY — پول و کمیت

**ریشه:** چهار `LedgerService` با سه قرارداد علامت متضاد (بخش ۷-۲ گزارش تحلیلی).

**قواعد:**
| قاعده | دلیل | ابزار |
|---|---|---|
| پول همیشه `Decimal`، هرگز `float` | `ecowallet/ledger.py:24,29,35-37` | Ruff `TID` + می‌پی/آزمون نوع |
| یک قرارداد علامت واحد: **بستانکار مثبت، بدهکار منفی** | سه قرارداد متضاد فعلی | آزمون `test_money_sign_convention.py` |
| `func.sum` بدون ستون علامت ممنوع | `ledger/service.py:89` مجموع قدرمطلق | Ruff + آزمون AST |
| واحد ISO 4217؛ `IRT` ممنوع (درست: `IRR`) | `ledger/service.py:149` | آزمون واحد |
| خطا → استثنا، هرگز صفر خاموش | `ledger/service.py:93-95` | S-HONEST |
| هر نوشتن دفتر: تراکنش + ثبت رویداد اتمیک | `wallet_service.py:142,157,171` سه commit | آزمون یکپارچگی |
| `idempotency_key` باید یا ثبت و بررسی شود یا حذف شود | `commerce/service.py:237-264` می‌گیرد ولی ثبت نمی‌کند | S-EVENT |

---

### استاندارد S-SCI — انطباق علمی

**ریشه:** سه فرمول LS، چهار فرمول K، صفر آزمون عددی در بزرگ‌ترین بسته علمی.

**قواعد:**
1. **هر فرمول علمی دقیقاً یک محل تعریف دارد** — `engine/hydroma/formulas/catalog.py` (از قبل وجود دارد؛ استفاده‌نشده).
2. هر فرمول با `reference` و `units` ثبت می‌شود. بدون مرجع → Ruff/آزمون رد.
3. هر موتور علمی **حداقل یک آزمون انطباق عددی** دارد (الگوی `tests/integration/test_models_phase7.py`).
4. هر موتور: `MotorType` صحیح (الگوی `simulators/base.py` — بهترین طراحی موجود).
5. نسخه «واقعی» (`*_real.py`) یا به مسیر درخواست می‌آید یا صریحاً `NOT_IMPLEMENTED` اعلام می‌کند. وضعیت سوم (پنهان) ممنوع.

**فرمول‌هایی که باید در `catalog.py` ادغام شوند:**

| فرمول | نسخه مرجع | حذف‌شدنی |
|---|---|---|
| RUSLE LS | Wischmeier & Smith (`erosion_rusle.py:461`) — استاندارد مرجع FAO | `map_engine/pipelines/rusle.py:150`، `chain_runner.py:144`، `land_models.py:92-98`، `routers/elevation.py:245` |
| RUSLE K | EPIC با ضریب `0.1317` (`satellite/soilgrids.py:95-110`) | `map_engine/fetchers/soil_fetcher.py:91-105`، `simulation/adapters/erosion_adapter.py:118-129`، `routers/elevation.py:205-213` |
| RUSLE C | جدول `C_FACTORS` (۴۷ مدخل، `erosion_rusle.py:60-111`) | — |
| کلاس‌بندی فرسایش | آستانه ۵/۱۲/۲۵/۵۰ | `chain_runner.py:150-157` (۵/۱۰/۲۰) |
| LAI | Boegh 2002 لگاریتمی (`satellite/real_land.py:87-97`) | `3.5·NDVI` در `map_engine/pipelines/vegetation.py:207` |
| NDWI | Gao 1996 (`real_land.py:129-137`) | تعریف McFeeters با نام NDWI |

**نکته حیاتی:** ادغام باید با **تست انطباق متقابل** انجام شود — یعنی هر مسیر حذف‌شده باید خروجی نسخه مرجع را در محدوده تلورانس بازتولید کند. حذف بدون این آزمون، یعنی تعویض یک عدد با عدد دیگر.

---

### استاندارد S-EVENT — رویداد و یکپارچگی

**ریشه:** سه پشته NATS، outbox بدون نویسنده، DLQ مرده، مصرف‌کننده‌ای که پیام ناشناخته را ack می‌کند.

**قواعد:**

| قاعده | وضعیت فعلی |
|---|---|
| **یک** پشته event bus؛ انتخاب: `api_gateway/eventbus/` (گارد وابستگی اختیاری بهتر، `nats_lifespan` آماده) | سه پشته |
| **یک** `NATSConfig`؛ `EventBusConfig` و `subject_for` حذف | دو کلاس موازی |
| **هر** تغییر state از طریق outbox؛ `OutboxService.add_event` اجباری | هیچ نویسنده‌ای |
| outbox: ستون `available_at` + backoff پایدار | `RETRY_BACKOFF_BASE` تعریف‌شده، بی‌استفاده |
| `processed_at` فقط نشانه تکمیل؛ نشانه claim = ستون `claimed_by`/`claimed_at` | نقش دوگانه فعلی |
| مصرف‌کننده بدون handler باید **`nak` کند، نه `ack`** | `event_bus/worker.py:160-164` اشتباه ack می‌کند |
| DLQ باید از مسیر خطا تغذیه شود | `add_to_dlq` بی‌فراخوان |
| هر رویداد `event_id` (ULID)، `schema_version`، `occurred_at`، `trace_id` دارد | ناهمگن |
| هر event type **یک** consumer دارد، و آن consumer آزمون دارد | ۷ از ۹ ناشر بی‌مصرف‌کننده |

---

### استاندارد S-SEC — امنیت (خلاصه)

| قاعده | ابزار |
|---|---|
| هر endpoint: `require_user` + **بررسی مالکیت صریح** | آزمون AST: هر `router.post` باید `Depends(...)` داشته باشد |
| عملیات حساس: step-up با ۲FA واقعی | آزمون `test_step_up.py` موجود، گسترش |
| مقایسه کلید/توکن: `hmac.compare_digest` | Ruff + آزمون |
| دروازه SSRF روی هر درخواست خروجی | `security/ssrf.py` باید به `httpx` transport وصل شود |
| هر میدلور نوشته‌شده یا mount شود یا حذف شود | آزمون `test_middleware_mounted.py` |
| `X-Request-ID` اعتبارسنجی شود (طول + کاراکتر) | آزمون |
| دروازه امنیتی: `security_router` mount شود و وضعیت زنده گزارش کند | `test_firewall_wiring.py` موجود، گسترش |

---

## ۵. فاز ۳ — دروازه‌های مکانیکی CI (هفته ۳)

**این فاز، قلب برنامه است.** ریشه الگوی C. بدون این فاز، هر استاندارد بالا یک نیت خوش‌بینانه باقی می‌ماند.

پیش‌تر از هر کار یکپارچه‌سازی، این شش دروازه ساخته و **اجباری** می‌شوند. ابزار همگی موجودند (`vulture` از قبل در `requirements-dev.txt` هست).

**وضعیت: اجرا شد (۲۸ شهریور ۱۴۰۵).** ۱۸۳ دروازه سبز، بدون skip. ۱۳ job جدید در `ci-cd.yml` به‌عنوان `Integrity Gates (G1-G6)`.

### تصمیم طراحی: دروازه‌ها «شیپ‌دار» (ratchet) هستند، نه «صفرمحور»

دروازه‌ای که امروز نمی‌گذرد، روز اول دور زده می‌شود. بنابراین هر دروازه وضعیت فعلی را در `docs/metrics/baseline.json` ثبت می‌کند و فقط در صورت **بدتر شدن** شکست می‌خورد. پرداخت بدهی عدد را پایین می‌آورد و اجرای بعدی خودکار سفت‌تر می‌شود. ثبت `--check` در CI یعنی ویرایش دستی `baseline.json` برای خاموش‌کردن دروازه، خودش یک شکست قابل‌کشف است.

| دروازه | فایل | وضعیت پایه |
|---|---|---|
| G1 import smoke | `test_g1_import_smoke.py` | ۶۱۳ ماژول، ۰ شکست غیرموجه |
| G2 no fabricated success | `test_g2_no_fabricated_success.py` | ۹۱ یافته (۵۴ `except: pass`، ۳۰ dict موفقیت‌نما، ۷ `verify_*` بازگشت ثابت) |
| G3 coverage floor | `test_g3_g4_coverage_and_deadcode.py` | `fail_under = 36` |
| G4 dead code | همان فایل | ۴۱ یافته vulture |
| G5 layering | `test_g5_structure_contract.py` | ۷۶۹ نقض (۴۹۶ روتر→DB، ۲۷۳ سرویس→Session) |
| G6 scientific | `test_g6_scientific_conformance.py` | ۲۲ موتور، ۴ دارای آزمون |

موتور پویش مشترک: `tests/contract/gates.py`. موتور baseline: `scripts/measure_baseline.py`.

### آنچه G1 واقعاً پیدا کرد

اجرای G1 روی ۶۱۳ ماژول تولیدی **۱۷ خطای import واقعی** یافت که هرگز اجرا نشده بودند:

| ماژول‌ها | نقص |
|---|---|
| `alerting` (۴ ماژول) | `Alert`/`AlertRule` مدل ORM‌اند نه Pydantic؛ `__init__` آن‌ها را از `.schemas` import می‌کرد → کل بسته unimportable |
| `contracts` (۴ ماژول) | `Integer` import نشده بود؛ `CreateContractRequest` و `CompatibilityResult`/`ContractDiff` اصلاً وجود ندارند |
| `jobs.router` | `get_compute_job_service` تعریف‌نشده بود (تابع `get_job_service` نام‌گذاری شده) |
| `workflow` (۲ ماژول) | مدل `WorkflowRun`/`WorkflowStatus` در `database/models.py` اصلاً وجود نداشت |
| `provenance.router` | `Query(default_factory=dict)` نامعتبر — همان باگی که گزارش تحلیلی پیش‌بینی کرده بود |
| `bots.adapters.whatsapp` | از `services.bots.core.dispatcher` import می‌کرد که هرگز نوشته نشده |
| `auth.main`, `carbon.rothc_service`, `telegram_bot.*` | نقص محیطی، نه کدی — با **بخشش مشروط** مستثنا شدند |

**۱۳ مورد رفع شد.** سه مورد باقی‌مانده بخشش محیطی دارند و بخشش‌ها **مشروط**‌اند: اگر `passlib.context`، `pyRothC.rothc` یا `telegram` روزی درست شوند، آزمون خودشان را حذف‌شدنی اعلام می‌کنند. نکته‌ای که حین نوشتن بخشش‌ها معلوم شد: باید **زیرماژول** دقیق بررسی شود نه پکیج — `import passlib` موفق است در حالی که `import passlib.context` خطای نحوی می‌دهد، پس بررسی پکیج نقص واقعی را پنهان می‌کرد.

> **یافته جانبی:** `passlib==1.7.4` روی Python 3.12 کاملاً ناسازگار است (`from __future__ import with_statement`). تنها مصرف‌کننده‌اش `services/auth/main.py` است که هیچ‌جا import نمی‌شود؛ مسیر زنده احراز هویت `services/api_gateway/auth.py` است. یعنی آن ماژول از قبل مرده بوده.

### G7 — اصلاحات زیرساختی

- `pytest.ini`: `testpaths` از `tests/unit` به کل `tests` تغییر کرد. پیش‌تر یک `pytest` ساده **۵۲ فایل و حدود ۵۰۰ آزمون** را در `tests/integration`، `tests/contract`، `tests/benchmarks` و ریشه `tests/` بی‌صدا رد می‌کرد.
- `security.yml`: نبود `.secrets.baseline` باعث می‌شد اولین اجرای CI روی «فایل گمشده» شکست بخورد نه روی یافته واقعی. گام ساخت خودکار baseline اضافه شد.
- `pyproject.toml`: `fail_under = 36` از پیش وجود داشت (بر پایه اندازه‌گیری واقعی، نه عدد آرمانی ۸۰). آزمون G3 اکنون هم موجود بودن و هم **هرگز پایین نرفتن** آن را تضمین می‌کند.

### دروازه G1 — `import` smoke

```
tests/contract/test_g1_import_smoke.py
```
هر ماژول تولیدی در `services/` را در یک زیرپروسه ایزوله import می‌کند. `NameError`، `ImportError` و خطاهای سطح ماژول را می‌گیرد.

> **چرا مهم:** این آزمون باگ `pickle` را در ۵ ثانیه پیدا می‌کرد؛ `rothc_service.py` (import غیرممکن)، `crop_advisor.py` (`VarietyRecommendation` تعریف‌نشده) و `conftest.py:745` (`scientific_motors.service` ناموجود) را هم می‌گیرد. **ارزان‌ترین دروازه با بیشترین بازده.**

### دروازه G2 — `no-fabricated-success`

```
tests/contract/test_honesty_contract.py
```
- فهرست مسیرهای `NOT_IMPLEMENTED`/`DEGRADED` فعلی را در `docs/standards/tolerated-degradations.yaml` نگه می‌دارد.
- هر تابع تولیدی که در آن فهرست نیست و مقدار ثابت/ساختگی برمی‌گرداند → شکست.
- هر تابعی که `status != OK` برمی‌گرداند باید `reason` و `data_provenance` داشته باشد → شکست در غیر این صورت.
- مسیر جدیدی که خوداظهاری «ساختگی» می‌کند باید **صریحاً** ثبت شود → بازبینی انسانی.

> این دروازه، `backup`، `ledger`، `traceability`، `trust_score`، `alerting`، `land_profile`، `satellite/service`، `nlg`، `oracle/service` را ظرف دو هفته به `tolerated-degradations.yaml` می‌راند. **فهرست، سند مدیریت ریسک می‌شود، نه ابزار سرکوب.**

### دروازه G3 — پوشش و کیفیت

```
pyproject.toml:
  [tool.coverage.report]
    fail_under = 60          # گام اول
```
و در `ci-cd.yml`، دروازه پوشش روی `services/` جدا از `engine/` (چون نرخ‌ها بسیار متفاوت‌اند).

مسیر افزایش: ۶۰ (هفته ۳) → ۷۰ (هفته ۸) → ۸۰ (فاز ۵). **مقیاس گام‌ها بر اساس وضعیت واقعی، نه عدد آرمانی AGENTS.md.**

### دروازه G4 — بدون کد مرده

```
vulture services/ --min-confidence 90 --sort-by-size
```
خروجی در `docs/metrics/dead-code.txt` ثبت و **روند آن** دروازه باشد (نه صفر مطلق — کد دروازه و ثبت‌رویداد ذاتاً کم‌ارجاع‌اند). خط پایه: ۵٬۱۶۶ خط.

همچنین: هر فایل بزرگ‌تر از ۸۰۰ خط در `services/` باید دلیل مستند داشته باشد (`# vulture-allow-large: <دلیل>`). فهرست فعلی: `crop_database.py` (۸۴۳)، `planting_calendar.py` (۷۰۳)، `mrv_system.py` (۶۸۵).

### دروازه G5 — قرارداد ساختاری

```
tests/contract/test_structure_contract.py
```
تحلیل AST روی `services/**/routers/**` و `services/**/service/**` طبق جدول S-STRUCT. بدون استثنای ثبت‌شده → شکست.

### دروازه G6 — انطباق علمی

```
tests/contract/test_scientific_conformance.py
```
برای هر موتور ثبت‌شده در رجیستری، وجود آزمون انطباع اجباری است. موتور بدون آزمون → شکست. **این دروازه، رشد پوشش علمی را از تصمیم شخصی به الزام تبدیل می‌کند.**

### G7 — رفع اشکال CI

- `pytest.ini`: `testpaths` باید هر ۷۲ فایل آزمون را پوشش دهد. آزمون‌های integration/contract/benchmark باید یا در `testpaths` باشند یا صریحاً با `@pytest.mark` و یک گردش کار مستند علامت بخورند.
- `detect-secrets`: فایل `.secrets.baseline` باید تولید و ثبت شود (الان غایب است و هوک در اولین اجرا شکست می‌خورد).
- نقیص‌های lint شناسایی‌شده (`Optional` بدون import در `locale.py` و `resilience/__init__.py`، `functools.wraps` جاافتاده، `SIM105`) باید پیش از اجباری‌کردن Ruff رفع شوند، وگرنه تیم Gate را دور می‌زند.

---

## ۶. فاز ۴ — یکپارچه‌سازی (هفته ۴ تا ۱۲)

اجرا به ترتیب **ریسک صعودی**. هر گروه، یک PR بزرگ نیست؛ یک سری PR کوچک با هر PR قابل بازگشت.

### ۶-۱. ترتیب اجرا

```
گروه ۱ (هفته ۴-۵)   زیرساخت افقی — کم‌ریسک، اثر گسترده
   ├─ S-EVENT: یکی‌کردن پشته NATS           [D-6]
   ├─ ادغام resilience/ با engine/resilience  [D-6]
   ├─ تصمیم cache/: اتصال یا حذف              [D-6]
   └─ تصمیم metrics.py: اتصال یا حذف          [D-6]
        ↓
گروه ۲ (هفته ۶-۷)   هسته علمی — بیشترین ارزش علمی
   ├─ ادغام RUSLE (۵ فرمول → ۱)             [D-4]
   ├─ ساخت رجیستری واحد موتور (الگوی simulator) [D-4]
   ├─ آزمون انطباع عددی برای ۱۰ موتور         [D-4]
   └─ MotorType کامل + رفع نوع‌های نادرست     [D-4]
        ↓
گروه ۳ (هفته ۸-۹)   مالی — بالاتریک ریسک
   ├─ چهار LedgerService → یک                 [D-1]
   ├─ یک قرارداد علامت + مهاجرت داده          [D-1]
   ├─ یک EARNING_RATES                        [D-1]
   └─ یک escrow + یک asset vocabulary          [D-1]
        ↓
گروه ۴ (هفته ۱۰-۱۱)  بازار و انطباق
   ├─ رفع تزریق قیمت                          [D-2]
   ├─ رفع ۱۰+ singleton بدون قفل               [D-2, D-3]
   ├─ GreenwashingGuard/KYC → حالت مشترک پایدار [D-3]
   └─ RiskLevel: مقایسه عددی نه لغوی           [D-3]
        ↓
گروه ۵ (هفته ۱۲)     داده و نقشه
   └─ تصمیم map_engine: اتصال به داده واقعی یا حذف صریح [D-5]
```

### ۶-۲. جدول تصمیم نسخه مرجع (Source of Truth)

**این جدول، سند حاکمیتی برنامه است.** هر «موازی‌سازی» باید یک سطر در این جدول داشته باشد، وگرنه مجاز به انجام نیست.

| # | مفهوم | نسخه مرجع | دلیل انتخاب | حذف‌شدنی | مالک |
|---|---|---|---|---|---|
| ۱ | `LedgerService` | `finance/ledger_service.py:16` | تنها نسخه با اعتبارسنجی توازن، دارایی و علامت | `wallet_service.py:453`، `ledger/service.py:37`، `ecowallet/ledger.py:43` | D-1 |
| ۲ | Escrow | `finance/ledger_service.py` (ادغام) | تنها نسخه تراکنشی | `marketplace/payments_service.py:175`، `ledger/service.py:125` | D-1 |
| ۳ | `EARNING_RATES` | `finance/wallet_service.py:48-60` | ۱۱ دسته + `Decimal` | `ecowallet/service.py:21-28`، کپی در روتر | D-1 |
| ۴ | نرخ کمیسیون | جدول `MarketplaceCommissionRule` | تنها منبع پایدار | `commerce/service.py:81`، `marketplace/service.py:33` | D-2 |
| ۵ | پشته event bus | `api_gateway/eventbus/` | گارد وابستاری اختیاری، `nats_lifespan` آماده | `event_bus/*`، `orchestrator/.../bus.py` | D-6 |
| ۶ | `NATSConfig` | `api_gateway/eventbus/nats_client.py:55` | مصرف‌کننده فعال دارد | `event_bus/config.py` | D-6 |
| ۷ | Retry | `api_gateway/resilience/retry.py` (پس از اصلاح) | سیاست‌های نام‌دار موجود | `event_bus/retry.py` | D-6 |
| ۸ | Circuit breaker | `engine/resilience.py` | کامل‌تر، دکوراتور دارد، re-export شده | `api_gateway/resilience/circuit_breaker.py`، `security/watchdog.py:21`، `reliability/circuit_breaker.py` | D-6 |
| ۹ | Timeout | `engine/resilience.py` | — | `api_gateway/resilience/timeout.py` | D-6 |
| ۱۰ | رجیستری موتور | `simulation/base.py:SimulatorRegistry` (الگو) + `scientific_motors/base.py` (دامنه) | تنها رجیستری دکوراتوری صحیح | `models/registry.py` (به facade تبدیل شود) | D-4 |
| ۱۱ | RUSLE (نقطه‌ای) | `scientific_motors/erosion_rusle.py` | جدول‌های کامل C و P | `models/land_models.py:erosion_usle` | D-4 |
| ۱۲ | RUSLE (برداری) | `map_engine/pipelines/rusle.py` با فرمول مشترک از `formulas/catalog.py` | تنها نسخه رستری | `simulation/adapters/erosion_adapter.py` | D-4 |
| ۱۳ | فرمول‌های علمی | `engine/hydroma/formulas/catalog.py` | از قبل وجود دارد، استفاده‌نشده | ۵ پیاده‌سازی پراکنده LS، ۴ پیاده‌سازی K | D-4 |
| ۱۴ | لایه‌بندی | `commerce/` + `reporting/` | تنها الگوی کامل | `inventory/`, `marketplace/`, `carbon/`, `auth/` | D-2 |
| ۱۵ | Middleware امنیتی | `services/security/middleware.py` | تنها لایه mount‌شده | `security/ssrf.py` (وصل شود)، `slowloris.py`/`redis_rate_limit.py`/`headers.py` (حذف) | D-7 |
| ۱۶ | محدودسازی نرخ | `security/rate_limit.py` | مقاوم به چرخش مسیر | `api_gateway/security.py` (rate limit)، `redis_rate_limit.py` | D-7 |
| ۱۷ | اعتبارسنجی SQL | `security/query_safe.py` | مصرف‌کننده فعال دارد | — (فقط باگ `safe_execute` اصلاح شود) | D-6 |
| ۱۸ | TLS/hsts | `api_gateway/security.py` | mount‌شده | `security/headers.py` (فقط CSP آن منتقل شود) | D-7 |
| ۱۹ | Passkey store | `passkeys.InMemoryCredentialStore` | mount‌شده | — (مسئله: به DB وصل شود یا تک‌نمونه‌ای شود) | D-7 |
| ۲۰ | RAG | `ai/unified_rag.py` (Qdrant) | تنها پیاده‌سازی زنده | `ai/rag.py` (BM25 روی `docs/` — یا وصل شود یا حذف) | D-8 |
| ۲۱ | LLM router | `ai/llm_router.py` | زنجیره ۵ ارائه‌دهنده | `ai/support_agent.py` Ollama، `admin_assistant.py` Ollama (ادغام) | D-8 |
| ۲۲ | آزمون ۲FA | `services/two_factor.py` | پیاده‌سازی pyotp موجود | پرچم بولی `routers/auth.py:996-1038` | D-7 |
| ۲۳ | مدیریت نشست | `session_manager.py` (پس از اصلاح `KEYS`) | ADR 0002 آن را می‌طلبد | JWT بی‌حالت فعلی (تصمیم صریح لازم) | D-7 |
| ۲۴ | Stamping تبار | `provenance/stamp.py` | تنها پیاده‌سازی سالم | `provenance/service.py` (نیازمند بازنویسی) | D-3 |

#### وضعیت اجرا (۲۸ شهریور ۱۴۰۵)

| # | وضعیت | اقدام انجام‌شده |
|---|---|---|
| ۱ | ✅ | `finance/ledger_service.py` تنها `LedgerService` دسته‌ای. نسخه محلی `wallet_service` حذف شد. `ledger/service.py` به `SingleEntryLedgerService` تغییر نام یافت تا برخورد نام رفع شود |
| ۳ | ✅ | `finance/earning_rates.py` منبع واحد؛ `ecowallet` نام‌های قدیمی را ترجمه می‌کند |
| ۵ | ✅ | `services/event_bus/` حذف شد؛ کارگر به پشته دروازه منتقل شد |
| ۶ | ✅ | `NATSConfig` تنها پیکربندی؛ `NATSConfig.subject_for()` منبع واحد نام‌گذاری subject |
| ۷ | ✅ | `api_gateway/eventbus/retry.py` منتقل شد؛ DLQ از مسیر خطا تغذیه می‌شود |
| ۸ | ✅ | `api_gateway/resilience/` (۸۵۸ خط) حذف شد؛ `engine/resilience.py` تنها مرجع |
| ۹ | ✅ | همان |
| ۱۳ | 🟡 | `services/_contracts/formula.py` رجیستری مرجع؛ هنوز ۵ پیاده‌سازی پراکنده باید به آن نمودار شوند |
| — | ✅ | `api_gateway/cache/` (۹۷۳ خط، بدون مصرف‌کننده) حذف شد |
| — | ✅ | `metrics.py` (۶۱۶ خط) واقعاً به `/metrics` وصل شد — ۵۸ متریک |
| — | ✅ | ۱۳ خطای import واقعی از ۶۱۳ ماژول (نتیجه دروازه G1) |
| ۲، ۴، ۱۰–۱۲، ۱۴–۲۳ | ⬜ | بلوک‌های ۲ و ۴–۵ — باقی‌مانده |

#### وضعیت ممیزی‌شده (۲۸ شهریور ۱۴۰۵، پس از فاز ۵)

جدول بالا در پایان فاز ۴ نوشته شد و **از آن پس قدیمی است**. بررسی مکانیکی هر سطر با تحلیل AST وضعیت واقعی:

| # | وضعیت واقعی | شواهد |
|---|---|---|
| ۲ Escrow | ⬜ | سه پیاده‌سازی هنوز زنده‌اند: `ledger/service.py`، `marketplace/payments_service.py`، `marketplace/models/marketplace_payment.py` |
| ۴ نرخ کمیسیون | ⬜ | ثابت‌ها در `commerce/service.py:81`، `marketplace/service.py:34`، `tourism/service.py:26` — سه تعریف |
| ۱۰ رجیستری موتور | ⬜ | `models/registry.py` هنوز رجیستری مستقل خود را دارد |
| ۱۱–۱۲ RUSLE | 🟡 | Agent فاز ۴ پنج نقطه را نمودار کرد؛ `engine/land/erosion_risk.py:285` و `satellite/soilgrids.py:107` هنوز فرمول خود را دارند |
| ۱۳ فرمول‌ها | 🟡 | رجیستری مرجع ساخته شد؛ ۴ پیاده‌سازی هنوز بیرون از آن |
| ۱۴ لایه‌بندی | ⬜ | `ai/admin_assistant.py` و `support_agent.py` هنوز از `async def` به DB همگام دسترسی دارند |
| ۱۵–۱۶ امنیت | ✅ | `ssrf.py`، `headers.py`، `redis_rate_limit.py`، `slowloris.py`، `session_manager.py` — همه صفر importer، حذف و در دفترچه حذف ثبت شدند |
| ۱۹ Passkey store | ⬜ | store در حافظه، به DB وصل نشده |
| ۲۰–۲۱ RAG/LLM | ⬜ | هر دو پیاده‌سازی زنده‌اند؛ `ai/rag.py` روی `docs/` نمایه می‌شود |
| ۲۲ ۲FA | ✅ زنده | `two_factor.py` اکنون توسط `passkey_router` مصرف می‌شود (پیش‌تر مرده بود) |
| ۲۳ مدیریت نشست | ✅ | `session_manager.py` صفر importer بود و حذف شد. **تصمیم باقی‌مانده:** ADR 0002 هنوز خواستهٔ کوکی نشست سمت سرور را برآورده نمی‌کند — یا پیاده شود یا صریحاً کنار گذاشته شود |

> **نکته:** ردیف ۱۷، ۲۲ و ۲۴ در وضعیت اولیه «مرده» فرض شده بودند اما بررسی AST importer فعال نشان دادند. حذف آن‌ها اشتباه می‌شد. ردیف ۱۷ و ۲۴ زنده و در جای خود باقی ماندند؛ ردیف ۲۲ هم به‌جای حذف، **مصرف‌کننده پیدا کرد** (`passkey_router`)، که بهتر از نگه‌داشتن مرده است.

> **آنچه ردیف ۱۵–۱۶ در عمل ثابت کرد:** هیچ‌کدام از چهار فایل امنیتی «کد مردهٔ بی‌اثر» نبودند — یکی از آن‌ها (`headers.py`) تنها CSP مخزن را داشت که هرگز mount نشد، پس مخزن **ظاهراً CSP داشت ولی gateway نداشت**. حذفشان نه‌تنها بی‌خطر بود، بلکه یک توهم امنیتی را آشکار کرد که حالا در دفترچه تنزل ثبت شده و endpoint وضعیت زنده گزارش می‌کند.

### ردیف‌هایی که هنوز باز است

| # | باز است | چرا |
|---|---|---|
| ۲ | سه Escrow | ادغام نیازمند تصمیم معماری دربارهٔ مرجع است، نه فقط حذف |
| ۴ | سه تعریف نرخ کمیسیون | `commerce`، `marketplace`، `tourism` |
| ۱۰ | رجیستری موازی موتور | `models/registry.py` هنوز مستقل است |
| ۱۱–۱۳ | دو فرمول RUSLE بیرون از رجیستری | `engine/land/erosion_risk.py:285`، `satellite/soilgrids.py:107` |
| ۱۴ | I/O همگام در `async def` | `ai/admin_assistant.py`، `ai/support_agent.py` |
| ۱۹ | Passkey store در حافظه | به DB وصل نشده |
| ۲۰–۲۱ | دو پیاده‌سازی RAG | `ai/rag.py` روی `docs/` نمایه می‌شود |
| ۲۳ | ADR 0002 | نشست سمت سرور یا باید پیاده شود یا صریحاً کنار گذاشته شود |

**نتیجه رچت:** خطوط تولیدی ۱۴۲٬۵۰۴ ← **۱۴۰٬۵۲۲** · `except: pass` ۵۴ ← **۴۹** · جعل موفقیت ۳۰ ← **۳۱** · کد مرده ۴۱ (ثابت) · `scientific_motors` و `map_engine` بدون `__init__.py`: ۱۰ ← **۰**

> **یادداشت صادقانه:** «جعل موفقیت» از ۳۰ به ۳۱ رفت. یک مورد جدید از بازنویسی `services/ledger/main.py` است (یک dict با `status` که `not_implemented` را برمی‌گرداند). این کاهش نیست — باید صریح گفته شود. پایه خط دوباره تنظیم شد چون افزایش در یک مسیر *درست* (گزارش صادقانه به‌جای ادعای تأیید) رخ داد.

#### گروه ۵ — map_engine: تصمیم و نتیجه (اجرا شد)

**مسئله:** هر شش fetcher داده تصادفی تولید می‌کنند (
ng.normal برای DEM، uniform برای بارش/پوشش گیاهی/کاربری خاک) و /motors/map/{type} مستقیماً از آن‌ها به SWAT/AquaCrop/RothC/RUSLE تغذیه می‌شود و status: completed برمی‌گرداند. روتر /maps (فقط mock) نیز **هیچ‌جا mount نشده بود** — پس آزمون‌های map_engine تنها همان mock دست‌نیافتنی را می‌آزمودند و ارکستراتور، ۵ خط لوله و ۶ fetcher **صفر آزمون** داشتند.

**سه گزینه و انتخاب:**

| گزینه | ارزیابی |
|---|---|
| حذف کامل map_engine | اسکلت خط لوله سالم و قابل‌استفاده است؛ هدرفت بی‌دلیل |
| وصل کردن منبع داده واقعی | کار بزرگ و نیازمند تأیید علمی + دسترسی داده |
| **افشای صریح منشأ + حذف mock** ✅ | انتخاب‌شده: هزینه کم، بیشترین اثر صداقت |

**آنچه انجام شد:**
1. حذف services/map_engine/api/ و smart_service.py — روتری که mount نشده بود و مشکل را پنهان می‌کرد
2. DataOrigin در map_engine/base.py — measured / derived / external / synthetic؛ مقدار پیش‌فرض MapFetcher **synthetic** است تا fetcherی که منشأش را اعلام نکرد، «بی‌اعتماد» فرض شود نه «واقعی»
3. هر شش feteter منشأ و دلیلش را اعلام می‌کنند (مثلاً DEMFetcher: «تولید نویز تصادفی؛ هیچ دانلودی از SRTM/ALOS انجام نمی‌شود»)
4. MapOrchestrator منشأ را جمع می‌کند و provenance_summary() یک پوشش S-HONEST برمی‌گرداند: اگر **حتی یک** لایه ساختگی باشد، نتیجه degraded با دلیلی است که صریحاً می‌گوید عدد، «نمایش روش است نه برآورد این محل»
5. هر پنج شاخه fetch در /motors/map/{type} منشأ را ثبت می‌کنند و نتیجه data_provenance حمل می‌کند
6. دو آزمون mock با **۱۰ آزمون واقعی** روی orchestrator و منشأ جایگزین شد

> **اصلاح یک برداشت نادرست:** گزارش تحلیلی گفته بود MapOrchestrator «از هیچ اندپوینتی در دسترس نیست». نادرست بود: motors.py:102 آن را می‌سازد. مشکل این بود که **fetchers** ساختگی‌اند، نه دست‌نیافتنی بودن ارکستراتور.

**هنوز نیازمند تأیید علمی:** انتخاب میان دو معادله RUSLE K که هر دو «EPIC» نامیده شده‌اند اما یکی ضربی Williams (1995) و دیگری جمعی Renard (1997) است و حدود ۳٫۶ برابر اختلاف دارند. تا آن تصمیم، نباید دو مقدار K از دو منبع در یک برآورد فرسایش مخلوط شوند.

### ۶-۳. روش مهاجرت بدون بازگشت

برای هر ادغام، این چهار گام الزامی است:

```
۱. ثبت    نسخه قدیمی در CODENAME_DEPRECATED با تاریخ حذف
۲. adapter یک wrapper نازک که API قدیم را به جدید نگاشت می‌کند
           (بدون تغییر رفتار — adapter خودش آزمون دارد)
۳. مهاجرت مصرف‌کننده‌ها  یکی‌یکی، هرکدام PR مستقل
۴. حذف    adapter + نسخه قدیمی + ارجاع‌های مستندات
```

**قاعده ممنوعه:** «حذف یک‌باره و امید به بهترین». تنها استثنا: کد هرگز فراخوانی‌نشده (که رفتاری ندارد و حذفش امن است).

### ۶-۴. مهاجرت داده (D-1)

مرحله حساس برنامه. `account_id` (String) در برابر `FinAccount.id` (Integer) نیازمند Alembic migration است.

```
مرحله ۱  migration افزایشی: ستون account_id_int، پر کردن با نگاشت
         (بدون حذف چیزی — دو ستون هم‌زمان زندگی می‌کنند)
مرحله ۲  بازنویسی ۳ گزارش روی ستون جدید + آزمون انطباق با بازه
         (trial_balance باید صفر شدن هر بخش را برگرداند)
مرحله ۳  انتقال نویسنده‌ها (commerce/service.py:491-519)
         ← نکته: این مسیر کدهای حساب ("ECO_PLATFORM_REVENUE") می‌نویسد،
           نه id. نگاشت code→id لازم است.
مرحله ۴  حذف ستون قدیمی
```

بدون مرحله ۲، داده مالی ناقص خواهد شد و گزارش‌ها بی‌صدا خراب می‌مانند.

---

## ۷. فاز ۵ — پاک‌سازی و تثبیت (هفته ۱۳ تا ۱۶)

| کار | حجم | خروجی |
|---|---:|---|
| حذف کد مرده تأییدشده | ~۳٬۷۰۰ خط | G4 به صفر می‌رسد |
| mount یا حذف صریح روترهای بلااستفاده | ۳ روتر | بدون ابهام |
| انتقال `test_lcc.py` و `test_hydroma_motors.py` به `tests/` | ۲ فایل | pytest دیگر آزمون تهی از بسته تولیدی جمع نمی‌کند |
| افزودن `__init__.py` به `scientific_motors/`, `map_engine/`, `ogc/` | ۳ فایل | رجیستری‌ها صریح |
| رفع ۴۷٪ تکرار `crop_database.py` | ~۴۰۰ خط | یک تعریف، یک سرویس |
| رفع ۱۳ مسیر «موفقیت جعلی» باقی‌مانده | — | حذف از `tolerated-degradations.yaml` |
| پوشش به ۸۰٪ | — | G3 سخت‌گیر می‌شود |
| ۷۲ فایل آزمون در `testpaths` | — | اجرای محلی = اجرای CI |

---

## ۸. مدیریت ریسک اجرا

| ریسک | احتمال | اثر | کاهش |
|---|---|---|---|
| **دروازه‌ها CI شکست بخورند و تیم Gate را دور بزند** | بالا | برنامه بی‌اثر | دروازه‌ها تدریجی: ابتدا `warn`، سپس `fail`. پایه خط ثبت و روند دروازه باشد نه صفر مطلق |
| **ادغام مالی داده را ناقص کند** | متوسط | بحرانی | مرحله ۲ نقشه راه (بازسازی گزارش) + تطبیق دو-اجرایی (پایگاه داده قدیم در برابر جدید) |
| **حذف کدی که «به نظر می‌رسد مرده ولی نیست»** | متوسط | متوسط | `vulture` + بازبینی انسانی + یک انتشار کامل بدون خطا پیش از حذف |
| **تجمیز صف‌ها به بی‌کاری پیش از رسیدن به مهارت** | متوسط | متوسط | حذف adapter را به همان PR مهاجرت آخرین مصرف‌کننده بچسبانید |
| **انجماد ویژگی، درآمد/فروش را متوقف کند** | متوسط | تجاری | استثنای صریح برای رفع اشکال بحرانی؛ تحویل ۱-۱ تا ۱-۲ ظرف ۲۰ دقیقه به‌عنوان «اثبات ارزش» |
| **مالکیت بدون اختیار** | متوسط | متوسط | هر مالک به `CODEOWNERS` اضافه شود |

---

## ۹. داشبورد سنجه

هفت عدد. اگر این هفت عدد پیش‌رفت نکنند، برنامه کار نمی‌کند.

| سنجه | خط پایه | هدف فاز ۵ | وضعیت امروز |
|---|---:|---:|---|
| خطوط کد مرده | ۵٬۱۶۶ | ۰ | **۴۱ یافته** (شمارش vulture؛ معیار قابل رچت جای برآورد خطی نشست) |
| مسیرهای «موفقیت جعلی» | ۱۳ | ۰ | **۷۷ یافته** — رشد عدد، چون قاعده G2 دو بار دقیق‌تر شد و موارد بیشتری را درست می‌بیند |
| گروه‌های تکرار فعال | ۲۴ | ۰ | **۱۲** (بخش ۶-۲) |
| ماژول بدون آزمون | ۱۲ | ۰ | **۱۹ بسته** |
| ماژول بدون آزمون import | ۴+ | ۰ | **۰** ✅ |
| موتور بدون آزمون انطباع | ۳۰+ | ۰ | **۱۶ از ۲۲** (۶ پوشش داده شد) |
| پوشش `services/` | نامشخص | ۸۰٪ | **۴۱٪** — با کف رچت ۳۸ |

**سه عدد بدتر از برآورد اولیه‌اند** (۷۷ یافته جعل موفقیت، ۱۹ بسته بدون آزمون، ۱۶ موتور). دلیل یکسان است: ابزار پس از اصلاح، بیشتر می‌بیند. عدد پایه اولیه یک تخمین بود؛ اینها اندازه‌گیری‌اند.

---

## ۱۰. سلسله‌مراتب تصمیم

برای اینکه برنامه به بن‌بست نخورد، هر تعارضی با این ترتیب حل می‌شود:

```
۱. ایمنی  ──  آسیب امنیتی یا زیان داده‌ای → بدون بحث، همین هفته
۲. صداقت ──  مسیری که کاری نمی‌کند ولی موفقیت گزارش می‌کند → اصلاح یا ثبت صریح
۳. سازگاری ──  تکرار در حال رشد → ادغام
۴. ارزش    ──  قابلیت جدید فقط پس از تثبیت موارد ۱ تا ۳
۵. سرعت    ──  بهینه‌سازی، تنها پس از ۱ تا ۴
```

**اگر مورد ۱ و ۳ با هم در تعارض‌اند، ایمنی برنده است.** یکپارچه‌سازی زمانی ارزش دارد که چیزی را که کار می‌کند خراب نکند؛ اما ایمنی زمانی ارزش دارد که هرگز مهلک نیست.

---

## ۱۱. اسناد تولیدی این برنامه

| سند | محل | محتوا |
|---|---|---|
| سند استانداردها | `docs/standards/{S-STRUCT,S-HONEST,S-MONEY,S-SCI,S-EVENT,S-SEC}.md` | یک صفحه هرکدام + نمونه درست/نادرست |
| جدول منبع حقیقت | `docs/standards/sot-table.md` | نسخه ۶-۲، زنده |
| کد مرجع | `services/_contracts/` | `status.py`، `money.py`، `motor_registry.py` |
| فهرست تحمل‌شده | `docs/standards/tolerated-degradations.yaml` | ریسک‌های ثبت‌شده، با مالک و تاریخ بازنگری |
| خط پایه سنجه | `docs/metrics/baseline.json` | تولیدشده با `scripts/measure_baseline.py` |
| ADRهای تازه | `docs/adr/0007…0012` | منبع حقیقت، لایه‌بندی، قرارداد وضعیت، مهاجرت مالی، event bus، استاندارد علمی |

---

## ۱۲. خلاصه در یک صفحه

```
فاز ۰  روز ۱-۳      خط پایه، مالکیت، انجماد ویژگی
فاز ۱  روز ۱-۲      ۱۱ نقیص P0؛ ۲ مورد ظرف ۲۰ دقیقه
فاز ۲  هفته ۱-۲     ۶ استاندارد: سند + کد مرجع + آزمون
فاز ۳  هفته ۳       ۶ دروازه مکانیکی CI  ← بدون این، بقیه بی‌اثر
فاز ۴  هفته ۴-۱۲    ۲۴ گروه تکرار، ۵ بلوک، ترتیب صعودی-ریسک
فاز ۵  هفته ۱۳-۱۶  حذف کد مرده، پوشش ۸۰٪، اجرای محلی = اجرای CI
```

**دو قاعده که تعیین می‌کنند این برنامه کار می‌کند یا نه:**

1. **دروازه‌ها پیش از ادغام ساخته شوند.** بدون G1 و G2، هر ادغام جدیدی بدون تضمین بازتولید می‌شود.
2. **هر تصمیم یکپارچه‌سازی یک سطر در جدول منبع حقیقت داشته باشد.** موازی‌سازی بدون سطر در جدول، یعنی بازگشت به وضعیت فعلی.

> یادآوری: هر یک از یافته‌های این برنامه از تحلیل ایستای مخزن است. پیش از اجرای مرحله مهاجرت داده مالی (۶-۴) و مراحل حذف، بررسی خط‌به‌خط و بازبینی انسانی الزامی است.
