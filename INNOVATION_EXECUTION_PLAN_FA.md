# برنامهٔ اجرایی پیاده‌سازی بانک نوآوری اکو نوژین

| | |
|---|---|
| **شناسهٔ سند** | `INNOVATION-EXEC-2026-09-29` |
| **نسخه** | ۱٫۰ |
| **تاریخ** | ۱۴۰۴/۰۷/۰۸ (۲۰۲۶-۰۹-۲۹) |
| **سند بالادستی** | `INNOVATION_BACKLOG_FA.md` (۱۱۰ قلم) |
| **ADR** | `docs/adr/0007-innovation-programme.md` |
| **نسخهٔ ماشین‌خوان** | `docs/innovation_backlog.csv` |
| **ابزار پیگیری** | `scripts/innovation_backlog.py` |

---

## ۰. قواعد حاکم بر این برنامه

این قواعد، میراث `docs/standards/` هستند و رعایتشان شرط اعتبار هر تغییری است که از این برنامه بیرون بیاید.

| قاعده | منبع | الزام عملی در این برنامه |
|---|---|---|
| عدم جعل داده | `S-HONEST`, `W-001` | هیچ endpoint جدیدی بدون `data_source` برنگردد. نبود داده واقعی = `credentials_required` یا `simulated` با برچسب صریح |
| انضباط واحدی | `S-SCI` | هر کمیت تازه با واحد صریح و تست واحد بیاید |
| ردیابی کالیبراسیون | `S-SCI` | هر مدل تازه `provenance` + `model_version` + `calibration_set_id` داشته باشد |
| منشأ در برابر وضعیت | `ENGINEERING_INDEX_FA.md §۴٫۱` | مدل تازه = `novel` + `research_definition`، وگرنه رد می‌شود |
| سند، وضع را توصیف می‌کند نه آرزو را | `ENGINEERING_INDEX_FA.md §۴٫۳` | در `INNOVATION_BACKLOG_FA.md` عبارت «کار خواهد شد» مجاز نیست |
| استاندارد دستکاری‌نشده | `ENGINEERING_INDEX_FA.md §۴٫۲` | اگر تغییری در استاندارد لازم شد: بازگردانی + بازاستخراج، نه دستکاری |
| انطباق با قرارداد | `tests/contract/gates.py` | هیچ PR سبز نیست اگر قرارداد نقض شود |
| RLS پیش‌فرض | `docs/adr/0004` | هر جدول جدید با RLS از روز اول |
| تقارن دوزبانه | `README.md` | هر قلم رابط کاربری، `fa` و `en` را با هم می‌آورد |
| حذف با تشریف | `docs/standards/deletion-procedure.md` | حذف کد = PR جدا + ثبت در `docs/standards/deletion-procedure.md` |

### ۰٫۱ دروازه‌های سرتاسری (هر PR باید رد شود)

```bash
# ۱) وابستگی و سلامت import
.venv\Scripts\python.exe -m pytest tests/contract/test_g1_import_smoke.py -q

# ۲) واحد و انتزاع پایتون
.venv\Scripts\python.exe -m pytest tests/unit -q

# ۳) علوم سخت‌گیرانه
.venv\Scripts\python.exe -m pytest engine/strict_tests -q

# ۴) بومی (C++20)
.venv\Scripts\python.exe scripts/run_cpp_tests.py

# ۵) قرارداد و صداقت
.venv\Scripts\python.exe -m pytest tests/contract -q

# ۶) مهاجرات پایگاه‌داده (SQLite)
.venv\Scripts\python.exe -m pytest tests/integration/test_sqlite_migrations.py -q

# ۷) لینت و نوع
ruff check .
ruff format --check .
mypy --strict engine/hydroma/config/settings.py services/api_gateway/

# ۸) فرانت‌اند
pnpm -C apps/web type-check
pnpm -C apps/web test

# ۹) قرارداد فرانت‌اند (Orval)
node scripts/check-api-contract.mjs

# ۱۰) انطباق پیشنهادی (از موج صفر)
node scripts/check-contrast.mjs
node scripts/check-cwv.mjs
node scripts/check-locale-encoding.mjs
node scripts/innovation_backlog_gate.mjs
```

---

## ۱. موج صفر — W0 (۰–۲ ماه): پایهٔ اعتماد

**هدف موج:** ۲۶ قلم. خروجی واحد: «هر چیزی که کاربر می‌بیند، مُهر دارد؛ هر چیزی که CI اجرا می‌کند، مسدود می‌شود.»

### ۱٫۱ فاز W0-A — مُهر منبع و zero-config (هفتهٔ ۱–۳)

#### W0-1 · مُهر منبع روی هر عدد (قلم ۱)

**مسیرها:** `engine/hydroma/formulas/registry.py` · `services/provenance/stamp.py` · `packages/ui/src/ProvenanceStamp.tsx` · `apps/web/src/components/scientific/ResultBlock.tsx`

**گام ۱ — بازرسی وضعیت موجود (بدون تغییر کد):**
```bash
.venv\Scripts\python.exe -c "from engine.hydroma.formulas.registry import *; print([n for n in dir() if 'REGISTR' in n.upper()])"
.venv\Scripts\python.exe scripts\registry_guard.py
```
ثبت در گزارش: کدام ستون‌های `provenance` امروز واقعاً پر می‌شوند. **اگر ستون پر نمی‌شود، این قلم به تعویق می‌افتد** — ساخت UI روی دادهٔ خالی نقض `S-HONEST` است.

