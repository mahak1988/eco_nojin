# تحقیق و تست عمیق موتور محاسباتی و مدل‌های `engine/` — Eco Nojin / HyDroMa

**تاریخ:** ۲۰۲۶-۰۹-۲۱ · **مسیر:** `D:\eco_nojin\engine` · **روش:** بازخوانی کد + استخراج معادلات + تطبیق با منابع مرجع + اجرای واقعی تست‌ها.

---

## ۱. اندازه و مبنای واقعی

| سنجه | مقدار |
|---|---|
| حجم موتور | **۵۵٬۶۸۱ خط** در ۶۹ زیرشاخه |
| هستهٔ C++ | ۱۰ هدر + ۱۰ سورس + ۲۵ فایل تست/بنچمارک + `nojin_calculator` |
| زیرماژول‌های پایتون | ۴۳ زیرشاخه (`soil`, `climate`, `watershed`, `carbon`, `mrv`, `models`, `simulation`, `biofertilizer`, `plant_neuro`, `groundwater`, `optimization`, …) |
| اجرای واقعی تست | **۷۷۹ پاس · ۲۳ رد · ۱۳ skip** (`pytest engine testing_lab tests/unit`) |
| از این تعداد، مرتبط با موتور | فقط **۴** رد: `test_soil` (۱) و `test_groundwater_phenology` (۳) |

> ⚠️ نکتهٔ ساختاری: `pytest.ini` مقدار `testpaths = services` دارد، بنابراین تست‌های موتور **در CI پیش‌فرض اجرا نمی‌شوند**. یعنی ۷۷۹ تست سبز موتور عملاً خارج از دروازهٔ کیفیت است.

---

## ۲. مدل‌هایی که با استاندارد تطبیق داده و **تأیید شدند**

| مدل | فایل | استاندارد مرجع | نتیجهٔ تطبیق |
|---|---|---|---|
| **Richards ۱بعدی (فرم مختلط + Picard اصلاح‌شده)** | `cpp_core/include/hydroma/richards.hpp` + `src/richards.cpp` | Richards 1931؛ Celia et al. 1990؛ van Genuchten 1980 | ✅ صحیح: `C(h)∂h/∂t = ∂/∂z[K(h)(∂h/∂z+1)]`، حجم محدود سلول‌مرکز، اویلر پس‌رو، تکرار Picard جرم‌پایدار |
| **Saint-Venant ۱بعدی** | `saint_venant.hpp/.cpp` | de Saint-Venant 1871؛ Toro 2001 (Rusanov/Lax-Friedrichs)؛ Chow 1959 (Manning) | ✅ صحیح: شار Rusanov + اصطکاک Manning + CFL؛ گزارش بستن جرم در `mass_balance` |
| **FAO-56 Penman-Monteith (ET0)** | `hydroma/climate/et_calculator.py:175-178` | FAO-56 (Allen et al. 1998) | ✅ **دقیقاً منطبق**: `[0.408ΔRn + γ·(900/(T+273))·u2·(es−ea)] / [Δ + γ(1+0.34u2)]` |
| **ضرایب دوگانهٔ Kc + بیلان ریشه** | `cpp_core/crop_water.hpp/.cpp` | FAO-56 (1998)؛ Allen et al. 2005 | ✅ منطبق: `Dr,i = Dr,i−1 − (P−RO) − I + ETc + DP`، `ETc = (Kcb·Ks + Ke)·ET0`، TEW/REW، `f_w` |
| **RUSLE** | `cpp_core/src/erosion.cpp` | USDA AH-703 (Renard 1997)؛ McCool 1987؛ Renard & Freimund 1994 | ✅ صحیح: `S=10.8sinθ+0.03` (<9%) و `16.8sinθ−0.50` (≥9%)؛ `β=(sinθ/0.0896)/(3sin^0.8θ+0.56)`، `m=β/(1+β)`، `L=(λ/22.13)^m`؛ `R=0.04830P^1.61` (P<850) و `587.8−1.219P+0.004105P²`؛ Kها مطابق جداول USDA |
| **Kirpich (Tc)** | `watershed/calculator.py:431` | Kirpich 1940 (فرم متریک) | ✅ `Tc = 0.0195·L^0.77·S^−0.385` |
| **Muskingum (مسیریابی)** | `watershed/calculator.py:461` | Chow 1959 | ✅ `C0=(−Kx+0.5Δt)/D`, `C1=(Kx+0.5Δt)/D`, `C2=(K−Kx−0.5Δt)/D`, `D=K−Kx+0.5Δt` |
| **روش منطقی رواناب** | `watershed/calculator.py:31` | Rational method | ✅ صحیح + **بلوک LIMITATIONS مستند شده** (محدودهٔ اعتبار < ۱ km²، کالیبراسیون لازم) |
| **جدول van Genuchten** | `soil/water_retention.py` → `SOIL_PARAMETERS_VG` | Carsel & Parrish 1988 | ✅ مقادیر C&P صحیح (loam: θr=0.078, **θs=0.43**, α=0.036, n=1.56) |
| **ثابت‌های RothC-26.3** | `simulation/runners/rothc_runner.py:23-36` | Coleman & Jenkinson 1996 | ✅ `DPM 10 / RPM 0.3 / BIO 0.66 / HUM 0.02`؛ مُدیفایر دما `47.9/(1+e^(106.06/(T+18.27)))`؛ مُدیفایر رطوبت دومُدیِ SMD؛ `IOM=0.049·SOC^1.139`؛ تقسیم بقایا `0.59/0.41` (=DPM/RPM 1.44)؛ `P=0.6`؛ واپاشی نمایی `1−e^(−kΔt)` |

