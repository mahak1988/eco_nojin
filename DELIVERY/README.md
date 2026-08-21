# DELIVERY — Eco Nojin / HyDroMa (2026-08-14)

خلاصه تحویل نهایی این دوره کاری. جزئیات کامل در `docs/` و گزارش‌های worker.

## ۱. هسته علمی C++20 — `engine/cpp_core/` (جدید/ارتقایافته)

| ماژول | فایل‌ها | وضعیت |
|---|---|---|
| ریچاردز ۱بعدی (فرم مختلط، پیکارد اصلاح‌شده Celia 1990) | `richards.hpp/cpp` | ✅ تست‌شده |
| سنت-ونانت ۱بعدی (حجم محدود Rusanov + مانینگ) | `saint_venant.hpp/cpp` | ✅ تست‌شده |
| تراز آب FAO-56 دوضریب Kc (Ks/Ke/TEW/REW) | `crop_water.hpp/cpp` | ✅ تست‌شده |
| رسوب توزیعی RUSLE + SDR + تله‌اندازی Brune | `sediment.hpp/cpp` | ✅ تست‌شده |
| نمونه‌برداری MC/LHS + انسیبل محصول | `sampling.hpp/cpp` | ✅ تست‌شده |
| ۵ ماژول v1 (هیدرولوژی، خاک، فرسایش، اقلیم، شاخص‌ها) | v1 | ✅ رفع باگ K |
| بیندینگ pybind11 + CMake + تست‌ها | `bindings/`, `CMakeLists.txt`, `tests/` | ✅ (نیاز CMake برای build بیندینگ) |

**تست‌ها:** ۷۰/۷۰ سبز (۳۵ v1 + ۳۵ advanced) — شامل حفظ جرم ریچاردز،
جرم سیلاب سنت-ونانت (<۲٪)، بستن تراز آب (~۰mm)، رگرسیون دوسویه
C++↔Python (مقدار K ون‌گنوختن).

**باگ علمی رفع‌شده:** فرمول Mualem–van Genuchten K(h) در C++ پرانتز بیرونی
نداشت (تا ۵۰,۰۰۰ برابر خطا) — با مرجع پایتون هم‌ارز و قفل شد.

## ۲. اصلاحات پایتون و سرویس‌ها (همه با pytest تأیید: ۱۲۸/۱۲۸)

- باگ `datetime` در `routers/carbon.py` (کرش POST /verify) — رفع
- CORS وحشی (`*` + credentials) — رفع با لیست صریح از env
- تست کهنه `mobile_features` — رفع به `inclusive_access`
- داده ماهواره: برچسب `data_source="simulated"` (صداقت داده)
- `requirements.txt` پین‌شده + `pyproject.toml` با dependencies واقعی + extras
- `README.md` دوزبانه سالم (رفع mojibake)
- `docker-compose.yml` بدون رمز جاسازی‌شده + `.env.example`
- دروازه احراز اختیاری `AUTH_ENABLED/AUTH_TOKEN` (با `compare_digest`)

## ۳. فرانت‌اند و i18n — `frontend/`

- ۱۴ زبان × ۹۵ کلید، ۰ missing/extra/empty
- RTL کامل برای fa/ar/ur (`i18n-context`, `LocaleAttributeSync`, CSS منطقی)
- `lib/config.ts` برای `NEXT_PUBLIC_API_URL` + ۹ پنل اصلاح‌شده
- دسترس‌پذیری: aria-live/alert/busy، focus-visible، lang پویا
- تایپ‌چک: فقط خطای از پیش موجود capacitor.config.ts

## ۴. مستندات — `docs/en|fa/`

- ۱۰_quality_standards (STD-001…015) · ۱۱_weaknesses_and_fixes (W-001…021)
  · ۱۲_30_year_strategy (تا ۲۰۵۵) — دوزبانه
- اسناد ۰۰ تا ۰۹ (دوره قبل) + README دوزبانه

## ۵. نوآوری با شواهد کمی — `benchmarks/`

- LHS: **۹۵×** کاهش خطای استاندارد vs مونت‌کارلو (C++: ۱۰۸×)
- نومبا vs پایتون خالص: ۶× (K ون‌گنوختن)، ۵۰× (مسکینگام)
- هم‌ارزی عددی C++ ↔ Numba با تست رگرسیون

## محدودیت‌های صادقانه

- ~~بیندینگ pybind11~~ ✅ **ساخته و سیمکشی شد** (CMake 4.4.2 + pybind11 3.1.0): `from engine.hydroma.cpp_bridge import hydroma_core` — حفظ جرم دقیق در ریچاردز از پایتون تأیید شد
- پروژه هنوز git نیست؛ سرویس‌های placeholder (auth/ledger/…) باقی‌اند
- داده ماهواره شبیه‌سازی‌شده است و برچسب دارد
- اسناد ۱۱ وضعیت‌های باز را صادقانه فهرست کرده‌اند

## نحوه اجرا

```bash
pip install -r requirements.txt
uvicorn services.api_gateway.main:app --reload --port 8000
cd frontend && npm install && npm run dev
pytest
cd engine/cpp_core && build_advanced.bat && hydroma_advanced_tests.exe
```