**گام ۲ — قرارداد `ProvenanceStamp` (خلف قرارداد موجود):**
```python
# engine/hydroma/formulas/records.py — الگوی رکورد موجود استفاده شود
class ProvenanceStamp(BaseModel):
    quantity: str                      # نام کمیت
    value: float | int | None
    unit: str                          # اجباری طبق S-SCI
    data_source: Literal["satellite", "climate", "soil", "model", "field", "simulated"]
    model_version: str | None          # None ⇒ الزام بازه عدم‌قطعیت
    calibration_set_id: str | None
    provenance: Literal["standard", "composite", "novel"]
    status: Literal["verified", "divergent", "stub"]
    uncertainty: tuple[float, float] | None
    retrieved_at: datetime
    label: Literal["measured", "modelled", "simulated", "credentials_required"]
```

**گام ۳ — سرویس stamp:**
`services/provenance/stamp.py` باید این را از هر رکورد فرمول بسازد و اگر `value is None` بود، `label="credentials_required"` بدهد. **هرگز عدد پیش‌فرض تولید نکن.**

**گام ۴ — کامپوننت UI:**
```tsx
// packages/ui/src/ProvenanceStamp.tsx
export function ProvenanceStamp({ stamp }: { stamp: ProvenanceStampDTO }) {
  const tone = {
    measured: 'success', modelled: 'info', simulated: 'warning', credentials_required: 'neutral',
  }[stamp.label];
  return (
    <button aria-label={t('provenance.open', { quantity: stamp.quantity })}
            className="inline-flex items-center gap-1 text-[10px]">
      <SourceGlyph label={stamp.label} />
      <span>{stamp.quantity}</span>
    </button>
  );
}
```
الزامات: `aria-label` فارسی و انگلیسی، `prefers-reduced-motion` رعایت شود، در RTL آینه‌نویسی صحیح (قلم ۹ را می‌شکند وگرنه).

**گام ۵ — دروازهٔ خودکار:**
تست جدید `tests/unit/test_provenance_completeness.py` که **هر عدد در پاسخ هر endpoint عمومی** را بررسی کند و اگر `provenance` نداشت fail شود. این تست، قلم ۱ را از «ویژگی» به «ضمانت» تبدیل می‌کند.

**معیار پذیرش:** ۱۰۰٪ اعداد نمایشی مُهر دارند؛ تست جدید سبز؛ `ruff` و `pnpm type-check` سبز.

---

#### W0-2 · حالت zero-config (قلم ۳)

**مسیرها:** `services/satellite/soilgrids.py` · `services/satellite/open_meteo.py` · `services/api_gateway/main.py`

**گام ۱ — مشخص کردن پارامترهای اجباری فعلی.** `POST /api/v1/platform/analyze` را بخوان و جدول بساز: کدام فیلدها بدون آن نمی‌توان اجرا کرد.

**گام ۲ — لایهٔ inference:**
```python
# services/scientific_motors/data_repository.py
class ZeroConfigResolver:
    async def resolve(self, lat: float, lon: float, land_use: str) -> ResolvedInputs:
        soil   = await soilgrids_client.fetch(lat, lon)     # ISRIC
        climate= await open_meteo_client.fetch(lat, lon)    # ERA5
        if soil is None or climate is None:
            raise CredentialsRequired(quantity=["soil_water", "eto"],
                                       partial=True, received=[])
        return ResolvedInputs(soil=soil, climate=climate, inferred=["theta_r", "n", "soc"])
```
قانون: هر فیلد استنتاج‌شده باید `inferred=True` بگیرد و در UI با برچسب «برآورد» نمایش یابد. این `S-HONEST` است.

**گام ۳ — fallback تدریجی:** اگر فقط خاک واقعی بود و اقلیم نبود، `partial=True` + وضعیت صادقانه.

**معیار پذیرش:** درخواست با فقط `{latitude, longitude, area_ha}` موفق شود؛ نرخ تکمیل جریان آنالیز +۴۰٪ نسبت به خط پایه.

---

#### W0-3 · جریان تدریجی نتیجه (قلم ۴)

**مسیرها:** `services/api_gateway/main.py` · `services/simulation/service.py` · `apps/web/src/lib/sse.ts`

پیاده‌سازی: `ENABLE_REALTIME_SSE` را روشن کن، روی `POST /simulations/{id}/run` مسیر `GET /simulations/{id}/events` اضافه کن که رویدادهای `stage_started` / `progress` / `stage_done` / `failed` را از همان outbox موجود (`services/integration/outbox.py`) بخواند.

نکتهٔ اجرایی: در شبکهٔ ضعیف، SSE شکست می‌خورد. fallback اجباری به polling ساده با همان شناسهٔ کار.

---

### ۱٫۲ فاز W0-B — عملکرد و دسترسی‌پذاری (هفتهٔ ۲–۵)

#### W0-4 · کش دو‌لایه (قلم ۱۹)

**مسیرها:** `engine/hydroma/` (جایگزینی `SQLiteCache`) · `services/reliability/` · جدید `services/cache/`

معماری:
```
L1  = functools.lru_cache داخل فرایند (TTL 60s، فقط کمیت‌های خالص)
L2  = Redis (TTL مشتق از فرمول؛ SoilGrids ۳۰ روز، ERA5 ۶ ساعت، نتیجهٔ سناریو ۱۵ دقیقه)
Invalidation = pub/sub روی تگ (نه کلید) ⇒ `invalidate("soilgrids")`
```