---

## ۳. نقص‌های کشف‌شده (به ترتیب شدت)

### 🔴 D1 — SCS-CN: اختلاط واحد اینچ/میلی‌متر ⇒ بیش‌برآورد ~۸ برابری رواناب
**فایل:** `engine/hydroma/models/runoff_model.py:102-122`
```python
s = (1000 / cn) - 10  # ← فرم اینچی
initial_abstraction = 0.2 * s
runoff_depth_mm = (precipitation_mm - initial_abstraction) ** 2 / (precipitation_mm + 0.8 * s)
```
`P` بر حسب **میلی‌متر** داده می‌شود ولی `S` با فرم اینچی ساخته می‌شود. فرم صحیح SI: `S = 25400/CN − 254` [mm].
**عدد شاهد:** CN=70، P=50 mm → کد: `Q=45.2 mm`؛ استاندارد: `Q=5.8 mm` ⇒ **≈۷.۸× بیش‌برآورد**. برای سیل/آبخیزداری این خطا مستقیم به ابعاد سازه‌ها منتقل می‌شود.

### 🔴 D2 — RothC: پارتیشن وابسته به رس حذف و با ثابت ۰.۴۶ جایگزین شده ⇒ بیش‌برآورد ترسیب کربن
**فایل:** `engine/hydroma/simulation/runners/rothc_runner.py:25-28, 56-61, 102-105`
- استاندارد RothC-26.3: `x = 1.67·(1.85 + 1.60·e^(−0.0786·%clay))` و نسبت `CO2/(BIO+HUM) = x` ⇒ سهم پایدارشده معمولاً **۱۵–۲۴٪** (مثلاً رس ۲۳٪ → ۲۲٪).
- کد: `X_STAB = 0.46` (۴۶٪ پایدارشده) و **مستقل از رس**؛ این عدد از معادلهٔ RothC هیچ‌گاه حاصل نمی‌شود (بیشینهٔ نظری ≈۰.۲۵).
- پیامد: نفس‌کشی کمتر از مقدار استاندارد و پایداری بیشتر ⇒ **بیش‌برآورد SOC و اعتبار کربن**.
- همچنین `initial_pools(initial_soc_t_ha, clay_pct)` پارامتر `clay_pct` را **هرگز استفاده نمی‌کند** (پارامتر مرده).
- ⚠️ نکتهٔ صداقت: خودِ فایل صراحتاً می‌گوید «pending reference validation» — که خوب است — اما عدد ۰.۴۶ باید اصلاح یا مستند شود.

