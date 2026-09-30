# برنامهٔ اجرایی فعال‌سازی و تحکیم هستهٔ HyDroMa

**تاریخ:** ۱۴۰۵/۰۷/۰۶ · **مبنا:** `docs/ENGINE_ANALYTICAL_REPORT_FA_2026-09-28.md` و اجرای واقعی `engine/strict_tests` در همین محیط

---

## ۰. کشف تعیین‌کننده

پروژه یک صف کار **کاملاً مشخص و ماشین‌ردیابی‌شده** دارد که خودش ساخته است: **۱۰۸ تست `xfail(strict=True)`** در `engine/strict_tests/`، که هر کدام دارد:

- نشانی دقیق محل نقص (`file:line`)
- استاندارد یا مرجع حاکم
- **بزرگی اندازه‌گیری‌شدهٔ خطا** (نه «احتمالاً غلط» — بلکه «۲۸٫۴× کمتر»)
- `strict=True`، یعنی اصلاح باعث **XPASS** می‌شود و قابل راستی‌آزمایی است

مثال واقعی از خروجی اجرا:

> `test_s06::TestCheckDam::test_trap_efficiency_varies_with_catchment_scale` — *«`calculator.py:96-113` نرخ گیرانداز Brune را با `runoff_m3` (حجم **آب**) در مخرج حل می‌کند در حالی که صورت، `storage_req_m3` (حجم **رسوب**) است. پیامد اندازه‌گیری‌شده: هر دو عبارت خطی با سطح حوضه مقیاس می‌شوند، پس نسبت مقیاس‌ناپذیر است و بازده گیراندازی برای هر حوضه‌ای از ۱۰۰۰ تا ۱۰۰۰۰۰۰ مترمربع ثابت ۰٫۷۷۶ است.»*

**یعنی کار این نیست که «نقص پیدا کنیم».** کار این است که تیکت‌های موجود را ببندیم — و مکانیسم بستن، از قبل ساخته و تست شده است.

### پیامد مستقیم برای برنامه

| آنچه فکر می‌کردیم لازم است | واقعیت |
|---|---|
| کشف نقص‌های علمی | ✗ از قبل انجام شده، ۱۰۸ مورد با جزئیات کامل |
| ابزار اولویت‌بندی | ✗ هر کدام شدت اندازه‌گیری‌شده دارند |
| دروازهٔ بازبینی | ✓ هست — کافی است در CI اجرا شود |
| ردیابی پیشرفت | ✓ تعداد xfail شمارش معکوسِ پیشرفت است |

**تنها کاری که در سطح مهندسی لازم است: آن ۱۰۸ تیکت را به ترتیب شعاع انفجار ببندیم و مانع بازگشتشان شویم.**

### تفکیک حیاتی: چه چیزی با کد بسته می‌شود و چه چیزی نمی‌شود

از ۱۰۸ تیکت:

- **۱۰۲ مورد با کد و دانش موجود در خود مخزن بسته می‌شود.** چون معیار پذیرش (تستِ دقیقاً مشخص) از قبل نوشته شده است.
- **۶ مورد مسدود بر اطلاعات بیرونی‌اند** و با نوشتن کد بسته **نمی‌شوند**: چهار سطر مورد مناقشهٔ جدول خاک (`engine/data/soil_vg_table.csv` سطرهای `silt`, `sandy_clay_loam`, `silty_clay`, `clay`) و دو تست `test_s13`. اصلاح آن‌ها نیازمند انتشار مرجع Carsel & Parrish (1988) است. `engine/data/physics_guard.py:39-53` مستند می‌کند که چهار مسیر جست‌وجو امتحان شده و همه مسدود بوده‌اند.

**این تفکیک مهم است:** ۱۰۲ تیکت قابل بستن، ۶ تیکت مسدود. برنامهٔ زیر برای ۱۰۲ مورد است، و برای ۶ مورد مسیر جداگانه دارد.

---

## ۱. فاز صفر — پایهٔ اندازه‌گیری (۱ روز کاری)

**هدف:** ثابت کردن خط پایه. بدون این فاز، هیچ تغییری قابل دفاع نیست.