قواعد حیاتی:
1. **فقط کمیت خالص کش می‌شود.** نتیجهٔ سناریو با ورودی تصادفی نباید کش شود.
2. TTL از فیزیک داده می‌آید، نه از حدس. جدول TTL باید در `docs/standards/S-SCI.md` ثبت شود.
3. `credentials_required` **هرگز** کش نمی‌شود — وگرنه نبود اعتبارنامهٔ ۲۴ ساعت باقی می‌ماند.
4. معیار: hit rate و P99 قبل/بعد در `reports/` ثبت شود.

---

#### W0-5 · اجرای غیربنکانی (قلم ۲۰)

**مسیرها:** `services/jobs/` · `services/workers/event_worker.py` · `services/integration/outbox.py` · `services/notification/`

الگوی دقیق:
1. `POST /simulations` بدنهٔ سنگین را نمی‌گیرد؛ فقط پارامترها و `id` برمی‌گرداند (202 Accepted).
2. job در outbox با `idempotency_key = hash(params)` ثبت می‌شود — تکرار درخواست نتیجهٔ تکراری نمی‌سازد.
3. worker در `workers/event_worker.py` اجرا و هر مرحله را رویداد می‌کند.
4. `GET /simulations/{id}` وضعیت + لینک به نتیجهٔ ذخیره‌شده در object storage.
5. پایان → اعلان از `services/notification/`.

معیار: `tests/load/locustfile.py` باید سناریوی سنگین داشته باشد که **صفر timeout** بدهد.

---

#### W0-6 · دروازهٔ WCAG (قلم ۹)

**مسیرها:** `scripts/check-contrast.mjs` · `scripts/check-locale-encoding.mjs` · جدید `.github/workflows/a11y-gate.yml`

پیاده‌سازی:
```bash
# ۱) کنتراست توکن‌ها (موجود — باید gate شود)
node scripts/check-contrast.mjs --fail-under 4.5
# ۲) کدگذاری locale (موجود — RTL و ارقام فارسی)
node scripts/check-locale-encoding.mjs --fail-on-error
# ۳) جدید: axe-core روی مسیرهای نماینده در هر جهت
npx playwright test apps/web/e2e/a11y --project=fa --project=ur --project=ar
```
نکتهٔ اجرایی: `ur` (اردو) با `fa` فرق دارد — خط نستعلیق `line-height` بیشتری می‌خواهد. اگر همان آستانهٔ خطا را بگذاری، تست مثبت کاذب می‌دهد.

---

#### W0-7 · حالت Lite و شب (قلم‌های ۱۳، ۱۱)

`apps/web/src/app/` — مسیرهای `/lite/*` جدا. سه قاعده:
1. بدون deck.gl، بدون Three.js، بدون نقشه. فقط فرم + نتیجه.
2. بودجهٔ سخت: ۲۰KB gzip جاوااسکریپت.
3. `check-cwv.mjs` روی این مسیر جدا اجرا شود با آستانهٔ LCP < 1.5s.

---

### ۱٫۳ فاز W0-C — شفافیت علمی (هفتهٔ ۳–۶)

#### W0-8 · ثبت مدل (قلم ۳۲) — **بسته‌کنندهٔ شکاف صداقت**

**وضعیت:** `ml/registry/` خالی است اما `provenance` ادعای `model_version` می‌کند. این تناقض را ببند.

پیاده‌سازی سبک (بدون افزودن وابستگی سنگین):
```
ml/registry/models/<name>/<version>/
├── provenance.json     # طبق README: الزام هر دادهٔ علمی تازه
├── metrics.json        # معیارهای اعتبارسنجی + مجموعهٔ کالیبراسیون
└── manifest.json       # checksum ورودی‌ها، انگشت کد، تاریخ
```
تست `tests/unit/test_model_registry.py`: هر مدلی که `model_version` می‌گیرد باید در registry وجود داشته باشد، وگرنه `S-HONEST` نقض است.

#### W0-9 · حذف یا تکمیل ۱۶ stub (قلم ۸۶)

**مرجع:** `docs/ENGINEERING_INDEX_FA.md:116-120`

روش اجباری و بدون ابهام — برای هر stub دقیقاً یکی از سه:
| تصمیم | شرط | اقدام |
|---|---|---|
| **حذف** | هیچ فراخوانی زنده‌ای ندارد | PR حذف + ثبت در `docs/standards/deletion-procedure.md` + `scripts/registry_guard.py` |
| **تکمیل** | مسیر اصلی محصول است | پیاده‌سازی + تست + `research_definition` اگر `novel` |
| **نگه‌داشتن صریح** | ارزش علمی دارد اما ناتمام | `stub_reason` دقیق‌تر + `xfail` در تست با همان دلیل |

اولویت با نمونهٔ `swatplus_watershed` و `modflow6_groundwater_flow` است که `NameError` می‌دهند — این‌ها **کد مردهٔ ثبت‌شده** هستند و بدترین نوع بدهی‌اند چون در رجیستری «موجود» به نظر می‌رسند.

**معیار:** ۰ stub بدون دلیل؛ رجیستری و اجرا هم‌راستا.

#### W0-10 · سبز کردن تست‌های قرمز (قلم ۸۷)

خروجی موجود: `reports/f0_1_xfail_ids.txt`. برای هر شناسه: درست کن، یا با همان دلیل `xfail` کن. تست قرمز مزمن، عادی‌سازی شکست یاد می‌دهد.

---

### ۱٫۴ فاز W0-D — امنیت و زیرساخت (هفتهٔ ۴–۸)

