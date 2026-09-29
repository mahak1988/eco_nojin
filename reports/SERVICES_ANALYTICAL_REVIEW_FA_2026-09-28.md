# گزارش تحلیلی معماری و کیفیت لایه سرویس‌ها

**Eco Nojin — بازنگری ساختاری `services/`**
تاریخ: ۲۸ شهریور ۱۴۰۵ (2026-09-28)
دامنه: کل درخت `services/` (۵۹۵ فایل پایتون، ۸۶٬۴۰۰ خط) به‌همراه بررسی تعامل با `engine/`، `database/`، `tests/` و `.github/workflows/`

---

## ۱. خلاصه اجرایی

پروژه Eco Nojin در وضعیت یک **مهندسیِ پرظرفیت با ناهمگنی شدید بلوغ** قرار دارد: لایه هسته (امنیت، رجیستری مدل، CI، آزمون انطباق عددی) با استاندارد بالای مهندسی و نظارت‌پذیری نوشته شده، اما لایه کسب‌وکار و بخش بزرگی از لایه علمی با همان دقت پیش نرفته است.

چهار گزاره محوری که از این بازنگری به دست می‌آید:

1. **دو خطای یک‌کلمه‌ای، بزرگ‌ترین زیرساخت‌های پروژه را خاموش کرده‌اند.** `FastAPI(...)` در `main.py:142` هرگز `lifespan` را نمی‌گیرد، پس کل مسیر راه‌اندازی (DB، NATS، مخزن‌ها) اجرا نمی‌شود. `class SafeUnpickler(pickle.Unpickler)` در `sentinel2_provider.py:50` بدون `import pickle` سطح ماژول، باعث `NameError` در import می‌شود و بزرگ‌ترین ارائه‌دهنده Sentinel-2 و زنجیره MRV را بی‌صدا از کار انداخته است. **این نشانه ساختاریِ نبودِ آزمون import است، نه بدشانسی.**

2. **لایه کسب‌وکار از نظر «صداقت رفتاری» فرو ریخته است.** در همان مخزنی که موتور SWAT+ صریحاً «No fabricated runoff» را تضمین می‌کند، ماژول `backup` یک خط کامنت SQL را به‌عنوان نسخه پشتیبان می‌نویسد و `verification_status="passed"` برمی‌گرداند؛ `traceability.verify_integrity()` همیشه `True` برمی‌گردد؛ `ledger.verify_chain()` همیشه `False` است؛ `ecosystem.trust_score` برای همه کاربران دقیقاً ۰٫۵ می‌دهد؛ `land_profile` کوه و دره می‌سازد و منبع را `SRTM` اعلام می‌کند. **این خطرناک‌ترین یافته این بازنگری است: سامانه در جاهایی که نباید، موفقیت را گزارش می‌کند.**

3. **بزرگ‌ترین بسته علمی پروژه، صفر آزمون عددی دارد.** `services/scientific_motors/` با ۸٬۶۰۰ خط و ۳۰+ کلاس — جایی که `AGENTS.md` انطباق با FAO/IPCC/OGC را از آن استناد می‌کند — هیچ آزمون عددی ندارد؛ تنها ارجاع موجود، پارس کردن `chain_runner.py` **به‌صورت متن منبع** است. در مقابل، رجیستری کوچک‌تر `services/models/` هشت آزمون انطباق عددی واقعی دارد. **الگو درست است، فقط اعمال نشده.**

4. **حدود ۵٬۲۰۰ خط کد (~۶٪ کل) یا هرگز فراخوانی نمی‌شود یا تکراری است** — شامل ۶۱۶ خط متریک Prometheus که هرگز import نمی‌شود، در حالی که لاگ راه‌اندازی ادعای فعال بودنشان را می‌کند (`main.py:192`). این کد مرده، باری است که توسعه‌دهنده جدید باید در ذهنش نگه دارد بی‌آنکه در runtime تأثیری داشته باشد.

**توصیه کلی:** پیش از افزودن هیچ قابلیت جدید، یک اسپرینت «صداقت و یکپارچگی» (Integrity Sprint) اجرا شود: (الف) چند اصلاح یک‌خطی بحرانی، (ب) حذف هر مسیر «موفقیت جعلی» تا زمان پیاده‌سازی واقعی، (پ) یک آزمون import + یک آزمون انطباق عددی برای بسته علمی، (ت) پاک‌سازی کد مرده.

---

## ۲. روش‌شناسی و دامنه

| بُعد | روش |
|---|---|
| ساختاری | شمارش LOC به تفکیک ماژول، نسبت کد تولیدی/آزمون، نقشه مصرف‌کنندگان با جست‌وجوی سراسری |
| رفتاری | خواندن مسیر درخواست از `main.py` تا میدلور، سرویس، مدل و پایگاه داده |
| پیکربندی | تطبیق `engine/hydroma/config/settings.py` با مصرف‌کنندگان واقعی |
| کیفیت | تطبیق قراردادهای `AGENTS.md` با وضعیت واقعی کد و CI |

**محدوده تحلیل:** `services/` با ۶۶ ورودی سطح‌بالا. برای دقت، ادعاهای بحرانی با بازخوانی مستقیم کد راستی‌آزمایی شده‌اند؛ مواردی که فقط از تحلیل ایستا به دست آمده‌اند با برچسب «مشکوک» مشخص شده‌اند.

---

## ۳. نمای کلان کمی

### ۳-۱. ابعاد کل

```
فایل‌های پایتون:      595      (تولیدی: 527 | آزمون: 68)
خطوط کل:              86,400
ماژول/زیرپکیج:       66
روترهای فعال:         74 فراخوانی include_router
فایل‌های روتر:         85
```

### ۳-۲. ده ماژول بزرگ‌تر

| رتبه | ماژول | فایل | خطوط تولیدی | خطوط آزمون | نسبت آزمون |
|---:|---|---:|---:|---:|---:|
| ۱ | `api_gateway` | ۱۱۴ | ۲۵٬۶۴۸ | ۱۹۴ | **۰٫۰۰۸** |
| ۲ | `scientific_motors` | ۳۳ | ۹٬۰۸۴ | ۰ | **۰** |
| ۳ | `marketplace` | ۲۶ | ۴٬۷۰۵ | ۱٬۰۳۴ | ۰٫۲۲ |
| ۴ | `security` | ۲۵ | ۲٬۶۷۰ | ۱٬۶۰۳ | **۰٫۶۰** |
| ۵ | `satellite` | ۱۶ | ۳٬۳۶۴ | ۲۳ | ۰٫۰۰۷ |
| ۶ | `carbon` | ۱۶ | ۲٬۱۹۶ | ۶۳۹ | ۰٫۲۹ |
| ۷ | `business_modules` | ۲۴ | ۲٬۷۴۳ | ۰ | **۰** |
| ۸ | `map_engine` | ۲۲ | ۲٬۴۷۸ | ۲۷ | ۰٫۰۱ |
| ۹ | `finance` | ۱۲ | ۱٬۷۳۳ | ۶۷۲ | ۰٫۳۹ |
| ۱۰ | `ai` | ۸ | ۱٬۶۶۵ | ۰ | **۰** |

### ۳-۳. توزیع آزمون — یک قطب‌شکاف آشکار

نسبت آزمون به‌طور سیستماتیک **معکوسِ ریسک** توزیع شده است:

- **`api_gateway`** با ۲۵٬۶۴۸ خط (۳۰٪ کل کد) فقط ۱۹۴ خط آزمون دارد — عملاً بدون پوشش مستقیم.
- **`security`** با ۲٬۶۷۰ خط، ۱٬۶۰۳ خط آزمون دارد (نسبت ۰٫۶۰) — بهترین وضعیت مخزن.
- **۱۲ ماژول اصلی کسب‌وکار صفر آزمون دارند**: `ledger`، `ecowallet`، `alerting`، `jobs`، `backup`، `contracts`، `workflow`، `provenance`، `notification`، `logistics`، `dispute_resolution`، `ai`.

یعنی دقیقاً همان ماژول‌هایی که بحرانی‌ترین نقیص‌ها را دارند (بخش ۷)، کمترین پوشش را دارند.

> نکته مثبت: آزمون‌های ریشه `tests/unit/` و `engine/strict_tests/` بسیار قوی‌اند (۸۳۸ + ۹۲۶ تست). به‌ویژه `tests/unit/test_repo_honesty.py` و `test_no_altered_standards.py` که صریحاً ادعاهای بی‌پشتوانه را می‌سنجند. **نقص در لایه سرویس است، نه در فرهنگ تست‌نویسی مخزن.**

---

## ۴. معماری: لایه‌ها و جریان درخواست

### ۴-۱. معماری اعلام‌شده در برابر معماری واقعی

`AGENTS.md` معماری «ماژولار، سرویس‌گرا، رویدادمحور» را توصیف می‌کند. واقعیت اجرایی:

```
                    ┌─────────────────────────────────────────┐
  HTTP درخواست ───▶ │ SpiderFirewallMiddleware (بیرونی‌ترین)   │ services/security/middleware.py
                    │  honeypot → antibot → WAF → anomaly       │
                    ├─────────────────────────────────────────┤
                    │ Locale → Idempotency → CSRF              │
                    ├─────────────────────────────────────────┤
                    │ RequestID → SecurityHeaders → RateLimit  │
                    ├─────────────────────────────────────────┤
                    │ HTTPSRedirect → Tenant → UploadSize       │
                    ├─────────────────────────────────────────┤
                    │ CORSMiddleware (innermost)               │
                    ├─────────────────────────────────────────┤
                    │ 74 روتر FastAPI  ──▶  Depends(auth)     │
                    └─────────────────────────────────────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
     لایه دامنه               لایه سرویس              موتورهای علمی
   (schemas/models)     (carbon/finance/market…)   (scientific_motors,
                                                    map_engine, satellite)
             │                        │                        │
             └────────────────────────┴────────────────────────┘
                                      ▼
                     database/hub.py (SQLAlchemy 2.0 async)
```

### ۴-۲. یافته ساختاری بحرانی: `lifespan` هرگز ثبت نمی‌شود

`services/api_gateway/main.py:203` تابع `lifespan(app)` را تعریف می‌کند (۷۳ خط: راه‌اندازی DB، اتصال NATS، مقداردهی مخزن‌های بازارگاه و کربن)، اما در خط ۱۴۲ اپلیکیشن ساخته می‌شود:

```python
app = FastAPI(title="Eco Nojin API Gateway")   # main.py:142 — بدون lifespan=
```

`lifespan` **هرگز به FastAPI داده نمی‌شود.** راستی‌آزمایی‌شده با جست‌وجوی `lifespan|FastAPI\(` در فایل: تنها سه تطابق، هیچ‌کدام `lifespan=` نیست.

**پیامد مستقیم:** کل مسیر راه‌اندازی اجرا نمی‌شود —
- `init_db()` فراخوانی نمی‌شود → جداول در توسعه ساخته نمی‌شوند (امروز فقط به‌لطف `Base.metadata.create_all` جای دیگری کار می‌کند یا اصلاً کار نمی‌کند)
- `await init_nats()` فراخوانی نمی‌شود → **گذرگاه رویداد در هر اجرا قطع است**
- `set_carbon_repository(...)` فراخوانی نمی‌شود → موتور کربن بدون مخزن کار می‌کند
- `shutdown_nats()` هرگز اجرا نمی‌شود

این یک خط، تفاوت میان «معماری اعلام‌شده» و «رفتار واقعی» را به‌تنهایی توضیح می‌دهد.

### ۴-۳. ترتیب میدلورها: CORS در داخلی‌ترین جای ممکن

ترتیب مؤثر (Starlette آخرین‌افزوده = بیرونی‌ترین) در `main.py:303-373` مشخص شده. سه مشکل:

1. **نظرات راهنما غلط‌اند.** `main.py:284` می‌گوید «CORS باید اول باشد» — اما CORS داخلی‌ترین میدلور اپ است و روترها پیش از آن ثبت شده‌اند (`main.py:145`).
2. **`main.py:350` می‌گوید «Idempotency باید بعد از auth باشد» — اما هیچ میدلور auth وجود ندارد.** احراز هویت کاملاً `Depends()`-محور است و پس از همه میدلورها اجرا می‌شود. این فقط یک نظر قدیمی نیست؛ یک باگ زنده است (بخش ۶-۱).
3. **پیامد CORS داخلی:** هر پاسخ زودهنگامِ میدلورهای بیرونی (۴۲۹ نرخ‌محدودسازی، ۴۰۳ CSRF، ۴۱۳ حجم آپلود، ۴۲۲ idempotency) **بدون هدر `Access-Control-Allow-Origin`** بازمی‌گردد. مرورگر خطای CORS مبهم نشان می‌دهد، نه «نرخ محدود است».