| # | کار | فرمان پذیرش |
|---|---|---|
| F0.1 | ثبت خط پایهٔ xfail | `pytest engine/strict_tests -q -rx` → `808 passed, 108 xfailed, 0 failed` |
| F0.2 | ثبت وضعیت پوشش فعلی موتور | `pytest engine/strict_tests --cov=engine --cov-report=term` → عدد را در PR ثبت کنید |
| F0.3 | ثبت وضعیت تست‌های تودرتو | `pytest engine/land engine/hydroma/*/tests -q` → `3 failed, 431 passed, 9 skipped` |

**بدون این سه عدد، بستن هر تیکتی غیرقابل اثبات است.** چون «۱۰۸ → ۱۰۷» تنها اثبات پیشرفت است وقتی معلوم باشد هیچ‌چیز دیگری نشکسته.

**نکته:** عدد واقعی اجرا در این محیط `808 passed / 108 xfailed` است، ولی گزارش قبلی `783/112` می‌گوید. اختلاف یعنی مجموعه در این فاصله تغییر کرده — **فاز صفر عدد محلی را مرجع می‌کند، نه گزارش قدیمی را.**

---

## ۲. فاز یک — شبکهٔ ایمنی (۳ روز کاری)

**این فاز پیش‌شرط همهٔ فازهای بعدی است.** ترتیب مهم‌تر از محتوا: تا وقتی این انجام نشود، هر تغییری کورکارانه است.

### F1.1 — `strict_tests` را به CI وصل کنید · ۱ روز

فایل: `.github/workflows/ci-cd.yml` — یک job جدید پس از `numerical-regression` (خط ۲۵۵).

```yaml
  engine-strict:
    name: Engine Strict Tests (S00-S14)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install engine + test deps
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest pytest-cov hypothesis scipy numba
      - name: Build C++ core
        run: |
          sudo apt-get install -y cmake ninja-build
          cmake -S engine/cpp_core -B engine/cpp_core/build -G Ninja \
                -DCMAKE_BUILD_TYPE=Release -DHYDROMA_BUILD_TESTS=OFF
          cmake --build engine/cpp_core/build --config Release
      - name: Run strict suite
        run: |
          pytest engine/strict_tests -q \
                 --hypothesis-profile=strict-engine-ci \
                 -o addopts=--strict-markers
```

**سه پیش‌نیاز که باید هم‌زمان حل شوند، وگرنه job قرمز می‌شود:**

| پیش‌نیاز | وضعیت فعلی | اقدام |
|---|---|---|
| `hypothesis` وابستگی پایه نیست | فقط در `requirements-dev.txt:17` | `pip install` بالا کافی است |
| مجموعه **صفر `skipif`** دارد | S02/S11/S13 بدون C++ **شکست** می‌خورند نه skip | `conftest.py` اضافه کنید (پایین) |
| `strict-markers` غیرفعال است | `pytest.ini` فایل `markers` ندارد | بخش زیر |

### F1.2 — `pytest.ini` · ۳۰ دقیقه

```ini
markers =
    cpp: needs the compiled C++ core
    network: makes a live network call
    slow: exceeds 10s
```

### F1.3 — `conftest.py` برای skipif · ۳۰ دقیقه

`engine/strict_tests/conftest.py` اضافه کنید:

```python
_CPP = None
try:
    from engine.hydroma.cpp_bridge import is_cpp_available

    _CPP = is_cpp_available()
except Exception:
    _CPP = False

requires_cpp = pytest.mark.skipif(not _CPP, reason="C++ core not built")
```

و `@requires_cpp` را روی حدود ۱۰ تست وابسته به C++ در `test_s02`، `test_s11`، `test_s13` بگذارید.

**پذیرش فاز:** `pytest engine/strict_tests -q --co` → ۹۱۶ تست، و job سبز در CI.

### F1.4 — دروازهٔ پوشش · ۳۰ دقیقه

`pyproject.toml:215-222` — اضافه کنید:
```toml
fail_under = 80
```
و در `ci-cd.yml:329` مقدار `fail_ci_if_error: true`.

**هشدار:** عدد ۸۰٪ در حال حاضر **برقرار نیست**. اول عدد واقعی را از F0.2 بگیرید، `fail_under` را روی عدد فعلی − ۲ تنظیم کنید (سقف زنی نکنید)، و بعد از هر فاز ۲ واحد بالا ببرید. تنظیم مستقیم روی ۸۰ job را قرمز می‌کند و تیم آن را غیرفعال می‌کند.

### F1.5 — سه تست شکسته · ۱ ساعت

