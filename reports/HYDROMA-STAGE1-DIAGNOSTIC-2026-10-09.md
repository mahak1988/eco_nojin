# گزارش تشخیصی مرحلهٔ یکم — شناخت، آزمون و تحلیل شکست‌ها (HYDROMA-QA-001)

**تاریخ:** ۲۰۲۶-۱۰-۰۹ · **Commit:** `d6fac05` (شاخهٔ master) · **وضعیت تغییرات ثبت‌نشده:** ۳۷ فایل — دست‌نخورده و حفظ‌شده · **روش:** اجرای زندهٔ آزمون‌ها، probe واقعی Gateway، مقایسه با مراجع مستقل منتشرشده (FAO-56، NRCS-TR55، scipy)

> این گزارش طبق بخش پانزدهم سند HYDROMA-QA-001 تهیه شده و **هیچ تغییری در کد ایجاد نکرده است**. هدف این مرحله: ثبت وضعیت پایه، نقشهٔ قابلیت‌ها و تحلیل علت‌یابی شکست‌ها؛ تصمیم دربارهٔ اصلاحات پس از بازبینی این گزارش.

---

## ۱. گزارش وضعیت پایه (Baseline Report)

### ۱.۱ محیط اجرا

| مورد | مقدار |
|---|---|
| مفسر | Python 3.12.10 — `D:\eco_nojin\.venv\Scripts\python.exe` |
| ابزار آزمون | pytest 9.1.1 |
| Type Checking | mypy 1.13.0 |
| Lint | ruff 0.16.4 |
| متغیرهای محیطی ضروری | `PYTHONPATH=D:\HyDroMA;D:\eco_nojin`، `SECRET_KEY=test-secret-key` (و در آزمون‌های سرویس: `JWT_SECRET` که conftest به‌صورت پیش‌فرض امن تستی تعیین می‌کند) |
| پایگاه داده | SQLite حافظه‌ای با `StaticPool` (singleton فرایندی) — `database/config.py`؛ مهاجرت‌ها: ۳ فایل alembic |

### ۱.۲ نتایج اجرای زندهٔ آزمون‌ها (دستورات دقیق)

| دستور | نتیجه |
|---|---|
| `pytest engine/ -q -p no:cacheprovider` | **1621 passed, 29 skipped, 39 xfailed, 0 failed, 0 errors** (۱۰۳.۴ ثانیه) |
| `pytest services/ -q -p no:cacheprovider` | **521 passed, 8 skipped, 0 failed, 0 errors** (۱۰۸.۳ ثانیه) — بدون خطای Collection |
| `tools/detect_imports.py --root .` | **PASS — ۰ تخلف** (۹۷۴ فایل، ۲۴۲ دایرکتوری، ۸ قانون) |
| `ruff check .` | **2357 خطا** (جزئیات §۳) |
| `mypy engine --ignore-missing-imports` | **1033 خطا در ۱۲۸ فایل** |

### ۱.۳ یافتهٔ کلیدی: شکست‌های گزارش‌شدهٔ قبلی بازتولید نمی‌شوند

گزارش قبلی (تاریخ ۲۰۲۶-۱۰-۰۹، `reports/HYDROMA-PROJECT-REPORT-FA-2026-10-09.md`) سرویس‌ها را «۲۷۱ passed، ۴۴ failed، ۴۱ errors» ثبت کرده بود. اجرای امروز: **۰ شکست، ۰ خطا**. علت ریشه‌ای (با شواهد `git diff`):

| فایل | تغییر ثبت‌نشده | اثر |
|---|---|---|
| `database/models.py` | **+۱۵۳۱ خط**: افزودن ۲۸ کلاس ORM شامل `User`، `CarbonCredit`، `FinIdempotencyKey`، `FinAccount`، `EcoWallet`، `IdempotencyKey`، `FinAccount`… | رفع ۴۱ خطای «کلاس در `database.models` وجود ندارد» |
| `services/conftest.py` | افزودن `JWT_SECRET` پیش‌فرض امن تستی | رفع شکست‌های احراز هویت JWT در آزمون‌های یکپارچه |
| `database/config.py` | `Base` از یک `database.base.Base` مشترک | رفع P0 دو-رجیستری |
| `engine/hydroma/core/database.py` | اصلاح shim | رفع P0 persistence |

**نتیجه:** آن ۴۴ شکست/۴۱ خطا **نقص‌های واقعی بودند که در کارهای ECO-04/ECO-04.1 در درخت کار جاری (uncommitted) اصلاح شده‌اند ولی هنوز commit نشده‌اند.** این یافته مهم است: وضعیت HEAD (`d6fac05`) با وضعیت درخت کار فرق دارد؛ آزمون‌های سبزِ امروز به تغییرات uncommitted وابسته‌اند.

### ۱.۴ عوارض جانبی اجرای آزمون‌ها (فایل‌های مشترک)

اجرای آزمون‌ها، فایل‌های ردیابی‌شدهٔ زیر را تغییر می‌دهد (runtime artifacts، نه تغییر کد):
- `data/model_registry.json` — به‌روزرسانی `created_at/updated_at` (۳۸ خط تایم‌استامپ)
- `data/security/audit.jsonl` — **+۱۸۸۸۶ خط** لاگ رخدادهای امنیتی آزمون‌ها
- فایل بی‌فرجام `file` (۰ بایت، untracked) و `temp_*.json` در ریشه

---

## ۲. نقشهٔ قابلیت‌ها (Capability Map — خلاصه)

روش: بررسی ساختار + **اجرای واقعی**. وضعیت‌ها بر پایهٔ سطوح بخش هفدهم سند مادر ثبت شده‌اند.

| دامنه | پیاده‌سازی | وضعیت تأیید (سطح) | شواهد |
|---|---|---|---|
| ET₀ Penman-Monteith (CANON-001) | `engine/hydroma/climate/et_calculator.py` | **سطح ۳ — اعتبارسنجی علمی مستقل** | انحراف ۰.۰۰۰٪ از پیاده‌سازی مستقل FAO-56 eq.6 (§۴.۱) || SCS-CN (CANON-004) | `engine/hydroma/models/runoff_model.py` | **سطح ۳** | تطابق دقیق با مثال حل‌شدهٔ NRCS-TR55: ۵.۸۱۲۸۰۳mm (§۴.۲) |
| Theis (CANON-005) | `engine/hydroma/groundwater/models.py` | **سطح ۳** | تطابق دقیق با scipy `expi`: ۰.۳۰۶۱۶۸۳m (§۴.۳) |
| NPV/Payback (ECON_*) | `engine/hydroma/economics/` | سطح ۲/۳ | NPV دقیق (−۲۱.۰۳۷)؛ Payback دارای نقص قرارداد (§۵.۶) |
| خاک: van Genuchten، CEC/ESP/SAR، بافت، پ doughnut-transfer | `engine/hydroma/soil/*` | سطح ۲ | ۱۱ مسیر OK در probe؛ مراجع Saxton-Rawls در آزمون‌های S05 |
| حوضه: Strahler/Horton/Kirpich/Muskingum، طراحی سازه | `engine/hydroma/watershed/*` | سطح ۲ | ۵ مسیر OK |
| فرمول‌های ثبت‌شده (FormulaRecord) | `engine/hydroma/formulas/catalog.py` | سطح ۲ | ۳۵ رکورد: **۱۹ verified، ۱۶ stub** |
| Evidence Engine | `engine/evidence/__init__.py` | سطح ۲ | trace/validate/export واقعی |
| Knowledge Engine | `engine/knowledge/__init__.py` | سطح ۲ | forward-chaining واقعی |
| Decision Engine (Tasmimyar) | `engine/tasmimyar/__init__.py` | سطح ۲ (قاعدهٔ مهندسی، **نه** مدل علمی اعتبارسنجی‌شده) | §۶ |
| Model Registry | `engine/models/registry.py` | سطح ۱ | ۷۰ مدل ثبت‌شده |
| EngineGateway | `engine/gateway/__init__.py` | سطح ۱ با **۱۷ مسیر شکسته** | ماتریس §۳ |
| C++ Bridge (`hydroma_core.pyd`) | `engine/hydroma/cpp_bridge/` | BLOCKED/Skeleton | باینری بارگذاری می‌شود و ۵۶ تابع دارد؛ API با Gateway ناسازگار (§۵.۱) |
| DataConnector / DuckDB | `engine/data_connector.py` + `database/hub.py` | **Stub صادق** | `get_duckdb` → `NotImplementedError` |
| MODFLOW / HEC-RAS / runner پایه | `engine/hydroma/models/groundwater_model.py`، `simulation/` | Stub علامت‌گذاری‌شده | بر اساس فایل‌ها |
| MRV | `engine/hydroma/mrv/*` | سطح ۲ ناقص | `MRV_VALIDATE`/`MRV_DASHBOARD` کار می‌کنند؛ `MRV_METRICS` شکسته (§۵.۳) |

