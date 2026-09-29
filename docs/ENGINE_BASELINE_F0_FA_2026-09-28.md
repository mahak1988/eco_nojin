# خط پایهٔ اندازه‌گیری — فاز صفر

**تاریخ اجرا:** ۱۴۰۵/۰۷/۰۶ · **سند مرجع:** `docs/ENGINE_ACTIVATION_PLAN_FA_2026-09-28.md` فاز صفر
**هدف:** ثبت سه عددی که بدون آن‌ها بستن هر تیکتی غیرقابل اثبات است. «۱۰۸ → ۱۰۷» تنها وقتی پیشرفت است که بدانیم هیچ‌چیز دیگری نشکسته.

---

## ۰. منشأ اندازه‌گیری

| مورد | مقدار |
|---|---|
| commit پایه | `5d8e98b` روی شاخه `main` |
| **وضعیت درخت کاری** | **کثیف** — ۳۱۵ مسیر تغییریافته + ۳۰۰ مسیر untracked (۹۵ مسیر داخل `engine/`) |
| پایتون | 3.12.10-final · win32 · venv محلی |
| C++ | `hydroma_core` کامپایل‌شده، `cpp_available=True` |
| وابستگی‌های غایب | `flopy`، `gpytorch`، `xrspatial`، `optuna`، `mlflow`، `dvc` |
| دستور | `--benchmark-disable` برای F0.3 |

> ⚠ **این اعداد فقط در برابر همین وضعیت درخت کاری بازتولیدپذیرند، نه در برابر HEAD.** درخت کاری ۳۱۵ فایل از commit پایه فاصله دارد. پیش از هر مقایسه، این را در نظر بگیرید یا روی یک commit تمیز تکرار کنید.

---

## ۱. F0.1 — خط پایهٔ `strict_tests`

```
916 collected · 808 passed · 108 xfailed · 0 failed · 52 warnings · 173.02s
```

**منبع: `reports/f0_1_strict.xml`** (مرجع، چون خروجی ترمینال در شکست‌های طولانی قابل اتکا نیست)

### توزیع تیکت‌ها بر حسب ماژول

| ماژول | تست | xfail | نرخ |
|---|---:|---:|---:|
| `test_s08_irrigation.py` | ۳۲ | **۱۴** | **۴۳٫۸٪** |
| `test_s03_hydrology_runoff.py` | ۴۷ | ۱۲ | ۲۵٫۵٪ |
| `test_s05_soil_retention.py` | ۸۱ | ۱۹ | ۲۳٫۵٪ |
| `test_s06_watershed_design.py` | ۱۱۱ | **۲۵** | ۲۲٫۵٪ |
| `test_s04_groundwater.py` | ۴۲ | ۹ | ۲۱٫۴٪ |
| `test_s11_parity_tripwires.py` | ۴۴ | ۵ | ۱۱٫۴٪ |
| `test_s07_carbon.py` | ۱۱۱ | ۱۲ | ۱۰٫۸٪ |
| `test_s02_climate_et0.py` | ۶۶ | ۵ | ۷٫۶٪ |
| `test_s13_soil_table.py` | ۴۷ | ۲ | ۴٫۳٪ |
| `test_s10_property_invariants.py` | ۳۷ | ۱ | ۲٫۷٪ |
| `test_s01_import_integrity.py` | ۲۳۴ | ۴ | ۱٫۷٪ |
| `test_s00_baseline.py` | ۱۵ | ۰ | ۰ |
| `test_s09_dimensional_consistency.py` | ۲۱ | ۰ | ۰ |
| `test_s12_table_registration.py` | ۱۶ | ۰ | ۰ |
| `test_s14_published_table.py` | ۱۲ | ۰ | ۰ |
| **جمع** | **۹۱۶** | **۱۰۸** | **۱۱٫۸٪** |

### خوانش این جدول