### 🔴 D3 — ECSI: عنوان «بر پایهٔ RothC-26.3» با پیاده‌سازی ناهمخوان
**فایل:** `engine/hydroma/models/ecsi.py`
| جزء | استاندارد RothC | پیاده‌سازی ECSI | اثر |
|---|---|---|---|
| مُدیفایر دما | `47.9/(1+e^(106.06/(T+18.27)))` (≈1.10 در ۱۰°C) | `e^(0.047T−0.86)` (≈0.68 در ۱۰°C) | واپاشی ~۱.۶× کمتر |
| مُدیفایر رطوبت | تابع SMD دومُدیِ | `clip(R/E·(1−clay),0,1)` | متفاوت و اشباع‌شونده |
| نسبت CO2/(BIO+HUM) | `1.67·(1.85+1.60e^(−0.0786·clay))` | `1.67+1.94·clay` **و اصلاً در `compute` استفاده نمی‌شود** | پارتیشن حذف شده |
| واپاشی | نمایی `1−e^(−kΔt)` | خطی `k·C·Δt` | برای DPM (k=10) ~۵× بیش‌برآورد |
| IOM | `0.049·SOC^1.139` | ثابت `POOL_FRACTIONS["IOM"]=0.38` برای همهٔ خاک‌ها | ناسازگار |
**جمع‌بندی:** ECSI یک شاخص ساده‌شده است، نه پورت RothC؛ ارجاع به Coleman & Jenkinson (1996) در docstring بیش‌ادعاست و ریسک حسابداری کربن ایجاد می‌کند. (سه مسیر کربن موازی: `ecsi.py`، `rothc_runner.py`، `carbon/calculator.py`.)

### 🔴 D4 — هستهٔ کامپایل‌شدهٔ C++ در زمان اجرا **بارگذاری نمی‌شود**
**شاهد اجرایی:**
```
from engine.hydroma.cpp_bridge import hydroma_core
→ ImportError: generic_type: type "WaveParameters" is already registered!
```
- فایل‌های `hydroma_core.cp311-win_amd64.pyd` و `cp312-win_amd64.pyd` موجودند اما import شکست می‌خورد (ثبت تکراری نوع در pybind11 / احتمالاً `.pyd` کهنه و ناهمخوان با سورس جاری — کلاس `WaveParameters` در هدرهای فعلی وجود ندارد).
- `cpp_bridge/__init__.py:51-53` فقط `logger.warning` می‌زند و **بی‌صدا** به fallback پایتون می‌رود.
- پیامد: ادعای «بیندینگ pybind11 ساخته و از پایتون تأیید شد» (DELIVERY README) **در وضعیت فعلی برقرار نیست**؛ عملکرد واقعی = پیاده‌سازی پایتون/Numba. تست‌های C++ (۷۰/۷۰) هم بدون کامپایل مجدد قابل بازتولید نیستند (هیچ `.exe` تست ساخته‌شده‌ای روی دیسک نیست).
- نکتهٔ مثبت: bridge تلِمتری `fallback_calls` دارد؛ اما این وضعیت degrade باید در `/health` و metrics دیده شود، نه فقط یک warning در لاگ.

### 🟠 D5 — نیاز آبشویی (Leaching Requirement): ضریب ۵ حذف شده + کلمپ جعلی
**فایل:** `engine/hydroma/soil/salinity.py:149-190`
- استاندارد FAO (Ayers & Westcot 1985 / Rhoades 1974): **`LR = ECw / (5·ECe − ECw)`**
- کد: `lr = ec_water / (target_ec - ec_water)` ⇒ **بدون ضریب ۵** ⇒ بیش‌برآورد شدید (مثال: ECw=1, ECe=4 → کد 0.33، استاندارد 0.053 ⇒ **~۶×**).
- سپس `lr = min(0.5, max(0.1, lr))` ⇒ **کف ۰.۱ تحمیل می‌کند**؛ یعنی حتی وقتی نیاز ناچیز است «۱۰٪ آب اضافه» گزارش می‌شود = تولید عدد بی‌پایه (نقض سیاست no-fabrication خودِ پروژه).
- `target_ec = 4.0` به‌عنوان «هدف بیشتر محصولات» پیش‌فرض گرفته شده؛ ۴ dS/m آستانهٔ *طبقه‌بندی* خاک شور است، نه هدف محصولی (آستانه‌ها محصول‌به‌محصول‌اند: FAO-29).

### 🟠 D6 — مدل آب زیرزمینی: ورودی `recharge_mm` هیچ اثری ندارد
**فایل:** `engine/hydroma/groundwater/models.py:53`
```python
recharge = max(inputs.soil_water_mm * inputs.rcoeff, 0.0)  # inputs.recharge_mm استفاده نمی‌شود
```
- تست `test_zero_recharge_drains_storage` با `recharge_mm=0` انتظار تهی‌شدن مخزن دارد؛ اما مدل همیشه از `soil_water×rcoeff` شارژ می‌سازد ⇒ **پارامتر مرده/گمراه‌کننده**.
- اصلاح: `recharge_mm` به‌عنوان شارژ صریح اولویت بگیرد و `soil_water×rcoeff` فقط به‌عنوان fallback (یا حذف فیلد از API).

