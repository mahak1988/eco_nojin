# 28. شروع فاز ۳ — زنجیره شبیهسازی یکپارچه (Kickoff)

**تاریخ:** 2026-08-17 | **وضعیت:** آماده اجرا | **طبقهبندی:** فنی
**مبنا:** سند ۲۷ فاز ۳ (هفته ۵–۱۰)؛ الزام بخش ۴۱ PDF؛ معماری بدون Docker.

> پیشنیازهای فاز ۱/۲ (پاکسازی تاریخچه، چرخش کلید، MRV) باید بسته شوند؛
> این سند نقشه اجرای زنجیره ۶ مدله است.

---

## ۱) راهبرد یکپارچهسازی (تصمیم کلیدی)

**اصل:** مدلهای معتبر جهان را یکپارچه میکنیم، بازنویسی نمیکنیم.
هر مدل یک **رپر استاندارد** میگیرد (همان interface: `run(inputs) -> outputs`)
و زنجیره با **ارکستراتور پایتون** و قرارداد داده بینمدلی به هم میپیوندد.

| مدل | راهبرد | وابستگی | وضعیت |
|---|---|---|---|
| **SWAT+** (هیدرولوژی حوضه) | اجرای باینری (subprocess) + پارس I/O فایل | اجرایی از swat.tamu.edu (ویندوز) | نیاز دانلود/مجوز — اولین گام |
| **RUSLE** | ✅ موجود در پروژه | — | آماده |
| **AquaCrop** | پکیج `aquacrop==3.1.0` (OSPy متنباز FAO) | pip | ✅ موجود در PyPI (تأیید شد) |
| **RothC** | پیادهسازی درونسازمانی از معادلات مرجع (≈۲۰۰ خط پایتون، دو مخزن بیوچار) | — | ساخت در اسپرینت ۱ |
| **WEAP** (تخصیص آب) | رایگان برای پژوهش؛ یا ماژول ساده تخصیص درونسازمانی (فاز بعد) | — | تصمیم در اسپرینت ۲ |
| **HEC-RAS** (هیدرولیک) | اجرایی رایگان USACE (subprocess) یا استفاده از هسته سنت-ونان موجود برای v1 | — | v1: هسته موجود |

## ۲) قرارداد داده بینمدلی (Data Contracts)

```
SWAT+   → {runoff_mm, recharge_mm, baseflow_mm}            → WEAP, HEC-RAS
RUSLE   → {erosion_t_ha_yr, c_factor}                      → MRV metrics
AquaCrop→ {yield_kg_ha, biomass, residue_kg_ha, wue}       → RothC (residue)
RothC   → {soc_change_t_ha_yr, co2e_t_ha}                  → MRV metrics
Scenarios: Baseline / Medium / Intensive با ماتریس پارامتر:
  CN (کاهش ۲–۸ / تا ۱۵ واحد)، Ks، AWC، C-factor (از NDVI)، P-factor (0.45–0.55 / 0.3–0.4)
```
فرمت: JSON Schema مشترک در `engine/hydroma/simulation/contracts.py` +
اعتبارسنجی pydantic؛ کش نتایج (Redis یا دیسک) + برچسب `data_source`.

## ۳) معماری ارکستراسیون

```
engine/hydroma/simulation/
├── contracts.py        # قراردادهای pydantic بین مدلها
├── orchestrator.py     # زنجیره: تعریف گراف + اجرا + کش + لاگ
├── scenarios.py        # سه سناریوی مداخله + ماتریس پارامتر
├── runners/
│   ├── base.py         # interface واحد: run(inputs)->outputs
│   ├── swat_runner.py  # subprocess + I/O فایل
│   ├── aquacrop_runner.py  # پکیج aquacrop
│   ├── rothc_runner.py     # پیادهسازی داخلی
│   └── hecras_runner.py    # v1: هسته سنت-ونان موجود
└── calibration.py      # Sobol sensitivity + Monte Carlo UQ + (EnKF-lite)
```

**گامهای اجرایی (اسپرینت ۱ — هفته ۱–۲ فاز ۳):**
1. `pip install aquacrop==3.1.0` + تست import و اجرای مثال گندم.
2. پیادهسازی `rothc_runner` (معادلات مرجع + تست در برابر داده منتشرشده).
3. `contracts.py` + `orchestrator.py` با دو مدل اول (RUSLE + AquaCrop) و سناریوها.
4. تستهای واحد (حداقل ۱۰) + حفظ ۳۸۵+ تست سبز.

**اسپرینت ۲ (هفته ۳–۴):** SWAT+ باینری + اتصال خروجی به WEAP/HEC-RAS؛
کالیبراسیون (Sobol + UQ)؛ API زنجیره برای تصمیمیار فاز ۴.

## ۴) ریسکها
- SWAT+ نیاز به مجوز/دانلود از swat.tamu.edu و آمادهسازی داده حوضه دارد
  (زمانبرترین بخش) — شروع زودهنگام.
- نسخههای مدل: قفل نسخه در requirements (aquacrop==3.1.0).
- سازگاری Python 3.11: aquacrop 3.x از numpy>=1.24 پشتیبانی میکند (بررسی در نصب).