- **`s08` با ۴۳٫۸٪ بالاترین نرخ را دارد** — از ۳۲ تست، ۱۴ تیکت باز است. `irrigation/scheduler.py` کوچک است (۱۷ عبارت) ولی **نزدیک نیمی از رفتارش بدون قرارداد اعتبارسنجی است.** ارزان‌ترین جای برای بستن ۱۴ تیکت.
- **`s06` بیشترین تعداد مطلق را دارد (۲۵)** — `watershed/calculator.py` ۷۵۰ خطی با طراحی مهندسی. بیشترین کار، ولی `T-16` (بازسازی Brune) به‌تنهایی چند تیکت را می‌بندد.
- **۱۰۸ تیکت، ۶۸ شناسهٔ یکتا** — یعنی ۴۰ مورد پارامتری‌اند (مثل `[0.0]`، `[-1.0]`، `[50.0]`) که یک اصلاح کد می‌بندد. **تعداد «موارد کار» واقعی نزدیک ۶۸ است، نه ۱۰۸.**
- **۴ ماژول صفر تیکت** (`s00`, `s09`, `s12`, `s14`) — این‌ها الگوی موفق‌اند. `s12` ثبت جداول و `s14` مسیر بستن جدول خاک را می‌آزمایند و هر دو سبزند.

### فهرست کامل تیکت‌ها
`reports/f0_1_xfail_ids.txt` (۶۸ شناسهٔ یکتا) · دلیل کامل هر کدام: `reports/f0_1_xfail_raw.txt`

---

## ۲. F0.2 — پوشش واقعی موتور

```
$ pytest engine/strict_tests --cov=engine
statements : 22508
covered    :  9589
missing    : 12919
PCT        :  37.56%
branches   :   723 / 4944   (14.6%)
```

**منبع: `reports/f0_2_coverage.json` · خلاصهٔ بسته‌ای: `reports/f0_2_coverage_summary.json`**

> **ادعای `AGENTS.md:84` و `docs/frontend/TESTING.md:30` مبنی بر ≥۸۰٪ پوشش، با ۳۷٫۵۶٪ واقعی، ۴۲ واحد دور است.** این عدد مربوط به `strict_tests` به‌تنهایی است؛ اجرای کل مجموعهٔ `tests/unit` عدد بالاتری می‌دهد، ولی `engine` در آن اجرا **پوشش چندانی اضافه نمی‌کند** (بیشتر تست‌های `engine` تودرتو هستند و در `tests/unit` نیستند).

### سلسله‌مراتب پوشش — و اینکه چرا باگ D8 زنده ماند

