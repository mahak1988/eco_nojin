# فاز ۲ — زنجیره کامل مدل‌های علمی (Scientific Chain)

> وضعیت: **پیاده‌سازی‌شده و تست‌شده** — اجرای زنجیره کامل از طریق HTTP در ۳.۴ ثانیه (با کش ۰.۰۱ ثانیه)، همه منابع رایگان.

زنجیره نهایی: **SWAT+ (آماده‌سازی) ← RUSLE ← AquaCrop ← RothC ← Pywr ← HEC-RAS (+ NSGA-II)**

---

## ۱) موتورهای جدید (`services/scientific_motors/`)

| فایل | موتور | وضعیت |
|---|---|---|
| `rothc_real.py` **(جدید)** | RothC-26.3 رسمی با پکیج **pyRothC** (جایگزین مدل ساده‌شده) | ✅ اجرای واقعی — ۲۰ سال در ۰.۰۳۵ ثانیه |
| `aquacrop_real.py` **(جدید)** | **AquaCrop-OSPy 3.1** رسمی (جایگزین مدل ساده‌شده) | ✅ اجرای واقعی — گندم تهران ۵.۶۷ t/ha |
| `swat_real.py` **(جدید)** | SWAT+ با **pySWATPlus 1.3** — آماده‌سازی پروژه از داده واقعی | ✅ `prep_ready`؛ اجرای کامل نیازمند باینری رایگان SWAT+ |
| `pywr_real.py` **(جدید)** | **Pywr 1.31** — شبکه تخصیص آب (جایگزین رایگان WEAP) | ✅ اجرای واقعی — قابلیت اطمینان تأمین ۱۴.۶٪، کسری ۲.۱ MCM |
| `hecras_real.py` **(جدید)** | خودکارسازی **HEC-RAS** (الگوی HEC-Commander) | ✅ تشخیص باینری + جایگزین مهندسی Manning با برچسب صادقانه |
| `optimize_chain.py` **(جدید)** | **pymoo 0.6 NSGA-II** — بهینه‌سازی چندهدفه | ✅ جبهه پارتو ۲۴ نقطه (سوروگیت مبتنی بر خروجی‌های واقعی زنجیره) |
| `chain_runner.py` **(توسعه)** | رانر زنجیره: کش sha256 + وضعیت هر موتور + KGE | ✅ اولین اجرا ۵.۱ ثانیه، کش‌شده ۰.۰۱ ثانیه |

### پکیج‌های نصب‌شده (همه رایگان)
`pywr 1.31.1`، `pymoo 0.6.2` (pandas به 2.3.3 برگشت — سازگار با کل پشته تأیید شد).

## ۲) نکات فنی مهم (مستند برای آینده)

- **pyRothC**: نام ایمپورت `pyRothC` (حروف بزرگ) است؛ `version` در pySWATPlus یک تابع است نه رشته.
- **AquaCrop-OSPy 3.1**: 
  - تاریخ‌ها: `sim_start/end` به شکل `YYYY/MM/DD`، `planting_date` به شکل **MM/DD** (سال از ساعت شبیه‌سازی می‌آید)
  - ستون‌های weather_df: `MinTemp MaxTemp Precipitation ReferenceET Date` (**Date آخر** — آرایه داخلی numpy به ترتیب وابسته است)
  - `initial_water_content` اجباری است → `InitialWaterContent()` (شروع از ظرفیت مزرعه)
  - خاک: نگاشت بافت SoilGrids → کلاس‌های داخلی (`clay_loam → ClayLoam`)؛ محصول: `wheat → Wheat`
  - خروجی: `get_simulation_results()` در v3 **DataFrame** است (نه dict) و yield از قبل tonne/ha
- **Pywr**: pandas 2.3 مقدار `"1M"` را نمی‌پذیرد → `pd.Timedelta("30D")` (freq="30D")؛ داده زمانی با `DataFrameParameter` و ایندکس دقیق بازه‌ها؛ خروجی ریکوردر شکل `(n,1)` دارد → `flatten()` الزامی
- **HEC-RAS**: باینری نصب نیست → `requires_hecras_install` + لینک رایگان USACE + ارتفاع آب با معادله Manning (برچسب `manning_approximation` — هرگز به‌عنوان خروجی HEC-RAS ارائه نمی‌شود)
- **SWAT+**: pySWATPlus ویرایشگر/کالیبراتور فایل‌های موجود است؛ اجرای کامل نیازمند باینری رایگان rev60 از swat.tamu.edu — وضعیت `prep_ready` صادقانه گزارش می‌شود

## ۳) اندپوینت

```
POST /api/v1/motors/chain
{
  "lat": 35.5, "lon": 51.5, "crop": "wheat",
  "planting_date": "2024-11-15", "years": 20,
  "slope_pct": 10, "optimize": true, "catchment_km2": 10
}
```
پاسخ شامل: `erosion`، `swat`، `water`، `flood`، `optimization`، `rothc`، `aquacrop`، `calibration`، `data_sources`، `cache_hit`.

## ۴) نتایج تست (تهران ۳۵.۵N / ۵۱.۵E، HTTP 200 در ۳.۴ ثانیه)

| بلوک | نتیجه |
|---|---|
| RUSLE | فرسایش **۱.۱۵ t/ha/yr** (کم‌خطر) — R=359.5، K=0.0516 (سیل‌گریدز) |
| SWAT+ prep | `prep_ready` — پروژه با اقلیم/خاک/کاربری واقعی |
| Pywr | قابلیت اطمینان **۱۴.۶٪**، کسری ۲.۱ MCM (مخزن کوچک ~۰.۱ MCM — واقع‌بینانه برای نیمه‌خشک) |
| HEC-RAS | Manning WSE **۰.۰۵ m** — نیاز به نصب HEC-RAS رایگان |
| RothC | SOC نهایی **۶۲.۸ t/ha**، تغییر -۰.۰۴۶ t/ha/yr |
| AquaCrop | گندم **۵.۶۷ t/ha**، برداشت ۲۰۲۵-۰۵-۳۱ |
| NSGA-II | جبهه پارتو ۲۴ نقطه؛ بهترین عملکرد ۸.۲۷ t/ha، کمترین فرسایش ۰.۲۳ t/ha/yr |
| KGE | `no_observed_data` (صادقانه — نیاز به سری مشاهداتی) |

## ۵) KPI

| شاخص | هدف | وضعیت |
|---|---|---|
| زمان پاسخ زنجیره کامل (با کش) | < ۶۰ ثانیه | ✅ **۵.۱ ثانیه** (کش: ۰.۰۱ ثانیه) |
| KGE کالیبراسیون | ≥ ۰.۵۵ | ⏳ پس از فراهم شدن داده مشاهداتی (`no_observed_data` صادقانه) |
| همه منابع رایگان | — | ✅ pywr, pymoo, pyRothC, AquaCrop-OSPy, pySWATPlus, HEC-RAS (رایگان USACE) |
| حذف مدل‌های ساده‌شده | — | ✅ RothC و AquaCrop به نسخه رسمی ارتقا یافتند؛ SWAT+/HEC-RAS به محض نصب باینری |

## ۶) قدم بعدی (فاز ۳)
اتصال داشبورد هیدروما و VLL به زنجیره واقعی؛ مقایسه سناریو کنار‌هم؛ رندر سیلاب HEC-RAS روی نقشه deck.gl؛ نصب باینری‌های رایگان SWAT+ و HEC-RAS برای اجرای کامل.