| قلم | پیاده‌سازی مشخص | معیار |
|---|---|---|
| ۴۳ (WAF/CSP) | CSP با nonce در `services/security/middleware.py`؛ rate limit توزیع‌شده Redis؛ `antibot.py` روی ثبت‌نام | کاهش ۹۰٪ ثبت‌نام انبوه |
| ۴۵ (نشت داده) | تست نشت روی `services/ai/rag.py`: دادهٔ کاربر نباید در لاگ یا پاسخ LLM برود | ۰ نشت |
| ۸۸ (قرارداد) | schemathesis + Pact روی `tests/contract/gates.py`؛ نقض = شکست CI | CI فقط با قرارداد سالم سبز |
| ۹۳ (feature flag) | لایهٔ نازک روی `settings` + Unleash؛ خاموش‌کردن فوری در بحران | رول‌آوت بدون downtime |
| ۹۴ (testcontainers) | CI با Postgres/Redis/NATS واقعی؛ `test_sqlite_migrations.py` به‌عنوان لایهٔ سریع باقی | کشف زودتر شکست |
| ۹۵ (immutable release) | SLSA + SBOM + امضای artifact؛ بدون این، staging غیرفعال می‌ماند | ۱۰۰٪ artifact امضاشده |
| ۱۰۹ (خط لوله) | Dagster روی `dvc.yaml` + `services/satellite` + `data_sources`؛ روزانه: دریافت → کالیبره → اجرا → انتشار | خط لولهٔ خودکار روزانه |
| ۴۷ (MCP) | سرور MCP روی FastAPI که ابزارهای `scientific_motors` را با ورودی ساختاریافته عرضه می‌کند | ثبت در اکوسیستم |
| ۵۱ (Webhook) | webhook با HMAC از همان outbox؛ مستند در `S-EVENT` | ۰ رویداد گمشده |
| ۶۶ (ردیابی) | Merkle proof روی مسیر محصول در `marketplace/traceability.py` — بدون توکن | ردیابی تا مصرف‌کننده |
| ۷۶، ۷۷ (پایداری) | متری انرژی CI + میزبانی سبز | کاهش ۳۰٪ انرژی |
| ۱۰۱ (A/B) | feature flag + analytics؛ فقط روی قابلیت‌های W0 | ۵ آزمایش در فصل |

### ۱٫۵ تصمیم سخت W0

> **قلم «صفر»: دربارهٔ `docs/adr/0001-language-strategy.md` تصمیم بگیرید.**

ADR سه سال است که Rust را برای sync و Go را برای gateway تعیین کرده و **هیچ خط کدی در مخزن نیست**. سه گزینه، یکی را انتخاب کنید و مکتوب کنید:

| گزینه | پیامد | توصیهٔ من |
|---|---|---|
| الف) اجرا در W2 | تعهد ۶–۱۸ ماهه، تیم دوگانهٔ زبان | ❌ اگر تیم کوچک است |
| ب) اصلاح ADR: FastAPI + WASM کافی است | یک زبان، یک پشته، اجرای همان چیزی که هست | ✅ برای تیم کوچک |
| ج) حذف کامل از ADR | سند سبک‌تر اما سابقهٔ تصمیم از بین می‌رود | ⚠️ فقط اگر قصد جایگزینی ندارید |

نگه‌داشتن یک ADR اجرانشده بدترین گزینه است، چون به همهٔ اسناد بعدی اعتبار کاذب می‌دهد.

---

## ۲. موج یک — W1 (۲–۶ ماه): قابل‌اعتماد، قابل‌فروش

### ۲٫۱ W1-A · علم درست (قلم‌های ۲، ۹۶، ۱۰۰، ۱۰۲، ۱۷، ۱۸)

**ترتیب اجرا اجباری است** — هر مرحله پیش‌نیاز مرحلهٔ بعد است:

```
[۱۷: تطابق backend] → [۱۸: Numba] → [۲۷: PINN] → [۲: نوار عدم‌قطعیت] → [۱۰۲: Test Twin] → [۹۶: داشبورد تصمیم]
```

| گام | قلم | جزئیات پیاده‌سازی | معیار |
|---|---|---|---|
| ۱ | ۱۷ | آزمون property-based روی `engine/hydroma/cpp_bridge`؛ هر دو backend روی ۱۰۰۰ ورودی تصادفی هم‌خوانی | اختلاف < 1e-9 |
| ۲ | ۱۸ | `@njit(cache=True)` در حلقهٔ داخلی RothC؛ `engine/safe_math.py` مرجع صحت | ۵× سرعت، پارادیگم تست سبز |
| ۳ | ۲۷ | PINN به‌صورت surrogate با **بازهٔ عدم‌قطعیت**؛ آزمون تطابق خطا اجباری در `engine/strict_tests` | RMSE < ۵٪ در برابر SWAT |
| ۴ | ۲ | خروجی p10–p90 از مرحلهٔ ۳؛ باند ECharts + پنجرهٔ «چرا این بازه» | نوار عدم‌قطعیت روی ۱۰۰٪ نمودارهای علمی |
| ۵ | ۱۰۲ | اجرای نسخهٔ موازی مدل پیش از تغییر، diff روی ۵۰۰ سناریوی تاریخی | ۰ regression علمی پنهان |
| ۶ | ۹۶ | هر تصمیم درجهٔ اطمینان می‌گیرد؛ بازهٔ پهن ⇒ «دادهٔ بیشتری لازم دارم» | کاهش ۲۰٪ تصمیم بد |
| ۷ | ۱۰۰ | داشبورد انحراف مدل از `models/validation/runner.py` + QA | تشخیص انحراف < ۷ روز |