| بسته | عبارت‌ها | پوشش | |
|---|---:|---:|---|
| `engine/land/terrain_analysis.py` | ۲۶۸ | **۸٫۲٪** | ██ |
| `engine/land/drainage.py` | ۱۸۲ | **۸٫۲٪** | ██ |
| `engine/land/surface_water_analysis.py` | ۱۲۳ | **۱۱٫۴٪** | ██ |
| `engine/land/capability.py` | ۶۶ | **۷٫۶٪** | █ |
| `engine/hydroma/optimization` | ۹۵ | ۱۴٫۷٪ | ███ |
| `engine/safe_math.py` | ۱۱۷ | ۱۶٫۲٪ | ████ |
| `engine/hydroma/data_pipeline` | ۹۶۱ | ۱۷٫۶٪ | ████ |
| `engine/hydroma/climate_adaptation` | ۹۳۴ | ۱۹٫۵٪ | ████ |
| `engine/hydroma/hybrid_ml` | ۵۰۱ | ۲۲٫۴٪ | █████ |
| `engine/hydroma/soil` | ۹۵۰ | ۲۳٫۳٪ | █████ |
| `engine/hydroma/biofertilizer` | ۲۱۶۹ | ۳۱٫۴٪ | ███████ |
| `engine/hydroma/data_assimilation` | ۲۹۴ | ۲۹٫۳٪ | ███████ |
| `engine/hydroma/economics` | ۳۶۶ | ۳۰٫۶٪ | ███████ |
| `engine/hydroma/plant_neuro` | ۳۴۷ | ۳۳٫۴٪ | ████████ |
| `engine/hydroma/cpp_bridge` | ۴۵۷ | ۳۴٫۶٪ | ████████ |
| `engine/hydroma/mrv` | ۴۳۴ | ۴۴٫۹٪ | █████████ |
| `engine/hydroma/models` | ۱۹۳۵ | ۴۱٫۹٪ | █████████ |
| `engine/hydroma/simulation` | ۷۴۵ | ۳۹٫۱٪ | █████████ |
| `engine/land/erosion_risk.py` | ۱۵۸ | ۶۴٫۶٪ | ███████████████ |
| `engine/hydroma/formulas` | ۹۳ | ۶۸٫۸٪ | ██████████████ |
| `engine/hydroma/config` | ۳۷۲ | ۷۰٫۷٪ | ███████████████ |
| `engine/data` | ۲۵۷ | ۷۷٫۰٪ | ████████████████ |
| `engine/baseline` | ۲۵۵ | ۷۸٫۸٪ | ████████████████ |
| `engine/hydroma/alembic_graph.py` | ۹۷ | ۸۵٫۶٪ | █████████████████ |
| `engine/hydroma/carbon` | ۹۴ | ۸۷٫۲٪ | █████████████████ |
| `engine/hydroma/climate` | ۸۹ | **۹۵٫۵٪** | ███████████████████ |
| `engine/hydroma/watershed` | ۲۳۹ | **۹۶٫۷٪** | ███████████████████ |
| `engine/strict_tests` | ۲۹۱۳ | ۹۷٫۴٪ | ███████████████████ |

**این جدول، رابطهٔ علّی را نشان می‌دهد:**

پوشش بالا ↔ کیفیت بالا. `climate` با ۹۵٫۵٪ و `watershed` با ۹۶٫۷٪ دو ماژولی هستند که گزارش تحلیلی آن‌ها را قوی خواند. `land/terrain_analysis` و `land/drainage` با **۸٫۲٪** دو ماژولی هستند که **بزرگ‌ترین نقص علمی موتور را در خود دارند.** پوشش ۸٪ یعنی تقریباً هیچ مسیر خطایی اجرا نمی‌شود، پس هیچ تستی نمی‌تواند آن را بگیرد.

**یعنی باگ D8 نادیده نگرفته نشد — اصلاً قابل دیدن نبود.**

### ۱۶ فایل کاملاً بدون پوشش (بیش از ۲۰ عبارت)

| فایل | عبارت |
|---|---:|
| `engine/hydroma/soil/tests/test_soil.py` | ۳۴۴ |
| `engine/hydroma/biofertilizer/tests/test_nojin_comprehensive.py` | ۲۸۱ |
| `engine/land/integration/tests/test_climate_integrator.py` | ۲۲۸ |
| `engine/land/tests/test_land_comprehensive.py` | ۲۰۳ |
| `engine/land/integration/tests/test_water_adapter.py` | ۱۶۴ |
| `engine/land/tests/test_land_improved.py` | ۱۵۹ |
| `engine/land/integration/tests/test_soil_integrator.py` | ۱۳۸ |
| `engine/land/integration/tests/test_comprehensive_analyzer.py` | ۸۸ |
| `engine/hydroma/biofertilizer/tests/test_nojin_calculator.py` | ۸۱ |
| `engine/hydroma/groundwater/tests/test_service.py` | ۷۴ |
| `engine/land/tests/test_slope.py` | ۷۳ |
| `engine/land/integration/tests/test_motors_hub.py` | ۶۵ |
| `engine/land/tests/test_models.py` | ۶۰ |
| `engine/land/tests/test_terrain.py` | ۴۹ |
| `engine/land/tests/test_capability.py` | ۳۶ |
| `engine/hydroma/biofertilizer/tests/conftest.py` | ۲۲ |