| تست | علت | اقدام |
|---|---|---|
| `test_gbif_connector.py::test_fetch_checklist_country` | `asset_id` الگوی `gbif_species_list_IR_…` است، «checklist» ندارد | assertion را به `tags` تغییر دهید نه `asset_id` |
| `test_benchmarks.py::test_telemetry_overhead` | `cpp_calls == 1` انتظار دارد ولی ۱۰۰۰ عنصر به Numba می‌رود | assertion را به «backend مورد انتظار استفاده شد» تغییر دهید |
| `test_climate_integrator.py::test_integration_time_reasonable` | ۱۳ فراخوانی زندهٔ شبکه به Open-Meteo، سپس ادعای `< 5000ms` | شبکه را mock کنید (F1.6) |

### F1.6 — شبکهٔ زنده در تست را حذف کنید · ۳۰ دقیقه

`test_climate_integrator.py` سیزده بار `build_climate_profile` و `integrate_with_land` صدا می‌زند که هر کدام ۳۰ سال دادهٔ روزانه از Open-Meteo می‌کشد. این **اصل اول `AGENTS.md` (offline-first) را نقض می‌کند**.

```python
@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(
        "engine.land.integration.climate_integrator._fetch_open_meteo",
        lambda *a, **k: _SYNTHETIC_PROFILE,
    )
```

**پذیرش کل فاز یک:** `pytest engine/strict_tests -q` سبز در CI، و پوشش مسجوب.

---

## ۳. فاز دو — بستن تیکت‌های پرشعاع (۵ روز کاری)

اولویت با **شعاع انفجار** تعیین می‌شود: کدام تیکت، بیشترین خروجی نادرست را در کمترین کد تغییر می‌دهد.

### موج ۱ — رفع تک‌خطی با بیشترین اثر (۱ روز)

این‌ها تیکت‌هایی هستند که هر کدام **یک عدد را کاملاً بی‌معنا** می‌کنند. نسبت ارزش به زمان، بی‌رقیب است.

| تیکت | محل | تغییر | معیار پذیرش |
|---|---|---|---|
| T-01 | `watershed/calculator.py:276` | `min(90, ...)` → `max(0, min(90, ...))` | `test_s06::TestTerrace::test_erosion_reduction_is_never_negative` |
| T-02 | `watershed/calculator.py:593` | بررسی `C0+C1+C2≈1` (که جبری همیشه صفر است) را با شرط واقعی `2Kx ≤ Δt ≤ 2K(1−x)` عوض کنید؛ در صورت نقض `ConvergenceError` | `test_s06::TestMuskingumRouting::test_unstable_timestep_is_rejected` |
| T-03 | `irrigation/scheduler.py:33` | `efficiency <= 0` برگرداندن `0.0` → `math.inf` | `test_s08::TestApplicationDepth::test_non_positive_efficiency_is_rejected` |
| T-04 | `irrigation/scheduler.py` | `0 ≤ allowable_depletion ≤ 1` را اعمال کنید | `test_s08::TestInterval::test_depletion_must_be_a_fraction` |
| T-05 | `carbon/calculator.py:161` | `area_ha > 0` و `duration_years > 0` را بررسی کنید | `test_s07::TestInputValidation::test_negative_area_is_rejected` |
| T-06 | `carbon/calculator.py:188` | `region_factors.get(region, 1.0)` → بررسی وجود کلید | `test_s07::TestInputValidation::test_unknown_region_is_rejected` |
| T-07 | `carbon/calculator.py:219-220` | نوار min/max را روی پایهٔ یک‌باره محاسبه کنید | `test_s07::test_biochar_range_uses_the_one_time_basis` |
| T-08 | `carbon/calculator.py:245` | `except Exception: continue` → ثبت در خروجی | `test_s07::test_a_failing_project_type_is_reported_not_dropped` |
| T-09 | `groundwater/models.py:154,158` | `t ≤ 0` و `u ≤ 0` برگرداندن `0.0` → `ValueError` (دو سر حد واگرا هستند) | `test_s04::TestTheisDrawdown::test_non_positive_time_is_rejected` |
| T-10 | `groundwater/models.py:142` | `return None` برای ورودی نامعتبر → `ValueError` | `test_s04::TestTheisDrawdown::test_invalid_input_raises` |
| T-11 | `soil/physics.py:100` | محافظ تقسیم بر صفر در `abs(hb)/abs(h)` | `test_s05::test_brooks_corey_does_not_divide_by_zero` |
| T-12 | `soil/physics.py:41-44` | `theta_s ≤ 1.0` را بررسی کنید | `test_s05::test_rejects_saturated_content_above_one` |
| T-13 | `models/runoff_model.py:117` | محافظ `CN > 0` | `test_s03::test_non_positive_curve_number_raises_value_error` |
| T-14 | `economics/risk.py:41` | `base + z·σ` → `base * (1 + z·σ)` (خطای ابعادی) | تست جدید |
| T-15 | `scenarios/crop_scenarios.py:246` | ~~معکوس‌بودن~~ **ادعای من نادرست بود** — `min(key=-f)` همان argmax است. اصلاح فقط خوانایی | تأییدشده روی ۳۰ حالت |