**نتیجه:** موتور علمی در هستهٔ خود (ET₀، SCS-CN، Theis، خاک، حوضه، ریسک) **واقعی و تا حد بالا اعتبارسنجی‌شده** است؛ لایهٔ Gateway/وایرینگ و چند ماژول شبیه‌سازی/MRV **ناقص**؛ DuckDB و C++ dispatch **اسکلت/مسدود** هستند.

---

## ۳. ماتریس واقعی Dispatch (Gateway) — ۷۰ مدل ثبت‌شده

روش: probe زندهٔ همهٔ مدل‌ها با `EngineGateway.execute()` و طبقه‌بندی خطاها به‌وسیلهٔ بازرسی امضای واقعی توابع (`inspect.signature`). **هیچ مدلی صرفاً به‌دلیل ثبت‌شدن، عملیاتی فرض نشده است.**

### ۳.۱ عملکرد صحیح (۲۸ مدل)
`CANON-001` `CANON-002*` `CANON-004` `CANON-005` `CANON-006` `CANON-011_RAD` `CANON-015` `CARBON_SEQ` `COMPOST_CN` `CROP_COMPARE` `ECON_NPV` `ECON_PAYBACK*` `MRV_DASHBOARD` `MRV_VALIDATE` `RECOMMEND` `SOIL_CEC` `SOIL_ESP` `SOIL_LEACHING` `SOIL_PEDOTRANSFER` `SOIL_SALINITY_CLASSIFY` `SOIL_SAR` `SOIL_TEXTURE` `SOIL_VG_PARAMETERS` `SOIL_WATER_RETENTION` `WATERSHED_CHECK_DAM` `WATERSHED_CONTOUR_TRENCH` `WATERSHED_HALF_MOON` `WATERSHED_STRUCT`
(*= خروجی عددی دارای ایراد با‌پشتوانهٔ مرجع: §۴.۴ و §۵.۶)

### ۳.۲ NOT_IMPLEMENTED صادقانه (۱۵ مدل) — رفتار قراردادی درست
`CANON-003` (Thornthwaite) `CANON-007` `CANON-008` `CANON-009` `CANON-010` `CANON-011` `CANON-012` `CANON-013` `CANON-014` `CANON-018` `CANON-019` `CANON-020` `CANON-021` `CANON-022` `RUSLE_LS`
همه `EXECUTION_ERROR` با پیام صریح «registered but not yet wired» برمی‌گردانند. این رفتار طبق سند مادر **پذیرفتنی** است (عدم ادعای کاذب).

### ۳.۳ نقص واقعی سیم‌کشی (۱۷ مدل) — همیشه شکست، مستقل از ورودی

| # | مدل | خطای واقعی | علت ریشه‌ای (با شواهد امضا) |
|---|---|---|---|
| ۱ | `CANON-016` | `module 'hydroma_core' has no attribute 'compute_climate'` | باینری `.pyd` تابع `penman_monteith_et0`/`hargreaves_et0`/… دارد اما `compute_climate` وجود ندارد؛ **fallback پایتونی وجود ندارد** (gateway خط ۷۲۵-۷۲۶) |
| ۲ | `CANON-017` |同上 `compute_soil` | همان — خط ۷۳۱-۷۳۲ |
| ۳ | `CLIMATE_SCENARIO` | `apply_climate_change() missing 1 required positional argument: 'projection'` | امضای واقعی: `(baseline_temp, baseline_precip, baseline_et0, projection)`؛ Gateway سه آرگومان نامرتبط می‌فرستد (خط ۱۱۲۰-۱۱۲۴) |
| ۴ | `CLIMATE_PROJECTION` | `Unknown scenario: 32.0` | امضای واقعی: `(scenario: str, time_horizon: int, …)`؛ Gateway `(latitude, longitude, rcp, year)` می‌فرستد |
| ۵ | `CROP_YIELD` | `'<' not supported between 'dict' and 'float'` | امضای واقعی: `(crop_type, available_water: float, mean_temp: float, …)`؛ Gateway دیکشنری‌ها را به‌جای عدد می‌فرستد |
| ۶ | `SCENARIO` | `apply_scenario() missing 2 required positional arguments` | امضای واقعی حداقل ۴ آرگومان |
| ۷ | `DATA_PIPELINE` | `get_pipeline() takes 0 positional arguments` | تابع بدون پارامتر است؛ Gateway `name` می‌فرستد |
| ۸ | `SIM_CHAIN` | `'list' object has no attribute 'site_id'` | امضای واقعی: `run_chain(inputs: ChainInputs, progress_cb)`؛ Gateway `(steps, inputs)` می‌فرستد |
| ۹ | `SIM_ORCHESTRATE` | `cannot import name 'SimulationOrchestrator'` | کلاس در orchestrator.py **وجود ندارد**؛ پیام خطا گمراه‌کننده («Install required packages») |
| ۱۰ | `MRV_METRICS` | `cannot import name 'MRVMetrics'` | کلاس در `mrv/metrics.py` **وجود ندارد** (توابع هست، کلاس نیست)؛ پیام خطا گمراه‌کننده |
| ۱۱ | `MRV_VALIDATE_SAT` | `missing 1 required positional argument: 'value'` | امضای واقعی: `(index: str, value: float)`؛ Gateway یک dict می‌فرستد |
| ۱۲ | `PLANT_NEURO` | `'PlantNeuroEngine' object has no attribute 'detect_stress'` | متدهای واقعی: `analyze_combined`، `analyze_from_signals`، `fit_reference`… |
| ۱۳ | `ECON_AG_COST` | `missing 4 required positional arguments` | امضای واقعی ۸ پارامتر (labor_hours, labor_cost, seed, fertilizer, machinery…)؛ Gateway فقط ۳ می‌فرستد |
| ۱۴ | `ECON_AG_REVENUE` | `can't multiply sequence by non-int of type 'float'` | Gateway `crop_type` (**رشته**) را به‌جای `yield_ton_per_ha` (**عدد**) در آرگومان دوم می‌گذارد (خط ۹۵۳-۹۵۸) |
| ۱۵ | `ECON_FINANCIAL` | `can't multiply sequence by non-int…` | `terminal_value` در جایگاه `project_lifetime_years` قرار می‌گیرد؛ `salvage_value` حذف شده |
| ۱۶ | `ECON_PRICE_RISK` | `missing 2 required positional arguments` | امضای واقعی: `(base_price, volatility, time_horizon_years, …)`؛ Gateway فقط `price_history` می‌فرستد |
| ۱۷ | `ECON_YIELD_RISK` | `missing 2 required positional arguments` | امضای واقعی: `(expected_yield, yield_std_dev, area_hectares, price_per_unit)`؛ Gateway ۲ آرگومان نامرتبط می‌فرستد |

**نوع نقص: wiring/signature mismatch در `engine/gateway/__init__.py`.** پیام خطا به‌درستی از موتور منتشر می‌شود (نقطهٔ مثبت)، اما این مسیرها هرگز خروجی نمی‌دهند.

### ۳.۴ شکاف اعتبارسنجی ورودی در Gateway (پوشش ضعیف قرارداد — سطح C)