> **این ۱۶ فایل همگی فایل تست‌اند و همگی ۰٪.** یعنی `strict_tests` آن‌ها را اجرا نمی‌کند (چون فقط `engine/strict_tests` را هدف گرفته). **پوشش ۳۷٫۵۶٪ فقط تصویر «موتور تحت آزمون سخت‌گیرانه» است، نه کل موتور.** برای عدد واقعی باید F0.2 دوباره با کل `engine` اجرا شود — که همان کاری است که جاب F1 انجام خواهد داد.

### پرتفاوت‌ترین شکاف‌ها (بر حسب عبارت پوشش‌نیافته)

| عبارت | پوشش | فایل |
|---:|---:|---|
| ۷۳۱ | ۱۱٫۴٪ | `hydroma/data_pipeline/pipeline.py` |
| ۴۲۸ | ۱۴٫۸٪ | `biofertilizer/advanced_calculator.py` |
| ۲۷۱ | ۲۶٫۱٪ | `biofertilizer/repositories.py` |
| ۲۴۶ | **۶٫۰٪** | `land/terrain_analysis.py` |
| ۲۳۶ | **۶٫۳٪** | `land/integration/climate_integrator.py` |
| ۲۲۴ | ۱۴٫۴٪ | `hybrid_ml/gp_surrogate.py` |
| ۲۲۰ | ۲۴٫۰٪ | `biofertilizer/calculator.py` |
| ۲۰۸ | ۲۴٫۰٪ | `data_assimilation/assimilation.py` |
| ۲۰۴ | **۹٫۱٪** | `climate_adaptation/seed_optimization_engine.py` |
| ۱۸۸ | ۱۷٫۶٪ | `distributed_ml/trainer.py` |

---

## ۳. F0.3 — تست‌های تودرتوی موتور

```
$ pytest engine/land engine/hydroma/*/tests  (8 مسیر)
2 failed · 432 passed · 9 skipped · 6 warnings · 38.09s
```

### شکست‌های پایدار (۲)

| تست | ریشه |
|---|---|
| `cpp_bridge/tests/test_benchmarks.py::TestTelemetryBenchmarks::test_telemetry_overhead` | `cpp_calls == 1` انتظار دارد، ولی ۱۰۰۰ عنصر زیر آستانهٔ `1e6` به Numba می‌رود |
| `data_pipeline/tests/test_gbif_connector.py::TestGBIFConnector::test_fetch_checklist_country` | `asset_id` الگوی `gbif_species_list_IR_…` است و رشتهٔ `checklist` ندارد |

### یافتهٔ مهم: یک تست **flaky** است

`land/integration/tests/test_climate_integrator.py::test_integration_time_reasonable` در **اجرای اول** شکست خورد و در **اجرای دوم** پاس شد:

| اجرا | نتیجه |
|---|---|
| اول (بدون `--benchmark-disable`) | ۳ شکست — شامل `test_integration_time_reasonable` |
| دوم (با `--benchmark-disable`) | ۲ شکست — بدون آن |

**علت قطعی:** `climate_integrator.py:474,484` یک فراخوانی زندهٔ HTTP به `archive-api.open-meteo.com` با `timeout=10.0` دارد، و تست ادعای `< 5000ms` می‌کند. یعنی **این تست به سرعت شبکهٔ عمومی وابسته است و ذاتاً ناپایدار است.**

> این نه یک نقص، بلکه **یافتهٔ فاز صفر** است: آن ۳ شکستی که برنامه ثبت کرده بود، در واقع **۲ شکست پایدار + ۱ ناپایدار** است. بدون اجرای دوباره، برنامه یک شکست غیرقابل بازتولید را در فهرست کار قرار می‌داد. این دقیقاً همان چیزی است که فاز صفر باید بگیرد.
>
> جاب F1.6 (حذف شبکهٔ زنده از تست) این را به‌طور دائمی حل می‌کند.