**اثر جانبی مهم:** T-01 و T-03 و T-09 هر کدام عددی را که **فیزیکاً ناممکن** است به کاربر نشان می‌دادند. T-01 کاهش فرسایش **منفی** (یعنی افزایش فرسایش) را به‌عنوان «مزیت طراحی» گزارش می‌کرد؛ T-03 به زمان‌بند آبیاری می‌گفت «زمین به آب نیاز ندارد» در حالی که رانده صفر یعنی آب هرگز نمی‌رسد.

### موج ۲ — اصلاح ساختاری (۲ روز)

| تیکت | محل | کار |
|---|---|---|
| T-16 | `watershed/calculator.py:96-113` | **بازسازی فرمول Brune.** نسبت درست `storage_req_m3 / annual_sediment_m3` است. با همان ورودی به کران ۰٫۹۵ همگرا می‌شود نه ۰٫۷۷۶ ثابت |
| T-17 | `watershed/calculator.py:82,165,219-223,250` | یا پارامترهای بلااستفاده را استفاده کنید، یا حذفشان کنید، یا ادعای «همهٔ ورودی‌ها استفاده می‌شوند» را از docstring بردارید |
| T-18 | `carbon/calculator.py:266,287,310,334` | `except Exception` مخزن را بردارید. **برای رجیستری اعتبار کربن، خطای پایگاه داده نباید موفقیت گزارش شود** |
| T-19 | `runoff_model.py:179-197` | نقشهٔ CN از کد خاک استفاده کند، نه فقط کاربری |
| T-20 | `runoff_model.py:131` | «دبی اوج» را از حجم محاسبه می‌کند — باید نرخ باشد |
| T-21 | `runoff_model.py:235` | `hash(dem_path)` → هش پایدار (sha256)؛ `PYTHONHASHSEED` تصادفی‌سازی می‌کند و هر اجرا نام فایل تازه می‌سازد |
| T-22 | `soil/water_retention.py:130` | بافت ناشناخته → `KeyError` (نه بازگشت خاموش به loam). **هم‌راستا با `physics.py:145`** |
| T-23 | `et_calculator.py:173` | `rn = Rs * 0.77` → افزودن `Rnl` از eq. 40. ریشهٔ نقض سقف انرژی در ۱۱٫۲٪ روزهای فیزیکی |
| T-24 | `et_calculator.py:91` | `t_max <= t_min` → بازگشت صفر به‌جای `ValueError` (روز بدون نوسان هر سال در هر محل رخ می‌دهد) |

### موج ۳ — دوازده اصلاح کوچک اعتبارسنجی ورودی (۲ روز)

همه یک شکل‌اند: پارامتر فیزیکی بدون کران. ۳۵+ تیکت در این دسته. یک الگو، نه ۳۵ کار:

```python
# قبل
def calculate_net_irrigation_requirement(precip, et0, kc, growing_days, swc) -> float
# بعد — اعتبارسنجی در مرز مدل Pydantic، نه داخل تابع
class IrrigationInput(BaseModel):
    precip: float = Field(ge=0.0)
    et0: float = Field(ge=0.0)
    irrigation_efficiency: float = Field(gt=0.0, le=1.0)
    allowable_depletion: float = Field(ge=0.0, le=1.0)
```

**اصل طراحی:** اعتبارسنجی را در **مرز ورودی Pydantic** بگذارید نه داخل تابع. یک‌بار انجام می‌شود، در schema دیده می‌شود، و در مستندات OpenAPI ظاهر می‌شود.