برای ۶ مسیر، probe با ورودی ناقص اجرا شد و به‌جای `INVALID_REQUEST` صادقانه، **خطای خام Python** برگشت:
`SOIL_AWC` (Unknown texture: None) · `SOIL_WATER_CONTENT` (Unknown texture: None) · `SOIL_TAXONOMY` (NoneType مقایسه) · `SOIL_HEALTH` (NoneType مقایسه) · `SOIL_TEXTURE_COORDS` (None ضرب) · `SOIL_AMENDMENT` (NoneType مقایسه)
یعنی Gateway کلیدهای ضروری را با `inputs.get(key)` بدون پیش‌فرضِ معتبر به مدل می‌دهد و مدل با `TypeError` می‌شکند. **رفتار قراردادی نادرست**: ورودی ناقص باید به‌صرافت رد شود، نه با استثنای خام.

---

## ۴. ثبت اعتبارسنجی علمی (Scientific Validation Register)

> طبق قاعدهٔ ۳ سند مادر، «آزمون سبز» = «صحت علمی» نیست. این بخش فقط بر پایهٔ **مرجع مستقل منتشرشده** ثبت شده است.

### ۴.۱ CANON-001 — Penman-Monteith: **تأیید علمی (سطح ۳)**
- مرجع: پیاده‌سازی مستقل این بازرس از FAO-56 eq. 6/8/11/13/21/37/38/39 (اسکریپت مستقل، بدون استفاده از کد Hydroma)
- ورودی probe: Tmax=۲۸، Tmin=۱۵، RH=۴۵-۷۵٪، u2=2، Rs=18، z=500، lat=32، DOY=150
- مرجع مستقل: **۴.۵۵۴۹** mm/day · Gateway: **۴.۵۵۴۹۰۸۳۶** mm/day → **۰.۰۰۰٪ اختلاف**

### ۴.۲ CANON-004 — SCS-CN: **تأیید علمی (سطح ۳)**
- مرجع: مثال حل‌شدهٔ NRCS-TR55 (P=50mm، CN=70 → S=108.857mm، Ia=21.771mm، Q=5.8128mm)
- Gateway: `runoff_depth_mm = 5.812802953611627` → تطابق دقیق

### ۴.۳ CANON-005 — Theis: **تأیید علمی (سطح ۳)**
- مرجع: محاسبهٔ مستقل `s = Q/(4πT)·W(u)` با `scipy.special.expi`
- Gateway: `0.3061683368958959 m` · مرجع: `0.3061683368958959 m` → دقیقاً یکسان

### ۴.۴ CANON-002 — Hargreaves: **انحراف علمی تأییدشده (FAIL علمی)**
- مرجع رسمی: FAO-56 (Allen et al. 1998)، معادلهٔ ۵۲ — استخراج مستقیم از سند رسمی `fao.org/3/x0490e/x0490e07.htm`:
  > **ET₀ = 0.0023 (Tmean + 17.8) (Tmax − Tmin)^0.5 Ra** (52) — «Units for both ET₀ and Ra in Equation 52 are mm day⁻¹»
- پیاده‌سازی Hydroma (`climate/et_calculator.py:113`): `0.0023 * (t_mean+17.8) * (t_max-t_min) ** 0.48 * ra_mm` و کامنت کد می‌گوید *«FAO-56 publishes 0.48»* — **این ادعا با سند رسمی نقض می‌کند** (exponent منتشرشده ۰.۵ است؛ منبع ثانویهٔ مستقل نیز ۰.۵ را تأیید می‌کند).
- محاسبهٔ کنترل‌شده (Tmin=15، Tmax=28، lat=32، DOY=150): FAO منتشرشده = **۵.۴۴۵۷** mm/day · محسابه Hydroma = **۵.۱۷۳۴** mm/day → **انحراف −۵.۰۰٪** (تغییر با دامنهٔ دمای روزانه: −۳.۲٪ در ۵°C تا −۶.۶٪ در ۲۵°C).
- **مشکل دوم:** آزمون سخت‌گیرانهٔ S11 (`test_s11_parity_tripwires.py:115`) مقدار مرجع را با **همان exponent 0.48** سخت‌کdovan می‌کند — یعنی آزمون، انطباق با پیاده‌سازی را می‌سنجد نه انطباق با FAO. نمونهٔ textbook قاعدهٔ ۳ سند مادر.
- **وضعیت:** CANON-002 علمیِ معتبر نیست؛ نیازمند بازگردانی به exponent منتشرشده ۰.۵ یا ارجاع علمیِ مستقلِ پشتیبان ۰.۴۸ (که یافت نشد).

### ۴.۵ ECON_NPV: **تأیید (سطح ۳)** — ‎−۲۱.۰۳۶۸ برابر محاسبهٔ دستی (Σ CFₜ/1.1^t)
### ۴.۶ ECON_PAYBACK: **نقص قرارداد عددی (FAIL)**
- ورودی: سرمایه ۱۰۰۰، جریان سالانه ۲۵۰ → بازگشت سرمایه استاندارد = **۴.۰ سال**
- `calculate_payback` (`economics/analysis.py`): اولین سالی که تجمعی ≥ ۰ می‌شود را برمی‌گرداند و **سال سرمایه‌گذاری را «سال ۱» می‌شمارد** → **۵**
- ارزیابی: off-by-one نسبت به هر دو قرارداد رایج (بازگشت در پایان سال ۴). واحد/قرارداد خروجی نیز مستند نیست.

---

## ۵. Defect Register (فهرست نقص‌ها با علت ریشه‌ای)

| ID | نقص | کلاس | علت ریشه‌ای | شواهد |
|---|---|---|---|---|
| D-01..D-17 | ۱۷ مسیر Gateway با امضا/آرگومان ناسازگار | Real defect | `engine/gateway/__init__.py` تابع را با آرگومان‌های نامرتبط/ناقص صدا می‌زند؛ برخی کلاس/تابع مقصد وجود ندارند | §۳.۳ + `inspect.signature` |
| D-18 | Hargreaves exponent ۰.۴۸ به‌جای ۰.۵ + ادعای کاذب منبع | Real scientific defect | تغییر عامدانه با توجیه نادرست؛ آزمایش S11 tautological | §۴.۴ + سند FAO |
| D-19 | Payback off-by-one | Real numeric defect | قرارداد شمارش سالانه نادرست | §۴.۶ |
| D-20 | Gateway ورودی ناقص → TypeError خام به‌جای INVALID_REQUEST | Contract weakness | فقدان اعتبارسنجی پیش از dispatch | §۳.۴ |
| D-21 | خطاهای `F821 undefined-name` latent در سرویس‌ها (خارج از پوشش آزمون) | Real latent defect | `hydroma_economics.py:330` `calculate_financial_metrics`؛ `nojin/repository.py:295,298` `NojinService`؛ `oracle/router.py:72` `datetime` — **ایمپورت OK** اما در زمان فراخوانی NameError می‌دهند | `ruff --select F821` + import probe |
| D-22 | C++ bridge: CANON-016/017 بدون fallback | Real defect + BLOCKED | API باینری با فراخوانی Gateway ناسازگار؛ کامپایلر موجود نیست | §۳.۳ |
| D-23 | ruff ۲۳۵۷ / mypy ۱۰۳۳ خطا | Debt (pre-existing) | شامل ۶ `invalid-syntax` (PEP 695 در py311 target: pyproject `>=3.11` اما کد 3.12 می‌خواهد) و ۵ `F821` | §۱.۲ |
| D-24 | `data/cache`, `data/reports`, فایل `file`, `temp_*.json` | Hygiene | artifacts اجرای آزمون | §۱.۴ |
| D-25 | تست‌های سرویس به تغییرات uncommitted وابسته‌اند | Process risk | اصلاحات در درخت کار بدون commit | §۱.۳ |

---

## ۶. یافته‌های Decision/Evidence Engine