### هشدارهای سازنده که کار می‌کنند

چهار سطر مورد مناقشهٔ جدول خاک **دقیقاً مطابق طراحی** هشدار دادند:

```
PhysicsWarning: soil texture 'clay': saturated conductivity 4.80 cm/day is disputed -
its neighbours must bracket it between 0.00 and 1.92. Conductivity cannot rise with
texture fineness. The value is served because callers depend on it, but it is a
design assumption, not a transcription. See engine/data/SOIL_TABLE_CONFLICTS.md,
and close it with: python -m engine.data.apply_published_table --from <published.csv>
```

**این دقیقاً رفتاری است که `physics_guard.py` برایش طراحی شده بود:** سطر را برمی‌گرداند (چون فراخوان‌ها به آن وابسته‌اند)، صادقانه برچسب می‌زند، و دستور بستن را می‌دهد. **سازوکار کار می‌کند — فقط در سطح `warning` است و در سرور خاموش می‌شود.**

### هشدار مهم دربارهٔ موازی‌سازی

```
NumbaPerformanceWarning: The keyword argument 'parallel=True' was specified
but no transformation for parallel execution was possible.
  test_benchmarks.py:275  @jit(nopython=True, parallel=True)
```

**این تأیید مستقلِ یافتهٔ گزارش تحلیلی است:** `README_STATUS_FA.md:106-112` می‌نویسد *«آیا `/openmp:llvm` واقعاً موازی می‌کند یا فقط پذیرفته می‌شود: تأییدنشده.»* این هشدار نشان می‌دهد **موازی‌سازی Numba در کد تست اصلاً فعال نیست**، و نتایج بنچمارکِ `test_ndvi_vs_numba` از چیزی که ادعا می‌کند ضعیف‌تر است.

---

## ۴. خلاصهٔ خط پایه

| شاخص | مقدار | منبع |
|---|---:|---|
| تست‌های `strict_tests` جمع‌شده | ۹۱۶ | `reports/f0_1_strict.xml` |
| پاس‌شده | ۸۰۸ | همان |
| **تیکت باز (`xfail`)** | **۱۰۸** (۶۸ شناسهٔ یکتا) | `reports/f0_1_xfail_ids.txt` |
| شکست‌خورده | ۰ | — |
| **پوشش `engine` توسط `strict_tests`** | **۳۷٫۵۶٪** | `reports/f0_2_coverage.json` |
| پوشش شاخه | ۱۴٫۶٪ (۷۲۳/۴۹۴۴) | همان |
| تست‌های تودرتو | ۴۳۲ پاس · ۲ شکست · ۹ skip | بخش ۳ |
| فایل‌های ۰٪ (≥۲۰ عبارت) | ۱۶ — همگی فایل تست | بخش ۲ |
| بدترین پوشش تولیدی | `land/terrain_analysis.py` ۶٫۰٪ · `land/drainage.py` ۸٫۲٪ | بخش ۲ |
| بالاترین نرخ تیکت | `test_s08_irrigation.py` ۴۳٫۸٪ | بخش ۱ |

### شاخص‌هایی که از این به بعد در هر PR گزارش می‌شوند

```
xfail            : 108 → هدف ≤ 10        (تخفیف ۹۱٪)
strict in CI     : 0/916 → هدف 916/916
engine coverage  : 37.56% → هدف ≥ 60%     (و بالاتر، با اجرای کل engine)
C++↔Python parity: 4.71% → هدف 0%
```

---

## ۵. دو تصمیمی که این فاز ایجاب کرد