### 🟠 D7 — سازه‌های آبخیزداری: ابعاد تجربی + پارامتر مرده + هزینهٔ ثابت
**فایل:** `engine/hydroma/watershed/calculator.py`
- `design_check_dam`: `dam_height = min(3.0, max(0.5, slope_pct/10))` (حدس تجربی) · `dam_length = 10` متر **هاردکد** برای هر مکان · **`target_retention_years` هرگز استفاده نمی‌شود** · بدون سرریز/freeboard و بدون بازده تله‌اندازی رسوب (Brune) · `cost = dam_volume × 150` ثابت.
- `design_contour_trench`: `spacing = max(5, 10/(slope_pct/100))` ⇒ در شیب ۱٪ می‌شود **۱۰۰۰ متر فاصله** (بدون سقف منطقی) · بازده نفوذ ثابت `0.8` · `cost = total_length × 8`.
- `design_half_moon`: قطر ۳ m، عمق ۰.۴ m، فاصلهٔ ۴ m — با راهنمای FAO (شعاع ۳–۵ m، عمق ۰.۳–۰.۵ m، فاصلهٔ ۴ m) **سازگار** ✅.
- این‌ها همان مواردی است که خودِ `reports/implementation_plan.md` (Sprint 3) برای اصلاح با فرمول‌های FAO/MAG فهرست کرده بود و هنوز باز است.

### 🟡 D8 — فنولوژی GDD: تشخیص مرز مرحله و نشانگر مبهم
**فایل:** `engine/hydroma/phenology.py`
- `_stage_from_gdd(50.0, wheat)` مقدار `pre_emergence` می‌دهد چون `gdd_emergence=120`. این **از نظر مدل درست است**، اما تست `test_stage_progression_wheat` انتظار `emergence` دارد ⇒ تست کهنه است (فقط همان یک assertion).
- `days_to_flowering = -1` به‌عنوان «نرسیده» ⇒ نشانگر مبهم (بهتر: `None`/`nan`) و تست `test_run_phenology_basic` با GDD=5 روزانه در ۱۰۰ روز (۵۰۰ GDD) به گل‌دهی گندم (۶۵۰ GDD) نمی‌رسد ⇒ انتظار تست غیرواقعی.
- مقادیر GDD گندم (۱۲۰/۳۵۰/۶۵۰/۹۵۰ با Tb=10) **در محدودهٔ منابع FAO** هستند ✅.

### 🟡 D9 — انتظار غلط تست/داکیومنت برای θs خام
**فایل:** `engine/hydroma/soil/tests/test_soil.py:306` و مثال docstring در `soil/water_retention.py:51`
انتظار `theta_s == 0.463` برای loam، در حالی که مقدار **صحیح C&P برابر 0.43** است؛ ۰.۴۶۳ مقدار Saxton & Rawls برای loam است و با α=0.036 و n=1.56 (که همان C&P هستند) در یک رکورد نمی‌گنجد. ⇒ **خطای تست و داکیومنت، نه کد**.

### 🟡 D10 — تست‌های موتور از دروازهٔ CI بیرون‌اند
`pytest.ini → testpaths = services`. با این تنظیم، `engine/**/tests`, `tests/unit`, `testing_lab` هرگز در اجرای پیش‌فرض/CI دیده نمی‌شوند.

---

## ۴. جدول جمع‌بندی (مدل‌به‌مدل)

