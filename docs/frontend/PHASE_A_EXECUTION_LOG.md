# گزارش اجرای فاز A — راه‌اندازی زنده و اتصال فرانت‌اند به بک‌اند و دیتابیس

**تاریخ اجرا:** ۲۰۲۶/۰۹/۲۸ · **مجری:** Agent (execution, not planning)
**پیش‌نیاز:** `docs/frontend/FRONTEND_BACKEND_CONNECTION_PLAN.md` (فاز A)

---

## ۱) خلاصهٔ نتیجه

| گام | وضعیت | شاهد |
|---|---|---|
| A1 اجرای مهاجرت‌ها روی دیتابیس | ✅ انجام شد (پس از رفع دو باگ) | `alembic current` → دو head؛ جداول ساخته شدند |
| A2 بالا آوردن دروازهٔ API | ✅ | `/api/v1/platform/health` → `operational` روی `127.0.0.1:8000` |
| A3 سیم‌کشی محیط فرانت‌اند | ✅ | `apps/web/.env.local` ساخته شد |
| A4 اجرای زندهٔ گیت‌ها در برابر gateway | ⚠️ اجرا شد — ۳ پاس / ۱ fail | Playwright chromium: `security.spec.ts` + `marketplace-flow.spec.ts` (۴۸ ثانیه)

---

## ۲) باگ‌هایی که در مسیر اجرا پیدا و رفع شدند

### باگ ۱ — مهاجرت `sponsorships` روی رشته‌ها `.value` صدا می‌زد
فایل: `alembic/versions/20260926_020000_sponsorships.py`
```python
# قبل (خطا: AttributeError: 'str' object has no attribute 'value')
sa.Column("tier", sa.Enum(*[t.value for t in _TIERS], name="sponsortier"), nullable=False)
# بعد
sa.Column("tier", sa.Enum(*_TIERS, name="sponsortier"), nullable=False)
```
همین خطا برای `_STATUSES` و `_PLACEMENTS` هم اصلاح شد. نتیجه: مهاجرت کامل اجرا شد.
نسخهٔ پشتیبان: `alembic/versions/20260926_020000_sponsorships.py.bak-20260928`

### باگ ۲ — وضعیت نیمه‌ساخته در SQLite
چون DDL در SQLite تراکنشی نیست، تلاش ناموفق قبلی جدول `sponsorships` را نیمه‌ساخته گذاشته بود و اجرای بعدی با `table sponsorships already exists` شکست می‌خورد.
اقدام: جدول خالیِ نیمه‌ساخته حذف و مهاجرت دوباره اجرا شد.

### یافتهٔ سوم — چند head در گراف مهاجرت
گراف دو شاخه دارد: `20260926_010000` (webauthn) و `20260927_010000_engine_result_tables`. بنابراین `alembic upgrade head` کار نمی‌کند و باید `alembic upgrade heads` زده شود. (خودِ مهاجرت `engine_result` هم در docstring همین را گفته است.)
**پیشنهاد:** یک revision ادغام (`alembic merge heads`) برای بازگشت به تک‌head.

---

## ۳) شواهد اجرایی (اندازه‌گیری‌شده)

### دیتابیس `data/econojin.db`
| سنجه | قبل | بعد |
|---|---|---|
| تعداد جداول | ۱۳۶ | **۱۴۲** |
| `sponsorships` | نبود | ساخته شد (۰ رکورد) |
| شش جدول نتیجهٔ موتور | نبودند | `runoff_calculation_results`، `groundwater_model_results`، `crop_water_req_results`، `structure_design_results`، `irrigation_design_results`، `calibration_results` — همه ساخته شدند |
| `alembic_version` | `20260926_010000` | `20260926_010000` + `20260927_010000_engine_result_tables` |
| پشتیبان | — | `data/econojin.db.bak-20260928` |