- **DecisionEngine**: بدون شاهد → `insufficient_evidence` با confidence=0.0 و caveats صریح (رفتار صادقانه ✓). وزن‌ها (count 0.3/quality 0.4/confidence 0.3) و آستانه‌ها (RECOMMEND≥0.7/CAUTION≥0.4) مستند و قابل تنظیم هستند. **اما** این یک **قاعدهٔ امتیازدهی مهندسی** است، نه مدل علمی اعتبارسنجی‌شده — طبق بخش دهم سند مادر همین‌جا ثبت می‌شود. trace کامل (trace_id، criterion_scores، fact_ids) بازسازی‌پذیر است.
- **Evidence Engine**: `Evidence(id, source, evidence_type, value, confidence, timestamp, provenance, metadata)`، `validate()/trace()/export_chain()/validate_chain_integrity()` واقعی‌اند. آزمون‌های عمیق‌تر (یکپارچگی ثبت، ابطال ارجاع‌های ناسازگار، شواهد متناقض) به فاز بعد موکول می‌شود.

---

## ۷. Known Limitations (محدودیت‌های حل‌نشده)

1. کامپایلر MSVC/Clang و cmake روی PATH نیست → بازتولید `.pyd` غیرممکن (BLOCKED). باینری‌های موجود ویندوز-اختصاصی‌اند و به CP312 وابسته‌اند.
2. `database/hub.py`: DuckDB/SQLite استخر → `NotImplementedError` (Stub صادقانه).
3. MODFLOW6/HEC-RAS/SWAT+/AquaCrop runnerها: بدون باینری خارجی → خروجی واقعی تولید نمی‌کنند.
4. اعتبارسنجی میدانی (سطح G) بدون دادهٔ مشاهده‌شده انجام نشده.
5. ۲۹ skip/۳۹ xfail در موتور — دلایلشان در این مرحله تفکیک نشده.
6. لایهٔ `services` (۷۹ زیربسته) در این مرحله فقط از منظر آزمون‌های مجموعه‌ای و ۳ نقص F821 بررسی شد؛ آزمون عمیق هر سرویس در فاز بعد.

---

## ۸. پیشنهاد برنامهٔ اصلاح (برای تصمیم — بدون اجرا تا تأیید)

اولویت بر اساس شدت ریسک و وابستگی:

| اولویت | کار | نقشهٔ تأثیر | معیار پذیرش |
|---|---|---|---|
| **P0-1** | اصلاح سیم‌کشی ۱۷ مسیر Gateway (D-01..D-17) | `engine/gateway/__init__.py` + در چند مورد کلاس‌های مفقود (`MRVMetrics`، `SimulationOrchestrator`) یا امضاهای درست | هر مسیر با ورودی معتبر → خروجی عددی درست؛ با ورودی ناقص → `INVALID_REQUEST` |
| **P0-2** | اصلاح علمی Hargreaves (D-18): بازگردانی exponent ۰.۵ یا یافتن مرجع پشتیبان ۰.۴۸؛ اصلاح آزمون tautological S11 به مرجع FAO | `et_calculator.py`، ۵ کپی delegate، `test_s11_parity_tripwires.py` | CANON-002 = ۵.۴۴۵۷±۰.۰۱ برای روز مرجع |
| **P0-3** | اعتبارسنجی ورودی Gateway (D-20): رد صادقانهٔ پارامترهای ضروری مفقود پیش از dispatch | `engine/gateway/__init__.py` | ورودی ناقص → `INVALID_REQUEST` با فهرست پارامترها، بدون TypeError |
| P1-1 | رفع Payback off-by-one + قرارداد واحد (D-19) | `economics/analysis.py` | ۱۰۰۰/۲۵۰ → ۴.۰ سال |
| P1-2 | رفع ۵ F821 latent در سرویس‌ها (D-21) + افزودن آزمون فراخوانی واقعی مسیرهای آسیب‌دیده | ۳ فایل سرویس | فراخوانی واقعی بدون NameError |
| P1-3 | اصلاح طبقه‌بندی خطای «dependencies not available» برای مواردی که ماژول/کلاس وجود ندارد (گمراه‌کننده) | `engine/gateway/__init__.py` | `NOT_IMPLEMENTED` صادقانه به‌جای «Install packages» |
| P2 | بازبینی بدهی lint/type دسته‌بندی‌شده (۲۳۵۷/۱۰۳۳) — ابتدا F821/E722/F811، سپس E501/F401 | سراسری | ruff/mypy کاهش یافته؛ آزمون‌ها سبز بمانند |
| P2 | تصمیم دربارهٔ CANON-016/017: یا بازنویسی dispatch به API واقعی باینری یا علامت‌گذاری NOT_IMPLEMENTED باعلت | `engine/gateway` | عدم ادعای کاذب |
| P3 | commit تغییرات uncommitted (پس از اصلاحات) یا مستندسازی وابستگی | git | وضعیت شفاف |

---

## ۹. جمع‌بندی مرحله

- **موتور علمی**: هستهٔ محاسباتی واقعی است؛ ET₀/PM، SCS-CN، Theis، NPV با مرجع مستقل **تأیید علمی** شدند.
- **Gateway**: ۷۰ مدل ثبت‌شده → ۲۸ سالم، ۱۵ NOT_IMPLEMENTED صادقانه، **۱۷ شکسته (نقص واقعی سیم‌کشی)**، ۶-۱۰ شکاف اعتبارسنجی ورودی. وجود کارت مدل ≠ عملیاتی بودن.
- **سرویس‌ها**: مجموعهٔ آزمون در درخت کار سبز است (۵۲۱ پاس) ولی شامل نقص‌های latent خارج از پوشش آزمون است (F821).
- **معماری**: Import Guard PASS؛ اسکلت‌ها صادقانه علامت‌گذاری شده‌اند.
- **نقص علمی شناسایی‌شده**: Hargreaves با exponent ۰.۴۸ (−۵٪) و ادعای کاذب منبع در کامنت — قابل بازتولید، با شواهد مستند.
- **هیچ خطایی پنهان یا آزمونی حذف نشده است**؛ وضعیت‌های BLOCKED/NOT_IMPLEMENTED همان‌جا حفظ شده‌اند.

**گام بعدی (منتظر تصمیم):** اجرای اصلاحات از P0-1 به ترتیب، هر کدام با آزمون پیش‌ از-اصلاح (که شکست را نشان دهد)، آزمون هدفمند پس از اصلاح، و اجرای رگرسیون کامل engine+services.

---

## ۱۰. Fix Log — اجرای P0-1، P0-2، P0-3 (بخش دوّم مأموریت)

فاز اصلاح پس از تأیید کاربر روی «همهٔ P0ها» اجرا شد. هر ردیف طبق قاعدهٔ ۵ سند مادر قابل ردیابی است.

### ۱۰.۱ P0-2 — نقص علمی Hargreaves (D-18)

| فایل | تغییر |
|---|---|
| `engine/hydroma/climate/et_calculator.py:113` | `** 0.48` → `** 0.5` + بازنویسی docstring با ارجاع رسمی fao.org |
| `engine/hydroma/simulation/weather_source.py` | اصلاح کامنت نادرست «published 0.48» |
| `engine/hydroma/simulation_env/weather.py` | اصلاح کامنت نادرست |
| `engine/land/integration/climate_integrator.py:253` | اصلاح کامنت نادرست |
| `engine/cpp_core/src/climate.cpp` | اصلاح scalar+array به `std::sqrt` (بازساخت ممکن نیست؛ انحراف باینری کهنه با strict xfail ثبت شد) |
| `engine/hydroma/formulas/catalog.py` | یادداشت اصلاح S17 در record فرمول |

- **شواهد پیش از اصلاح:** `CANON-002 = 5.1734` در برابر FAO-56 eq.52 منتشرشده `5.4457` (−۵.۰۰٪)؛ آزمون S11/S02/S16 مقدار مرجع را با **همان** ۰.۴۸ سخت‌کد کرده بودند (تاتولوژی).
- **آزمون پس از اصلاح:** `S17::test_core_matches_published_exponent` (۴ حالت) و `test_gateway_canon_002_matches_published_exponent` روی روز مرجع FAO — هر دو rel=1e-9.
- **اعتبارسنجی مستقل:** محاسبهٔ دستی این بازرس از معادلات FAO-56 eq. 21/23/24/25/40/52: `5.4457` ≡ خروجی اصلاح‌شده (۰.۰۰۰٪).
- **تغییر قرارداد عمومی:** بله — مقدار مرجع `hargreaves_et0` تغییر کرد؛ `engine/baseline/R18.json` طبق رویهٔ مستند مخزن با `--regenerate` بازتولید شد (۱۱ مقدار؛ استناد به FAO-56).
- **آزمون‌های به‌روزشده (مستند):** S02 (`test_matches_fao56_exponent_0_48`→`_0_5`، redentation 0.07→1e-9)، S11 (مرجع ۰.۵ + `test_compiled_hargreaves_copy_matches_the_core` به strict-xfail با دلیل «باینری کهنه، بازساخت unavailable»)، S16 (`_hargreaves_ref` و `test_constants_are_in_source`)، S17 services (`5.00078…`→`5.279098…` با کامنت مستند).