> **قانون طلایی مرحلهٔ ۳:** PINN بدون بازهٔ عدم‌قطعیت و بدون آزمون تطابق خطا، **ممنوع**. مدل سریع‌تر با دقت پنهان‌تر، بدترین نوع شکست علمی است چون کاربر نمی‌داند.

### ۲٫۲ W1-B · هوش (قلم‌های ۲۷، ۲۸، ۳۰، ۳۳، ۳۴، ۳۵، ۳۶)

| قلم | مسیر | جزئیات | معیار |
|---|---|---|---|
| ۲۸ | `engine/hydroma/phenology.py` + `drought_motor.py` | زنجیرهٔ هشدار: هواشناسی → `phenology` → آستانهٔ تنش → `notification` | کاهش ۲۰٪ زمان تشخیص |
| ۳۰ | `services/ai/llm_router.py` | هر ابزار `scientific_motors` یک schema ورودی دارد؛ RAG فقط روی `data_manual` و `formulas/catalog` | دقت > ۸۵٪ |
| ۳۳ | `services/mrv/kobo.py` | مدل طبقه‌بندی + نگاشت خطا به توصیهٔ `crop_advisor` | دقت > ۸۰٪ محلی |
| ۳۴ | اپ موبایل `mobile/` | مدل Lite روی دستگاه؛ ارسال فقط بردار ویژگی نه ویدیو | تأخیر < 2s، < 5MB |
| ۳۵ | `services/analysis/scenario_agent.py` | تفکیک علّی روی دادهٔ سناریو | پذیرش توصیه +۱۵٪ |
| ۳۶ | `ml/features/` | تقویت زیست‌فیزیکی نه صرفاً هندسی | +۱۰٪ دقت |
| ۲۹ | `ml/` | RL برای سیاست آبیاری؛ آموزش روی دادهٔ سناریو + تأیید با SWAT | صرفه‌جویی ≥ ۱۵٪ |

### ۲٫۳ W1-C · مهار سطح (قلم‌های ۱۵، ۱۶، ۲۴، ۴۴)

**این فاز پیش‌نیاز هر چیزی است که بخواهد روی معماری فعلی ساخته شود.** اگر این انجام نشود، هر قلم W1 دیگر هزینهٔ نگهداری را بالا می‌برد.

#### گام ۱ — ۱۵: نقشهٔ ۵۷ سرویس → ۱۸ دامنه

نگاشت پیشنهادی (بر پایهٔ هم‌پوشانی شناسایی‌شده):

| دامنهٔ جدید | جذب‌کننده‌ها |
|---|---|
| `carbon` | `carbon` + `oracle` + `ecosystem` |
| `ledger` | `ledger` + `finance` + `ecowallet` + اختلاف مالی |
| `marketplace` | `marketplace` + `commerce` + `inventory` + `logistics` + `contracts` |
| `science` | `science` + `data` + `data_sources` + `data_manual` + `validation` |
| `quality` | `quality` + `quality_assurance` + `models` |
| `ops` | `observability` + `alerting` + `jobs` + `workers` + `reliability` + `backup` + `workflow` |
| `trust` | `provenance` + `privacy` + `audit` + `security` |
| `simulation` | `simulation` + `scientific_motors` + `design_engine` |
| `geo` | `satellite` + `map_engine` + `landscape` + `land` + `ogc` |
| `field` | `field_monitoring` + `mobile_monitoring` + `livestock` |
| `ai` | `ai` + `analysis` + `bots` + `telegram_bot` |
| `admin` | `admin` + `content` + `notification` + `sponsors` |
| `platform` | `api_gateway` + `auth` + `integration` + `supabase` |
| `research` | `analytics` + `reporting` + `tourism` + `ecosystem` |

روش اجرا:
1. **اول فقط رجیستری، بدون جابه‌جایی.** `services/_service_registry.yaml` با `domain`, `owner`, `paths`, `routers`, `tables`.
2. `scripts/registry_guard.py` را گسترش بده تا هر ماژول جدید ملزم به اعلام دامنه شود. **این نقطهٔ اعمال است، نه سند.**
3. سپس جابه‌جایی فایل، ماژول‌به‌ماژول، هرکدام PR مستقل.
4. در پایان، `services/<domain>/` ساختار واقعی می‌شود.

#### گام ۲ — ۱۶: FastAPI ماژولار
`main.py` از mount-all به mount-per-domain. معیار: `tests/contract/test_unmounted_routers.py` باید به تست **مثبت** تبدیل شود: هر router اعلام‌شده واقعاً mount است.

#### گام ۳ — ۲۴: مرز ایمنی نوع
`mypy --strict` روی `engine/hydroma/` و `services/_contracts/`. مرجع: `services/_contracts/money.py` و `formula.py` که الگوی خوبی دارند. `Decimal` برای پول، واحد صریح برای کمیت.

#### گام ۴ — ۴۴: جداسازی شبکه
`k8s/base/network-policies.yaml` با deny-by-default؛ تست نشت داده بین دامنه‌ها.

### ۲٫۴ W1-D · کاربر میدانی (قلم‌های ۵، ۶، ۷، ۱۰، ۱۲، ۱۴)