| # | مدل / رشته | فایل کلیدی | استاندارد | وضعیت | شاهد |
|---|---|---|---|---|---|
| 1 | Richards 1D | `cpp_core/src/richards.cpp` | Celia 1990 | ✅ معادله درست / ⚠️ اجرای C++ غیرفعال | هدر + D4 |
| 2 | Saint-Venant 1D | `cpp_core/src/saint_venant.cpp` | Toro 2001 | ✅ | هدر |
| 3 | FAO-56 ET0 | `climate/et_calculator.py` | FAO-56 | ✅ دقیق | خطوط ۱۷۵–۱۷۸ |
| 4 | FAO-56 dual-Kc | `cpp_core/src/crop_water.cpp` | FAO-56/2005 | ✅ | هدر |
| 5 | RUSLE | `cpp_core/src/erosion.cpp` | AH-703/McCool | ✅ دقیق | خطوط ۱۸–۵۴ |
| 6 | SCS-CN | `models/runoff_model.py` | SCS/NRCS | 🔴 باگ واحد (~۸×) | خطوط ۱۰۲–۱۱۴ |
| 7 | Rational | `watershed/calculator.py` | — | ✅ + LIMITATIONS | خطوط ۳۱–۶۰ |
| 8 | Kirpich | `watershed/calculator.py` | Kirpich 1940 | ✅ | خطوط ۴۳۱–۴۵۰ |
| 9 | Muskingum | `watershed/calculator.py` | Chow 1959 | ✅ | خطوط ۴۶۱–۵۰۰ |
| 10 | RothC port | `simulation/runners/rothc_runner.py` | Coleman 1996 | 🟠 پارتیشن رس | خطوط ۲۵–۳۲ |
| 11 | ECSI | `models/ecsi.py` | Coleman 1996 | 🔴 ناهمخوان | خطوط ۷۴–۱۴۷ |
| 12 | van Genuchten | `soil/water_retention.py` | C&P 1988 | ✅ کد / ❌ تست | تست خط ۳۰۶ |
| 13 | نیاز آبشویی | `soil/salinity.py` | FAO-29 (Rhoades) | 🔴 ضریب ۵ + کلمپ | خطوط ۱۷۸–۱۸۰ |
| 14 | آب زیرزمینی (bucket) | `groundwater/models.py` | linear reservoir | 🟠 ورودی مرده | خط ۵۳ |
| 15 | فنولوژی GDD | `phenology.py` | FAO | 🟡 تست/نشانگر | خطوط ۳۲–۳۹ |
| 16 | سازه‌های آبخیز | `watershed/calculator.py` | FAO/MAG | 🟠 تجربی + پارامتر مرده | خطوط ۶۷–۱۳۰ |
| 17 | نمونه‌برداری MC/LHS | `cpp_core/src/sampling.cpp` | — | ✅ موجود، اجرا C++ غیرفعال | — |
| 18 | عدم‌قطعیت/بهینه‌سازی | `climate_adaptation/uncertainty_knowledge_engine.py`, `optimization/optimizer.py`, `scenarios/monte_carlo.py`, `models/hlhs.py` | MC/LHS/NSGA | 📋 فهرست‌شده، ممیزی عمیق انجام نشد | — |
| 19 | Biofertilizer C/N | `materials/compost_formulator.py`, `biofertilizer/*` | FAO C/N 25–35 | 📋 فهرست‌شده، ممیزی عمیق انجام نشد | — |
| 20 | Plant-Neuro | `plant_neuro/*` | — | 📋 فهرست‌شده (۳۹ تست دارد) | — |

---

## ۵. توصیه‌های اولویت‌دار

| اولویت | اقدام | فایل |
|---|---|---|
| P0 | اصلاح واحد SCS-CN (`S = 25400/CN − 254` برای mm) + تست رگرسیون با مثال استاندارد (CN=70, P=50mm ⇒ Q≈5.8mm) | `models/runoff_model.py` |
| P0 | اصلاح پارتیشن RothC با فرم کلاس‌وابسته و استفاده از `clay_pct`؛ افزودن تست مرجع RothC | `simulation/runners/rothc_runner.py` |
| P0 | تعیین تکلیف ECSI: یا با همان ریاضی RothC یکسان شود یا از عنوان «RothC-26.3» و ارجاع Coleman حذف شود | `models/ecsi.py` |
| P0 | تعمیر/بازسازی `.pyd` هستهٔ C++ و نمایش وضعیت degrade در `/health` و metrics (نه فقط warning) | `cpp_bridge/__init__.py`, CMake |
| P1 | اصلاح فرمول LR به `ECw/(5ECe−ECw)` و حذف کلمپ ۰.۱/۰.۵ | `soil/salinity.py` |
| P1 | استفاده از `recharge_mm` (یا حذف از API) در مدل آب زیرزمینی | `groundwater/models.py` |
| P1 | جایگزینی ابعاد تجربی سازه‌ها با فرمول‌های FAO/MAG (سرریز، freeboard، Brune، هزینهٔ منطقه‌ای) + استفاده از `target_retention_years` | `watershed/calculator.py` |
| P2 | اصلاح انتظار تست θs (0.463 → 0.43) و docstring | `soil/tests/test_soil.py`, `soil/water_retention.py` |
| P2 | نشانگر `None` به‌جای `-1` در فنولوژی + اصلاح تست با ورودی واقع‌گرایانه | `phenology.py`, `tests/unit/test_groundwater_phenology.py` |
| P2 | افزودن `engine`, `tests/unit`, `testing_lab` به `testpaths` تا موتور در CI سنجیده شود | `pytest.ini` |