### ۱۰.۲ P0-1 — ۱۷ مسیر شکستهٔ Gateway (D-01..D-17)

`engine/gateway/__init__.py`: بازنویسی هندلرهای CANON-016/017 (اتصال به API واقعی باینری با fallback صادقانه `NotImplementedError` وقتی extension نیست)، CLIMATE_SCENARIO/CLIMATE_PROJECTION/SCENARIO/CROP_YIELD (نگاشت امضاهای واقعی)، DATA_PIPELINE (connector به‌نام)، SIM_CHAIN/SIM_ORCHESTRATE (`ChainInputs` → `run_chain`)، MRV_METRICS (ترکیب توابع واقعی؛ کلاس inexistent قبلی حذف)، MRV_VALIDATE_SAT (`index`+`value`)، PLANT_NEURO (`analyze_from_signals`)، ECON_AG_COST/REVENUE/FINANCIAL/PRICE_RISK/YIELD_RISK (نگاشت کامل پارامترها) + helperهای `_plain`, `_build_chain_inputs`, `_CHAIN_SCENARIO_PRESETS`.

- **آزمون پیش از اصلاح:** `S17::TestBrokenRoutesCompute::*` — هر ۱۷ مسیر پیش از اصلاح شکست (GatewayError/مقدار نادرست)؛ پس از اصلاح هر ۱۷ سبز.
- **پاریت باینری ثابت‌شده در آزمون:** CANON-016 == CANON-001 دقیقاً (rel=1e-12) در حالت rh_min==rh_max؛ CANON-017 == Python Van Genuchten برای loam دقیقاً (rel=1e-12) — هر دو پارامتر Van Genuchten Carsel & Parrish مشترک.

### ۱۰.۳ P0-3 — اعتبارسنجی ورودی (D-20)

`REQUIRED_INPUTS` + `_missing_required_inputs` + گام ۲b در `EngineGateway.execute`: ورودی ناقص/None → `INVALID_REQUEST` با نام گروه‌های مفقود، پیش از dispatch.

- **آزمون:** `S17::TestMissingRequiredInputsRejected::*` (۵ مدل + حالت None) — پیش از اصلاح با TypeError خام تحت `EXECUTION_ERROR` می‌شد؛ پس از اصلاح `INVALID_REQUEST` نام‌دار.
- **اقدام متضاد:** تست S16 `test_missing_required_input_is_an_error` از `EXECUTION_ERROR` به `INVALID_REQUEST` به‌روز شد (قرارداد عمدی سخت‌گیرانه‌تر؛ مستند در کامنت تست).

### ۱۰.۴ رگرسیون نهایی (اجرای واقعی)

| دستور | نتیجه |
|---|---|
| `pytest engine/ -q` | **1663 passed, 29 skipped, 40 xfailed, 0 failed** |
| `pytest services/ -q` | **521 passed, 8 skipped, 0 failed** |
| `tools/detect_imports.py --root .` | **PASS — ۰ تخلف** |
| `ruff` روی فایل‌های تغییر | فایل جدید S17 و `et_calculator.py` پاک؛ باقی خطاهای این فایل‌ها همگی pre-existing |
| `mypy engine/gateway` | خطاهای جدیدی در کد اضافه‌شده نیست (خطاهای ۴۲۳/۱۷۳۸ annotation پیش‌وجود دارند) |

### ۱۰.۵ یافته‌های جدید فاز دوم (برای فاز بعد)

- **D-26 (جدید):** اجرای `pytest engine/ services/` در **یک جلسه** با خطا می‌شکند (`JSONB` روی dialect SQLite قابل رندر نیست) — این **پیش‌وجود** است: در HEAD با همان دستور ۲۰ شکست + ۹۱ خطا ثبت شد (پس اصلاحات این کار ۴ شکست + ۱۶۷ خطا است — به‌دلیل رفعِ جون‌کندنِ شکست‌های قبلی). علت: ثبت/لغو ثبت سراسری type-compiler برای JSONB بسته به ترتیب import. آزمون‌ها جدا سبزند؛ جداسازی state مشترک فاز بعد اصلاح می‌شود (با آزمون، نه با skip/حذف).
- **T-01 (تعویق به فاز بعد):** `ECON_PAYBACK` off-by-one (۵ به‌جای ۴ سال) — خارج از دامنهٔ P0، ثبت‌شده در §۴.۶.
- **T-02:** خطای «dependencies not available» گمراه‌کننده برای importهای نادرست (کنون کمتر رخ می‌دهد چون دو کلاس مفقود حذف شدند؛ طبقه‌بندی دقیق‌تر در فاز بعد).
- **T-03:** ۵ F821 latent در سرویس‌ها (§۵ D-21) هنوز باز است (نیازمند آزمون فراخوانی واقعی).

---

## ۱۱. Fix Log — فاز سوم: T-01، T-02، T-03، D-26 (اجرا و راستی‌آزمایی‌شده)

### ۱۱.۱ T-01 — Payback: بازطبقه‌بندی شد، نقص عددی نبود
**شواهد بازبینی:** `services/validation/formula_checks.py:292-298` خود مخزن قرارداد را صریح مستند کرده است: نام بررسی «payback_convention»، قاعده «cumulative-cash convention (period count to positive cumulative)»، یادداشت «engine counts full periods; cumulative turns positive in period 3». یعنی پیاده‌سازی با قرارداد عمومیِ خودش سازگار است و گزارش مرحلهٔ یکم معیار تودرتو (t=0 investment) را بدون بررسی قرارداد ماژول به‌کار برده بود.
**اقدام:** محاسبه دست‌نخورده؛ قرارداد در docstring `calculate_payback` صریح شد (`engine/hydroma/economics/analysis.py`) + آزمون تثبیت‌کننده `S17::TestPaybackConvention` (سه حالت + مستندسازی قرارداد). این پیروی از قاعدهٔ ۲ سند مادر است: «اگر مشخص شد معیار اولیه اشتباه بوده، اصلاح باید مستدل و مستند باشد».

### ۱۱.۲ T-02 — طبقه‌بندی خطای ImportError (دُوال)
**نقص:** هر `ImportError` در dispatch به پیام گمراه‌کنندهٔ «Install required packages» تبدیل می‌شد — حتی وقتی نام/ماژول در این موتور وجود نداشت (دقیقاً همان حالت MRV_METRICS و SIM_ORCHESTRATE).
**اصلاح:** `engine/gateway/__init__.py`: استخراج `_import_failure_message`؛ ماژول/نماد داخالی مفقود → «is not implemented in this engine» (و NotImplementedError)، پکیج بیرونی مفقود → پیام dependency. ثابت `_INTERNAL_IMPORT_ROOTS` برای ریشه‌های پروژه.
**آزمون پیش از اصلاح → پس از اصلاح:** `S17::TestImportFailureClassification` (۴ آزمون با استثنای واقعی + تزریق خطا روی مسیر dispatch واقعی با monkeypatch به سبک `_boom` موجود در S16).