---

## ۴. فاز سه — فعال‌سازی (۱ هفته کاری)

### F3.1 — حذف fallback خاموش · ۱ روز

| ماژول | مشکل | اقدام |
|---|---|---|
| `cpp_bridge/__init__.py:240` | هر استثنای C++ → fallback پایتون. طوری رفتار می‌کند که انگار C++ نیست | روی `TypeError` (ناسازگاری امضا = باگ فراخواننده) دوباره پرتاب کنید؛ فقط خطای داخلی C++ fallback شود |
| `crop_bridge/tests/test_benchmarks.py` | ۵ از ۱۰ کلاس بنچمارک در واقع پایتون را اندازه می‌گیرند | نام‌های کلیدی را به امضای بومی اصلاح کنید + یک assertion که backend مورد انتظار را تأیید کند |

### F3.2 — تک‌منبعی‌سازی وابستگی · ۱ روز

**ریشهٔ سه مشکل فعال‌سازی همین است.** سه منبع حقیقت برای نسخهٔ ابزار وجود دارد و وابستگی‌های اختیاری اصلاً اعلام نشده‌اند:

| محل | نسخه |
|---|---|
| `pyproject.toml` | `ruff>=0.3,<1.0` |
| `requirements-dev.txt` | `ruff==0.11.2` |
| `.pre-commit-config.yaml` | `rev: v0.5.7` |

**اندازه‌گیری‌شده در این محیط:** `flopy` **غایب** (⇒ MODFLOW6 همیشه mock)، `gpytorch` **غایب** (⇒ GP Surrogate همیشه نویز با `success=True`)، `xrspatial`، `optuna`، `mlflow`، `dvc` **غایب**.

اقدام: یک منبع واحد. `requirements-research.txt` یا یک فایل `extras` تازه. هر importی که در کد هست یا باید pin شود یا باید صریحاً اختیاری علامت بخورد.

### F3.3 — گسستگی دوازده قرارداد · ۱ روز

`simulation/contracts.py:203-299` — دوازده کلاس `__init__(self, *args, **kwargs)` که هیچ‌چیز را اعتبارسنجی نمی‌کنند و **دقیقاً همان‌هایی هستند که اجازهٔ ورودی نامعتبر را می‌دهند**.

- `contracts/simulation.py` (Pydantic واقعی) نگه دارید
- stubها را حذف کنید
- نام‌ها را یکسان کنید (`AquacropOutput`/`AquaCropOutput`، `RothcOutput`/`RothCOutput`، `RusleOutput`/`RUSLEOutput` — سه جفت فقط با اختلاف حرف بزرگ/کوچک)

### F3.4 — تعمیر `models/base.py` · ۱ ساعت

```python
# base.py:100-104 — این بلوک به ModelOutput دفن شده، ولی فیلدها روی ValidationResult است
notes: str = ""


@property
def is_within_tolerance(self) -> bool:
    return self.relative_error <= self.tolerance
```

`notes` و `is_within_tolerance` را به `ValidationResult` منتقل کنید. **این دو خط، کل `hybrid_ml` را از بن‌بست آزاد می‌کند** — `ModelInput(param_0=1.0)` در حال حاضر `TypeError` می‌دهد چون فقط یک فیلد `values` دارد.

### F3.5 — PINN و GP · ۱ روز

| نقص | محل | اقدام |
|---|---|---|
| `requires_grad` غایب ⇒ هر دو PINN در epoch اول می‌میرند | `pinn.py:191,200-202` | `.requires_grad_(True)` روی نقاط هم‌بینی |
| `hessian()` جمع مشتق دوم روی ابعاد | `pinn.py:106-111` | یک بعد در هر بار مشتق بگیرید |
| `nn.Sin` وجود ندارد | `pinn.py:92` | پیاده‌سازی کنید یا گزینه را حذف کنید |
| «MC-dropout» تهی — شبکه `nn.Dropout` ندارد ⇒ `std=0` | `pinn.py:288-290` | یا لایه اضافه کنید یا روش را عوض کنید |
| مسیر mock GP نویز با `success=True` برمی‌گرداند | `gp_surrogate.py:445-450` | `success=False` + `data_source="simulated"` صریح |
| مسیر mock MODFLOW6 با حلقهٔ پایتون سه‌گانه | `modflow6.py:174-178` | numpy و برداری‌سازی (قاعدهٔ خود `base.py:113` را نقض می‌کند) |