---

## ۶. فرمان‌های بازتولید

```powershell
# اجرای تست‌های موتور (خارج از testpaths پیش‌فرض)
D:\eco_nojin\.venv\Scripts\python.exe -m pytest engine testing_lab tests/unit -q
# → 23 failed, 779 passed, 13 skipped

# فقط ۴ خطای مرتبط با موتور
D:\eco_nojin\.venv\Scripts\python.exe -m pytest engine/hydroma/soil/tests/test_soil.py tests/unit/test_groundwater_phenology.py -q
# → 4 failed, 63 passed

# وضعیت هستهٔ C++
D:\eco_nojin\.venv\Scripts\python.exe -c "from engine.hydroma.cpp_bridge import hydroma_core"
# → ImportError: generic_type: type "WaveParameters" is already registered!
```


---

## ?. ??????? ????????? ??? ????? (????-??-??)

| # | ????? | ???? | ????? | ??? ??????? |
|---|---|---|---|---|
| D1 | SCS-CN ?? ???? ???? | `models/runoff_model.py` | `S = 25400/CN ? 254` [mm] + ???? `CN ? 100` | `TestScsCnUnits` (CN=70, P=50 ? Q?5.8 mm) |
| D2 | ??????? ???? ?.?? ?? RothC | `simulation/runners/rothc_runner.py` | ?????? `stabilization_split(clay)` ?? `x = 1.67(1.85 + 1.60?e^(?0.0786?clay))`? ??? ??????? ????? `clay_pct` ?? `initial_pools`? ????? `co2_fraction`/`stabilized_fraction` ?? ????? | `TestRothcPartition` (?? ??.?? ? stab ? ?.????) |
| D5 | ????? ?????? ???? ???? ? + ?? ???? | `soil/salinity.py` | `LR = ECw/(5?ECe ? ECw)`? ??? ???? ?.?/?.?? ?????????? ???? ?? ??????? | `TestLeachingRequirement` |
| D6 | ????? ????? `recharge_mm` | `groundwater/models.py` | `recharge_mm: float \| None = None` ? ????? ???? (???? ?) ????? ????? ??????? ?? ??? ??? ???? ?? `soil_water?rcoeff` ???? ?????? | `TestGroundwaterRecharge` |
| D8 | ???? ?????? grain_fill / ?????? ???? | `phenology.py` | ?????? ????? flowering/grain_fill ?? ????? ??? ?????? ????????????? (?????? AquaCrop/FAO-56) | `TestPhenologyStages` |
| D9 | ?????? ??? ?s | `soil/tests/test_soil.py` + docstring | ?.??? ? ?.?? (Carsel & Parrish 1988) | ???? ??? |
| D10 | ??????? ??? ??????? | `tests/unit/test_groundwater_phenology.py` | ??? pre-emergence ????? ??? ????? ?????? ???????????? (GDD ??.?/???) ??? ?/??? | ???? ?????? |

???? ??? ????: `tests/unit/test_engine_numeric_fixes.py` ? **?? ??? ???????** ?? ?? ????? ?? ?? ???? ?????? ????? ??????.

### ?????? ????? ????? (??? ? ???)

| ???? | ??? | ??? |
|---|---|---|
| ?? ?? ?? `engine testing_lab tests/unit` | ?? | **??** |
| ??? | ??? | **???** |
| **????? ????? ?? ?????** | **?** | **? (???)** |
| ????? ?????????? | ? | ??? ???? ?? ?????: ecowallet ??? blockchain ?? mrv_cdse ?? settings ?? seed_demo ? |

```
D:\eco_nojin\.venv\Scripts\python.exe -m pytest engine testing_lab tests/unit -q
# ? 19 failed, 797 passed, 13 skipped   (??? ???? ?????)
```