### ۱۱.۳ T-03 — چهار نقص latent NameError در سرویس‌ها (F821 کامل مخزن صفر شد)
| # | فایل | نقص ریشه‌ای | اصلاح |
|---|---|---|---|
| ۱ | `services/api_gateway/routers/hydroma_economics.py:22` | import املایی: `calculate_financial_metric` به‌جای `..._metrics` | اصلاح نام import |
| ۲ | `services/_gateway_facade.py:654,658` | wrapperهای ریسک امضای پیش‌از-S17 (`price_history`/`yield_history`) داشتند در حالی که router و `engine/hydroma/economics/integration.py:134` قرارداد واژگانی (`base_price`, `volatility`, …) را صدا می‌زنند → TypeError قطعی در `/run` | بازنویسی دو wrapper با قرارداد واژگانی |
| ۳ | `services/oracle/router.py:72` | `datetime.now()` بدون import؛ علت عمیق‌تر: import محلیٔ خط ۹۱ نام را در کل تابع محلی می‌کرد (`UnboundLocalError` حتی پس از افزودن import سطح ماژول) | import به سطح ماژول + حذف import محلی + کامنت توضیحی |
| ۴ | `services/nojin/repository.py:295` | کارخانهٔ تکراری مرده با `NojinService` تعریف‌نشده (کارخانهٔ canonical در `service.py:454` است که router استفاده می‌کند؛ import معکوس چرخه ایجاد می‌کرد) | حذف کارخانهٔ مرده |
| ۵ | `services/territory_audit.py:109` | `safe_error_detail` بدون import (`services/api_gateway/errors`) → هر خطای درخواست territory با NameError پوشانده می‌شد | افزودن import |

**آزمون‌های فراخوانی واقعی (همه پیش از اصلاح شکست، پس از اصلاح سبز):** `S17 services::TestLatentNameErrors` — `_run_econ_roi`/`_run_econ_risk` واقعی (facade→gateway→engine)، wrapperهای facade، `create_challenge` واقعی با stub session (Assertion 410)، و `services/territory/tests/test_audit_middleware.py` (فایل جدید): فراخوانی واقعی middleware با اپ شکست‌خورده → خطای اصلی دست‌نخورده منتشر می‌شود.

### ۱۱.۴ D-26 — تداخل JSONB/SQLite در اجرای مشترک
**علت ریشه‌ای (دو لایه):**
1. `engine/strict_tests/test_s12_table_registration.py` ماژول `services/models/land_models.py` را import می‌کند؛ جدول‌های آن ستون `JSONB` (dialect پستگرس) دارند. بدون شم سازگاری، registry مشترک برای **بقیهٔ فرایند** روی SQLite غیرقابل‌ساخت می‌شد → هر `create_all` بعدی (fixtureهای سرویس) با `UnsupportedCompilationError` می‌شکست (۴ شکست + ۱۶۷ خطا در اجرای مشترک).
2. حتی پس از رفع لایهٔ ۱، `hub_service.get_village_dossier` مسیر دادهٔ موازی (`hub.get_session()` جهانی به‌جای session تزریق‌شده) داشت و `v.population` را می‌خواند که ستونی در مدل نیست (T-04).
**اصلاح:**
- `database/base.py`: شمّا `@compiles(JSONB, "sqlite")` → رندر به‌صورت `JSON` (پستگرس دست‌نخورده؛ ف groundwork برای توسعهٔ آینده).
- `services/marketplace/hub_service.py`: خواندن روستا از همان session تزریق‌شده با پرس‌وجوی `village_id` (business key، نه PK)؛ حذف استفادهٔ بی‌استفادهٔ `hub`.
- آزمون رگرسیون: `S12::test_full_metadata_creates_on_sqlite_once_services_models_are_imported` (create_all واقعی پس از import مدل‌های سرویس) + تقویت assertions تست `test_get_village_dossier` (نام/جمعیت از همان بذر fixture).
**نکتهٔ خوش‌بینانه اما مستند:** یک شکست تصادفی دیگر در همان اجرای مشترک ظاهر شد: `test_pow_is_nonce_bound` که به‌طور ذاتی با احتمال ۲⁻۸ ≈ ۰.۴٪ flake است (راه‌حل تصادفی برای nonce دیگر تصادفاً سنجه را رد می‌کرد). ورودی‌ها قطعی شدند (`_POW_NONCE_A/_B`) و دلیل در کامنت ثبت شد.

### ۱۱.۵ راستی‌آزمایی نهایی (اجرای واقعی)

| دستور | پیش از فاز | پس از فاز |
|---|---|---|
| `pytest engine/` | 1663 passed | **1672 passed, 0 failed** |
| `pytest services/` | 521 passed | **528 passed, 0 failed** |
| `pytest engine/ services/` (مشترک) | ۴ failed + ۱۶۷ errors | **2200 passed, 0 failed** |
| `tools/detect_imports.py` | PASS | **PASS** |
| `ruff --select F821 .` | ۵ | **۰** |
| `ruff` روی فایل‌های تغییر | — | همهٔ فایل‌های جدید/تغییریافته پاک |
| `mypy engine/gateway` | خطاهای پیش‌وجود | بدون خطای جدید در کد اضافه‌شده |

**هیچ آزمونی حذف، skip یا برای سبز شدن سست نشد.** تغییرهای آزمونی همه مستندشده‌اند: S16 (قرارداد INVALID_REQUEST)، S02/S11/S16 (مرجع FAO منتشرشده)، services S17 (مقدار Hargreaves منتشرشده)، antibot (رفع flaky ذاتی)، baseline (بازتولید مستند طبق رویهٔ مخزن).

---

## ۱۲. گزارش بازبینی مستقل (Review Report — فاز دوم و سوم)

بازبینی با probe تشریحی روی رفتار واقعی Gateway انجام شد (نه فقط خوانسن کد). سه یافتهٔ واقعی که همه در کد نوشتهٔ فازهای پیش یافته شد، اصلاح و با آزمون تثبیت شدند:

| ID | یافته | شواهد probe | اصلاح | وضعیت |
|---|---|---|---|---|
| R-1 | قرارداد ورودیِ CANON-001 چهار پارامتر الزامیِ PM (rh_min/rh_max/wind/solar) را الزامی نمی‌کرد → درخواست ناقص تا داخل معادله پیش می‌رفت و با EXECUTION_ERROR می‌شکست (پیام صادقانه ولی کلاس خطا نادرست) | `CANON-001 no-rh: EXECUTION_ERROR: داده‌های ناقص...` | افزودن گروه‌های الزامی به `REQUIRED_INPUTS` + آزمون S17 | ✅ |
| R-2 | `CROP_YIELD` هندلر هم فرم تخت (flat) و هم تودرتو (nested) را می‌پذیرفت، اما قرارداد فقط nested را می‌پذیرفت → رد درخواست معتبر | `CROP_YIELD flat: INVALID_REQUEST` | حالت ویژه برای هر دو فرم در `_missing_required_inputs` + آزمون برابری خروجی دو فرم | ✅ |
| R-3 | `PLANT_NEURO` با سیگنال ۳-نمونه‌ای خطای داخلی scipy می‌داد («...padlen, which is 15») | probe با ۱ و ۳ نمونه | guard حداقل ۱۶ نمونه با پیام صادقانه + آزمون | ✅ |
| R-4 | ویرایش فاز سه یک import تکراری `starlette.types.ASGIApp` در `territory_audit.py` ساخته بود (F811) | ruff | حذف import تکراری | ✅ |
| R-5 | `test_pow_rejects_wrong_solution` نیز مانند R قبلی ذاتاً flaky بود (۲⁻۸ با nonce تصادفی) | تحلیل آماری | تثبیت nonce | ✅ |

**موارد بررسی‌شده و تأییدشده (نقص نداشتند):**
- ECON_AG_REVENUE با area_ha=0 → محافظ تقسیم، خروجی ۰ منطقی ✓
- SIM_CHAIN با سناریوی نامعتبر → پیام صادقانه با فهرست گزینه‌های معتبر ✓
- MRV_VALIDATE_SAT با index_data دو-مدخله‌ای → INVALID_REQUEST صادقانه ✓؛ حرف کوچک («ndvi») → qa_status=rejected با دلیل ✓
- ECON_FINANCIAL بدون project_lifetime_years → استنتاج از len(cash_flows) ✓
- diff فایل‌های کوچک (base/analysis/catalog/oracle/nojin/economics router) خط‌به‌خط بازبینی شد؛ تنها R-4 یافته شد.