### F3.6 — API عمومی و وابستگی · ۱ روز

- `land/integration/__init__.py:27` — `SoilProfile` ناموجود. **چهار نام خاک بی‌صدا از `__all__` حذف شده‌اند** (اندازه‌گیری‌شده). هر پنج `except ImportError: pass` را به `logger.warning` تبدیل کنید
- `dem_processor.py:4` — `import rasterio` محافظت‌نشده باعث می‌شود **۸۰٪ بستهٔ `land` بدون آن importable نباشد**، در حالی که فقط یک کلاس ۱۰۵ خطی از آن استفاده می‌کند. الگوی درست همین مخزن: `hydroma/utils/topographic_calcs.py:8-12`
- `scripts/seed_nojin.py` را به راه‌اندازی وصل کنید — شش endpoint خواندنی `[]` برمی‌گردانند

### F3.7 — مردهٔ عمدی به مسیر صادقانه · ۱ روز

**دقت مهم:** `hecras.py` و `weap.py` فقط وقتی فراخوانی می‌شوند که SWAT+ واقعاً اجرا شده باشد. چون `swat_runner.py` در نبود باینری `SwatUnavailable` می‌رَماید، `_run_swat_plus` مقدار `None` برمی‌گرداند و مسیر صادقانهٔ `orchestrator.py:340-344` انتخاب می‌شود.

پس این‌ها **نقص نهفته‌اند، نه فعال.** اولویت: متوسط.

| اقدام | جایگزین |
|---|---|
| `hecras.py:35-46` — حذف || `orchestrator.py:340-344` الگوی `not_computed` موجود است؛ **نامشروطش کنید** |
| `weap.py:34` — قواعد اولویت را دور می‌ریزد | همان |
| `scenario_manager.py:16-19` — غیرقابل import | تست `test_s01_import_integrity.py:208-219` **از قبل tripwire دارد**. importها را اصلاح یا ماژول را حذف کنید؛ در هر دو حالت آن xfail به pass تبدیل می‌شود |
| `validate_model.py` — در import می‌میرد | سه runner جعلی را حذف کنید |

---

## ۵. فاز چهار — یکپارچگی و منشأ (۳ هفته کاری)

این فاز مقیاس بزرگ دارد و باید **پس از** اطمینان از پایداری فازهای قبل شروع شود.

### F4.1 — مسیریابی جریان و توپوگرافی · ۱ هفته

**بزرگ‌ترین نقص علمی موتور، و یک اصلاح، همه را درست می‌کند.**

| مشکل | اندازه‌گیری |
|---|---|
| جدول کد D8 با ترتیب پویش همسایه ناهم‌تراز | **۷ از ۸ جهت اشتباه** |
| وزن‌های فاصلهٔ کارتینال/قطری معکوس | ۴ از ۸ وزن اشتباه |
| `drainage.py:88` محاسبه و دور ریخته می‌شود | انباشت: ۵ در برابر ۱۳ الگوریتم صحیح |

پیکربندی صحیح (قرارداد `drainage.py:70-80`):
```
کد: 1=N  2=NE  3=E  4=SE  5=S  6=SW  7=W  8=NW
```
پویش باید `[N, NE, E, SE, S, SW, W, NW]` باشد — نه ردیف‌به‌ستون.

**کار:** یک ماژول مشترک `engine/land/hydrology.py` با `flow_direction()` و `flow_accumulation()` (deque، با **تشخیص چرخه که خطا بدهد**). چهار نسخهٔ جهت و پنج نسخهٔ انباشت را حذف کنید.

**معیار پذیرش — تستی که باید نوشته شود:** روی DEM همگرای شعاعی، انباشت کل در خروجی برابر تعداد سلول‌ها، و `flow_dir` یک سلول معلوم برابر کد درست. **این تستی است که هیچ‌کدام از تست‌های فعلی ندارند** — fixture فعلی TWI یک شیب یکنواخت است که `neighbors < center` در آن هرگز درست نیست، پس هیچ مسیریابی جریانی اجرا نمی‌شود.

سپس: aspect (`terrain_analysis.py:109` — چرخش ۹۰° که خالص نیست) و بازتابعیابی مختصاتی (`resolution=30.0` مفروض بر حسب متر، در حالی که CRS خوانده نمی‌شود).