**۱. عدد پوشش را کجا تنظیم کنیم.**
عدد واقعی `strict_tests` ۳۷٫۵٪ است. اگر جاب F1 فقط `engine/strict_tests` را اجرا کند، عدد کل موتور بالاتر خواهد بود چون تست‌های تودرتو هم اجرا می‌شوند. **توصیه:** در جاب F1 هر دو مسیر را اجرا کنید، عدد واقعی را اندازه بگیرید، و `fail_under` را روی `عدد − ۲` بگذارید. **تنظیم مستقیم روی ۸۰، جاب را قرمز می‌کند و تیم آن را غیرفعال خواهد کرد** — و غیرفعال‌سازی دروازه، دقیقاً همان شکافی است که این برنامه برای بستنش طراحی شده.

**۲. آن ۱۶ فایل تست با پوشش ۰٪.**
این‌ها فایل تست‌اند که `strict_tests` اجرا نمی‌کند. دو حالت دارند:
- **واقعاً ارزشمندند** (`test_soil.py` با ۳۴۴ عبارت، `test_nojin_comprehensive.py` با ۲۸۱) ← باید به جاب CI اضافه شوند
- **میلهٔ پوشش را پایین می‌آورند بدون ارزش افزوده** ← باید از محاسبهٔ پوشش مستثنا شوند (`omit`)

**پیشنهاد:** `engine/land/tests/` و `engine/land/integration/tests/` را نگه دارید و وارد جاب کنید (چون دقیقاً همان جایی هستند که باگ D8 زنده مانده)، ولی ابتدا تست‌های `isinstance`-محور و `or`-دیسjunction را اصلاح کنید — وگرنه ۴۳۲ تست پاس می‌دهند بدون آنکه چیزی را بسنجند.

---

## ۶. مصنوعات تولیدشده

| فایل | محتوا |
|---|---|
| `reports/f0_1_strict.xml` | خروجی junit مجموعهٔ `strict_tests` — مرجع F0.1 |
| `reports/f0_1_xfail_ids.txt` | ۶۸ شناسهٔ یکتای تیکت باز |
| `reports/f0_1_xfail_raw.txt` | دلیل کامل هر ۱۰۸ تیکت (با `file:line` و بزرگی خطا) |
| `reports/f0_2_coverage.json` | گزارش خام پوشش — مرجع F0.2 |
| `reports/f0_2_coverage_summary.json` | خلاصهٔ بسته‌ای + فهرست فایل‌ها |

**دستور تکرارپذیری:**
```powershell
.venv\Scripts\python.exe -m pytest engine/strict_tests -q -p no:cacheprovider --tb=no `
    --junitxml=reports/f0_1_strict.xml
.venv\Scripts\python.exe -m pytest engine/strict_tests -q -p no:cacheprovider --tb=no `
    --cov=engine --cov-report=json:reports/f0_2_coverage.json
.venv\Scripts\python.exe -m pytest engine/land engine/hydroma/cpp_bridge/tests `
    engine/hydroma/soil/tests engine/hydroma/watershed/tests engine/hydroma/biofertilizer/tests `
    engine/hydroma/groundwater/tests engine/hydroma/plant_neuro/tests `
    engine/hydroma/data_pipeline/tests -q -p no:cacheprovider --tb=no -rf --benchmark-disable
```

---

## ۷. وضعیت فاز صفر

| # | کار | وضعیت |
|---|---|---|
| F0.1 | خط پایهٔ `xfail` | ✅ **۸۰۸ پاس · ۱۰۸ تیکت · ۰ شکست · ۱۷۳ ثانیه** |
| F0.2 | پوشش واقعی موتور | ✅ **۳۷٫۵۶٪** (ادعای ۸۰٪ رد شد) |
| F0.3 | تست‌های تودرتو | ✅ **۴۳۲ پاس · ۲ شکست پایدار · ۹ skip** — و یک تست ناپایدار شناسایی شد |
| — | مصنوع خط پایه | ✅ همین سند + ۵ فایل در `reports/` |

**فاز صفر کامل شد.** گام بعدی: **فاز یک** — نصب `strict_tests` در CI، که بدون آن هیچ‌یک از این اعداد پس از فردا قابل مقایسه نخواهد بود.