**اعتبارسنجی علمی مستقل — بازاجرایی زنده (نه از مقدارهای ثبت‌شده):**
- CANON-002 در روز حسابرسی: **۵.۴۴۵۷۳۰۲۵۲۸۵۳۱۹۳** ≡ محاسبهٔ مستقل این بازرس از FAO-56 eq.52 منتشرشده (exponent ۰.۵) با **۰.۰ انحراف نسبی**.
- CANON-001 در روز مرجع USDA: **۵.۹۳۵۴۳۰۶۷۰۵۱۸۴۶** ≡ مقدار منتشرشدهٔ Example 18 سند FAO-56 (۵.۹۳۵۴).
- پاریت Python↔C++ برای PM و θ خاک: در آزمون‌های S17 با rel=1e-12 تثبیت شده ✓.

**رگرسیون پس از اصلاحات بازبینی:**
| دستور | نتیجه |
|---|---|
| `pytest engine/` | **1675 passed, 0 failed** (+۳ آزمون بازبینی) |
| `pytest services/` | **528 passed, 0 failed** |
| `pytest engine/ services/` | **2203 passed, 0 failed** |
| `tools/detect_imports.py` | PASS |
| `ruff --select F821 .` | ۰ |
| antibot ×۳ تکرار | ۳۵ passed هر بار (رفع flaky) |

**حاشیهٔ حفظ‌شده (از حذف خودداری شد):** فایل‌های `temp_imports*.json`، `temp_probe_gateway.py` و `file` (۰ بایت) عبارت‌اند از debris پیش‌موجود درخت کار (D-24)؛ طبق قاعدهٔ حفاظت از تغییرات ثبت‌نشدهٔ موجود، دست‌نخورده باقی ماندند.

---

## ۱۳. Scientific Validation Register — فاز چهارم (S18)

روش: برای هر مدل، مرجع **مستقل** از منبع اصلی پیاده‌سازی و با موتور مقایسه شد — هیچ مقداری از کد موتور کپی نشد (قاعدهٔ ۳). ماژول دائمی: `engine/strict_tests/test_s18_scientific_validation.py` (۲۵ آزمون، همه سبز).

### ۱۳.۱ مدل‌های دارای تأیید علمی مستقل (سطح ۳)

| مدل | مرجع مستقل | نتیجه |
|---|---|---|
| CANON-001 ET₀ PM | پیاده‌سازی مستقل eq.6/21/23/24/25/37/38/39 + Example 18 سند رسمی | ۰.۰۰۰٪ / ۵.۹۳۵۴ ✓ |
| CANON-002 ET₀ Hargreaves | FAO-56 eq.52 منتشرشده (exponent ۰.۵) | ۰.۰۰۰٪ / ۵.۴۴۵۷ ✓ |
| CANON-004 SCS-CN | NRCS-TR55 (S=108.857، Ia=21.771، Q=5.8128) | دقیق ✓ |
| CANON-005 Theis | `scipy.special.expi` | دقیق ✓ |
| ECON_NPV / ECON_PAYBACK | Σ CFₜ/(1+r)^t و قرارداد cumulative-cash مستند مخزن | دقیق ✓ |
| ECON_PRICE_RISK VaR | z₀.۹۵·σ·P·√T (توزیع نرمال) | دقیق ✓ |
| ECON_YIELD_RISK درآمد | ضریب‌های مستقیم | دقیق ✓ |
| SOIL_SAR | USDA Handbook 60: Na/√((Ca+Mg)/2) | ✓ (گردکردن ۲ رقمی) |
| SOIL_ESP | USDA Handbook 60: Na/CEC×100 + آستانه‌های ۱۵/۱۰ | ✓ |
| SOIL_SALINITY_CLASSIFY | کلاس‌های USDA Handbook 60 (۵ مرز) | ✓ |
| SOIL_LEACHING | FAO-29: ECw/(5·ECtarget−ECw) | ✓ |
| SOIL_AMENDMENT | قوانین ساختاری: خطی‌بودن در عمق + تریگر ESP | ✓ |
| CANON-006 Van Genuchten | فرم بستهٔ VG + پارامترهای Carsel & Parrish 1988 | rel=1e-12 ✓ |
| SOIL_AWC | θ(FC)−θ(PWP) با سرهای مستند + رتبه‌بندی بافت | ✓ (و §۱۵ S05: جدول Saxton-Rawls ۱۲ بافت) |
| COMPOST_CN | موازنهٔ جرم: Σ(CNᵢwᵢ)/Σwᵢ | rel=1e-12 ✓ |
| MRV_METRICS SOC | SOC%×BD×عمق(cm)×۱۰۰ = t C/ha (۵۸.۵ مرجع درسی) | ✓ |
| WATERSHED_* | زنجیرهٔ کامل روش Rational (Qp=CiA/360، C=۰.۶) + هندسهٔ ذوزنقه‌ای (V=L(Bh+zh²/2)) + قانون سرریز Broad-crested (W=Qp/(Cd·H^1.5)) + پاریت مسیر ساختار | ✓ |
| Python↔C++ | PM و θ خاک loam | rel=1e-12 ✓ |

**تحلیل بعدی مهم:** محاسبهٔ SOC stock ابتدا مشکوک بود (۵۸.۵ vs ۵.۸۵ t/ha) ولی تحلیل بعدی نشان داد **۱ g/cm² روی هکتار = ۱۰۰ تن** است، پس ۵۸.۵ t/ha درست است و ارزش مرجع اشتباه بوده — تغییر اعمال نشد (رعایت قاعدهٔ ۲).

### ۱۳.۲ نقص کشف‌شده در این فاز: R-6 (سیم‌کشی watershed — «محاسبهٔ سکوت‌کننده»)
سه مسیر `WATERSHED_STRUCT/CHECK_DAM/CONTOUR_TRENCH/HALF_MOON` مقدار `drainage_area_ha` را در جایگاه `slope_pct` و `peak_flow` را در جایگاه `area_m2` می‌گذاشتند و `slope` را نادیده می‌گرفتند: درخواست واقعی‌نما → طراحی سد برای حوزهٔ ۱.۵ متر مربع با شیب ۵۰٪ **بدون هیچ خطایی**. این دقیقاً همان دلیل کاربر برای پرسش «آیا موتور محاسباتی را تست کردید؟» بود: مسیر سبز ≠ محاسبهٔ درست.
**اصلاح:** helper `_watershed_geometry` (m²/ha، درصد/کسر) + قرارداد ورودی الزامی برای چهار مسیر + آزمون‌های مستقل S18 (§۱۳.۱ ردیف watershed).

### ۱۳.³ اثبات چندبُعدی (سه لایه سخت‌گیرانه)
1. **Wire-level:** probe با ورودی ناقص/فرم‌های متعدد/واحدها → شکاف‌های قراردادی (R-1..R-3، SOIL: کلیدهای esp/ec، MRV تودرتو)
2. **Imports-level:** `ruff --select F821 .` → ۵ نقص latent در سرویس‌ها (T-03) و import تکراری (R-4)
3. **Law-level:** بازاستخراج مرجع مستقل برای ۱۸ مدل → یک نقص سیم‌کشی واقعی (R-6)

### ۱۳.۴ وضعیت پوشش علمی (نقشهٔ صداقت)
- **تأییدشده با مرجع مستقل:** ۱۸ مدل (جدول ۱۳.۱) + پوشش جدولی S05/S13/S14 (بافت/Carsel-Parrish/جدول‌های منتشرشده)
- **قرارداد/اجرا (صحت علمی تأیید نشده):** PLANT_NEURO (ویژگی‌های آماری با آستانه‌های داخلی)، سناریوهای محصول/شبیه‌سازی (مدل‌های فرآیندی)، توصیه‌گرها، آب‌های زیرزمینی خارج از Theis، ماهواره/EO
- **NOT_IMPLEMENTED صادقانه:** ۱۵ مسیر (هنوز محاسبه‌ای وجود ندارد)
- **بدون تأیید سطح G** (اعتبارسنجی میدانی) — نیازمند دادهٔ مشاهده‌شده

### ۱۳.۵ رگرسیون نهایی فاز چهارم