### ۴-۴. ناهمگنی لایه‌بندی در ماژول‌های کسب‌وکار

چهار قرارداد متفاوت هم‌زمان در حال اجرا هستند:

| الگو | ماژول‌های منطبق |
|---|---|
| `service + models + schemas + router` (تمیز) | `alerting`, `jobs`, `backup`, `provenance`, `contracts` |
| `service + routers` بدون repository | `commerce`, `inventory` |
| `service` + دسترسی مستقیم DB + چند سبک موازی | `carbon` (AsyncSession + Session), `marketplace` (سه سبک), `finance`/`ledger`/`ecowallet` (AsyncSession + Session + Any) |
| تخت، بدون router | `ledger`, `workflow`, `notification` |

**نشانه بارز:** منطق کسب‌وکار در خود روترها نشسته است. نمونه‌ها: `commerce/routers/commerce.py:79-80,104-109` (دسترسی مستقیم DB)، `inventory/routers/inventory.py:158-161` (`__import__("sqlalchemy").select` داخل هندلر)، `admin_content.py:120,133-134` (نوشتن در روتر)، و بدتر از همه `ai/admin_assistant.py:140-199` که **۹ کوئری همگام DB را از داخل `async def` صدا می‌زند و حلقه رویداد را بلوکه می‌کند.**

---

## ۵. لایه علمی و داده

### ۵-۱. معماری دوتایی — یک تصمیم طراحی بسیار خوب

`services/scientific_motors/` ۹٬۰۸۴ خط دارد و برای هر مدل **دو پیاده‌سازی** نگه می‌دارد:

| مدل | نسخه داخلی (ساده‌شده) | نسخه واقعی (پوسته موتور خارجی) | وضعیت |
|---|---|---|---|
| AquaCrop | `aquacrop.py` (۲۴۰) | `aquacrop_real.py` (۵۵۸) + `aquacrop_real_motor.py` (۳۲۵) | نسخه واقعی به API وصل **نیست** |
| SWAT+ | `swat_plus.py` (۱۹۶) | `swat_real.py` (۱۴۴) | وصل نیست |
| HEC-RAS | `hecras.py` (۲۱۷) | `hecras_real.py` (۱۵۰) | وصل نیست |
| RothC | `rothc.py` (۲۰۰) | `rothc_real.py` (۱۵۵) | وصل نیست |
| تخصیص آب | — | `pywr_real.py` (۱۴۸) | — |

**آنچه اینجا تحسین‌برانگیز است:** قرارداد «تضعیف صادقانه» در مستندات این فایل‌ها مدون شده. برای نمونه `swat_real.py`:

> *"pySWATPlus یک ویرایشگر/کالیبراتور فایل است؛ اجرای کامل شبیه‌سازی به فایل اجرایی رایگان SWAT+ rev60 نیاز دارد. **No fabricated runoff.**"*

و `hecras_real.py`:

> *"...به‌همراه تقریب صریحاً برچسب‌خورده Manning تا زنجیره همچنان شاخص سیل بدهد (**هرگز به‌عنوان خروجی HEC-RAS ارائه نمی‌شود**)."*

این دقیقاً همان رفتاری است که در لایه کسب‌وکار غایب است. **الگوی `*_real.py` باید به‌عنوان استاندارد پروژه در سراسر `services/` تسری شود.**

**اما — سه پیامد جدی:**

1. روترهای `motors.py:13-18` فقط نسخه‌های ساده‌شده را در معرض قرار می‌دهند. نسخه‌های واقعی — که تنها جایی هستند که «این محاسبه واقعاً انجام شده» ادعا می‌شود — از طریق API **غیرقابل دسترس‌اند**. بنابراین کاربر API نهایتاً با تقریب‌های numpy کار می‌کند، بدون آنکه بداند.
2. خودِ لایه «واقعی» هم کامل سالم نیست: `swat_real.py` اسکلت آماده‌سازی است (بخش ۵-۹)، `aquacrop_real.py` داده هواشناسی **مصنوعی** تولید می‌کند (`:112-136`)، و `aquacrop_adapter.py` امضای نامعتبر OSPy دارد و اصلاً کار نمی‌کند.
3. **نشت مستقیم به لایه کسب‌وکار:** `carbon_sequestration.py` یک پیاده‌سازی **سوم** RothC با چهار استخر است، مستقل از هر دو نسخه دیگر — و `rothc.py` نسخه داخلی خطای موازنه جرم دارد (بخش ۵-۵). یعنی سه پیاده‌سازی مستقل از یک مدل، هرکدام با نقص خود.

> **نکته روش‌شناختی:** اعداد این گزارش از شمارش مستقیم با PowerShell (`Measure-Object -Line`) به دست آمده‌اند و با شمارش ابزارهای دیگر چند درصد تفاوت دارند. ارقام نسبی و رتبه‌بندی معتبرند؛ ارقام مطلق تقریبی.

### ۵-۲. نقص بحرانی: `sentinel2_provider.py` اصلاً import نمی‌شود 🔴

`services/satellite/sentinel2_provider.py:50`:

```python
class SafeUnpickler(pickle.Unpickler):
```

اما `import pickle` **در سطح ماژول وجود ندارد** — تنها در خط ۴۰۸ به‌صورت محلی و داخل تابع `_save_to_disk_cache` انجام شده است. عبارت پایه کلاس در زمان ایجاد کلاس ارزیابی می‌شود، بنابراین:

> `NameError: name 'pickle' is not defined` — **در لحظه import**

راستی‌آزمایی‌شده: `Select-String` برای `^import` در فایل، `pickle` را فقط در خطوط ۴۰۸/۴۲۱/۴۳۲ (داخل تابع) نشان می‌دهد.

**زنجیره شکست:**
- `scientific_motors/satellite_integration.py:46` ← شکست
- `scientific_motors/mrv_system.py:44` ← شکست
- `telegram_bot/integration.py:29-49` کل بلوک را در یک `try/except Exception` می‌پیچد → `NameError` بلعیده می‌شود، `_satellite = None` می‌شود و `analyze_land()` برای **هر پنج موتور** `{"error": "Motors not available"}` برمی‌گرداند — **بی‌صدا**.

یعنی بزرگ‌ترین و کامل‌ترین ارائه‌دهنده Sentinel-2 پروژه (۱٬۰۲۶ خط) در عمل **هیچ‌گاه اجرا نمی‌شود**، و شکست آن به‌جای ۵۰۰، پاسخ موفقیت‌نمای «موتورها در دسترس نیستند» می‌شود.

### ۵-۳. چهار انتزاع موتور موازی و ناسازگار

| مکان | سازوکار | دامنه |
|---|---|---|
| `scientific_motors/base.py:91-132` | `AbstractScientificMotor` ABC | ۳۰+ کلاس — **بدون رجیستری**؛ نمونه‌ها ad-hoc در محل فراخوانی ساخته می‌شوند |
| `models/registry.py:37-108` | `list[ModelInfo]` با ۲۲ عضو + `@lru_cache` | تنها رجیستری واقعی — اما **مجموعه‌ای تقریباً نامت交集** با `scientific_motors` |
| `simulation/base.py:72-101` | `SimulatorRegistry` (تک‌نمونه با `__new__` + دیکشنری کلاسی) | ۸ شبیه‌ساز + ۸ آداپتور خودثبت‌شونده |
| `map_engine/orchestrator.py:55-70` | دیکشنری نمونه fetcher/pipeline | ۶ fetcher + ۵ pipeline |

سه قالب کش ناسازگار، بدون TTL یا ابطال در هیچ‌کدام:
- `chain_runner._cache_key` (`:71-116`) → `data/motors/cache/chain_<sha256>.json` — **بدون TTL، بدون مهر تبار/version**؛ تغییر کتابخانه یا داده بالادست، ورودی کهنه را بی‌اعتبار نمی‌کند
- `models/registry.py:82-108` → کش درون‌فرایندی با سقف ۱۰۰
- `map_engine/orchestrator.py:147-185` → JSON + بررسی وجود COG

**سوءاستفاده از `MotorType`:** این enum فقط ۶ عضو دارد ولی ۱۱ کلاس نوع نادرست گزارش می‌کنند — از جمله `RUSLEMotor`، `CarbonSequestrationMotor`، `IrrigationSchedulerMotor`، `MRVSystemMotor`، `CropAdvisorMotor`، `PlantingCalendarMotor`، `LandCapabilityMotor` که همگی `BIOFERTILIZER` را ادعا می‌کنند (با کامنت صریح `# Reuse until we add LCC enum`)، و `PywrWaterAllocationMotor` و `MultiObjectiveOptimizer` که `WHAT_IF` می‌دهند. `CarbonMrvMotor` و `EconomyMotor` اصلاً `AbstractScientificMotor` نیستند و `motor_type` را به‌صورت `str` خام برمی‌گردانند.

### ۵-۴. سه فرمول ناسازگار LS و چهار K ناسازگار در RUSLE

**ضریب شیب (LS) — سه پیاده‌سازی متضاد:**

| محل | فرمول | مرجع |
|---|---|---|
| `map_engine/pipelines/rusle.py:150` | `65.41·sin²β + 4.56·sinβ + 0.065` | Foster/Nearing |
| `scientific_motors/erosion_rusle.py:461` | `(9.8·sinβ + 0.03) / (16.8·sinβ − 0.50)` | Wischmeier & Smith |
| `chain_runner.py:144` | `0.065 + 0.045·s + 0.0065·s²` | چندجمله‌ای در **درصد شیب، بدون تریگونومتری** |

علاوه بر آن، `land_models.py:92-98` و `api_gateway/routers/elevation.py:245` دو نسخه چهارم و پنجم اضافه می‌کنند. حتی آستانه‌های کلاس‌بندی فرسایش ناسازگارند: ۵/۱۲/۲۵/۵۰ در دو فایل، اما ۵/۱۰/۲۰ در `chain_runner.py:150-157`.

**ضریب خاک (K) — چهار روش با اختلاف تا ۷٫۶ برابر:**

| محل | روش | بازه برش |
|---|---|---|
| `satellite/soilgrids.py:95-110` | EPIC با ضریب `0.1317`، `c = soc_g_kg/1000` | `[0.001, 0.09]` |
| `map_engine/fetchers/soil_fetcher.py:91-105` | EPIC **بدون** `0.1317`، `oc_frac = oc/100` | `[0.005, 0.8]` |
| `simulation/adapters/erosion_adapter.py:118-129` | دیکشنری بافت | `0.15–0.45` (خارج از بازه استاندارد) |
| `routers/elevation.py:205-213` | `base_k` + تنظیم ماده آلی | — |

دو نسخه EPIC واحد SOC متفاوت (کسر در برابر درصد) می‌خواهند و هیچ نگهبان نوعی وجود ندارد. یعنی **یک مقدار K می‌تواند بسته به اینکه کدام مسیر فراخوانی شده ۷٫۶ برابر متفاوت باشد.**

### ۵-۵. خطای موازنه جرم در مدل کربن شاخص

`services/scientific_motors/rothc.py:190-197`:

```python
# 46% to BIO, 54% to HUM
dpm_to_hum = dpm_loss * 0.54
rpm_to_hum = rpm_loss * 0.54
bio_to_hum = bio_loss * 0.46
bio_loss * 0.54        # ← نتیجه دور ریخته می‌شود
hum_to_bio = hum_loss * 0.46
```

انتقال ۵۴٪ از استخر BIO به HUM محاسبه و **بلافاصله دور ریخته** می‌شود. نتیجه: استخر HUM به‌طور سیستماتیک کم‌تغذیه می‌شود. (برچسب کامنت `:190` نیز وارونه است: ۰٫۴۶ به `bio_to_hum` نسبت داده شده.)

این یک باگ خاموش در **پرچم‌دارترین مدل کربن پروژه** است — از آنجا که `AGENTS.md` «دقت علمی» را اصل معماری اعلام می‌کند، این نوع نقیص بیشترین هزینه علمی را دارد.

### ۵-۶. نقص‌های بی‌صدای دیگر در لایه علمی

