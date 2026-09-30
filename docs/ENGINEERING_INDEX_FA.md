# نمایهٔ مستندات فنی
## Eco Nojin · مهاجرت و بازبینی معماری

این فایل **نقطهٔ ورود** است. پیش از آن، هشت سند در چهار پوشه پراکنده بودند و
هیچ‌کدام به بقیه ارجاع نمی‌دادند.

همهٔ اسناد این فهرست **وضع موجود** را توصیف می‌کنند. هیچ‌کدام برنامهٔ آینده نیست.

---

## ۱. ممیزی و برنامه

| سند | چه چیزی |
|---|---|
| [`reports/TECHNICAL_AUDIT_FA_2026-09-25.md`](../reports/TECHNICAL_AUDIT_FA_2026-09-25.md) | ممیزی ۲۸ یافته‌ای بک‌اند و موتور |
| [`reports/REMEDIATION_PLAN_FA_2026-09-25.md`](../reports/REMEDIATION_PLAN_FA_2026-09-25.md) | برنامهٔ هفت‌موجی، ۱۸ محور ادغام |
| [`reports/WAVE_3_INTEGRATION_PLAN_FA_2026-09-26.md`](../reports/WAVE_3_INTEGRATION_PLAN_FA_2026-09-26.md) | موج ۳: ادغام، ۱۸ محور با اندازه‌گیری تازه |
| [`reports/WBI_Q1_Q2_PLAN_FA_2026-09-26.md`](../reports/WBI_Q1_Q2_PLAN_FA_2026-09-26.md) | Q1 و Q2 شاخص WBI |
| [`reports/OPEN_ITEMS_FA_2026-09-26.md`](../reports/OPEN_ITEMS_FA_2026-09-26.md) | مشخصات دو قلم باز، برای تصمیم مشترک |

## ۲. وضع موجود موتور

| سند | چه چیزی |
|---|---|
| [`engine/cpp_core/README_BUILD_STATUS_FA.md`](../engine/cpp_core/README_BUILD_STATUS_FA.md) | هستهٔ بومی: چگونه ساخته می‌شود، چه چیزی هست و چه چیزی نیست |
| [`engine/hydroma/cpp_bridge/README_STATUS_FA.md`](../engine/hydroma/cpp_bridge/README_STATUS_FA.md) | پل، گزینش backend، و یک بارگذار |
| [`engine/hydroma/formulas/README_STATUS_FA.md`](../engine/hydroma/formulas/README_STATUS_FA.md) | دفترچهٔ فرمول: وضعیت هر کمیت |

## ۳. مراجع کد

| مسیر | چه چیزی |
|---|---|
| [`engine/hydroma/formulas/records.py`](../engine/hydroma/formulas/records.py) | شکل رکورد: منشأ از وضعیت جداست |
| [`engine/hydroma/formulas/registry.py`](../engine/hydroma/formulas/registry.py) | چهار قاعدهٔ اعمال‌شده |
| [`engine/hydroma/formulas/catalog.py`](../engine/hydroma/formulas/catalog.py) | رکوردها |
| [`engine/hydroma/formulas/research/`](../engine/hydroma/formulas/research/) | **تعریف تحقیقاتی** سهم‌های پژوهشی |
| [`engine/hydroma/models/validation/loader.py`](../engine/hydroma/models/validation/loader.py) | بارگذار مجموعهٔ اعتبارسنجی |
| [`engine/hydroma/models/validation/runner.py`](../engine/hydroma/models/validation/runner.py) | تفکیک «عدم تطابق کد» از «مورد ناسازگار» |
| [`engine/cpp_core/build_pybind.bat`](../engine/cpp_core/build_pybind.bat) | ساخت ماژول بومی |
| [`engine/cpp_core/build_tests.bat`](../engine/cpp_core/build_tests.bat) | ساخت آزمون‌های بومی، هسته یک‌بار |
| [`scripts/run_cpp_tests.py`](../scripts/run_cpp_tests.py) | دروازهٔ آزمون بومی |
| [`scripts/run_tests.py`](../scripts/run_tests.py) | اجرای هر دو مجموعه |
| [`scripts/doc_coverage.py`](../scripts/doc_coverage.py) | گزارش پوشش مستندات |
| [`tests/db_support.py`](../tests/db_support.py) | بازنشانی مستقل‌از‌ترتیب شِما |