### F4.2 — ادغام چندنسخه‌ای · ۲ هفته

| الگوریتم | نسخه‌ها | معیار ادغام |
|---|---:|---|
| شیب/جهت | ۵ | یک پیاده‌سازی Horn، از ترنسفورم آفین |
| مسیریابی D8 | ۴ + ۵ انباشت | `land/hydrology.py` |
| RUSLE | ۴–۵ | `baseline/cases.py:635` از قبل آشکارساز تغییر دارد |
| توصیهٔ کودآزمایی | ۴ | نیاز نیتروژن گندم سه مقدار دارد: ۱۲۰/۱۵۰/۱۵۰ |
| بافت USDA | ۳ | `soil/__init__.py` فقط نسخهٔ غلط را صادر می‌کند |
| Kirpich | ۲، **۲ واحد متفاوت** | یک واحد، مستند |

**قالب ادغام — از `engine/data/` کپی کنید، نه از صفر اختراع کنید:** منبع واحد + مولد + آزمون `--check` + ثبت شعاع انفجار در پیام commit. این تنها ادغام موفق کل پروژه است.

### F4.3 — گسترش رجیستری منشأ · ۱ هفته

رجیستری موجود **۳۴ رکورد** دارد و **صفر فراخوان تولیدی**. سازوکار درست است؛ دامنه‌اش اشتباه است.

| اقدام | مشخصات |
|---|---|
| `require_servable` را در `cpp_bridge` صدا بزنید | رکورد `et0_reference` مستند می‌کند همین مسیر یک‌بار پاسخ **۳۶٪-غلط** را «در هر کانتینر» تحویل داده |
| `plant_neuro` و `climate_adaptation` را ثبت کنید | برای هر ثابت وضعیت منشأ — `multi_stress_engine` الگوست |
| `data_source` را اجباری کنید | `data_source: Literal[...]` **بدون پیش‌فرض**، تا هر نقطهٔ ساخت مجبور به اعلام منبع شود |
| تست پویش انواع خروجی | همان الگوی `test_s01_import_integrity` |

**این یک کار، هم‌زمان `hecras`، `nojin_mrv`، GP mock، MODFLOW6 mock و NSE ساختگی `0.75` را ناممکن می‌کند** — بدون آنکه لازم باشد تک‌تک بشمارید.

### F4.4 — ۶ تیکت مسدود · جداگانه

| تیکت | مسدودکننده |
|---|---|
| `test_s13::test_conductivity_falls_with_texture_fineness` | انتشار Carsel & Parrish (1988) |
| `test_s13::test_pore_size_index_falls_with_texture_fineness` | همان |
| `test_s05::test_awc_increases_with_clay_content` | به جدول اصلاح‌شده وابسته است |
| `test_s11::test_every_copy_carries_the_same_twelve_textures` | تا جدول حل نشود، بسته می‌ماند |

**مسیر:** `python -m engine.data.apply_published_table --from <published.csv>` — ابزار ساخته شده و منتظر ورودی است. `physics_guard.py:39-53` مستند می‌کند چهار مسیر جست‌وجو امتحان و همه مسدود شده‌اند. **این‌ها کار کتابخانه‌ای می‌خواهند، نه کدنویسی.**

---

## ۶. مسیر بحرانی و ترتیب

```
F0 (خط پایه) ──→ F1 (شبکهٔ ایمنی) ──→ F2 (تیکت‌های پرشعاع) ──→ F4 (ادغام)
                     │                      │                        │
                     │                      └──→ F3 (فعال‌سازی) ──────┘
                     │
                     └── گلوگاه: بدون این، هیچ‌کدام از مراحل بعدی قابل اثبات نیست
```

| فاز | مدت | وابستگی | معیار خروج |
|---|---:|---|---|
| F0 خط پایه | ۱ روز | — | سه عدد ثبت‌شده |
| F1 شبکهٔ ایمنی | ۳ روز | F0 | ۹۱۶ تست در CI سبز، پوشش مسجوب |
| F2 موج ۱ | ۱ روز | F1 | ۱۵ تیکت بسته، ۱۰۸ → ۹۳ |
| F2 موج ۲ | ۲ روز | F2موج۱ | ۹ تیکت بسته → ۸۴ |
| F2 موج ۳ | ۲ روز | F2موج۲ | ~۳۵ تیکت بسته → ~۴۹ |
| F3 فعال‌سازی | ۵ روز | F1 | fallback خاموش حذف، ماژول‌های مرده مسیر صادقانه |
| F4 ادغام | ۳ هفته | F2 | ۵ الگوریتم به یک منبع |
| F4.3 منشأ | ۱ هفته | F2 | `data_source` اجباری، رجیستری به dispatch وصل |