| محل | نقص |
|---|---|
| `satellite/era5_fetch.py:74` | `for start, end in _chunk([start, end])` فقط روی **دو نقطه انتهایی** تکرار می‌کند → برای بازه ۱۵ ژانویه تا ۲۰ مارس فقط ۴ تاریخ نادرست درخواست می‌شود، نه کل بازه |
| `satellite/sentinel2_provider.py:292` | `_save_to_cache` کلید را با `datetime.now()` مهر می‌زند → هرگز با کلید محاسبه‌شده از بازه واقعی مطابقت نمی‌کند → **کش هرگز بازخوانی نمی‌شود** |
| `chain_runner.py:143` | `math.radians(math.atan(slope_pct / 100.0))` عبارت بی‌اثر؛ شیب رادیانی دور ریخته و LS از چندجمله‌ای درصد شیل ساخته می‌شود |
| `scientific_motors/crop_database.py` | **۴۷٪ تکرار**: `CropFamily`/`CropProfile` (`:25-146` و `:176-296`)، `CROP_DATABASE` (`:353-540` و `:719-746`)، `CropDatabaseService` (`:348-545` و `:553-774`)، `import logging` در `:12` و `:153`. محتوا: **فقط یک محصول («گندم»)** در برابر ادعای docstring «۳۰+ گونه، ۵۰۰۰+ رقم» |
| `scientific_motors/data_repository.py` | `@lru_cache` روی **متدهای نمونه** (`:68,102,128,263,312`) → نشت حافظه نامحدود؛ `sqlite3.Connection` به‌صورت **صفت کلاس** (`:31`)؛ هفت متد پارامترهای خود را **نادیده می‌گیرند** و همه ردیف‌ها را برمی‌گردانند |
| `land/land_profile.py:57-78` | چشم‌انداز ساختگی: `elevation_min: 100.0 … land_capability_class: "III", dem_source: "SRTM"` — در حالی که docstring `:50-51` «placeholder» را می‌پذیرد و **منبع داده را جعلاً SRTM اعلام می‌کند** |
| `map_engine/*` | **همه ۶ fetcher داده مصنوعی تولید می‌کنند** (`rng.normal` برای DEM، uniform برای بارش/پوشش گیاهی/کاربری خاک). روتر `map_engine/api/__init__.py:1-45` فقط `SmartMapService` (mock با `np.full((8,8), 2.8)`) را نمونه‌سازی می‌کند — **خطوط لوله واقعی از هیچ اندپوینتی در دسترس نیستند** |
| `satellite/service.py:132-168` | `compute_ndvi` و `compute_vegetation_indices` مقادیر هاردکد برمی‌گردانند و **کاملاً `lat`/`lon`/`start_date`/`end_date` را نادیده می‌گیرند** (کامنت `:132`: `# For demo: return mock data`) |
| `satellite/monitoring_service.py:194-207` | `detect_changes` → `change_detected: True, magnitude: 0.15, confidence: 0.85` با کامنت `# شبیه‌سازی` |
| `satellite/openet_service.py:14-22` | `return Ellipsis` به‌عنوان `et_ensemble_mm` به‌علاوه `confidence: 0.89` |
| `scientific_motors/whatif_engine.py:69-70,96` | دو `inputs.get(...)` بی‌اثر؛ `carbon_samples` تولید می‌شود ولی **هیچ‌گاه اعمال نمی‌شود** |
| `scientific_motors/climate_motor.py:64,139-152` | `(1.0 + 0.0 * sin(radians(lat)))` باعث inert شدن `lat_deg`؛ تجمیع ماهانه با **قطعات ثابت ۳۰ روزه** به‌جای ماه تقویمی |
| `livestock/simulators/cattle.py:38-41` | `hasattr(self, "DAILY_DAILY_PCT")` — غلط املایی روی نامی که هرگز تعریف نشده |
| `data_manual/motor_feed.py:250-262` | کلیدهای دیکشنری بافت **موجیبیک** (فارسی خراب‌شده) → `usda_texture_class` همیشه به شاخص ۵ برمی‌گردد |
| `satellite/nasa_power.py:111` | حاشیه‌نویسی `Optional[float]` بدون import — فقط با `from __future__ import annotations` زنده مانده |

### ۵-۷. سه تعریف متفاوت برای یک نام شاخص

`NDWI` در سه جا با سه تعریف متفاوت:
- `satellite/real_land.py:129-137` — Gao (1996): `NIR − SWIR`
- `map_engine/pipelines/vegetation.py:59` — McFeeters: `Green − NIR`
- `map_engine/pipelines/vegetation.py:71-73` — **همان فرمول**، اما با نام `NDRE`

و LAI: `3.5·NDVI` (تقریبی) در برابر فرمول لگاریتمی Boegh 2002 در `real_land.py:87-97`.

**راستی‌آزمایی امنیتی مثبت:** جست‌وجوی سراسری برای کلیدها، توکن‌ها، رمزها و literalهای `-----BEGIN` در کل `services/` **هیچ راز hardcode‌شده‌ای یافت نشد.** تنها مقدار محیطی hardcode‌شده، URL پروژه Supabase به‌عنوان مقدار پیش‌فرض `os.getenv` در `ogc/features.py:20` است (راز نیست، اما یک محیط مشخص را در کد تثبیت می‌کند).

### ۵-۸. الگوی پایه و نقاط ضعف ثبت

`scientific_motors/base.py` (۱۳۲ خط) یک ABC تمیز است، اما:

- **هیچ رجیستری وجود ندارد.** موتورها در `motors.py:108,123,153,176,209` و `chain_runner.py:283` به‌صورت ad-hoc ساخته می‌شوند.
- `AbstractScientificMotor.__init__` در خط ۹۶ `mkdir(parents=True, exist_ok=True)` را اجرا می‌کند — **اثر جانبی در زمان ساخت شیء**، و هیچ موتوری جز `chain_runner` از آن استفاده نمی‌کند.
- سه موتور قرارداد را نقض می‌کنند: `carbon_sequestration.py:146-152` و `mrv_system.py:147-160` هرگز `super().__init__()` را صدا نمی‌زنند، پس `self.cache_dir` تعریف‌نشده است.
- `MotorResult.created_at` از `datetime.utcnow` استفاده می‌کند (`:75`) — منسوخ در ۳٫۱۲ و ناسازگار با `datetime.now(UTC)` در لایه کسب‌وکار.
- `chain_runner.py:475` صریحاً اعلام می‌کند: `"note": "single-point KGE placeholder (needs time series)"` — و در عین حال بلوک `data_sources` (`:537-542`) به fallbackها اعتراف می‌کند. **این خوب است.**

### ۵-۹. فهرست زنجیره اصلی و جایگزین‌های آن

`chain_runner.run_scientific_chain` (`:207-545`) به ترتیب: SoilGrids → RUSLE نقطه‌ای → `SWATPrepMotor` → `PywrWaterAllocationMotor` → `HECRASFloodMotor` (با fallback Manning) → `RealRothCMotor` (pyRothC) → `RealAquaCropMotor` (OSPy) → `MultiObjectiveOptimizer`.

دو نکته:
- **بهینه‌ساز چندهدفه روی جایگزین (surrogate) اجرا می‌شود، نه مدل واقعی.** `optimize_chain.py:33-60` یک `GaussianProcessRegressor` برازش می‌کند و NSGA-II (pymoo) روی آن اجرا می‌شود. **هیچ‌گاه `run_scientific_chain` واقعی صدا زده نمی‌شود.** جبهه پارتو گزارش‌شده بهینه‌سازی مدل واقعی نیست.
- **`swat_real.py` اسکلت آماده‌سازی است، نه اجرا.** `_swat_version()` (`:96-100`) فقط گزارش می‌دهد که آیا `pySWATPlus` import می‌شود؛ «اجرا» (`:112-150`) یک توصیف‌گر JSON پارامتر روی دیسک می‌نویسد. با وجود import شدن `Txtinout` و `DataManager` در `:30-32`، هیچ فراخوانی واقعی SWAT+ انجام نمی‌شود.

### ۵-۱۰. وضعیت آزمون لایه علمی

| مؤلفه | آزمون | واقعیت |
|---|---|---|
| `services/models` registry | `tests/integration/test_models_phase7.py` — **بهترین آزمون دامنه** | ۲۲ مدل، ۸ بررسی انطباق عددی، ۴ آزمون API |
| کلاینت‌های ماهواره‌ای | ۷ فایل آزمون | بررسی `configured`، کش توکن، STAC، SCL masking |
| `simulation` | ۱۸۱ خط، ۸ شبیه‌ساز | **خوب** — از جمله آزمون معنادار «بادشکن باید فرسایش را کاهش دهد» (`:103-129`) |
| `map_engine` | ۳۲ خط | **۲ آزمون، هر دو علیه `SmartMapService` (mock)**. ارکستراتور، هر ۵ خط لوله و هر ۶ fetcher: **صفر آزمون** |
| `satellite/tests/test_integration.py` | ۲۸ خط | **۲ آزمون ضعیف** — `assert result is not None` |
| `land/tests/test_land_profile.py` | ۲۸ خط | آزمون **همان stub هاردکد** را می‌سنجد (`is not None`) |
| **`scientific_motors` (۳۰+ کلاس، ۸٬۶۰۰ خط)** | **هیچ** | تنها ارجاع: `tests/unit/test_rusle_uncorrelated.py:66-77` که `chain_runner.py` را **به‌صورت متن منبع** پارس می‌کند و `RUSLE_CALIBRATION == 1.0` را ادعا می‌کند. **هیچ آزمون عددی از هیچ موتوری وجود ندارد.** |

**بدترین شکاف پروژه:** بزرگ‌ترین بسته علمی پروژه — جایی که `AGENTS.md` انطباق با FAO/IPCC/OGC را از آن استناد می‌کند — **صفر آزمون عددی** دارد، در حالی که بسته `models/` با ۲۲ مدل کوچک‌تر، هشت بررسی انطباق عددی دارد.

### ۵-۱۱. فایل‌های بی‌استفاده و ساختار بسته

- **`scientific_motors/test_lcc.py` (۹۷ خط)** — یک **اسکریپت** با `if __name__ == "__main__"` در ریشه پکیج تولیدی. سه تابع در سطح ماژول با نام `test_*` و **صفر assertion** تعریف می‌کند، بنابراین pytest سه آزمون تهی از بسته تولیدی جمع می‌کند.
- **`map_engine/test_hydroma_motors.py` (۱۵۸ خط)** — همان مشکل، به‌علاوه `sys.path.insert(0, ".")` در خط ۱۲.
- **`aquacrop_adapter.py` (۴۳ خط)** — نه import می‌شود، نه معتبر است: `AquaCropModel(soil=..., crop=..., weather=...)` امضای OSPy نیست؛ `model.get_yield()` وجود ندارد.
- **`crop_advisor.py:359,374`** به `VarietyRecommendation` ارجاع می‌دهد که **در کل مخزن تعریف نشده** → `NameError` در صورت فراخوانی. فقط به این دلیل خفته است که `_suggest_varieties` هرگز صدا زده نمی‌شود.
- **`services/scientific_motors/، map_engine/، ogc/` هیچ `__init__.py` ندارند** (به‌عنوان namespace package کار می‌کنند). بزرگ‌ترین پکیج پروژه بدون docstring بسته و `__all__`.
- **`services/conftest.py:745,753`** از `services.scientific_motors.service` import می‌کند که **وجود ندارد** → fixture همیشه skip می‌شود.
- **تکرار کامل:** `data_sources/copernicus_cds.py` (۱۴۸ خط) و `satellite/cds.py` (۱۴۸ خط) — کلاینت CDS خط‌به‌خط یکسان در دو مکان.
- **importهای مرده:** چهار فایل (`erosion_rusle.py:17-28`، `carbon_sequestration.py:49-58`، `irrigation_scheduler.py:32-43`، `satellite_integration.py:39-46`) نمادهای C++ (`_cpp_rusle`, `_cpp_soil_k`, `_cpp_rainfall_r`, `_cpp_richards` و…) را import می‌کنند و **هرگز استفاده نمی‌کنند** — یعنی هسته C++ عملاً به موتورهای علمی متصل نیست.

### ۵-۱۲. منابع داده و اعتبارنامه‌ها