### دروازهٔ API (زنده روی ۸۰۰۰)
| Endpoint | نتیجه |
|---|---|
| `/api/v1/platform/health` | `operational` · `db_reachable: true` · `cpp_available: true` |
| `/api/v1/platform/stats` | **`total_landscapes: 204`** (دادهٔ واقعی) · `total_projects: 0` |
| `/api/v1/marketplace/stats` | `total_products: 5` · `total_producers: 3` |
| `/api/v1/hydroma/models` | فهرست مدل‌ها (Richards 1D، Saint-Venant، …) |
| `/health` (سطح دروازه) | `degraded` — برخی ماژول‌ها ناقص |
| `/openapi.json` زنده | **۴۸۹ مسیر** (فایل مخزن: ۴۸۲ → ۷ مسیر اختلاف) |

### اتصال فرانت‌اند → بک‌اند (از طریق BFF)
| مسیر | نتیجه |
|---|---|
| `GET /api/v1/platform/health` از پورت فرانت | ۲۰۰ + JSON واقعی |
| `GET /api/v1/platform/stats` از پورت فرانت | ۲۰۰ + `total_landscapes: 204` |
| `GET /api/v1/marketplace/stats` از پورت فرانت | ۲۰۰ + ۵ محصول، ۳ تولیدکننده |
| صفحهٔ SSR `/fa/market` | ۲۰۰ (HTML ۶۴۷KB، خوانده‌شده از بک‌اند) |

**نتیجه:** مسیر «مرورگر → BFF → دروازهٔ FastAPI → SQLite» زنده و کارکننده است.

---

## ۴) تنظیمات محیطی ساخته‌شده

`apps/web/.env.local` (توسعهٔ محلی):
```
NEXT_PUBLIC_API_BASE_URL=/api
NEXT_PUBLIC_APP_URL=http://localhost:3001
NEXT_PUBLIC_SITE_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:8000
API_PROXY_TARGET=http://127.0.0.1:8000
SESSION_TTL_SECONDS=28800
```

---

## ۵) نتیجهٔ اجرای گیت زنده (A4)

**فرمان:** `npx playwright test tests/security.spec.ts tests/marketplace-flow.spec.ts --project=chromium`
**نتیجه:** `3 passed · 1 failed (48.3s)` — این نخستین اجرای گیت در برابر دروازهٔ زندهٔ محلی است.

### شکست اندازه‌گیری‌شده
| قلم | مقدار |
|---|---|
| تست | `tests/marketplace-flow.spec.ts:3` — «bazaar registry and creation entry render honest states» |
| انتظار | دیده‌شدن لینک با نام دسترسی `ورود` |
| خطا | `getByRole('link', { name: 'ورود', exact: true })` پیدا نشد (timeout 5s) |
| خوانش | صفحهٔ ورودی بازارگاه در حالت خارج از نشست، «رفتار ورود» قابل‌کلیک نشان نمی‌دهد |
| پیوست | `test-results/marketplace-flow-.../test-failed-1.png` |
| اقدام | یا افزودن لینک ورود به هدر همان سطح، یا به‌روزرسانی اسپک اگر رفتار عوض شده |

> این شکست، خودش «سود» است: پیش از این هیچ گیتی در برابر دروازهٔ زنده اجرا نشده بود؛ اکنون یک شکاف واقعی UI در سطح بازارگاه ثبت شده است.

---

## ۶) گام بعدی (فاز B)

| # | کار | چرا |
|---|---|---|
| B1 | بازتولید `openapi.json` از دروازهٔ زنده | ۷ مسیر اختلاف اندازه‌گیری شد |
| B2 | `generate:api` (Orval) و `type-check` | کلاینت هم‌سنخ با ۴۸۹ مسیر |
| B3 | تست قرارداد در CI | جلوگیری از bind بدون endpoint |
| A4-ب | اجرای کامل ۱۹ اسپک Playwright روی هر پنج project | بستن دروازهٔ فاز A با ثبت نتیجه |
| — | `alembic merge heads` | بازگشت به تک‌head |