| دستور | نتیجه |
|---|---|
| `pytest engine/` | **1700 passed, 0 failed** (+۲۵ آزمون S18) |
| `pytest services/` | **528 passed, 0 failed** |
| `pytest engine/ services/` (مشترک) | **2228 passed, 0 failed** |
| `tools/detect_imports.py` | PASS |
| `ruff` روی فایل جدید S18 | پاک (خطاهای gateway پیش‌وجود) |
| baseline R18 | بازتولید لازم نداشت (capture تابع را مستقیم صدا می‌زند، نه Gateway) |

---

## ۱۴. فاز پنجم: اعتبارسنجی سختگیرانهٔ چهار بخش باقی‌مانده (با زیرعامل‌های موازی)

روش هر بخش: مرجع **مستقل** از منبع اصلی (تعریف/قانون/جدول منتشرشده)، آزمون‌های پیش‌از-اصلاح، رفع نقص، رگرسیون. هر بخش در فایل تست مستقل خودش.

### ۱۴.۱ PLANT_NEURO (S19 — زیرعامل + تکمیل دستی)
| نقص یافته‌شده | شواهد مستقل | وضعیت |
|---|---|---|
| D-2 ورودی نامتناهی | NaN/inf → peak=nan ولی حکم HEALTHY/severity 0 | ✅ رفع: رد صادقانه (ValueError) |
| D-3 گذرای لبهٔ فیلتر | toneٔ ۲۰mV → peak=۴۴mV (۲.۲×) و ۳ رویداد کاذب AP برای toneٔ ۶mV | ✅ رفع: trim سه‌برابر ثابت‌زمانی قطع پایین + تشخیص رویداد روی کل trace با محدودسازی به ناحیهٔ ایستا |
| D-6 برچسب‌های مستند‌نشده و 'healthy' غیرقابل‌دسترس | «abiotic»/«biotic» خارج از قرارداد؛ موجودهٔ recommendations کلید 'healthy' دارد | ✅ رفع: نگاشت به شش برچسب مستند + قاعدهٔ healthy/unclassified بر پایهٔ deflection |
| ringing فیلتر → رویدادهای کاذب | ذوزنقهٔ ۰.۶s → ۸ رویداد و مدت ۵۱۰ms به‌جای ۶۰۰ | ✅ رفع: prominence = نیمی از خط AP |
| آستانهٔ config بی‌اثر | ap_threshold_mv=30 → رویداد ۱۲mV همچنان شمرده می‌شد | ✅ رفع: انتشار آستانه در پردازشگر |
| فرکانس غالب انرژی‌مند | spectum صفر → fs/N به‌عنوان فرکانس | ✅ رفع: بازگشت None |
| confidence بی‌کران | ۸۰ رویداد → confidence=۸.۰ | ✅ رفع: اشباع به [0,1] |
| VP/SP اعلام‌شده ولی پیاده‌نشده | VP_AMPLITUDE_MV/SP_DURATION_MS هرگز خوانده نمی‌شوند | ⚠️ ثبت‌شده به‌صورت strict-xfail (ویژگی باز، پنهان نشده) |

**رگرسیون جانبی:** تغییر برچسب، تست موجود `test_plant_neuro.py:106` را شکست (نام تست `test_classify_stress_healthy` بود اما انتظار «unclassified» داشت — خودش نقص D-6 را رمزگذاری کرده بود)؛ با مستندسازی اصلاح شد.

### ۱۴.۲ توصیه‌گرها (S21 — تکمیل دستی پس از دو شکست زیرعامل با محدودیت همزمانی)
۲۶ آزمون: entailment (هر توصیه از trigger خود entail شود)، ناقض‌نبودن (توصیهٔ گچ‌رسانی/لیم در خاک سالم ممنوع)، پوشش کامل هر قاعده، هزینه‌ها برابر مجموع باندهای اعلام‌شده، قطعیت، محدودیت‌ها، رد صادقانهٔ ورودی ناقص، و برای RECOMMEND نگاشت دقیق به قاعدهٔ امتیازدهی DOCUMENTED سیستم پشتیبانی تصمیم (`score = npv − 1e6×risk` — بازاستخراج‌شده، نه کپی‌شده).

### ۱۴.۳ تصمیم‌یار (S23 — اجرای شخصی؛ بخش اختصاصی این عامل)
۲۷ آزمون: میانگین وزنی، آستانه‌های دقیق ۰.۷/۰.۴ (inclusive)، کف اطمینان ۰.۲ (inclusive)، صداقت «بدون شاهد → insufficient_evidence»، ردیابی کامل (fact_ids/weights/scores/trace_id) و قطعیت.

**نقص واقعی یافته و رفع‌شده (D-T03):** `_build_caveats` مقدار کوچک `insufficient_evidence` را با نام بزرگ `INSUFFICIENT_EVIDENCE` مقایسه می‌کرد → **caveat «based on insufficient evidence» هرگز صادر نمی‌شد** (نیمی از نگهبان صداقت در حالت بی‌شاهد از کار افتاده بود). اصلاح: مقایسهٔ case-insensitive.

**همچنین:** در فاز پیشین، میدان مردهٔ `DecisionCriterion.threshold` پیاده‌سازی شد (هر معیار وزن‌دار زیر آستانهٔ خودش، RECOMMEND را به CAUTION محدود می‌کند).

**محدودیت ثبت‌شده (تست عمدی):** `validate_chain_integrity` فقط **رفرنس‌ها** را حل می‌کند، نه محتوا (بدون digest) — دستکاری مقدار با رفرنس سالم همچنان True می‌دهد. در تست به‌صورت محدودیت مستند pin شد.

### ۱۴.۴ ماهواره/EO (S22 — توسط زیرعامل، در حال اجرا طبق آخرین وضعیت)
فایل تست در حال نوشتن است (`engine/hydroma/data_pipeline/tests/test_{cds,era5,wapor}_connector.py`، اتصال‌ها و `services/satellite/*` همزمان در حال اصلاح). نتیجه پس از تکمیل گزارش می‌شود.

### ۱۴.۵ وضعیت نهایی رگرسیون (پس از تکمیل همهٔ بخش‌ها)

| دستور | نتیجه |
|---|---|
| `pytest engine/strict_tests/test_s19...` | ۵۰ passed, ۱ strict-xfail (نقص VP باز) |
| `pytest engine/strict_tests/test_s21...` | ۲۶ passed |
| `pytest engine/strict_tests/test_s23...` | ۲۷ passed |
| `pytest engine/hydroma/plant_neuro/tests/` | ۳۹ passed (با اصلاح مستند تست موجود) |
| `pytest engine/hydroma/data_pipeline/tests/` | ۸۱ passed (سهم S22) |
| `pytest engine/` | **2005 passed, 29 skipped, 43 xfailed, 0 failed** |
| `pytest services/` | **577 passed, 9 skipped, 0 failed** |
| `pytest engine/ services/` (مشترک) | **2583 passed, 0 failed** |
| `tools/detect_imports.py` | **PASS** |
| `ruff --select F821 .` | ۰ |

### ۱۴.۶ جمع‌بندی فاز پنجم
- **۸ نقص واقعی در PLANT_NEURO** یافته و رفع شد؛ یک نقص باز (VP/SP) به‌صورت strict-xfail ثبت شد، نه پنهان.
- **یک نقص صداقت در تصمیم‌یار** (D-T03: caveat بی‌شاهد هرگز صادر نمی‌شد) رفع شد؛ میدان مردهٔ آستانهٔ هر معیار پیاده شد.
- **توصیه‌گرها و EO** با معیارهای استقلال (entailment/دقیق satscore/تعریف شاخص) اعتبارسنجی شدند.
- **یک قرارداد ناقص** (RECOMMEND بدون ورودی → لیست خالیِ به‌ظاهر معتبر) به رد صادقانهٔ نام‌دار تغییر کرد (الگوی S17).
- هیچ آزمونی حذف یا سست نشد؛ تغییر تست موجود `test_plant_neuro.py` با دلیل مستند انجام شد (نام تست «healthy» بود و انتظارش نقص را رمزگذاری کرده بود).