| قلم | جزئیات | معیار |
|---|---|---|
| ۷ USSD | `services/bots` — منوی کامل با سقف ۱۶۰ کاراکتر فارسی / ۱۸۲ لاتین؛ `fa` + `ar` + `ur`؛ تست `test_ussd.py` گسترش | MAU کاربران USSD |
| ۵ آفلاین | بستهٔ مزرعه: پروفایل خاک + نقشهٔ پایه + مدل‌ها + راهنمای محلی؛ Serwist + OPFS | اجرای آفلاین ≥ ۹۰٪ |
| ۱۲ نقشه | PMTiles + برش منطقه‌ای؛ کاشی جهانی بارگیری نشود | < 5MB برای یک منطقه |
| ۱۰ «چرا این توصیه؟» | زنجیرهٔ علّی از `formulas/catalog` + `science/citations` | تکمیل چرخهٔ راهنمایی |
| ۶ پروفایل نقش | واحدها، پیچیدگی مدل، زبان، حالت آفلاین برای دامدار/کشاورز/پژوهشگر | رضایت +۲۰٪ |
| ۱۴ آیکون بومی | آیکون‌ست محلی + آزمون معنایی | صفر ابهام |

### ۲٫۵ W1-E · استاندارد، درآمد، اعتماد (قلم‌های ۴۲، ۴۸، ۴۹، ۵۰، ۵۵، ۶۴، ۶۵، ۸۰–۸۵)

| قلم | جزئیات | معیار |
|---|---|---|
| ۴۹ STAC | `scripts/fetch_stac.py` را به سرویس کاتالوگ تبدیل کن؛ pgstac | کشف < ۲ ثانیه |
| ۴۸ OGC | Features + WaterML موجود؛ Coverages + SensorThings اضافه | انطباق OGC TC |
| ۵۰ API محصول | `openapi.json` + `orval.config.ts` آماده؛ نسخه‌بندی، rate limit، مستندات، صفحهٔ قیمت | ۱۰ مشتری پایلوت |
| ۴۲ گواهی صداقت | attestation قابل‌راستی‌آزمایی برای هر report؛ `check-verified-claims.mjs` تقویت شود | پذیرش توسط ۱ بیمه/خریدار |
| ۶۴ توکن بدون ICO | `MintController.sol` + `PhaseGate.sol`: بدون سوداگری، فقط کاربرد | ۰ ادعای سوداگری |
| ۶۵ DID | `passkeys.py` + `IdentitySBT` + `privacy/vault.py`؛ کنترل داده توسط کشاورز | درآمد دادهٔ کاربر |
| ۸۰–۸۵ درآمد | `finance` + `ecowallet` + `sponsors`: اشتراک + کارمزد MRV + API + اسپانسر | تنوع درآمد > ۳ منبع |

### ۲٫۶ W1-F · زیرساخت، تصمیم‌محور، رابط (قلم‌های ۲۱، ۲۳، ۵۴، ۶۸، ۷۰، ۷۱، ۷۲، ۷۴، ۷۵، ۷۸، ۷۹، ۹۱، ۹۲، ۹۷–۹۹)

| قلم | جزئیات | معیار |
|---|---|---|
| ۹۷ بهینه‌سازی | `optimize_chain.py` + `land_capability.py` + SWAT surrogate؛ LP/MILP با قیود | افزایش سود ۵–۱۵٪ |
| ۹۸ What-if | `whatif_engine.py` + Sankey | تعامل ۳۰٪ |
| ۹۹ LCA | `mrv` + محصول؛ ISO 14067 | برچسب روی ۱۰ محصول |
| ۷۲ AR | AR.js/WebXR + `map_engine`؛ لایهٔ رطوبت روی زمین | استفادهٔ هفتگی ۲۰٪ |
| ۷۴ صوت | Whisper محلی + LLM؛ «آبم را کی بدهم؟» | موفقیت گفتاری ۷۰٪ |
| ۷۵ WebGPU | انتقال `Visualization3D` | FPS > ۶۰ |
| ۹۱ Chaos | `eco_chaos_test_v2.py`: قطع CDSE، کندی DB، timeout شبکه | MTTR < 5min |
| ۹۲ مشاهده‌پذیری | OpenTelemetry روی همهٔ دامنه‌های W1-C | ردیابی ۱۰۰٪ |
| ۲۳ data mesh | DuckDB + Parquet + `dvc.yaml`؛ مالکیت داده در دامنه | گزارش < 30s روی ۱ سال |
| ۷۰، ۷۱ | GPU burst برای batch؛ serverless برای بار متغیر | ۱۰ سناریو < 10min؛ ۶۰٪ صرفه‌جویی idle |

---

## ۳. موج دو — W2 (۶–۱۸ ماه): غیرمتمرکز، نانومقیاس

**شرط ورود:** W1-C (مهار سطح) کامل و W1-A (علم درست) پایدار. بدون این دو، هر قلم W2 روی شن ساخته می‌شود.

### ۳٫۱ W2-A · نانوفناوری (قلم‌های ۵۶، ۵۷، ۵۸، ۶۰، ۶۱)

این تنها دسته‌ای است که به سخت‌افزار فیزیکی نیاز دارد و بنابراین مسیر متفاوتی دارد:

| قلم | فاز | جزئیات | معیار |
|---|---|---|---|
| ۵۶ نانوحسگر LoRaWAN | نمونه‌سازی | گره ۳ کلودولاری رطوبت/EC/نیتروژن؛ gateway روی `field_monitoring`؛ داده مستقیم به ورودی مدل | کاهش ۳۰٪ خطای آبیاری |
| ۶۱ انرژی خودگردان | نمونه‌سازی | حذف باتری؛ عمر ۳+ سال | عمر بدون تعویض |
| ۵۷ بیوفیلتر نانویی | آزمون زمینه‌ای | `biofertilizer.py` + نانوحامل؛ اتصال به مدل SWC؛ اعتبارسنجی در MRV | آزمون معتبر |
| ۶۰ نانوپلاستیک | پایش | طیف‌سنجی Raman؛ خروجی به `data_manual` | ۱۰ نمونه گزارش |
| ۵۸ نانوفیلتر آب | محصول | دو درآمدی: سلامت + آبیاری | < 10 NTU |