| منبع | فایل | احراز هویت | مدیریت کلید |
|---|---|---|---|
| SoilGrids (ISRIC) | `satellite/soilgrids.py:12-20` | ندارد | نیازی نیست |
| Sentinel-2 L2A | `satellite/sentinel2_provider.py:66-145` | CDSE OAuth2 | `CDSE_CLIENT_ID`/`SECRET` از env — `CdseUnavailable` صادقانه |
| Copernicus CDS | `satellite/copernicus.py`, `era5_fetch.py:30-74` | CDS key | `CDSAPI_URL`/`CDS_KEY` |
| NASA POWER | `satellite/nasa_power.py:61` | ندارد | نیازی نیست |
| Open-Meteo (ERA5) | `satellite/open_meteo.py:31-36` | ندارد | نیازی نیست — خطای شبکه → `"source": "unavailable"` |
| KoboToolbox (SOC میدانی) | `mrv/kobo.py:70-71` | هدر Token | `KOBO_TOKEN` + `KOBO_FORM_ID` — `requires_credentials` صادقانه |
| **ODATA v1** | `satellite/service.py:44-49` | فقط آرگومان سازنده | **بدون fallback به env** → `authenticate()` بی‌صدا `False` برمی‌گرداند و `search_sentinel2` بدون `Authorization` (`:103`) درخواست می‌فرستد |

نکته مثبت: برخلاف بسیاری از پروژه‌ها، **مدیریت اعتبارنامه در `services/` الگوی منسجمی دارد** — هر جا کلید نبود، وضعیت صریح (`configured=False`، `requires_credentials`، `unavailable`) برگردانده می‌شود.

### ۵-۱۳. تقسیم مصرف‌کنندگان — بخش بزرگی از موتورها از مسیر درخواست قطع است

جست‌وجوی سراسری نشان می‌دهد تنها **۶ روتر** به `scientific_motors` وابسته‌اند: `motors.py`، `climate.py`, `mrv.py`, `ogc_router.py`, `economy.py`, `ai_advice_router.py`. بقیه مصرف‌کننده فقط آزمون‌ها و `carbon/service.py` هستند.

با احتساب موارد بخش ۵-۶، عملاً **این مسیرها به هیچ کاربری نمی‌رسند:**

| مسیر | دلیل |
|---|---|
| `sentinel2_provider` (۱٬۰۲۶ خط) | `NameError` در import (۵-۲) |
| `map_engine` خط لوله واقعی + ۶ fetcher | روتر `api/__init__.py` فقط `SmartMapService` (mock) را نمونه‌سازی می‌کند |
| نسخه‌های `*_real.py` | روتر `motors.py:13-18` فقط نسخه‌های ساده‌شده را در معرض قرار می‌دهد |
| `swat_real`, `hecras_real`, `pywr_real`, `aquacrop_real_motor` | فقط در `chain_runner` داخلی |
| `openet_service`, `aquacrop_adapter`, `core_integration` | هیچ مصرف‌کننده‌ای ندارند |
| `crop_advisor._suggest_varieties`, `climate_motor`, `calibration` | خارج از `AbstractScientificMotor` یا هرگز صدا زده نمی‌شوند |

یعنی از ۹٬۰۸۴ خط موتور علمی، آنچه کاربر API واقعاً تجربه می‌کند عبارت است از: تقریب‌های numpy، موتورهایی که در زنجیره به‌صورت fallback اجرا می‌شوند، و چند مسیر که شکست خاموش دارند.

---

## ۶. گذرگاه API و زیرساخت

### ۶-۱. نقیص بحرانی: نشت پاسخ بین‌کاربری در میدلور Idempotency

`services/api_gateway/middleware/idempotency.py:141`:

```python
user_id = getattr(request.state, "user_id", None) or "anonymous"
```

جست‌وجوی سراسری نشان می‌دهد `request.state.user_id` **فقط در دو فایل تست** ست می‌شود؛ هیچ کد تولیدی‌ای آن را تنظیم نمی‌کند (تنها تولیدکننده `request.state.*`، میدلور Tenant است که فقط `tenant_id` می‌سازد). نتیجه:

در محیط عملیاتی، **همه درخواست‌ها با هویت `"anonymous"` ثبت می‌شوند.** در حالی که `database/models.py:435` ایندکس یکتا تعریف می‌کند:

```python
Index("ix_fin_idempotency_user_key", "user_id", "key", unique=True)
```

دو پیامد:
1. کلید یکسانِ دو کاربر به یک ردیف می‌رسد و `idempotency.py:160-165` **بدنه و کد پاسخ ذخیره‌شده کاربر دیگر را برمی‌گرداند** — افشای پاسخ بین‌کاربری روی مسیرهایی مانند `/api/v1/marketplace/orders` و `/api/v1/finance/payments/intent`.
2. درخواست‌های هم‌زمان به خطای `IntegrityError` مدیریت‌نشده → ۵۰۰.

نکات تکمیلی:
- `X-Client-Secret` (`:124`) یک هدر سمت کلاینت است؛ محاسبه SHA256 روی آن **هیچ چیزی را اثبات نمی‌کند** — یک کنترل امنیتی به‌ظاهر.
- `PROTECTED_PREFIXES` (`:26`) و `IDEMPOTENCY_TTL_HOURS` (`:22`) تعریف شده‌اند و هرگز استفاده نمی‌شوند؛ مقداردهی در خط ۱۸۴ درون‌سخت‌افزاری است.
- بدنه درخواست خوانده و دور ریخته می‌شود (`:120`) — جریان‌های بزرگ آپلود را می‌شکند.

### ۶-۲. CSRF: قفل کامل کلاینت‌های مبتنی بر کوکی

`services/security/csrf.py:65-67` الگوی «کوکی دوباره‌ارسالی» را پیاده می‌کند:

```python
csrf_token = request.headers.get("x-csrf-token")
cookie_token = request.cookies.get("econojin_csrf")
if not csrf_token or not cookie_token or csrf_token != cookie_token:
    return JSONResponse(status_code=403, ...)
```

**هیچ‌جا در مخزن کوکی `econojin_csrf` ست نمی‌شود.** راستی‌آزمایی: `CSRF_COOKIE` فقط در تعریف (`:15`) و همین خواندن (`:66`) ظاهر می‌شود. تابع `set_auth_cookies` (`auth.py:387-415`) فقط کوکی access و refresh را می‌نویسد.

پیامد: چون `auth.py:396-415` عمداً JWT را به کوکی httpOnly منتقل کرده (اصلاح C5)، **تمام درخواست‌های ناامنِ مبتنی بر کوکی که Bearer ندارند و در `EXEMPT_PREFIXES` نیستند، ۴۰۳ می‌گیرند.** جریانی که CSRF قرار بوده محافظت کند، دقیقاً همان جریانی است که کار نمی‌کند.

### ۶-۳. نرخ‌محدودسازی: تفکیک‌پذیری بر اساس کاربر، بی‌اثر

`services/api_gateway/security.py` می‌گوید callers باید از `is_allowed()` استفاده کنند (`:86-89`)، اما `dispatch` در `:182` مستقیماً `_check_redis`/`_check_memory` را صدا می‌زند. نتیجه: **`key_by_subject` (`:60,72,122-143`) که برای کاربران پشت NAT اضافه شده، هیچ اثری ندارد.**

همچنین `trusted_proxies` در `main.py:346` اصلاً پاس داده نمی‌شود → `_trusted_proxy_networks` خالی می‌ماند → **`X-Forwarded-For` نادیده گرفته می‌شود** و همه کلاینت‌های پشت یک لودبالانسر در یک سطل قرار می‌گیرند. در حالی که همان تنظیم برای `SpiderFirewallMiddleware` پاس داده می‌شود (`:367-372`) — **دو مدل اعتماد متفاوت در دو لایه.**

نشت حافظه: `self._hits: defaultdict(deque)` (`:73`) هرگز بر اساس کلید پاک‌سازی نمی‌شود؛ فقط محتوای deque کوتاه می‌شود. مهاجم با چرخاندن IP (یا IPv6 /64) این دیکشنری را بی‌حد رشد می‌دهد.

### ۶-۴. کش: طراحی خوب، اجرای_fail-hard

`services/api_gateway/cache/` (۹۷۳ خط) طراحی معماری خوبی دارد: L1 درون‌فرایندی + L2 Redis، ارتقای L2→L1، اینولیدیشن تگ‌محور با pub/sub، لرزش ±۱۰٪ روی TTL، بازرسی سلامت و گرم‌کننده. **اما کل بسته هرگز از بیرون فراخوانی نمی‌شود** (فقط در `cache/__init__.py` ارجاع دارد).

اگر روزی وصل شود، این نقیص‌ها مانع‌اند:

- **کش fail-open نیست، fail-hard است.** `RedisCache.get` فقط تجزیه JSON را محافظت می‌کند (`:217-237`)؛ خودِ `await self._client.get(...)` در `:213` محافظتی ندارد. قطعی Redis → `ConnectionError` → **۵۰۰ روی همه اندپوینت‌های کش‌دار.**
- **شمارنده hit، اینولیدیشن تگ را بی‌صدا نابود می‌کند.** `_increment_hits` (`:247`) با `set()` بدون `ex=` نوشته می‌شود، در حالی که کلید با `setex` (`:279`) ساخته شده بود. این تبدیل کلید را **ابدی** می‌کند. ایندکس تگ TTL دارد و منقضی می‌شود → `invalidate_tag` چیزی برنمی‌گرداند → مقدار هرگز باطل نمی‌شود. و چون `expires_at` سمت کلاینت در `get` بررسی می‌شود (`:226)، این کهنگی کاملاً پنهان است.
- **دو سامانه اینولیدیشن ناسازگار:** `RedisCache` از کانال `{prefix}tags` با تگ خام استفاده می‌کند؛ `CacheInvalidator` از `{prefix}invalidation` با پوشش JSON. هرگز یکدیگر را نمی‌بینند.
- **TTL درخواستی نادیده گرفته می‌شود:** `MultiLevelCache.set` ورودی L1 را با `self.config.l1_ttl` (پیش‌فرض ۶۰ ثانیه) می‌نویسد (`:434`) و آرگومان `ttl` را دور می‌اندازد. `set(k, v, ttl=10)` تا ۶۰ ثانیه سرو می‌شود.
- **بدون قفل:** `initialize()` (`:360-366`) و الگوی `get_*` بدون قفل → نشت ConnectionPool و PubSub در درخواست‌های هم‌زمان نخستین.

### ۶-۵. تاب‌آوری: پیاده‌سازی کامل اما قطع‌شده

`services/api_gateway/resilience/` (۸۵۸ خط) شامل circuit breaker، retry و timeout — **هیچ‌چیز بیرون از خود بسته آن را import نمی‌کند.** پیاده‌سازی موازی و کامل‌تری در `engine/resilience.py` وجود دارد که `engine/__init__.py` همان را re-export می‌کند. نقیص‌های بسته مرده:

- **`with_resilience` (`:49-121`) به‌طور پیش‌فرض retry را حذف می‌کند.** چون `circuit_breaker=True` پیش‌فرض است، `return await circuit_breaker.call(_call)` در خط ۱۰۶ بازمی‌گردد و شاخه `if retry_policy:` در `:119` **هیچ‌گاه اجرا نمی‌شود.** وعده «circuit breaker + retry + timeout» به «فقط circuit breaker» تبدیل می‌شود.
- **`RetryPolicy.retrying()` (`:97-122`) از پایه معیوب است:** یک `@asynccontextmanager` که پس از گرفتن استثنا **دوباره `yield` می‌کند**. `contextlib` در این حالت `RuntimeError("generator didn't stop after athrow()")` می‌دهد — خطایی که هیچ ارتباطی با کد کاربر ندارد.
- **`call_with_timeout` (`:193-203`) اصلاً timeout را اعمال نمی‌کند.** `check_deadline()` بلافاصله پس از تنظیم deadline آینده اجرا می‌شود، پس هرگز نمی‌تواند فعال شود؛ فراخوانی `await func(...)` کاملاً بی‌کران است. تنها اعمال واقعی در `with_timeout` (`:97`) است که `call_with_timeout` هرگز صدایش نمی‌زند.
- **HALF_OPEN بدون محدودیت پروب:** `is_available` با `return True` تمام می‌شود (`:90`) و مستندات کلاس از «infinite probe» وعده می‌دهد (`:61`). هر هم‌زمانی که `recovery_timeout` بگذرد، عبور می‌کند.
- **رجیستری سراسری بدون قفل:** `get_circuit_breaker` (`:221`) بررسی-و-اقد روی dict ساده انجام می‌دهد → دو نمونه برای یک نام → **نیمی از ترافیک از مدار باز عبور می‌کند.**

### ۶-۶. مشاهده‌پذیری: ابزار موجود، اتصال غایب

- **لاگ ساختاریافته فعال است** (`observability/structured_logger.py`) اما `StructuredLoggingMiddleware` **هرگز mount نشده** — یعنی خط لاگ ساختاریافته `http_request` در تولید وجود ندارد، هرچند هدف اسپرینت ۱٫۱ دقیقاً همین بود.
- **`metrics.py` (۶۱۶ خط، ~۳۰ متریک) هرگز import نمی‌شود.** در حالی که `main.py:192` می‌نویسد: `"✅ Prometheus metrics instrumentation enabled (with custom metrics)"` — **این پیام نادرست است.**
- **`clear_correlation_id` (`:48`) هرگز فراخوانی نمی‌شود.** `RequestIDMiddleware` (`security.py:234`) توکن را دور می‌ریزد. در برنامه‌های چندنخی این نشت زمینه (context) می‌شود.
- **`X-Request-ID` اعتبارسنجی نمی‌شود** — مقدار سمت کلاینت بدون بررسی طول و کاراکتر وارد لاگ و هدر پاسخ می‌شود (بردار تزریق لاگ).
- **نشست‌های بدون trace:** `set_tracer_provider` بدون flush در shutdown (`:46`) → از‌دست رفتن spanهای ناتمام.
- ** سطح سه پارادایم لاگ در یک گذرگاه:** `structlog` (main)، `logging.getLogger` (csrf.py:11)، `logger` ماژولی (main.py:137). هرکدام پیکربندی جدا.

### ۶-۷. گذرگاه رویداد: سه پیاده‌سازی موازی

| پیاده‌سازی | فایل‌ها | مصرف‌کننده |
|---|---|---|
| A | `api_gateway/eventbus/` (NATSConfig) | `outbox_worker.py:19` |
| B | `services/event_bus/` (EventBusConfig) | `workers/event_worker.py:7` |
| C | `orchestrator/src/messaging/bus.py` | ارکستراتور |

`NATSConfig` و `EventBusConfig` مو‌به‌مو یکسان‌اند و **منطق نگاشت subject متفاوت دارند** (`nats_client.py:251` در برابر `event_bus/config.py subject_for`) — یعنی یک رویداد منطقی ممکن است بسته به اینکه کدام پشته منتشرش کند روی subject متفاوتی بنشیند.

**هشدار مهم — راستی‌آزمایی‌شده:** `dlq.py` متد `add_to_dlq` دارد اما **هیچ فراخوانی‌ای ندارد**؛ در عوض `nats_client.py:313-321` یک `nak()` خام بدون backoff می‌زند. پیام سمی با تمام سرعت تا `max_deliver` بازارسالی می‌شود و **صف مرده هرگز تغذیه نمی‌شود.**

### ۶-۸. Outbox: الگوی درست، بدون نویسنده

`services/integration/outbox.py` الگوی outbox تراکنشی را درست تعریف می‌کند — اما **هیچ ماژولی کسب‌وکاری `add_event` را صدا نمی‌زند.** `IntOutboxEvent` فقط خوانده می‌شود. یعنی تغییر وضعیت و انتشار رویداد در هیچ‌جا اتمیک نیست.

نقیص‌های worker:
- `with_for_update(skip_locked=True)` روی SQLite بی‌اثر است (SQLAlchemy آن را حذف می‌کند) → در توسعه هیچ claim اتمیکی وجود ندارد.
- ایندکس جزئی `postgresql_where="processed_at IS NULL"` روی SQLite ساخته نمی‌شود.
- `RETRY_BACKOFF_BASE` تعریف شده و هرگز استفاده نمی‌شود؛ ستون `available_at` هم وجود ندارد → **بازارسالی فوری بدون backoff**.
- `processed_at` دو نقش ناسازگار دارد: نشانه claim (`:63`) و نشانه تکمیل (`sync.py:124`) — دو مصرف‌کننده بدون قفل مشترک روی یک جدول.
- پاک‌سازی: `cleanup_expired_idempotency_keys` (`:215-222`) `DELETE` می‌زند ولی **هرگز commit نمی‌کند** — حذف بی‌اثر است.

### ۶-۹. مصرف‌کننده، سیاه‌چاله است

`services/workers/event_worker.py:12` هیچ `handlers=` پاس نمی‌دهد. رفتار `event_bus/worker.py:160-164` در نبود handler:

```python
if handler is None:
    logger.warning("No handler registered for event %s", event_type)
    await _ack(message)
    return
```

یعنی کارگر فعلی **هر پیامی را که نفهمد ack می‌کند و دور می‌ریزد.**

---

## ۷. لایه کسب‌وکار — یافته‌های بحرانی

این بخش، پرریسک‌ترین ناحیه مخزن است. یافته‌ها به ترتیب شدت:

### ۷-۱. ناسازگاری نوع ستون: گزارش‌های مالی هیچ‌وقت کار نمی‌کنند 🔴

```python
# database/models.py:242
FinJournalEntry.account_id = Column(String, nullable=False, index=True)
# database/models.py:254
FinAccount.id = Column(Integer, ...)   # کلید اصلی
```

سه گزارش این دو را JOIN می‌کنند:
- `finance/ledger_service.py:193` → `trial_balance`
- `finance/ledger_service.py:271` → `profit_and_loss`
- `finance/reconciliation.py:83` → `_get_ledger_balance`

**ستون String هرگز می‌تواند با کلید اصلی Integer برابر باشد.** این JOINها صفر ردیف برمی‌گردانند:
- `trial_balance` و `profit_and_loss` همیشه خالی
- `reconcile_wallet_ledger` برای هر کیف پول `ledger_balance = 0` محاسبه می‌کند → **هر کیف پول به اندازه کل موجودی‌اش مغایرت گزارش می‌کند**

راه‌حل نیمه‌کاره‌ای در `ledger_service.py:286-292` فقط در سطح پایتون (دیکشنری) اعمال شده و JOIN سطح SQL را اصلاح نمی‌کند.

### ۷-۲. چهار `LedgerService` با سه قرارداد علامت متضاد 🔴

| # | مکان | اعتبارسنجی | علامت موجودی |
|---|---|---|---|
| ۱ | `finance/ledger_service.py:16` | کامل (متوازن، مثبت، فهرست دارایی) | بستانکار مثبت، بدهکار منفی |
| ۲ | `finance/wallet_service.py:453` | **هیچ** | `بدهکار − بستانکار` (معکوس) |
| ۳ | `ledger/service.py:37` | هیچ | `func.sum` خام (بدون علامت) |
| ۴ | `ecowallet/ledger.py:43` | هیچ | `float` (نه `Decimal`) |

نتیجه: `reconcile_wallet_ledger` کیف پول را با موجودیِ محاسبه‌شده با **قرارداد معکوس** مقایسه می‌کند → مغایرت کاذب روی هر حساب. افزون بر آن، `create_journal_batch` مسیر کیف پول (`wallet_service.py:469-491`) **هیچ بررسی توازنی ندارد** → دفتر نامتوازن از مسیر کیف پول قابل ساخت است.

### ۷-۳. زنجیره هش در `ledger/` وجود ندارد 🔴

ادعای docstring: «*immutable double-entry … Full audit trail with hash-chained entries*» (`ledger/service.py:1,7,38`).

واقعیت:
- `LedgerEntry` در `database/models.py:202-215` **ستون `hash` و `prev_hash` ندارد**
- `ledger/service.py:113` این ستون‌ها را می‌خواند → `AttributeError` → بلعیده در `except Exception` (`:117`) → `return False`
- **بنابراین `verify_chain()` همیشه `False` برمی‌گرداند**
- حتی اگر ستون‌ها بودند: `:54` در نوشتن هش را **با** `datetime.now(UTC).isoformat()` می‌سازد ولی `:110` در بازبینی **بدون آن**. تطابق هرگز ممکن نیست.
- `get_balance` (`:89`) مجموع قدرمطلق‌هاست و **در هر خطا `Decimal("0")` برمی‌گرداند** (`:93-95`) — خطای پایگاه داده به‌عنوان موجودی صفر گزارش می‌شود.
- `post_entry` در خطا **موفقیت‌نما برمی‌گرداند**: `{"status": "memory_only"}` (`:80-82`) — زیان حسابداری خاموش.

### ۷-۴. سیستم‌های «موفقیت جعلی» — الگوی غالب ناایمنی 🔴

| ماژول | ادعا | واقعیت |
|---|---|---|
| `backup/service.py:462,476` | نسخه پشتیبان + `verification_status="passed"` | یک خط کامنت SQL نوشته می‌شود؛ «راستی‌آزمایی» هش فایلی را که خودش نوشته با هش همان فایل مقایسه می‌کند (تحمیل‌پذیر) |
| `backup/service.py:500-508` | بازیابی | هر دو متد `pass`؛ سپس `status=COMPLETED` |
| `marketplace/traceability.py:116-119` | تأیید یکپارچگی زنجیره تأمین | هش محاسبه و **دور ریخته** می‌شود؛ `return True` |
| `ledger/service.py:80-82` | ثبت دفتر | شکست → `{"status": "memory_only"}` |
| `ecosystem/trust_score.py:91-100` | ثبت رویداد اعتماد | دیکشنری ساخته و دور ریخته می‌شود؛ `return True` |
| `ecosystem/trust_score.py:164-166` | امتیاز اعتماد | `return []` → **همه کاربران دقیقاً ۰٫۵** |
| `oracle/service.py:212-254` | تأیید داده ماهواره‌ای/عکس GPS/گواهی آزمایشگاه | بازگرداندن ثابت مثبت؛ چیزی بررسی نمی‌شود |
| `nlg.py:140-148` | پاسخ مبتنی بر شواهد | در نبود شواهد، **رکورد شاهد جعلی می‌سازد** و پرسش کاربر را به‌عنوان پاسخ برمی‌گرداند |
| `nlg.py:169` | `provider: "local-nlg"` | رشته ثابت؛ **هیچ LLMی صدا زده نمی‌شود** |
| `finance/reconciliation.py:92-112` | تطبیق سفارش/پرداخت و موجودی | `# TODO`؛ همیشه `discrepancies_count: 0` |
| `alerting/service.py:289-300` | ارزیابی و شلیک هشدار | `# This is a placeholder` → `{"fired": 0, "resolved": 0}` |
| `routers/auth.py:1044-1077` | مدیریت نشست | لیست سخت‌کد `127.0.0.1` / `Mozilla/5.0`؛ `revoke_session` **هیچ بررسی مالکیتی ندارد** و هیچ چیزی را لغو نمی‌کند |
| `routers/auth.py:1136-1149` | وضعیت نرخ محدودسازی | بازگرداندن ثابت `3 / 57 / 45` |

**این مهم‌ترین یافته این گزارش است.** در پلتفرمی که ادعای انطباق با استانداردهای OGC/IPCC/FAO و صدور گواهی کربن دارد، مسیرهای انطباق **نباید موفقیت گزارش کنند وقتی کاری انجام نشده**. این ریسک حقوقی و reputational دارد، نه فقط فنی.

### ۷-۵. عدم مجوزدهی در ماژول انطباق و توکن‌سازی 🔴

- **هر ۱۲ مسیر `routers/compliance.py` فقط `require_user` دارند** — هیچ `require_admin`، هیچ بررسی مالکیت. یعنی هر کاربر احراز‌شده می‌تواند:
  - رکورد KYC هر کاربر دیگری را بخواند (`:149`) — شامل **تاریخ تولد** (`:168-172`)
  - هر کاربری را **VERIFIED** کند (`:178`) یا **رد** کند (`:191`)
  - برای پروژه رقیب پرچم `critical` سبزنمایی بسازد (`:241`، چون `claimed_tonnes` سمت کلاینت است)
- **`routers/carbon.py:76-98`** (`POST /api/v1/carbon/tokenize`) فقط `require_user` دارد: **هر کاربر احراز‌شده می‌تواند برای هر `project_id` و هر مقدار، اعتبار کربن صادر کند.** بررسی مالکیت در `transfer` (`:101-120`) و `retire` (`:123-138`) هم وجود ندارد.
- **`kyc_aml.py:203` مقایسه لغوی روی `RiskLevel`:** مقادیر `"low"/"medium"/"high"/"critical"` به‌صورت رشته مقایسه می‌شوند → `MEDIUM > HIGH` غلط و `CRITICAL > LOW` غلط. **یافته AML با سطح CRITICAL به LOW تنزل می‌یابد.**

### ۷-۶. دور زدن کامل Step-Up Authentication 🔴

`services/security/step_up.py` (۲۷۰ خط) با ۲۵ تست اختصاصی، یکی از بهترین پیاده‌سازی‌های مخزن است: اثبات کوتاه‌عمر (۱۲۰ ثانیه)، دروازه `typ="step_up"`، اتصال به `purpose`، سقف `auth_time`، محدودیت `amr` به روش‌های قوی، `jti` تک‌مصرف.

**اما روتر آن را دور می‌زند.** `routers/passkey_router.py:162-189`:

```python
class StepUpRequest(BaseModel):
    purpose: str
    method: str            # ← سمت کلاینت
    auth_time: int | None  # ← سمت کلاینت
```

`POST /api/v1/security/step-up` فقط یک access token معتبر لازم دارد. بررسی می‌کند که `method` رشته‌ای در فهرست مجاز باشد، سپس `issue_step_up(...)` را صدا می‌زند. **هیچ TOTP، هیچ OTP، هیچ آیین WebAuthn اجرا نمی‌شود.** هر کاربر احراز‌شده می‌تواند با `{"purpose":"account.delete","method":"totp"}` یک اثبات کاملاً معتبر بسازد. زنجیره اعتماد `verify_step_up` عملاً به ادعای خود فراخوان تقلیل می‌یابد.

### ۷-۷. باگ‌هایی که ۱۰۰٪ شکست می‌خورند

| محل | نقص |
|---|---|
| `jobs/service.py:93,111` | `ComputeJob` ساخته و دور ریخته می‌شود؛ سپس **schema پاینتیک** به `db.add()` داده می‌شود → `UnmappedClassError` |
| `jobs/service.py:255-256` | `update_job_status` به متغیر تعریف‌نشده `data` ارجاع می‌دهد → `NameError` در هر فراخوانی |
| `carbon/rothc_service.py:4` | `from services.carbon.schemas import CarbonSequestrationForecast` — این کلاس **در کل مخزن وجود ندارد** → `ImportError` |
| `compliance.py:138` | `register_user(user_id, **model_dump(...))` → `TypeError: got multiple values for argument 'user_id'` |
| `provenance/router.py:179` | `Query(default_factory=dict, ...)` — `Query` چنین پارامتری ندارد → خطا در زمان ثبت مسیر |
| `marketplace/service.py:415` | `MarketplaceCommissionRule.village_id is None` **درون `.where()`** — ارزیابی پایتون → `False` → `WHERE false` → `create_order` خطای ۵۰۰ می‌دهد |
| `carbon/integration/credit_bridge.py:483` | `AsyncSession.scalar()` بدون `await` → همیشه `None` → **تشخیص شمارش مضاعف همیشه `OFF_CHAIN_ONLY`** |
| `fin/reconciliation.py` | ۲ از ۳ بررسی `TODO` است، ولی `overall_ok` گزارش می‌شود |

### ۷-۸. چندپارگی معماری داده

سه جدول `EARNING_RATES` با نام‌گذاری متفاوت (`soil_restoration` / `soil_health`)، سه تعریف نرخ کمیسیون (`commerce/service.py:81`, `marketplace/service.py:33`, جدول DB)، سه واژگان دارایی (`IRR`/`ECO`/`CARBON_tCO2e` در برابر `IRT` — که ISO 4217 آن را `IRR` می‌نویسد)، سه پیاده‌سازی escrow، دو `OutboxWorker`، دو `get_hub_service` با سیاست‌های متفاوت singleton.

**الگوی singleton بدون قفل** در ۱۰+ نقطه: `product_catalog.py:362`, `order_management.py:418`, `marketplace/service.py:468,485`, `kyc_aml.py:242`, `credit_bridge.py:552`, `traceability.py:123`, `ecowallet/ledger.py:139`, `nats_client.py:371`, `llm_router.py:314`, `embedding_service.py:298`.

خطرناک‌ترین مورد، `marketplace/service.py:468`:
```python
def get_marketplace_service(db=None):
    if _marketplace_service is None:
        _marketplace_service = MarketplaceService(db)   # db اولین فراخوان را برای همیشه قفل می‌کند
```
اگر اولین فراخوان `db=None` بگیرد، **همه فراخوان‌های بعدی سرویسی با `self.db = None` می‌گیرند** → `AttributeError` روی هر عملیات.

### ۷-۹. تزریق قیمت سمت کلاینت

`marketplace/service.py:186-189`:
```python
for item in items:
    subtotal += Decimal(str(item["price"])) * item["quantity"]
```

قیمت واحد از بدنه درخواست می‌آید، نه از `MarketplaceProduct.price`. خریدار می‌تواند `price: 1` برای محصولی با قیمت ۳۵۰٬۰۰۰ ریال بفرستد و کل مبلغ سفارش، کارمزد پلتفرم و کارمزد منظره از عدد مهاجم محاسبه می‌شود. هیچ استعلام قیمت سمت سروری وجود ندارد. **آزمون `marketplace/tests/test_integration.py:47` همین ورودی را تثبیت کرده است.**

### ۷-۱۰. هوش مصنوعی

`services/ai/` (۱٬۶۶۵ خط، **صفر آزمون**):

- **تزریق prompt:** در `unified_rag.py:206-209` محتوای اسناد بازیابی‌شده (نامطمئن) **بدون جداکننده** به‌صورت خام به پیام کاربر الحاق می‌شود. system prompt «فقط بر اساس زمینه پاسخ بده» است — توصیه‌ای، نه اعمال‌شده.
- **فقدان جداسازی مستأجر:** `add_documents`/`search` هیچ دامنه‌بندی کاربر یا مستأجر ندارند → اسناد هر کاربر برای پرسش هر کاربر دیگر قابل بازیابی است.
- **افشای اطلاعات:** استثنای خام به کاربر نهایی — `unified_rag.py:216`، `support_agent.py:188`، `admin_assistant.py:480,515`.
- **کنترل هزینه ناکافی:** شمارنده درخواست بدون حسابداری توکن یا هزینه؛ `_save()` بدون قفل (کارگرهای موازی یکدیگر را بازنویسی می‌کنند)؛ retry سه‌گانه **بیرون** حلقه سه‌ارائه‌ای → حداکثر ۱۵ فراخوانی بالادستی برای یک درخواست، بدون deadline کلی.
- **`confidentiality` RAG:** فیلتر سخت زبان در `unified_rag.py:136`؛ `_detect_language` در خط ۸۰ خطا را به `"fa"` نگاشت می‌کند → پرسش کوتاه فارسی روی اسناد انگلیسی **صفر نتیجه**.

---

## ۸. امنیت و احراز هویت

### ۸-۱. آنچه خوب است

`SpiderFirewallMiddleware` (`services/security/middleware.py`, ۳۶۵ خط) تنها بخشی است که لایه‌های دفاعی را واقعاً در مسیر درخواست مونت کرده: honeypot → ضدربات → WAF (۱۸ قاعده امضا، آستانه ۴۰) → نرخ‌محدودسازی → امتیازدهی ناهنجاری. ساختار ASGI خام، محدودیت‌ها صریحاً مستند شده، و `test_firewall_wiring.py` (۵۲۵ خط، ۳۹ تست) آن را **واقعاً** تست می‌کند — از جمله اینکه جعل `X-Forwarded-For` نتواند هویت جدید بسازد.

`auth.py` نیز در چند نقطه قوی است: `_signing_key()` (`:89-105`) کلیدهای کوتاه یا عمومی را رد می‌کند؛ `is_refresh_token_revoked` در نبود ردیف **fail-closed** است؛ چرخش refresh با `SELECT ... FOR UPDATE` در `routers/auth.py:597-608`؛ مسیر ثبت‌نام نقش مدیر را رد می‌کند (`:258-259`).

### ۸-۲. کد امنیتی نوشته‌شده اما نصب‌نشده

| فایل | خطوط | وضعیت |
|---|---|---|
| `security/ssrf.py` | ۱۰۹ | **هرگز import نمی‌شود**؛ هیچ درخواست خروجی محافظت نمی‌شود |
| `security/headers.py` | ۵۲ | **هرگز import نمی‌شود** — تنها `Content-Security-Policy` کل مخزن اینجاست |
| `security/slowloris.py` | ۱۵۹ | هرگز import نمی‌شود؛ **و منطقی هم خراب است** (`UnboundLocalError` در `:110`، اعتماد به XFF در `:60`) |
| `security/redis_rate_limit.py` | ۹۶ | هرگز import نمی‌شود؛ **و ضعیف‌تر** از `rate_limit.py` فعال (سطل بر اساس `ip:path` — همان بایپ چرخش مسیر) |
| `routers/security_router.py` | ۱۴۳ | **هرگز mount نمی‌شود** — یعنی هیچ نقطه دیدی از وضعیت امنیتی در زمان اجرا وجود ندارد |
| `privacy/vault.py` | ۲۰۹ | غیرکارکردی (بخش ۸-۴) |
| `pqcrypto.hybrid_*` | — | هرگز در مسیر امنیتی صدا زده نمی‌شود |

### ۸-۳. احراز هویت: مسیرهای باز

- **`auth_supabase.py:624-729` — ساخت حساب بدون هویت.** `GET /api/v1/auth/supabase/oauth/callback` پارامتر `mock: bool = False` را از query می‌گیرد. با `?mock=true` (یا هر زمان که Supabase در دسترس نباشد) تابع `_local_oauth_callback` ایمیل را از `code_verifier` **سمت مهاجم** مشتق می‌کند، حساب می‌سازد و **access و refresh token معتبر** برمی‌گرداند. هیچ اعتباری لازم نیست. روتر mount شده است.
- **`auth.py:289-325` — `require_admin_with_mfa` همیشه ۴۰۳.** خط ۳۱۳ روی `AsyncSession` متد همگام `.query()` را صدا می‌زند → `AttributeError` → بلعیده در `except Exception: pass` (`:316-317`). تمام روترهای ادمین وابسته به آن **دست‌نیافتنی‌اند**.
- **`require_api_key` (`:341`)** مقایسه غیرثابت‌زمان (`!=`) دارد — ناسازگار با `hmac.compare_digest` که در `security.py:252` (نسخه رهاشده) استفاده شده بود.
- **`auth.py:101` می‌تواند `RuntimeError` بدهد** → در استقرار با کلید ضعیف، هر درخواست احراز هویت ۵۰۰ می‌شود نه ۴۰۱.
- **`User.role` پیش‌فرض `"regular"`** اما `"regular"` در `ALL_ROLES` (`:66-73`) نیست → کاربر پیش‌فرض توسط `require_roles` رد می‌شود؛ `role_of` (`:349`) بی‌صدا به `farmer` تنزل می‌دهد.
- **`session_manager.py` (۱۲۹ خط) و `two_factor.py` (۴۹ خط) کاملاً مرده‌اند** — هیچ importی. `revoke_all_for_user` در `:100-126` از `KEYS "session:*"` استفاده می‌کند (الگوی ضدالگوی Redis در تولید). کدهای بازیابی TOTP با **SHA-256 بدون نمک** هش می‌شوند (`:45-49`).
- **2FA یک پرچم بولی است، نه 2FA.** `routers/auth.py:996-1038` بدون درخواست کد، رفتنی در جدول سراسری `settings` با کلید `2fa_enabled_{user_id}` می‌نویسد.

### ۸-۴. `PrivacyVault` غیرکارکردی است

`services/privacy/vault.py` (۲۰۹ خط) سه نقص مرگبار دارد:

1. `store` دو شناسه متفاوت تولید می‌کند (`:80` و `:91`) — فایل با یکی نوشته و شناسه دیگری ذخیره می‌شود → **هر بازیابی بعدی شکست می‌خورد**.
2. `retrieve` (`:135-137`) **متن رمز‌شده را به‌عنوان کلید Fernet استفاده می‌کند** → همیشه `InvalidToken`.
3. **کنترل دسترسی یک `pass` است** (`:120-122`). پارامترهای `requester_id` و `requester_role` دریافت و **استفاده نمی‌شوند**؛ لاگ همیشه `"requester": "system"` ثبت می‌کند.

**نتیجه: هیچ ذخیره‌سازی رمزگذاری‌شده off-chain کارآمدی وجود ندارد.**

### ۸-۵. `security_router` mount نشده — نقطه کور قابلیت مشاهده

`routers/security_router.py:23-42` یک طراحی واقعاً خوب دارد: `_mounted_middleware` وضعیت **زنده** `app.middleware_stack` را می‌خواند، نه پرچم‌های هاردکد — و تست رگرسیون دارد. اما هرگز در `include_router` ثبت نشده است. یعنی:
- `GET /api/v1/security/status` در دسترس نیست
- ادعای `"csp": "self + free data providers"` در `:80-86` برای اپ در حال اجرا نادرست است
- `audit.py` و `provenance/router.py` نیز mount نشده‌اند

---

## ۹. کیفیت، آزمون و CI

### ۹-۱. CI وجود دارد و قابل‌توجه است ✅

ادعای «نبود CI» نادرست است. `.github/workflows/` شامل ۶ گردش کار است:

| گردش کار | محتوا |
|---|---|
| `ci-cd.yml` (۴۴۷ خط) | Ruff lint + format، `mypy --strict` روی `settings.py` و `api_gateway/`، آزمون قرارداد (Schemathesis)، تست جهش (mutmut) با دروازه امتیاز، تست رگرسیون عددی، تست بار (Locust)، آزمون واحد با `--cov=engine --cov=services`، آزمون یکپارچه، تست مهاجرت SQLite و PostgreSQL، ساخت و push داکر، استقرار |
| `ci.yml` | فرانت‌اند: تولید نوع، lint، type-check، تست، build، E2E، i18n، Lighthouse |
| `security.yml` | gitleaks، detect-secrets، bandit |
| `cpp-build.yml`، `i18n-ci.yml`، `hydroma-slaughterhouse.yml` | تخصصی |

**نقاط ضعف مشخص:**
- **هیچ `fail_under` پوششی در کل مخزن وجود ندارد.** ادعای `--cov-fail-under=80` در `AGENTS.md` سندی است که چیزی آن را اعمال نمی‌کند.
- **پیکربندی `pytest.ini` testpaths = `services engine testing_lab tests/unit`** — یعنی اجرای `pytest` خام **۵۲ فایل و حدود ۵۰۰ تست را بی‌صدا رد می‌کند**: کل `tests/integration/` (۲۰ فایل)، `tests/contract/`، ۳۳ فایل ریشه `tests/test_*.py`، و `tests/benchmarks/`. گردش کار CI هرکدام را جدا اجرا می‌کند، پس این در CI پوشش دارد — اما اجرای محلی، تجربه گمراه‌کننده‌ای است.
- `detect-secrets` به `.secrets.baseline` ارجاع می‌دهد که در مخزن نیست → هوک در اولین اجرا شکست می‌خورد.
- `services/audit/__init__.py` خالی است، ولی `services/conftest.py:228,236` می‌کوشد `services.audit.service` را import کند — که **وجود ندارد**؛ fixture همیشه skip می‌شود.

### ۹-۲. کد مرده و تکراری

| دسته | LOC تخمینی |
|---|---:|
| کد هرگز فراخوانی‌نشده (قطعی) | ≈ ۳٬۷۰۰ |
| پیاده‌سازی موازیِ در دسترس ولی تکراری (`event_bus/*`) | ≈ ۶۳۰ |
| روترهای mount‌نشده (`security_router`, `audit`, `provenance`) | ≈ ۴۷۰ |
| **جمع** | **≈ ۵٬۱۶۶ (۶٪ کل)** |

نمونه‌های شاخص: `api_gateway/metrics.py` (۶۱۶ خط، ~۳۰ متریک، هرگز import نشده)؛ `api_gateway/security_legacy.py` (۲۵۰ خط، نسخه بایگانی‌شده‌ای که docstring خودش را «میدلورهای ارجاع‌شده در main.py» معرفی می‌کند — نادرست)؛ `api_gateway/cache/` (۹۷۳ خط)؛ `api_gateway/resilience/` (۸۵۸ خط).

**پیامد عملی:** لاگ راه‌اندازی دروغ می‌گوید (`main.py:192`)، توسعه‌دهنده در `AGENTS.md` و ADRها چیزهایی را توصیف‌شده می‌بیند که اجرا نمی‌شوند، و هر اشکال‌زدایی در کد مرده وقت تلف می‌کند.

### ۹-۳. نقض قراردادهای سبک‌کد پروژه

مواردی که **باید** `ruff check .` را در CI fail کنند اما ظاهراً پاس می‌شوند یا پیکربندی ناقص است:

- `middleware/locale.py:22` — `Optional` بدون import (F821)
- `resilience/__init__.py:128` — `Optional` تعریف‌شده ولی استفاده‌نشده (F401)
- `security.py:1` و `security_legacy.py:1` — `from __future__ import annotations` **پیش از docstring** → `security.__doc__` برابر `None`؛ ماژول بی‌مستندات است
- `metrics.py:350` — `except Exception: pass` به‌جای `contextlib.suppress` (SIM105)
- `resilience/timeout.py:155` و چند دکوراتور دیگر — `functools.wraps` جا افتاده

---

## ۱۰. ماتریس ریسک

### ۱۰-۱. ریسک بحرانی (P0 — رفع فوری)

| # | یافته | محل | اثر |
|---|---|---|---|
| ۱ | `lifespan` ثبت نشده | `main.py:142` | راه‌اندازی DB، NATS و مخزن‌ها هرگز اجرا نمی‌شود |
| ۲ | `class SafeUnpickler(pickle.Unpickler)` بدون `import pickle` | `sentinel2_provider.py:50` | **بزرگ‌ترین ارائه‌دهنده Sentinel-2 (۱٬۰۲۶ خط) و زنجیره MRV هرگز اجرا نمی‌شوند**؛ خطا بی‌صدا به «موتورها در دسترس نیستند» تبدیل می‌شود |
| ۳ | `IdempotencyMiddleware` همه را «anonymous» می‌بیند | `idempotency.py:141` | افشای پاسخ بین‌کاربری + ۵۰۰ |
| ۴ | `FinJournalEntry.account_id` (String) JOIN به `FinAccount.id` (Integer) | `models.py:242,254` | همه گزارش‌های مالی خالی؛ مغایرت کاذب روی هر کیف پول |
| ۵ | Step-Up بدون اجرای ۲FA | `passkey_router.py:162-189` | هر کاربر می‌تواند اثبات حساس بسازد |
| ۶ | `?mock=true` حساب می‌سازد | `auth_supabase.py:624-729` | ساخت حساب و نشست بدون هویت |
| ۷ | `POST /carbon/tokenize` بدون نقش مدیر | `routers/carbon.py:76-98` | هر کاربر می‌تواند اعتبار کربن صادر کند |
| ۸ | ۱۲ مسیر انطباق بدون مالکیت | `routers/compliance.py` | خواندن/تغییر KYC هر کاربر؛ ساخت پرچم سبزنمایی برای رقیب |
| ۹ | گزارش موفقیت جعلی در `backup` | `backup/service.py:462-508` | پشتیبان‌گیری و بازیابی بی‌اثر با وضعیت موفق |
| ۱۰ | `verify_chain()` همیشه `False`؛ هش وجود ندارد | `ledger/service.py:113` | ادعای تغییرناپذیری دفتر نادرست است |
| ۱۱ | `CreditBridge._get_off_chain_state` بدون `await` | `credit_bridge.py:483` | تشخیص شمارش مضاعف کاملاً کور است |

### ۱۰-۲. ریسک بالا (P1 — اسپرینت جاری)

| # | یافته | محل |
|---|---|---|
| ۱۱ | CSRF کوکی ست نمی‌شود → قفل کلاینت‌های کوکی‌محور | `csrf.py:65-67` |
| ۱۲ | `key_by_subject` و `trusted_proxies` بی‌اثر | `security.py:60,76` |
| ۱۳ | `with_resilience` بدون retry | `resilience/__init__.py:106` |
| ۱۱۴ | ۴ `LedgerService` با ۳ قرارداد علامت | `finance/`, `ledger/`, `ecowallet/` |
| ۱۵ | `jobs` ۱۰۰٪ خراب (`UnmappedClassError`، `NameError`) | `jobs/service.py:93,255` |
| ۱۶ | `rothc_service` import ناممکن | `carbon/rothc_service.py:4` |
| ۱۷ | تزریق قیمت سمت کلاینت | `marketplace/service.py:186` |
| ۱۸ | `marketplace` به مخازن `None` وصل، با لاگ «initialized» | `main.py:239-247` |
| ۱۹ | outbox نویسنده ندارد؛ backoff وجود ندارد | `integration/outbox.py`, `outbox_worker.py` |
| ۲۰ | DLQ هرگز تغذیه نمی‌شود | `eventbus/dlq.py` |
| ۲۱ | تزریق prompt + فقدان جداسازی مستأجر در RAG | `ai/unified_rag.py:206,86-160` |
| ۲۲ | `alerting.evaluate_rules` اسکلت | `alerting/service.py:289` |
| ۲۳ | `trust_score` همیشه ۰٫۵ | `ecosystem/trust_score.py:164` |
| ۲۴ | `require_admin_with_mfa` همیشه ۴۰۳ | `auth.py:313` |
| ۲۵ | `rothc.py:196` انتقال جرم ۵۴٪ را دور می‌ریزد | `scientific_motors/rothc.py:196` |
| ۲۶ | `era5_fetch` فقط نقاط انتهایی را پیمایش می‌کند | `satellite/era5_fetch.py:74` |
| ۲۷ | `land_profile` چشم‌انداز جعلی با منبع «SRTM» | `land/land_profile.py:57-78` |
| ۲۸ | آزمون ساختگی `land_capability == "III"` را تثبیت می‌کند | `land/tests/test_land_profile.py:20-22` |

### ۱۰-۳. ریسک متوسط (P2)

- `ssrf.py` نصب‌نشده → هیچ درخواست خروجی محافظت نمی‌شود؛ `anti_phishing.page_clone_signature` URL دلخواه کاربر را بدون فهرست‌سفید می‌گیرد
- تنها CSP مخزن در `headers.py` نصب‌نشده
- ۱۲ ماژول کسب‌وکار بدون آزمون
- `scientific_motors` با ۸٬۶۰۰ خط کلاس‌های علمی، **صفر آزمون عددی**
- سه فرمول LS و چهار فرمول K ناسازگار (اختلاف تا ۷٫۶ برابر)
- سه رجیستری موتور موازی با سه قالب کش ناسازگار، بدون TTL یا ابطال
- بهینه‌ساز چندهدفه روی جایگزین GP اجرا می‌شود، نه مدل واقعی
- `swat_real.py` فقط توصیف‌گر JSON می‌نویسد؛ اجرای SWAT+ انجام نمی‌شود
- ۱۰+ singleton بدون قفل
- ۱۴+ بلوک I/O همگام داخل `async def`
- ۵ الگوی N+1
- `try/except: pass` در ۲۰+ نقطه که خطا را به داده نمایشی تبدیل می‌کند
- `api_gateway` با ۳۰٪ سهم کد، ۰٫۰۰۸ نسبت آزمون
- همه ۶ fetcher در `map_engine` داده تصادفی تولید می‌کنند
- `import pickle` مرده در چهار فایل موتور → **هسته C++ عملاً به موتورهای علمی متصل نیست**

---

## ۱۱. نقاط قوتی که باید حفظ شوند

گزارش بدون این بخش ناعادلانه می‌شد. موارد زیر سرمایه‌ای هستند که نباید در انقباض کد آسیب ببینند:

1. **قرارداد «تضعیف صادقانه» در `scientific_motors/*_real.py`.** صریح‌ترین نمونه: `swat_real.py` می‌گوید «No fabricated runoff» و وضعیت `run_requires_executable` برمی‌گرداند. `hecras_real.py` تقریب Manning را صریحاً برچسب می‌زند و می‌گوید «هرگز به‌عنوان خروجی HEC-RAS ارائه نمی‌شود». `chain_runner.py:537-542` بلوک `data_sources` را به fallbackها اعتراف می‌کند و `:475` اعلام می‌کند KGE تک‌نقطه‌ای «placeholder» است. **این استاندارد باید به `services/` سراسری تسری شود.**

2. **دیوار آتش عنکبوتی.** `services/security/middleware.py` + ۱۵۵ آزمون اختصاصی در `services/security/tests/` با نسبت آزمون ۰٫۶۰ — بهترین وضعیت مخزن. آزمون‌ها مسیر واقعی را materialise می‌کنند.

3. **فرهنگ «آزمون صداقت».** `tests/unit/test_repo_honesty.py`، `test_no_altered_standards.py`، `test_formula_provenance.py` و ۹۲۶ آزمون در `engine/strict_tests/` — دقیقاً همان انضباطی که لایه سرویس به آن نیاز دارد. **ابزار موجود است؛ فقط به ماژول‌های سرویس اعمال نشده.**

4. **آزمون انطباق عددی واقعی برای رجیستری `models`.** `tests/integration/test_models_phase7.py` هشت بررسی انطباق عددی دارد (Hargreaves، حجم SCS، کران‌های van Genuchten، یکنوایی زیست‌توده، نامنفی بودن پنج استخر RothC، شوری، pedotransfer). **این دقیقاً الگویی است که `scientific_motors` باید به آن تسری یابد.**

5. **آزمون معنادار فیزیکی در `simulation`.** `services/simulation/tests/test_integration.py:103-129` آزمون می‌کند که بادشکن باید فرسایش را کاهش دهد — این آزمون «معنا» را می‌سنجد، نه فقط اجرا شدن کد.

6. **چرخش واقعی refresh token** با `SELECT ... FOR UPDATE` (`routers/auth.py:597-608`) و fail-closed بودن بررسی ابطال.

7. **مدیریت اعتبارنامه منسجم در لایه داده.** هر جا کلید نبود، وضعیت صریح برگردانده می‌شود (`configured=False`، `requires_credentials`، `unavailable`) — و **هیچ راز hardcode‌شده‌ای در کل `services/` یافت نشد.**

8. **مهاجرت‌ها و CI.** شش گردش کار واقعی شامل آزمون جهش، Schemathesis، رگرسیون عددی و آزمون مهاجرت دوسکویی.

---

## ۱۲. نقشه راه اصلاحی

### ۱۲-۱. ۴۸ ساعت — توقف جریان خون

1. `main.py:142` → `FastAPI(title=..., lifespan=lifespan)` — **یک تغییر، اثر زنجیره‌ای**
2. **`sentinel2_provider.py:50`** → افزودن `import pickle` به سطح ماژول. یک خط؛ بزرگ‌ترین ارائه‌دهنده داده ماهواره‌ای و زنجیره MRV را بازمی‌گرداند
3. ردیابی `request.state.user_id` در میدلور احراز هویت (یا انتقال کلید idempotency به `tenant_id`/توکن هش‌شده)
4. بستن ۱۲ مسیر `compliance.py` و ۳ مسیر `carbon.py` — حداقل `require_admin` + بررسی مالکیت
5. حذف پارامتر `mock` از `auth_supabase.py` یا محدود کردن آن به `app_env` سخت‌افزاری
6. اجبار TOTP/WebAuthn واقعی در `passkey_router.step_up`
7. حذف `verification_status="passed"` و `status=COMPLETED` جعلی در `backup/service.py` تا زمان پیاده‌سازی
8. ست کردن کوکی CSRF یا بازطراحی به‌جای prefix-match روی ۲۰ مسیر

### ۱۲-۲. ۲ هفته — یکپارچگی داده و علم

9. تصمیم درباره `account_id`: یا `Integer` شود، یا JOINها روی `code` منتقل شوند. سپس بازنویسی `trial_balance`، `profit_and_loss`، `reconcile_wallet_ledger`
10. یکپارچه‌سازی چهار `LedgerService` در یک، با یک قرارداد علامت
11. تصمیم درباره `ledger/service.py`: یا ستون‌های هش اضافه شود، یا ادعای «hash-chained» از docstring حذف شود
12. اصلاح `credit_bridge.py:483` (افزودن `await`) و بازنویسی آزمون تشخیص شمارش مضاعف
13. **یک کتابخانه واحد RUSLE:** یک فرمول LS، یک روش K با واحد صریح، یک آستانه کلاس‌بندی. حذف چهار نسخه موازی
14. اصلاح `rothc.py:196` (انتقال ۵۴٪ BIO→HUM) و بازکالیبراسیون
15. اصلاح `era5_fetch.py:74` (پیمایش فقط نقاط انتهایی) و `sentinel2_provider.py:292` (کلید کش هرگز مطابقت نمی‌کند)
16. پاک‌سازی outbox: حذف `RETRY_BACKOFF_BASE` یا افزودن ستون `available_at`؛ تفکیک نشانه claim از نشانه تکمیل
17. تغذیه DLQ از مسیر `nak()` در `nats_client.py:313`
18. حذف کامنت ساختگی `dem_source="SRTM"` در `land/land_profile.py:57-78` و فهرست کردن stubهای `satellite/service.py:132-168`

### ۱۲-۳. ۴ هفته — بهداشت معماری

19. **پاک‌سازی کد مرده** (≈ ۵٬۱۶۶ خط): حذف `security_legacy.py`، `metrics.py` یا اتصال واقعی آن، `cache/` یا اتصال آن، تصمیم نهایی درباره `resilience/` (ادغام با `engine/resilience.py`)، `ssrf.py`/`slowloris.py`/`redis_rate_limit.py`/`headers.py` یا اتصال یا حذف
20. mount کردن `security_router`، `audit/router.py`، `provenance/router.py` — یا حذف صریح
21. قفل روی همه singletonها؛ حذف الگوی `get_marketplace_service(db)`
22. اصلاح قیمت سمت سرور در `marketplace/service.py`
23. پاک‌سازی `except Exception: pass` — یا ثبت لاگ، یا برگرداندن خطا به‌جای داده نمایشی
24. انتقال `test_hydroma_motors.py` و `test_lcc.py` از پکیج تولیدی به پوشه `tests/` (سه آزمون تهی فعلاً از بسته تولیدی جمع می‌شوند)
25. رفع ۴۷٪ تکرار در `crop_database.py`؛ اصلاح ادعای «۳۰+ گونه» یا تکمیل پایگاه داده
26. حذف `import pickle` مرده از چهار فایل موتور — یا اتصال واقعی هسته C++
27. تصمیم درباره موازی‌سازی: یک `NATSConfig`، یک `LedgerService`، یک رجیستری موتور، یک پشته event bus
28. گسترش `MotorType` از ۶ به کل دامنه؛ حذف `mock` داخلی از روتر `map_engine/api` و اتصال `MapOrchestrator`

### ۱۲-۴. ۸ هفته — پوشش و تضمین

29. **آزمون انطباق عددی برای `scientific_motors`** — تسری الگوی `test_models_phase7.py`: حداقل ۱۰ آزمون انطباق (موازنه جرم RothC، بازه RUSLE، شرایط مرزی SCS-CN، یکنوایی LAI، رفتارهای حدی Kc…) — **این مهم‌ترین شکاف پروژه است**
30. آزمون برای هر ۱۲ ماژول صفر-آزمون کسب‌وکار (اولویت با `ledger`, `jobs`, `backup`, `alerting`, `carbon/integration`)
31. آزمون `import` برای هر ماژول تولیدی (این تست، باگ `pickle` را در ۵ ثانیه پیدا می‌کرد)
32. افزودن `fail_under` واقعی به `pyproject.toml` و دروازه سخت در `ci-cd.yml`
33. تسری الگوی `*_real.py` به کل `services/` — سازوکار نوع‌برداری واحد (`status: degraded` + `reason` به‌جای بازگرداندن داده نمایشی)
34. افزودن آزمون «صداقت» در سطح سرویس، هم‌سان `test_repo_honesty.py` — که هیچ مسیری نتواند بدون پیاده‌سازی واقعی `status=success` برگرداند، و هیچ موتوری نتواند `mock` بازگرداند بدون `data_provenance` صریح
35. رفع نقیص‌های lint/type که `AGENTS.md` وعده داده ولی `ci-cd.yml` اعمال نمی‌کند

### ۱۲-۵. یک‌ربعی — اصلاح معماری

36. یکپارچه‌سازی لایه‌بندی: قرارداد واحد `models / schemas / service / repository / router`، انتقال منطق از روترها
37. جداسازی مستأجر در RAG و در همه مدل‌های داده
38. فعال‌سازی کش با رفتار fail-open و TTL صحیح
39. بررسی معماری (ADR) برای تصمیم‌های بزرگ: وضعیت `lifespan`، مدل نشست (ADR 0002 می‌گوید کوکی opaque با حالت سمت سرور؛ پیاده‌سازی فعلی stateless است و `session_manager.py` مرده)
40. انتقال موتورهای `*_real.py` به مسیر درخواست، با قرارداد صادقانه
41. تصمیم درباره وصل کردن `MapOrchestrator` و داده واقعی جایگزین fetchers تصادفی — در غیر این صورت حذف صریح `map_engine` از ادعای «موتور نقشه»

---

## ۱۳. نتیجه‌گیری

`services/` یک پایه فنی باارزش است: ۸۶ هزار خط، دروازه API بالغ با ۷۴ روتر و زنجیره میدلور حساب‌شده، هسته امنیتی واقعاً تست‌شده، رجیستری مدل با آزمون انطباق عددی، و CI قابل‌توجه.

مسئله، **توزیع نامتوازن بلوغ** است. بلوغ در `security/`، `models/` و `simulation/` بالاست و در `jobs/`، `ledger/`، `backup/`، `alerting/`، `compliance/`، `scientific_motors/` تقریباً صفر. نتیجه، پروفایل خطرناکی است: **ماژول‌هایی که بیشترین آسیب بالقوه را در صورت خطا دارند (مالی، انطباق، پشتیبان، علم)، هم بیشترین نقص را دارند و هم کمترین آزمون و کمترین اتصال به مسیر درخواست را.**

دو الگوی ساختاری این بازنگری را قابل پیش‌بینی کرده‌اند:

**الگوی اول — «شکست بی‌صدا».** هرجا یک استثنا بلعیده می‌شود یا یک مسیر شکست می‌خورد، نتیجه یک `try/except: pass` یا یک `except Exception` است که به داده نمایشی یا وضعیت موفقیت‌نما تبدیل می‌شود. `NameError` در `sentinel2_provider` به «موتورها در دسترس نیستند» تبدیل می‌شود؛ خطای `db.add()` در `jobs` به `AttributeError` می‌رسد؛ خطای ذخیره در `ledger` به `{"status": "memory_only"}` تبدیل می‌شود. **ریشه مشترک: نبود مرز روشن بین «خطا» و «نتیجه معتبر».**

**الگوی دوم — «موازی‌سازی بدون حاکمیت».** چهار `LedgerService`، چهار انتزاع موتور، سه رجیستری، دو `NATSConfig`، سه جدول `EARNING_RATES`، سه فرمول LS و چهار فرمول K. هر کدام به‌تنهایی معقول است؛ با هم، هیچ‌کس نمی‌تواند بگوید کدام نسخه مرجع است. **ریشه مشترک: نبود یک نهاد مالک برای تصمیم‌های معماری دامنه‌ای.**

نکته مرکزی: **مسئله اصلی کد نیست، صداقت رفتار است.** مخزن در لایه علمی یاد گرفته که وقتی نمی‌تواند کاری را انجام دهد، بگوید — `swat_real` می‌گوید «No fabricated runoff»، `chain_runner` به fallbackها اعتراف می‌کند، `satellite` وضعیت `requires_credentials` برمی‌گرداند. در لایه کسب‌وکار این درس هنوز اعمال نشده — و همان‌جا که صداقت بیشترین ارزش را دارد (انطباق کربن، صدور گواهی، پشتیبان‌گیری، زنجیره تأمین، رتبه اعتماد).

خبر خوب این است که **فرهنگ لازم از قبل در مخزن وجود دارد**: `tests/unit/test_repo_honesty.py`، `test_no_altered_standards.py` و `engine/strict_tests/` دقیقاً همان انضباطی را دارند که لایه سرویس کم دارد. رجیستری `models/` هم نشان می‌دهد آزمون انطباق عددی برای موتورهای علمی **عملی است**، نه خیالی. مشکل، انتقال این دو الگوی موجود به `scientific_motors/` و ماژول‌های کسب‌وکار است — نه ساختن چیزی از صفر.

پیشنهاد روشن: **اسپرینت «صداقت و یکپارچگی»** را پیش از هر قابلیت جدیدی اجرا کنید. یازده یافته P0 فهرست‌شده، عمدتاً اصلاحات یک‌خطی یا کوچک و متمرکزند؛ هیچ‌کدام نیازمند بازطراحی نیست و دو مورد نخست (ثبت `lifespan` و افزودن `import pickle`) به‌تنهایی دو زیرساخت بزرگ را بازمی‌گردانند. اما تا زمانی که `verify_chain()` همیشه `False` برمی‌گرداند، `backup` با فایل یک‌خطی «موفق» اعلام می‌کند، و `land_profile` منبع داده را `SRTM` می‌نویسد، هر ادعای انطباق با استانداردهای بین‌المللی — که در `AGENTS.md` یک اصل معماری است — روی زمین بنا نیست.

---

*این گزارش بر پایه تحلیل ایستای مخزن در تاریخ ۲۸ شهریور ۱۴۰۵ تهیه شده است. ادعاهای بحرانی با بازخوانی مستقیم کد راستی‌آزمایی شده‌اند. برای اجرای اقلام بخش ۱۲، بررسی خط‌به‌خط هر مورد پیش از تغییر توصیه می‌شود.*