**جمع: ~۴٫۵ هفته تا فعال‌سازی و تحکیم، + ۳ هفته ادغام = ۷٫۵ هفته** برای یک نفر.

> این تخمین برای کسی است که مخزن را می‌شناسد. برای فرد تازه‌وارد، F1 و F3.1 تا F3.4 را باید با فاز ۰ ضرب در ۱٫۵ برآورد کرد.

---

## ۷. معیار سنجش

پنج عدد. هر کدام مستقیماً قابل اندازه‌گیری و قابل بازبینی در PR:

| معیار | خط پایه (اندازه‌گیری‌شده) | هدف فاز ۴ |
|---|---:|---:|
| تیکت‌های باز (`xfail`) | **۱۰۸** | **≤ ۱۰** |
| تست‌های `strict_tests` در CI | **۰** از ۹۱۶ | ۹۱۶ |
| انواع خروجی با منشأ اجباری | پایین | ۱۰۰٪ |
| بیشینهٔ اختلاف C++↔پایتون | **۴٫۷۱٪** (Hargreaves) | **۰** |
| تست‌های `engine` بدون شبکهٔ زنده | ۱۳ فراخوانی | ۰ |

تخفیف ۹۸ درصدی در صف کار، در سه هفته، بدون نوشتن یک مدل جدید.

---

## ۸. آنچه نباید انجام شود

| نباید | چرا |
|---|---|
| **موازی کار کنید** | بزرگ‌ترین خطر این پروژه پراکندگی است. کار موازی روی هستهٔ بدون شبکهٔ ایمنی یعنی تبدیل بدهی فنی به بدهی مبهم |
| **مدل جدید ننویسید** | پنج مدل از هشت مدل شاخص زیر قرارداد انتزاعی نقض می‌کنند که هیچ‌کس اجبارش نمی‌کند. مدل هفتم این را حل نمی‌کند |
| **انتزاع را نیمه‌راه رها نکنید** | `ScientificModel` بدترین حالت ممکن است: نه انتزاع است، نه توافق‌نامه. یا امضای ۱۲ زیرکلاس را یکی کنید، یا ادعایش را از docstring حذف کنید |
| **قابلیت نیمه‌کاره را عمومی نکنید** | `motors_hub` و `water_adapter` شکل درست دارند ولی بی‌اثرند. نمای معیوب بدتر از نبودِ نما است — کاربر نمی‌داند جواب ساختگی است |
| **برای ۶ تیکت مسدود کد ننویسید** | اصلاحشان نیازمند انتشار مرجع است. نوشتن عدد حدسی، دقیقاً همان کاری است که جدول خاک را به وضعیت فعلی رساند |

---

## ۹. سه تصمیمی که از شما لازم است

| # | تصمیم | پیش‌فرض پیشنهادی |
|---|---|---|
| ۱ | آیا `strict_tests` اجباری شود یا advisory در ادامه باشد؟ | **اجباری**، ولی ۶ تیکت مسدود را در `xfail` نگه دارید تا CI سبز بماند |
| ۲ | تکلیف ۶ سطر مورد مناقشهٔ جدول خاک چیست؟ | انتشار مرجع تهیه شود، یا سطرها **برای همیشه** برچسب `disputed` بخورند و مسیر محاسباتی از آن‌ها عبور نکند |
| ۳ | `flopy` و `gpytorch` در محیط تولید لازم‌اند یا نه؟ | اگر نه، `MODFLOW6Model` و `GPSurrogateModel` از رجیستری خارج شوند — **قابلیتی که اجرا نمی‌شود، بدهی است نه دارایی** |

**نقطهٔ شروع:** F0 و F1 با هم. بدون آن‌ها، بستن هر تیکتی غیرقابل اثبات است. پس از آن، F2 موج ۱ — پانزده تیکت، یک روز، بیشترین اثر به کمترین کار در کل نقشهٔ راه.