> **واقع‌گرایی:** این دسته به بودجهٔ سخت‌افزاری و شریک دانشگاهی نیاز دارد. اگر سؤال ۶ بخش ۱۱ پاسخ منفی بدهد، کل W2-A به W3 منتقل می‌شود. **این را به تعویق نیندازید — هزینهٔ تصمیم دیرهنگام بالاست.**

### ۳٫۲ W2-B · وب۳ و هویت (قلم‌های ۳۸، ۳۹، ۴۰، ۶۲، ۶۷)

```
[۳۹: PQC هیبرید] → [۳۸: VC هویت] → [۶۲: بازار کربن L2] → [۶۷: دوقلوی رویدادمحور]
                                    ↓
                              [۴۰: حریم خصوصی موقعیت]
```

| قلم | جزئیات | معیار |
|---|---|---|
| ۳۹ | `ledger/pqc.py` + `security/pqcrypto.py`: ML-KEM + امضای هیبرید | گزارش آمادگی + تست هیبرید |
| ۳۸ | W3C VC + OID4VCI روی `services/auth` + `IdentitySBT.sol` | انطباق OID4VCI |
| ۶۲ | L2 ارزان + IPFS؛ `ImpactCertificate.sol`؛ **`PhaseGate` و `MintController` باید واقعاً مسیر صدور را ببندند** | ۱ خریدار بین‌المللی |
| ۶۷ | دوقلوی زنده از `simulation` + `whatif_engine` + جریان ماهواره/حسگر | به‌روزرسانی ≤ ۷ روز |
| ۴۰ | geohashing + minimização؛ دقت کافی برای محاسبه بدون افشای ملک | انطباق GDPR |

> **قانون S-MONEY و قرارداد:** هیچ مسیر مالی جدیدی بدون قاعدهٔ نسخه‌دار از `services/_contracts/money.py` عبور نکند. `Decimal`، نه `float`.

### ۳٫۳ W2-C · پلتفرم و یادگیری (قلم‌های ۲۶، ۲۹، ۳۱، ۵۳، ۸۳، ۸۹، ۹۰، ۱۱۰)

| قلم | جزئیات | معیار |
|---|---|---|
| ۵۳ افزونه | `interfaces/` + `formulas/registry.py` زیرساخت ثبت موجود است؛ افزونهٔ شخصی‌سازی مدل برای نهاد/کشور با sandbox | ۳ افزونهٔ شخص ثالث |
| ۲۶ WASM | پورت `engine/cpp_core` به wasm-bindgen برای FAO-56 و RUSLE ساده | RUSLE < 50ms در مرورگر |
| ۱۱۰ کالیبراسیون جمعی | کشاورز/دانشگاه/نهاد با هم مدل را کالیبره کنند؛ `models/validation` | ۱۰ کالیبراسیون |
| ۸۳ بیمه/بانک | API + شراکت B2B؛ ریسک پارامتری | ۱ شریک |
| ۲۹، ۳۱ | RL برای آبیاری؛ چندعاملی برای تخصیص منابع | صرفه‌جویی ۱۵٪؛ توافق پایدار |
| ۸۹، ۹۰ | اجرای تصمیم W0 — یا اجرا یا اصلاح ADR | تصمیم مکتوب |

---

## ۴. موج سه — W3 (۱۸+ ماه): مرزهای جدید

**قاعدهٔ ورود:** بدون W1 و W2 پایدار، هیچ قلم W3 شروع نمی‌شود. دلیل: بیشتر قلم‌های W3 هزینهٔ نگهداری دائمی دارند و روی معماری ناپایدار بدترین بازده را می‌دهند.

| قلم | توضیح | شرط شروع |
|---|---|---|
| ۲۵ دروازهٔ Go | فقط اگر تصمیم W0 = گزینهٔ الف بود | تصمیم W0 مثبت |
| ۳۷ ZK روی کربن | اثبات درستی RothC بدون افشای پارامتر مزرعه؛ رقابت مستقیم با Indigo+Zama | W2-C کامل + مشتری کربن |
| ۵۹ نانوحسگر گاز | CO₂/CH₄ خاک برای زمینی‌کردن MRV | W2-A کامل |
| ۶۳ DAO | تخصیص صندوق با vote-escrow؛ `EcoGovernance.sol` موجود | بازار کربن فعال |
| ۱۰۳ SLM تخصصی | تنظیم مدل روی FAO/IPCC/ISRIC + دادهٔ خود | W2-B + RAG پایدار |
| ۱۰۴ عامل خودمختار | تحلیل، فرضیه، آزمایش، گزارش | SLM موجود |
| ۱۰۵ ویکی زنده | حافظهٔ سازمانی از نتایج مدل | SLM + agent |
| ۱۰۶ بیوتکنولوژی | همکاری پژوهشی؛ مرز بعدی کشاورزی | شریک دانشگاهی |
| ۱۰۷ اقتصاد دایره‌ای | بازار ضایعات و بازیافت | W1-E کامل |
| ۱۰۸ دوقلوی منطقه‌ای | از قطعه به حوضه/شهر؛ تصمیم منابع مشترک | ۱ منطقهٔ پایلوت |

---

## ۵. نقشهٔ وابستگی