## ۴. سه تمایز که همهٔ اسناد بر آن تکیه می‌کنند

این سه، ستون فقرات مستندات این کار هستند. اگر یکی از آن‌ها رعایت نشود، سند
بی‌ارزش می‌شود.

### ۴.۱ منشأ در برابر وضعیت

| منشأ (`provenance`) | چیست |
|---|---|
| `standard` | نتیجهٔ منتشرشده |
| `composite` | عوامل منتشرشده، **ترکیب از آنِ ماست** |
| `novel` | **سهم پژوهشی این پروژه** |

| وضعیت (`status`) | چیست |
|---|---|
| `verified` | لنگرها برقرارند و آزمون‌ها می‌گذرند |
| `divergent` | دو پیاده‌سازی اختلاف دارند |
| `stub` | بی‌استفاده یا اثبات‌نشده |

**قاعده:** فرمول `novel` بدون `research_definition` **رد می‌شود**. نوآوری بدون
تعریف، قابل بازبینی و بازتولید نیست.

**قاعده:** فرمولی که ضریب بی‌منبع دارد **نباید `verified` علامت بخورد** — چون
آن ادعا بیش از آنچه می‌دانیم است. آزمون این را در کد اعمال می‌کند.

### ۴.۲ استاندارد دستکاری‌شده، سهم پژوهشی نیست

سه دسته وجود دارد و تصمیمشان یکسان نیست:

| دسته | تصمیم |
|---|---|
| استاندارد | ارجاع و آزمون بماند |
| سهم پژوهشی | تعریف تحقیقاتی نوشته شود |
| **استاندارد دستکاری‌شده** | **تغییر برداشته شود** — استاندارد بازگردانده می‌شود، بازاستخراج نه |

نمونهٔ دستهٔ سوم: `core.py` ضریب `×0.10` را روی RUSLE اعمال می‌کرد — کمیتی
منتشرشده که ده برابر تقسیم شده بود. این نوآوری نیست؛ قرض‌گرفتن اعتبار از منبعی است
که آن را تعریف نمی‌کند.

### ۴.۳ سند، وضع را توصیف می‌کند نه آرزو را

قاعدهٔ سخت: «کار خواهد شد»، «در آینده»، «هدف» — در سند وضع موجود نمی‌آید.
هر عدد از اجرای کد می‌آید یا صریحاً با «اندازه‌گیری نشده» علامت می‌خورد.

---

## ۵. پوشش مستندات — عدد، نه ادعا

بررسی پوشش در `tests/unit/test_documentation_coverage.py` اجرا می‌شود و
`scripts/doc_coverage.py` آن را گزارش می‌کند.

| سنجه | عدد |
|---|---:|
| اسناد مورد انتظار، موجود | ۹ از ۹ |
| ماژول‌های افزوده، با docstring | ۱۲ از ۱۲ |
| اسکریپت‌های ساخت، با سربرگ توضیحی | ۲ از ۲ |
| کلاس‌های محاسبه‌گر ثبت‌نشده در دفترچه | **۰** |
| stub بدون دلیل | **۰** (فیلد `stub_reason` اجباری است) |
| آزمون‌های واحد | **۹۰۴ پاس، ۱۱ رد‌شده** |
| بررسی بومی | **۲۳۷ موفق، ۱ ناموفق** |

**آنچه آگاهانه ثبت نشده و نباید ثبت شود:**

`ModelRegistry`، `SQLiteCache`، `SimulationController`، `ScientificModel` (کلاس
انتزاعی)، `ValidationResult`، `HYRUEParams`، `DroughtScenario`، `GlobalWatchdog`،
`ClimateFetcher`، `ScientificCalculator`.

این‌ها معادله نیستند. ثبتشان همان خطایی است که نخستین survey مرتکب شد وقتی حدود
۲۰ قلم را در یک سطل ریخت.

**وضعیت ۱۶ stub** — هر کدام در `stub_reason` خود می‌گوید چه چیزی کم است. مهم‌ترین‌ها:

| کمیت | چه کم است |
|---|---|
| `modflow6_groundwater_flow`، `swatplus_watershed` | `ModelOutput` هرگز import نمی‌شود ⇒ `NameError` |
| `saint_venant_1d` | باقی‌ماندهٔ حفاظت ۱۰۲٪ در B=10 |
| `wbi_water_bankruptcy` | ۷ از ۸ عامل بی‌منبع؛ ادعای ۸۰٪ بدون artifact |
| `climate_adaptation_stress_engine` | ~۲۵ قاعده بدون جدول ارجاع |
| `rothc_temperature_modifier` | فرم تأیید شد؛ **مخرج** تأییدنشده |

**شکاف شناخته‌شده:** خانوادهٔ `engine/hydroma/climate_adaptation/` حدود **۲۵ قاعدهٔ
شماره‌گذاری‌شده** (`h01`…`h25`) دارد که `REFERENCES` ندارد و چهار کلاسش بدون
docstring است. این یک بدهی مستندسازی است و در
`reports/OPEN_ITEMS_FA_2026-09-26.md` ثبت شده، نه اینکه پنهان بماند.

---

## ۶. اجرای آزمون‌ها

```bash
python scripts/run_tests.py            # هر دو مجموعه
python scripts/run_tests.py --unit     # فقط پایتون
python scripts/run_tests.py --native   # فقط بومی
```

### ۶.۱ سرعت — اعداد اندازه‌گیری‌شده

| مجموعه | قبل | بعد |
|---|---:|---:|
| بومی | چند دقیقه | **۴۴ ثانیه** |
| پایتون (تک‌worker) | ۱۰۰ ثانیه | ۱۰۰ ثانیه |
| پایتون (۸ worker) | — | **۸۸ ثانیه** |

**دو واقعیت که باید گفته شوند و نه پنهان:**

1. بهبود بومی واقعی و بزرگ است. `build_tests.bat` اکنون هسته را **یک‌بار** به‌صورت
   کتابخانهٔ استاتیک می‌سازد و هر آزمون را به آن لینک می‌کند؛ پیش از آن، هر ۱۳ فایل
   آزمون هر ۱۱ منبع هسته را دوباره کامپایل می‌کرد.
2. **بهبود پایتون فقط ۱۳٪ است و علتش زمان‌بندی نیست.** مجموعه چند آزمون گران دارد تا
   ۱۲٫۶ ثانیه، نه تعداد زیادی آزمون ارزان؛ و آن آزمون‌ها کار رمزنگاری و I/O
   می‌کنند که موازی نمی‌شود. توزیع per-test (`--dist load`) آزمایش شد و از per-file
   بهتر نیست. برای بهبود بیشتر باید خودِ آزمون‌های کند اصلاح شوند، که کار جداست.

### ۶.۲ دو اشکال که آزمون‌ها را ناپایدار می‌کردند و رفع شدند

1. **آزمون بومی نوسانی بود.** `dam break: mass conserved within 2%` در حدود نیمی از
   اجراها شکست می‌خورد. علت یک **data race** در `saint_venant.cpp` بود: چهره‌های مرزی از
   درون حلقهٔ موازی در متغیرهای اسکالر نوشته می‌شدند و شمارندهٔ سلول‌های خشک‌شده همان‌جا
   increment می‌شد. ایزوله‌سازی: تک‌نویس ۸/۸ پاس، چندنویسی ۴/۸. اکنون چهره‌ها per-cell
   ثبت و شمارنده‌ها کاهش OpenMP‌اند — **۱۰/۱۰ قطعی**.
2. **جمع‌آوری آزمون می‌شکست.** `admin_users.py` و `admin_content.py` از `class Config`
   استفاده می‌کردند که Pydantic v2 منسوخ کرده، و pytest هشدار را به خطا تبدیل می‌کرد.
   بسته به ترتیب import، یا شش فایل هنگام جمع‌آوری می‌افتادند. چهار مورد به
   `model_config = ConfigDict(...)` تبدیل شد. **این نقص پیش از این کار وجود داشت.**

### ۶.۳ نوسانی‌بودن باقی‌مانده

دو آزمون `test_blockchain.py` تنها پاس می‌شوند ولی در اجرای کامل گاهی ۴۰۴ می‌دهند —
**جداسازی آزمون**، و هنوز رفع نشده است. همین‌طور آزمون‌های دفترچهٔ فرمول وضعیت سراسری را
تغییر می‌دادند و بازنمی‌گرداندند؛ فیکسچر بازگردانی اضافه شد.
