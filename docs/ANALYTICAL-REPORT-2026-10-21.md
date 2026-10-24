
# گزارش تحلیلی جامع پروژه HyDroMA (اکو نوژین)

**تاریخ تحلیل:** ۲۰۲۶-۱۰-۲۱  
**تحلیل‌گر:** CodeGeeX AI  
**دامنه:** کل مخزن `D:\HyDroMA` — موتور علمی، پلتفرم خدمات، دیتابیس، ابزارها و مستندات

---

## ۱. خلاصه اجرایی

پروژه **HyDroMA (اکو نوژین)** یک پلتفرم جامع مدل‌سازی علمی آب-انرژی-کشاورزی است که از دو نیمه اصلی تشکیل شده:

| نیمه | نقش | تکنولوژی | اندازه |
|---|---|---|---|
| **engine/** | هسته علمی آفلاین (FOSS-only) | Python + NumPy/SciPy + C++/pybind11 + Numba | ~70 مدل ثبت‌شده، ۴۰+ دامنه |
| **services/** | پلتفرم کسب‌وکار FastAPI | FastAPI + SQLAlchemy + Pydantic | ۷۱+ دامنه سرویس، ۱۱۸+ route |

**نقاط قوت بنیادین:**
- ✅ معماری دو-نیمه با مرز سخت (Import Guard) — بهترین شیء Separation of Concerns
- ✅ قرارداد صداقت (Honesty Contract) — «وجود فایل = قابلیت نیست»
- ✅ ۱۰ ترمز ایمنی (SB-01..SB-10) و ۱۳ قاعده معماری (AR-01..AR-13)
- ✅ Money = Decimal (هرگز float) — دوبل‌انتری دفتر کل با اعتبارسنجی
- ✅ مدل‌های علمی با لنگر بیرونی مستقل (FAO-56, NEH/TR-55, Theis, RothC)
- ✅ برنامه بازسازی ۸-فازه (B0-B7) کامل اجرا شده — ۴۵ نقص رفع، ۶۵۷۲ تست

**نقاط ضعف بحرانی:**
- ❌ ۵۵ مدل از ۷۰ مدل unvalidated (تنها ۱۸.۶٪ S3)
- ❌ ده شاخص نوین (§۶.۲) هیچ‌کدام پیاده نیستند
- ❌ `model_dispatcher.py` با ۲۶۱۹ خط — نقض سقف ۸۰۰ خط
- ❌ `quantity.py` فقط یک stub ۱۰-خطی — `pint` هنوز ادغام نشده
- ❌ `data/mirror/` وجود ندارد — E2E آینه داده مسدود
- ❌ ۱۳ تصمیم باز (D-03..D-18) مانع پیشرفت فازها
- ❌ فرانت‌اند حذف شده — محصول فقط API است

---

## ۲. تحلیل معماری

### ۲.۱ مرز معماری (Architecture Boundary)

```
services/ ←── Gateway Facade ←── EngineGateway ←── engine/
   (FastAPI)    (_gateway_facade.py)    (gateway/__init__.py)   (scientific core)
```

**ارزیابی:** این الگو **عالی** است. مرز سخت بین لایه کسب‌وکار و هسته علمی با `tools/detect_imports.py` (AST static import guard) اعمال می‌شود. سرویس‌ها فقط از طریق `_gateway_facade.py` به موتور دسترسی دارند.

**مشکل:** ۶ bypass در `_gateway_facade_adapters/` که مستقیماً `engine.hydroma.*` را وارد می‌کنند. این تخلف‌ها در `import_guard_policy.json` ثبت شده‌اند اما باید از طریق `EngineGateway` کوچ داده شوند.

### ۲.۲ الگوی Gateway

`EngineGateway` با ۷۰+ مدل ثبت‌شده و dispatch route table، یک **Facade Pattern** قوی است. اما:

- **مشکل اندازه:** `model_dispatcher.py` با ۲۶۱۹ خط یک **God Object** است. هر تغییر مدل نیازمند ویرایش این فایل است.
- **پیشنهاد:** شکستن به domain-specific dispatchers (hydrology_dispatcher, soil_dispatcher, climate_dispatcher, ...) با یک registry pattern.

### ۲.۳ Dependency Inversion (Ports & Adapters)

```
engine/ports/ →抽象 پورت‌ها (PersistencePort, EvidenceAdapter)
adapters/     → پیاده‌سازی (sqlite_persistence)
```

**ارزیابی:** الگو **درست** پیاده شده. هسته به پورت وابسته است نه پیاده‌سازی. اما `database.config` هنوز یک استثنای ثبت‌نشده در import guard دارد.

### ۲.۴ حکمرانی AI (AI Governance)

چه سطح اختیار:
1. **اطلاعی** → Daneshyar (فقط شواهد ارائه می‌دهد)
2. **عملیاتی کم‌ریسک** → Tasmimyar CAUTION ≥ ۰.۴
3. **اجرایی محدود** → RECOMMEND ≥ ۰.۷ + SB-05
4. **حساس** → STOP + تأیید انسانی

**ارزیابی:** چارچوب **بسیار پیشرفته** است. اصل «AI حق تغییر معادله/پارامتر علمی ندارد» (AR-07) یک safeguard حیاتی است.

---

## ۳. تحلیل کیفیت کد

### ۳.۱ تست

| سوئیت | تعداد | وضعیت |
|---|---|---|
| `pytest engine/` | ~۲۷۰۰ passed | ۷ شکست (اثر انتقال اسناد + drift) |
| `pytest engine/strict_tests` | ۱۳۲۳ passed | ۰ شکست ✅ |
| `pytest services/` | ~۱۴۵۰ passed | ۱ شکست |
| `pytest tests/` | ۱۲۴ passed | ✅ |
| **مجموع** | **~۶۵۷۲** | |

**نکات:**
- strict_tests با ۱۳۲۳ تست علمی یک **standout** است — تطابق با FAO-56, SPI, Theis, RUSLE
- ۷۱/۷۱ دامنه سرویس تست دارند (پیش از بازسازی: ۳۹ بدون تست)
- Heavy RAG tests (torch/sentence-transformers) تحت xdist crash می‌کنند — نیاز به sharding

### ۳.۲ Lint و Type Safety

| ابزار | نتیجه | ارزیابی |
|---|---|---|
| ruff | ~۸۱۵ finding (baseline ۷۶۹) | بدهی lint قابل توجه (+۴۶) |
| mypy engine/ | ۰ خطا در ۴۱۶ فایل | **عالی** ✅ |
| import guard | ۰ تخلف (بعد از رفع) | ✅ |

### ۳.۳ فایل‌های حجیم

| فایل | خطوط | سقف | وضعیت |
|---|---|---|---|
| `engine/gateway/model_dispatcher.py` | ۲۶۱۹ | ۸۰۰ | ❌ نقض شدید |
| `services/api_gateway/main.py` | ۱۱۷۸ | — | ⚠️ monolith |
| `database/models.py` | ۲۰۰۰ | — | ⚠️ بزرگ |
| `services/_gateway_facade.py` | ۱۳۵۵ | — | ⚠️ بزرگ |

---

## ۴. تحلیل امنیت

### ۴.۱ نقاط قوت
- ✅ HMAC webhook با fail-closed (BANK_WEBHOOK_SECRET)
- ✅ Rate limiting احراز هویت (token-bucket)
- ✅ PrivacyVault رمزگذاری‌شده (بعد از رفع ۶ نقص)
- ✅ Prometheus bind به 127.0.0.1 (config-gated)
- ✅ Money detox + Scientific detox sweeps

### ۴.۲ نقاط ضعف باقی‌مانده
- ⚠️ SEC-05: endpointهای cost/compute بدون authz (voice, mrv, science)
- ⚠️ SEC-06: backup router با 16 endpoint بدون authz
- ⚠️ SEC-13: CSRF exemptions روی routeهای state-changing auth
- ⚠️ SEC-16: enumeration risk
- ⚠️ SEC-17: 2FA بدون TOTP
- ⚠️ SEC-19: password policy ضعیف
- ⚠️ SQLite 3.49.1 < 3.51.3 — WAL fail-open

---

## ۵. تحلیل داده و مدل

### ۵.۱ وضعیت مدل‌های علمی

```
S0 (stub)        :  ۰
S1 (implemented) : ۴۷  (۶۷.۱٪)
S2 (tested)      : ۱۰  (۱۴.۳٪)
S3 (validated)   : ۱۳  (۱۸.۶٪) ← هدف: ≥۸۰٪
```

**این بزرگترین gap پروژه است.** ۵۵ مدل unvalidated یعنی بیش از ۷۸٪ مدل‌ها شواهد مستقل ندارند.

### ۵.۲ لنگرهای بیرونی

| CANON | مدل | وضعیت |
|---|---|---|
| CANON-001 | ET₀ Penman-Monteith | ✅ VALIDATED_EXTERNAL |
| CANON-002 | ET₀ Hargreaves | ✅ VALIDATED_EXTERNAL |
| CANON-004 | SCS-CN | ✅ VALIDATED_EXTERNAL |
| CANON-005 | Theis | ⚠️ VALIDATED_METHOD |
| CANON-006 | van Genuchten | ⚠️ PARTIAL |

### ۵.۳ ده شاخص نوین (§۶.۲)

FDII · CDHE · CMSI · WSNI · RRI · IWEq · WAI · WVI · PSI · CW — **هیچ‌کدام پیاده نیستند.**  
قاعده: هر شاخص پیش از کدنویسی باید **تعریف چاپ‌شده + لنگر مرجع مستقل** داشته باشد.

### ۵.۴ دیتابیس

- **SQLite** (لایه ۱) + **PostgreSQL** اختیاری (لایه ۳)
- **Alembic:** single head، ۱۵+ revision، idempotent pattern ✅
- **مشکل:** جداول ecocoin در هیچ migration نیستند، village ~۱۸ جدول بدون migration
- **مشکل:** `quantity.py` فقط stub — `pint` هنوز ادغام نشده (G-Z5)

---

## ۶. تحلیل دامنه‌های سرویس

پلتفرم خدمات با **۷۱+ دامنه** بسیار گسترده است:

| دسته | دامنه‌ها | ارزیابی |
|---|---|---|
| **هسته کسب‌وکار** | finance, commerce, inventory, marketplace, wallet | ✅ پیاده‌شده و تست‌شده |
| **علمی/محیط‌زیستی** | carbon, mrv, science, satellite, ecosystem | ⚠️ بخشی پیاده |
| **اجتماعی/محلی** | village, tourism, land, rangeland, livestock | ⚠️ بخشی پیاده |
| **زیرساختی** | auth, notification, observability, reliability, backup | ⚠️ بخشی |
| **پیشرفته** | blockchain, ai, oracle, simulation, knowledge | ⚠️ بخشی/stub |
| **قانونی/انطباق** | legal, compliance, privacy, audit, provenance | ⚠️ بخشی |

**ریسک:** گستردگی بیش از حد دامنه‌ها بدون عمق کافی در هرکدام. برخی دامنه‌ها (oracle, design_engine, nojin) نقص‌های نهفته داشتند.

---

## ۷. تحلیل عملیات و استقرار

| مورد | وضعیت | اولویت |
|---|---|---|
| Docker حذف شده (DP-2) | runtime/ supervisor خالص‌پایتون | ✅ |
| SQLite WAL safe | نیاز به upgrade به 3.51.3 | P1 |
| OTel tracing | config-gated (OTEL_ENABLED) | P2 |
| Backup/restore drill | شواهد اجرا ثبت شد | P2 |
| Performance baseline | گزارش نوشته شد | ✅ |
| Heavy RAG sharding | نیاز به CI job جداگانه | P1 |

---

## ۸. نکات بهبود (اولویت‌بندی)

### 🔴 اولویت P0 — بحرانی

| # | بهبود | توضیح | تلاش |
|---|---|---|---|
| 1 | **شکستن `model_dispatcher.py`** | ۲۶۱۹→<۸۰۰ خط. استخراج domain dispatchers با registry pattern | بالا |
| 2 | **ادغام `pint` در `quantity.py`** | جایگزینی stub با `pint.UnitRegistry` واقعی — الزام AR-06 | متوسط |
| 3 | **رفع مسیر اسناد سخت‌کد** | `test_architecture_rules.py:34` → `docs/specs/` | کم |
| 4 | **بستن تخلف‌های import guard** | کوچ `_gateway_facade_adapters/` از طریق Gateway | متوسط |

### 🟠 اولویت P1 — مهم

| # | بهبود | توضیح | تلاش |
|---|---|---|---|
| 5 | **اعتبارسنجی مدل‌های موتور** | ۵۵ مدل unvalidated → هدف ≥۲۵٪ S3 در ۹۰ روز | بسیار بالا |
| 6 | **پیاده‌سازی شاخص‌های نوین** | FDII, CDHE, CMSI, ... — هرکدام با لنگر مرجع مستقل | بالا |
| 7 | **ارتقای SQLite به 3.51.3** | فعال‌سازی WAL ایمن + رفع SEC-10 | کم |
| 8 | **بستن شکاف‌های امنیتی** | SEC-05 (authz), SEC-06 (backup guard), SEC-13/16/17/19 | متوسط |
| 9 | **ایجاد `data/mirror/`** | آینه داده باز + E2E ingestion pipeline | بالا |
| 10 | **شارد RAG در CI** | جدا کردن torch/sentence-transformers از xdist | کم |

### 🟡 اولویت P2 — مطلوب

| # | بهبود | توضیح | تلاش |
|---|---|---|---|
| 11 | **کاهش بدهی lint** | ruff ۸۱۵→۷۶۹ baseline — E501, F401, F811, F821 | مکانیکی |
| 12 | **مهاجرت جداول خارج registry** | ecocoin pair + village tables → Alembic | متوسط |
| 13 | **شکستن `main.py` assembly** | ۱۱۷۸ خط → router auto-registration | متوسط |
| 14 | **بستن تصمیمات باز** | D-04 (Eco Coin), D-07 (payment), D-15 (hosting) | تصمیم |
| 15 | **Provenance روی هر payload** | سیم‌کشی تولید → تصمیم → evidence | متوسط |

### 🟢 اولویت P3 — بلندمدت

| # | بهبود | توضیح | تلاس |
|---|---|---|---|
| 16 | **فرانت‌اند (D-18)** | React/Vite با OpenAPI contract — محصول قابل استفاده کاربر | بسیار بالا |
| 17 | **Canary Dispatch (A/B مدل)** | زیرساخت مقایسه مدل‌های جایگزین | بالا |
| 18 | **Microservice split** | فقط با load evidence (DP-2) | بالا |
| 19 | **NPV/Payback یکسان‌سازی** | دو قرارداد ناهمخوان در بسته | متوسط |
| 20 | **i18n کامل** | ۱۵ locale ناقص | متوسط |

---

## ۹. نقشه راه پیشنهادی ۹۰ روزه

### فاز ۱ (هفته ۱-۲): تثبیت
- شکستن `model_dispatcher.py` → domain dispatchers
- ادغام `pint` در `quantity.py`
- رفع مسیر اسناد + بستن import guard violations
- ارتقای SQLite + شارد RAG

### فاز ۲ (هفته ۳-۶): اعتبارسنجی
- اعتبارسنجی ۱۰ مدل اولویت‌بالا (هدف: S3 از ۱۸.۶٪ به ۲۵٪)
- پیاده‌سازی ۳ شاخص نوین با لنگر مرجع
- بستن شکاف‌های امنیتی P1
- ایجاد `data/mirror/` + ingestion pipeline

### فاز ۳ (هفته ۷-۱۰): بهبود کیفیت
- کاهش بدهی lint به baseline
- مهاجرت جداول خارج registry
- Provenance روی هر payload علمی
- بستن تصمیمات باز (D-04, D-07, D-15)

### فاز ۴ (هفته ۱۱-۱۳): آماده‌سازی release
- فرانت‌اند MVP (React/Vite + OpenAPI)
- Canary Dispatch زیرساخت
- E2E journey tests
- Performance baseline refresh
- Release runbook نهایی

---

## ۱۰. جمع‌بندی

پروژه **HyDroMA** یک **شاهکار معماری** در حوزه مدل‌سازی علمی آب-کشاورزی است. قرارداد صداقت، ترمزهای ایمنی، مرز سخت معماری و حکمرانی AI آن در سطح **best-in-class** هستند. با این حال، فاصله بین «معماری عالی» و «محصول قابل ارائه» هنوز قابل توجه است:

| بعد | نمره (از ۱۰) | توضیح |
|---|---|---|
| معماری | **۹** | مرز سخت، ports/adapters، Gateway pattern |
| کیفیت کد | **۶** | فایل‌های حجیم، بدهی lint، stub‌ها |
| تست | **۷** | ۶۵۷۲ تست خوب، اما strict_tests فقط ۱۳۲۳ |
| اعتبارسنجی علمی | **۴** | فقط ۱۸.۶٪ S3 — بزرگترین gap |
| امنیت | **۶** | بخشی رفع شده، شکاف‌های باقی‌مانده |
| عملیات | **۵** | بدون Docker، SQLite قدیمی، OTel غیرفعال |
| محصول | **۳** | بدون فرانت‌اند، تصمیمات باز، شاخص‌ها ناقص |

**اولویت مطلق:** اعتبارسنجی مدل‌های علمی (P1 #5) — این هسته ارزش‌آفرینی پروژه است و بدون آن، تمام زیرساخت اطراف آن ارزش عملیاتی ندارد.

---

*این گزارش توسط CodeGeeX AI بر اساس مطالعه عمیق کد، مستندات و گزارش‌های موجود پروژه تهیه شده است.*
