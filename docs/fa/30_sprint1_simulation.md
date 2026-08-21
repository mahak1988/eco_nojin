# 30. اسپرینت ۱ فاز ۳ — هسته زنجیره شبیه سازی

**تاریخ:** 2026-08-17 | **وضعیت:** فعال | **طبقه بندی:** فنی
**مبنا:** سند ۲۸ (شروع فاز ۳)؛ سند ۲۷ فاز ۳.

> تحویل اسپرینت ۱: ماژول `engine/hydroma/simulation/` — قراردادهای
> بین مدلی، ماتریس سناریو، پورت RothC، رپر AquaCrop-OSPy 3.1 و ارکستراتور
> زنجیره RUSLE → AquaCrop → RothC.

---

## ۱) اجزا (کامیت این سند)

| مؤلفه | مسیر | نقش |
|---|---|---|
| قراردادهای داده | `simulation/contracts.py` | مدل های pydantic بین مدلی + برچسب صداقت (`data_source` + `model`) |
| سناریوها | `simulation/scenarios.py` | ماتریس Baseline/Medium/Intensive (CN، C-factor، P-factor) |
| پورت RothC | `simulation/runners/rothc_runner.py` | پیاده سازی ماهانه RothC-26.3: چهار مخزن فعال + IOM، اصلاحگر دما/رطوبت، تفکیک 46/54 |
| رپر AquaCrop | `simulation/runners/aquacrop_runner.py` | پکیج رسمی `aquacrop==3.1.0`؛ آب وهوای مصنوعی یا ورودی کاربر؛ parse Yield/Biomass |
| رپر RUSLE | در `orchestrator.py` | هسته C++ موجود (با fallback همان معادله) |
| ارکستراتور | `simulation/orchestrator.py` | اجرای زنجیره برای یک سایت+سناریو با provenance کامل |

## ۲) نکات فنی مستندشده (یافته های یکپارچه سازی)
- **aquacrop 3.1**: ترتیب ستون های آب وهوا positional است:
  `MinTemp, MaxTemp, Precipitation, ReferenceET, Date` (Date آخر —
  مطابق CSV نمونه خود پکیج)؛ تاریخ کاشت Crop با فرمت `MM/DD`؛
  خروجی عملکرد با کلید `Dry yield (tonne/ha)` (تبدیل به kg/ha)؛
  زیستتوده از `get_crop_growth()['biomass']` با **max فصل** (آخرین عنصر بعد
  از برداشت صفر است).
- **RothC**: اصلاح گر دما `47.9/(1+exp(106.06/(T+18.27)))` — مقدار ۱ در
  ~۱۰°C (نه ۲۵°C)؛ آب در دو شاخه piecewise استاندارد؛ حفاظت جرم در تستها
  تضمین می شود.
- **صداقت**: همه خروجی ها `data_source="simulated"` + نام/نسخه مدل دارند؛
  هیچ خروجی مدل به عنوان داده میدانی ارائه نمی شود.

## ۳) وضعیت اعتبارسنجی (صادقانه)
- RothC: **validation در برابر خروجی مرجع RothC-26.3 در اسپرینت ۲** —
  تا آن زمان برچسب `model="RothC (in-house port, pending reference validation)"`.
- AquaCrop: پکیج رسمی FAO — خروجی معتبر؛ آب وهوای پیشفرض مصنوعی است
  (جایگزینی با داده هواشناسی واقعی در اسپرینت ۲).

## ۴) تستها
- ۲۳ تست جدید (RothC: حفاظت جرم، واپاشی، اثر دما، شاخه های رطوبت؛
  AquaCrop: اجرای کامل فصل گندم؛ ارکستراتور: زنجیره کامل، کاهش فرسایش
  مطابق فاکتورها، برچسبهای صداقت).
- کل سویت: **۴۵۴ پاس** (از ۴۳۱).

## ۵) گام بعدی (اسپرینت ۲)
SWAT+ باینری + اتصال خروجی به WEAP/HEC-RAS؛ کالیبراسیون (Sobol + UQ)؛
validation مرجع RothC؛ آب وهوای واقعی؛ اندپوینت `POST /api/v1/simulation/run`.