```
W0-A (مُهر منبع) ──┬─→ W1-A۲ (عدم‌قطعیت) ──→ W1-A۳ (PINN) ──→ W1-E (گواهی صداقت)
                    └─→ W1-E (API محصول)

W0-C۲ (ثبت مدل) ──→ W1-B (همهٔ ML) ──→ W2-C (RL، چندعاملی) ──→ W3 (SLM، عامل)

W0-B (کش) ──→ W1-A۱ (Numba) ──→ W1-C (مهار سطح) ──┬─→ W2 (همهٔ ادغام‌ها)
                                                       └─→ W3 (همه)

W0-D (زیرساخت) ──→ W1-F (زیرساخت) ──→ W2-B (وب۳) ──→ W3۳۷ (ZK)

تصمیم ADR ──→ W2-C (۸۹، ۹۰) ──→ W3۲۵ (Go)
```

**قاعدهٔ عبور:** هیچ قلمی که وابستگی‌اش سبز نشده، شروع نمی‌شود. این را `scripts/innovation_backlog.py` می‌تواند بررسی کند.

---

## ۶. معیار موفقیت موج (Definition of Done)

هر موج فقط وقتی بسته می‌شود که **همهٔ** شرایط زیر برقرار باشد:

| # | شرط | روش تأیید |
|---|---|---|
| ۱ | همهٔ قلم‌های موج وضعیت `done` در `docs/innovation_backlog.csv` | `python scripts/innovation_backlog.py status --wave W0` |
| ۲ | دروازهٔ کامل بخش ۰٫۱ سبز | اجرای دستی + CI |
| ۳ | همهٔ KPIهای موج اندازه‌گیری و در `reports/` ثبت شده | `python scripts/innovation_backlog.py kpi --wave W0` |
| ۴ | هیچ `xfail` جدید بدون دلیل | بازبینی `reports/f0_1_xfail_ids.txt` |
| ۵| `AGENTS.md` به‌روز شده (اگر دستور تغییر کرده) | بازبینی انسانی |
| ۶| ADR برای تصمیم‌های معماری موج نوشته شده | `docs/adr/` |
| ۷| هیچ secret وارد نشده | gitleaks در pre-commit |

---

## ۷. ریسک اجرایی برنامه

| ریسک | احتمال | اثر | کاهش |
|---|---|---|---|
| مهار سطح (W1-C) انجام نشود و بانک روی معماری ناپایدار رشد کند | بالا | بالا | W1-C را به ابتدای موج ۱ منتقل کنید، نه انتهای آن |
| تیم کوچک هر دو بخش علم و محصول را هم‌زمان بکشد | بالا | بالا | در هر لحظه فقط **یک** دامنهٔ W1 فعال باشد |
| Moonshot زودهنگام (W3) شروع شود | متوسط | بالا | دروازهٔ ورود بخش ۴ غیرقابل عبور است |
| `credentials_required` در UI پنهان شود و صداقت بشکند | متوسط | بسیار بالا | تست `test_provenance_completeness.py` + بازبینی انسانی |
| افزونه‌های npm/کتابخانه آلوده وارد شوند | متوسط | بالا | SBOM + pin + audit دوره‌ای (قلم ۹۵) |
| هزینهٔ GPU/داده برای W2 نباشد | متوسط | متوسط | W2-A به W3 منتقل می‌شود؛ ۷۰/۷۱ به‌عنوان جایگزین |
| تصمیم ADR به تعویق بیفتد | بالا | متوسط | ددلاین: پایان W0. بعد از آن یعنی ADR اجرانشدهٔ چهار‌ساله |

---

## ۸. ابزار پیگیری

```bash
# خلاصهٔ کل بانک
.venv\Scripts\python.exe scripts\innovation_backlog.py summary

# وضعیت یک موج
.venv\Scripts\python.exe scripts\innovation_backlog.py status --wave W0

# اقلام آمادهٔ شروع (وابستگی‌ها سبز)
.venv\Scripts\python.exe scripts\innovation_backlog.py ready

# موارد مسدود
.venv\Scripts\python.exe scripts\innovation_backlog.py blocked

# KPIهای موج
.venv\Scripts\python.exe scripts\innovation_backlog.py kpi --wave W0

# اعتبارسنجی CSV (دروازهٔ CI)
.venv\Scripts\python.exe scripts\innovation_backlog.py validate
```

خروجی `validate` در دروازهٔ CI اجباری است: هر قلم باید `status` معتبر، `wave` معتبر، و KPI غیرخالی داشته باشد.

---

## ۹. خلاصهٔ اجرایی برنامه

| موج | بازه | قلم | خروجی کلیدی |
|---|---|---|---|
| **W0** | ۰–۲ ماه | ۲۶ | مُهر منبع، zero-config، دروازهٔ CI، ثبت مدل، حذف stub، MCP، امنیت |
| **W1** | ۲–۶ ماه | ۵۲ | عدم‌قطعیت، PINN تولیدی، مهار ۵۷→۱۸، USSD، API محصول، بهینه‌سازی |
| **W2** | ۶–۱۸ ماه | ۲۲ | نانوحسگر، بازار کربن L2، VC، PQC، دوقلوی رویدادمحور |
| **W3** | ۱۸+ ماه | ۱۰ | ZK، SLM تخصصی، عامل خودمختار، دوقلوی منطقه‌ای |
| **جمع** | | **۱۱۰** | |

**نسبت انواع:** ۳۸ تکاملی (E) · ۳۷ ادغام فناورانه (I) · ۱۳ Moonshot (M) — فراتر از حداقل خواسته‌شده (۱۵ / ۱۵ / ۱۰).
**پوشش نانوفناوری:** ۶ قلم (۵۶–۶۱) + همگرایی در ۳۷، ۵۷، ۶۹، ۷۳، ۱۰۶.
