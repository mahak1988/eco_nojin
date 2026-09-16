# پیاده‌سازی برنامهٔ بازارگاه ۲.۰ (Hybrid Web2.5) — گزارش ثبت اجرا

> تاریخ: ۲۰۲۶-۰۹-۱۵ · محدوده: انطباق و پیاده‌سازی کامل «برنامهٔ جامع بازارگاه» (چشم‌انداز پلتفرم → بازارچه → فروشگاه → محصول) روی کدبیس موجود اکو نوژین · این سند جایگزین/مکمل `MARKETPLACE_ROADMAP.md` است.

## ۱. جدول انطباق برنامه ↔ کد

| فاز برنامه | خواسته | وضعیت قبل | اقدام اجراشده | فایل‌ها | وضعیت |
|---|---|---|---|---|---|
| ۰ | معماری Web2.5، لایه‌بندی | لایه‌بندی موجود | سیم‌کشی کامل API + میان‌افزارهای امنیت | `services/api_gateway/main.py`, `security.py` | ✅ |
| ۱.۱ | مدل Marketplace/Founer/Member/Seller/Product | عضو/فروشنده/محصول موجود | **MarketplaceFounder** + ثبت در models | `services/marketplace/models/marketplace_founder.py` | ✅ |
| ۱.۲ | حل اختلاف | — | سرویس + مدل + روتر (از اجرای نیمه‌کاره قبلی، تکمیل و ایمن‌سازی) | `services/dispute_resolution/*` | ✅ |
| ۱.۲ | لجستیک | — | ماشین‌حالت ارسال + روتر | `services/logistics/*` | ✅ |
| ۱.۲ | تضمین کیفیت | — | بازرسی + گواهی + روتر | `services/quality_assurance/*` | ✅ |
| ۱.۳ | مایگریشن دیتابیس | وجود نداشت | **revision `b2f8a4c61e90`** — ۷ جدول | `alembic/versions/b2f8a4c61e90_*.py` | ✅ اعمال شد |
| ۲ | ۴ قرارداد هوشمند | `contracts/src` فقط ۲ قرارداد قدیمی OZ-v4 | **۵ قرارداد** (+۲ ارتقای legacy) + ۱۷ تست سبز | `contracts/src/{IdentitySBT,EscrowWithDispute,MarketplaceLiability,BrandLicense,PaymentSplitter}.sol` | ✅ 17/17 |
| ۳ | API بکاند | main.py به روترهای ناموجود ارجاع داشت (شکسته) | ۳ wrapper روتر در gateway + auth روی نوشتن/لیست | `services/api_gateway/routers/{disputes,logistics,quality}.py` | ✅ |
| ۴ | فرانت: Zustand + hooks + صفحات | react-query v5 موجود، Zustand نصب نیست | **جایگزینی آگاهانه**: TanStack Query hooks (بدون افزودن وابستگی قفل‌شکن) + ۲ صفحه + lib | `hooks/useBazargahV2.ts`, `lib/bazargahV2Api.ts`, `pages/dispute/*` | ✅ |
| ۵ | تست و استقرار | — | pytest 12/12 · hardhat 17/17 · tsc پاک · TestClient 200/401/404 | — | ✅ (پایلوت فاز ۷ آینده) |

## ۲. باگ‌های کشف و رفع‌شده در این اجرا

1. **`main.py` شکسته بود**: `from .routers import logistics, quality, disputes` به فایل‌های ناموجود ارجاع داشت → سه wrapper در `api_gateway/routers` ساخته شد که روترهای واقعی `services/*` را re-export می‌کنند (تک منبع حقیقت، صفر فایل یتیم).
2. **`services/api_gateway/security.py` هرگز ساخته نشده بود** (import در main.py خط ۲۱۵) → چهار میان‌افزار پیاده شد: `HTTPSRedirectMiddleware` (شرطی با `ECONOJIN_REQUIRE_HTTPS` تا توسعهٔ HTTP نشکند)، `RateLimitMiddleware` (Redis با fallback درون-حافظه)، `SecurityHeadersMiddleware`، `RequestIDMiddleware`. `middleware/__init__.py` نیز اصلاح شد.
3. **دو head در alembic** (`425ba660dd2d` و مایگریشن من) → زنجیره خطی شد و `upgrade head` با موفقیت اجرا شد. نکته: `alembic.ini` به `test_migration.db` اشاره می‌کند؛ در استقرار واقعی URL را override کنید (env.py از config می‌خواند). DB زمان-اجرا (`data/econojin.db`) با `Base.metadata.create_all` همگام شد.
4. **کلید توکن خراب در فرانت**: `'hydrom…oken'` (کاراکتر U+2026 داخل کلید!) در `marketplaceApi.ts` (۲ مورد) و `hydromaApi.ts` (۱ مورد) → به `'hydroma_token'` اصلاح شد + `AuthContext` حالا توکن را در localStorage ذخیره/پاک می‌کند.
5. **قراردادهای legacy با OZ v4**: مسیر `security/ReentrancyGuard|Pausable` → `utils/`، حذف `Counters`، `_beforeTokenTransfer` → `_update` (سازگار OZ v5.6.1).
6. **محدودیت آفلاین solc**: دانلود 0.8.26 ممکن نشد؛ `IdentitySBT` به‌صورت مستقل (بدون زنجیرهٔ `Strings→Bytes` که mcopy می‌خواهد) بازنویسی شد تا با **0.8.24 کش‌شده** کامپایل شود.

## ۳. تفاوت‌های آگاهانه با متن برنامه

- **Zustand نصب نشد** (قفل وابستگی‌ها و بیلد می‌شکند بدون `pnpm install`)؛ الگوی موجود TanStack Query + Context همان جداسازی state سرور/کلاینت را می‌دهد.
- **PostGIS/Geography به ORM اضافه نشد** (SQLite-portability تست‌ها)؛ موقعیت به‌صورت lat/lon و مسیر کوچ به‌صورت JSONB قابل افزودن است؛ ستون‌های `migration_route` فاز بعدی با geoalchemy2 + Postgres.
- `useInsuranceFund` در برنامهٔ پیوستی باگ داشت (`msg.sender` هم‌زمان پلتفرم و بازارچه) → در قرارداد نهایی آدرس بازارچه پارامتر شد.
- `payable().transfer` → `call{value}` (الگوی امن‌تر، گس ثابت ۲۳۰۰ حذف).
- اعلان‌ها (فاز ۳ برنامه): سرویس `services/notification` موجود است؛ اتصال dispute→notification به‌عنوان قدم بعدی (بدون channel واقعی email/SMS).

## ۴. اندپوینت‌های جدید (تأییدشده با TestClient)

```
POST   /api/v1/disputes                    (auth)  ایجاد شکایت
GET    /api/v1/disputes                    (auth)  فهرست (فیلتر status)
GET    /api/v1/disputes/{id}                       جزئیات + رویدادها
POST   /api/v1/disputes/{id}/resolve       (auth)  حل (resolved|rejected)
POST   /api/v1/disputes/{id}/escalate      (auth)  ارجاع به سطح بالاتر
POST   /api/v1/logistics/shipments         (auth)  ایجاد مرسوله
GET    /api/v1/logistics/shipments/{id}            ردیابی (404 در نبود)
POST   /api/v1/logistics/shipments/{id}/status (auth) ماشین‌حالت ارسال
POST   /api/v1/quality/inspections         (auth)  بازرسی
POST   /api/v1/quality/inspections/{id}/result (auth) نتیجه + گواهی خودکار ≥85
GET    /api/v1/quality/inspections                 فهرست بازرسی‌ها
```

## ۵. قراردادهای هوشمند (contracts/src) — 17/17 تست سبز

| قرارداد | نقش | تست‌های کلیدی |
|---|---|---|
| `IdentitySBT.sol` | هویت Soulbound عضو روستا/عشایر (غیرقابل‌انتقال) | صدور مجاز، جلوگیری از صدور غیرمجاز، انتقال‌ناپذیری (کال سطح‌پایین)، لغو |
| `EscrowWithDispute.sol` | امانی با اختلاف سه‌مرحله‌ای (فروشنده ۴۸h → بازارچه ۷۲h → پلتفرم) | تقسیم ۹۶/۳/۱ در تحویل، بازپرداخت داوطلبانه، جریمهٔ بیمه، داوری پس از مهلت |
| `MarketplaceLiability.sol` | صندوق بیمه + امتیاز مسئولیت‌پذیری + تعلیق | حداقل صندوق، پرداخت به خریدار، بلاک تعلیق‌شده |
| `BrandLicense.sol` | مجوز زیربرند فروشگاه‌ها تحت برند روستا | صدور/اعتبار/لغو/فقط-پلتفرم |
| `PaymentSplitter.sol` | تقسیم تناسبی پرداخت (۹۶/۳/۱) | release سه ذی‌نفع، رد غیر-payee |

اجرا: `cd contracts && $env:PRIVATE_KEY='<کلید آزمایشی/واقعی>' && npx hardhat test` · استقرار: `npx hardhat run scripts/deploy.js --network <mumbai|polygon|localhost>`

## ۶. Runbook

```powershell
# بکاند
D:\eco_nojin\.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --port 8000
# تست بکاند
.venv\Scripts\python.exe -m pytest services\marketplace\tests -q
# فرانت
cd frontend ; pnpm dev      # تست تایپ: pnpm type-check
# قراردادها
cd contracts ; npx hardhat test
```

## ۷. کارهای باقی‌مانده (مسیر فاز ۵ تا ۸ برنامه)

- اتصال روتر `/payments` به درگاه واسط ایرانی (زرین‌پال) + escrow هوشمند در مسیر پرداخت واقعی
- اتصال `BlockchainService` بکاند به قراردادهای مستقرشده (آدرس‌ها در `.env`)
- کانال‌های واقعی notification (ایمیل/SMS/Push) + اطلاع‌رسانی خودکار در رویدادهای dispute/shipment
- مهاجرت Geography/PostGIS برای مسیر کوچ عشایری + ایندکس GIST
- ممیزی امنیتی مستقل قراردادها قبل از mainnet (خروجی تست، جایگزین ممیزی نیست)
- فاز ۷/۸ برنامه: پایلوت روستایی و داشبورد KPI (اهداف کمیِ فایل برنامه حفظ شده است)

## ۸. تست مرورگر (بینایی) — ۲۰۲۶-۰۹-۱۵

- ابزار: Playwright + Chrome واقعی (`channel: "chrome"`, headless) — اسکریپت: `frontend/tests/browser-vision-test.cjs`
- استک: بکاند uvicorn روی `127.0.0.1:8000` (کد جدید — smoke: 200/401/404) + فرانت Vite روی `localhost:5174`
- نتایج: `/marketplace` ✅ · `/marketplace/disputes/new` ✅ · `/marketplace/disputes` ✅ (هر سه PASS، صفر خطای کنسول)
- تحلیل بینایی (AutoGLM image-recognition روی اسکرین‌شات‌ها):
  - کاتالوگ: کارت محصولات (زعفران خراسان، گندم ارگانیک گلستان، لبنیات عشایری و…)، فیلتر دسته‌ها، جستجو، مرتب‌سازی — سالم
  - فرم شکایت: فیلد شماره سفارش، دراپ‌داون نوع شکایت (کیفیت کالا)، توضیحات، دکمه ثبت + آیتم ناوبری جدید «شکایات» فعال
  - فهرست شکایات: عنوان، دکمه «+ شکایت جدید» و پیام صادقانه ۴۰۱ برای کاربر واردنشده (رفتار صحیح)
- خروجی‌ها: `reports/browser-test-2026-09-15/{catalog,dispute-form,disputes-list}.png`
- یافتهٔ اصلاحی حین تست: مسیرهای dispute ابتدا فقط در `AppShell` (بلوک تست) تزریق شده بودند؛ به بلوک اصلی `App` (قبل از وایلدکارد `/marketplace/*`) منتقل شد.

## ۹. درگاههای پرداخت چندگانه + اسکرو (plan v2.1) — ۲۰۲۶-۰۹-۱۵

- سرویس: `services/marketplace/payments_service.py` — درگاهها: `zarinpal` (REST v4 واقعی + sandbox)، `bank` (کارت‌به‌کارت با شماره پیگیری)، `international` (لینک checkout خارجی از env)؛ خطای پیکربندی صادقانه (fail-loud).
- اسکرو: لجر غیرقابل‌تغییر `marketplace_escrow_entries` — hold پس از تأیید درگاه → release خودکار هنگام `POST /orders/{id}/confirm` (تأیید تحویل) → refund ادمین برای اختلافات. قرارداد `EscrowWithDispute` همان جریان را on-chain پوشش میدهد.
- اندپوینتهای جدید: `POST /payments` (gateway-aware)، `POST /payments/{id}/confirm`، `POST /payments/{id}/escrow/release|refund` (ادمین)، `GET /payments/zarinpal/callback`. مایگریشن `d4e5f6a7b8c9` (۲ جدول) + `e6f7a8b9c0d1` (PostGIS مسیر کوچ عشایری — فقط Postgres، گاردشده).
- تست: ۶ تست جدید (`test_payments.py`) — مجموع pytest 18/18 سبز. محافظت Idempotency-Key (میان‌افزار مالی) در فرانت با UUID per-request اعمال شد (`lib/paymentsApi.ts`).
- فرانت: CheckoutPage بازنویسی — انتخاب درگاه (۳ کارت با لهجه رنگی)، بنر اسکرو با آیکون سپر، جریان کارت‌به‌کارت (دستورالعمل + شماره پیگیری)، خطای صادقانه برای درگاه پیکربندینشده.
- قراردادهای مکتوب با دکمه تعهد: `VendorApplication` و `CreateMarketplace` اکنون با «دستورالعمل + متن قرارداد» (نسخه‌دار v1) و دو چک‌باکس تعهد شروع میشوند؛ فرم تا تایید قفل است و نسخه/زمان پذیرش در payload ثبت میشود. تم روستایی/عشایری: نوار کلیم (terracotta/نیلی/زعفرانی)، کارت کاغذ کاهگلی `#faf5ea`/`#fdfaf3`، فیلدها با پسزمینه گرم (سفید حذف شد)، پالت انتخابی بازارچه (۶ تم: کاشی فیروزه، گل سرخ زاگرس، نیل عشایری، کاهگل کویر، انار، زعفران) در `brand_colors` ذخیره میشود.
- قراردادها: شبکه `amoy` به hardhat اضافه شد؛ deploy.js روی hardhat network اجرا و هر ۵ قرارداد مستقر شد (dry-run)؛ استقرار Amoy نیازمند کلید تأمینشده. ممیزی داخلی: `docs/fa/68_bazargah_contracts_security_review.md`.
- تست مرورگر v2: checkout/apply/create هر سه PASS (صفر خطای کنسول) + تحلیل بینایی AutoGLM تأیید بصری (کارت‌های درگاه، بنر سپر اسکرو، نوار کلیم، جعبه‌های قرارداد، چک‌باکس‌های تعهد، پالتها، قفل فرم تا تایید).

## ۱۰. چرخهٔ سوم — ترتیب تاسیس، اصلاحات UI و صفحات تنوع (۲۰۲۶-۰۹-۱۵)

- **ترتیب تاسیس (بازارچه ← فروشگاه)**: تعهدنامهٔ رسمی «تشکیل و اداره بازارچه در منظره محلی» با ۱۱ ماده (حاکمیت، لایهها، عضویت، برند جمعی، صندوق منظر، PGS، اسکرو، داوری، امتیاز مسئولیتپذیری، خروج، پذیرش الکترونیکی) در `CreateMarketplace` نوشته شد و اعلان «برای تأسیس فروشگاه ابتدا بازارچه ایجاد کنید» با لینک به ثبت بازارچه در دروازهٔ قرارداد صفحهٔ فروشنده اضافه شد.
- **رفع ۴۰۳ سبد خرید**: `/api/v1/marketplace` به `EXEMPT_PREFIXES` میانافزار CSRF اضافه شد (APIهای Bearer/مهمان بدون کوکی سشن)؛ تست: POST سبد بدون توکن اکنون 401/422 است نه 403.
- **UI بازارگاه**: فوتر از همه صفحات `/marketplace/*` حذف شد (PublicLayout chromeless) و «بازارگاه» به منوی هدر اصلی اضافه شد.
- **نمودار محصول**: حاشیهها و عرض محور اصلاح و LabelList داخل میلهها اضافه شد — برچسبهای کربن/آب کامل داخل نمودار رندر میشوند (تأیید DOM/SVG).
- **صفحات تنوع محصول**: مسیر `/marketplace/category/:category` + بنر دسته (آیکون/نام دوزبانه از CATEGORY_CONFIG) + همگامسازی فیلتر با مسیر — ۹ دسته (غلات، میوهها، سبزیجات، شیر، گوشت، ادویه، دستساز، روستایی، سایر).
- **تست مرورگر**: category/grains PASS · حذف فوتر PASS · منوی هدر PASS · برچسبهای نمودار PASS (در SVG) · اعلان بازارچهاول PASS — صفر خطای کنسول. اسکرینشاتها: category-grains، product-chart، marketplace-nofooter.
- باقیمانده شفاف: سیمکشی dispute→notification (ماژول اعلان فعلاً فقط health/Pydantic دارد)، استقرار واقعی Amoy (نیازمند کلید تأمینشده)، درگاههای واقعی زرینپال/بینالمللی (نیازمند merchant/URL در env).

## ۱۱. چرخهٔ چهارم — سبد مهمان، اعلانها و پالت طلایی (۲۰۲۶-۰۹-۱۵)

- **سبد مهمان (رفع 401 کاربر)**: چهار اندپوینت سبد به `get_current_user_optional` + هدر `X-Guest-Id` منتقل شدند (`_buyer_id`); فرانت در `marketplaceApi` شناسه مهمان ماندگار میسازد و همیشه ارسال میکند. باگ نهفتهٔ `cart.id` روی دیکشنری (500) نیز رفع شد. تست مرورگر: مهمان ← افزودن به سبد ← **200** ← صفحه سبد رندر ✅
- **اعلانهای درونبرنامه‌ای (تکمیل سیمکشی)**: جدول `app_notifications` (مایگریشن `f7b9c1d3e5a2`) + `NotificationDbService` + اندپوینتهای `GET /notifications` و `POST /notifications/{id}/read`؛ سیمکشیشده در: تأیید پرداخت (اسکرو)، تأیید تحویل (آزادسازی اسکرو)، ثبت شکایت (به طرف مقابل). ۳ تست جدید — pytest **21/21**.
- **پالت رنگی نهایی**: تمام فیلدهای بازارگاه (۱۴ فایل) کاغذ گرم `#fdf8ee` با متن قهوهای تیره؛ صفحات روستایی (فروشنده/بازارچه): متن طلایی `#a8841c` + لهجههای `#e8c66b` (طلایی لوگو) — تأیید بینایی. تعهدنامه منظر به ۱۱ ماده رسمی گسترش یافت.
- نکته نگهداشت: سرور uvicorn قبلی (pid دیگر) کد کهنه سرو میکرد؛ پس از هر تغییر بکاند، restart الزامی است (--reload فعال نبود).

## ۱۲. تست E2E زنجیرهٔ کامل (سبز — ۷/۷)

اسکریپت: `scripts/e2e_bazargah_flow.py` (اجرا: `.venv/Scripts/python.exe scripts/e2e_bazargah_flow.py`)
کاربر واقعی در DB ساخته میشود (e2e-buyer@econojin.local / role=buyer) و کل زنجیره روی اپ درون-فرآیند اجرا میشود:

1. ✅ کاتالوگ → محصول واقعی
2. ✅ ایجاد سفارش (100kg — حداقل مجاز دمو)
3. ✅ افزودن به سبد با احراز هویت → 200
4. ✅ ایجاد پرداخت بانکی → awaiting_verification
5. ✅ تأیید با شماره پیگیری → اسکرو HELD
6. ✅ تأیید تحویل → اسکرو RELEASED به فروشنده (خودکار)
7. ✅ اعلانهای خریدار: ۳ مورد (پرداخت تأیید شد / تحویل تأیید شد — اسکرو آزاد شد)

باگهای یافته و رفعشده در این تست: `PaymentGateways.get_payment` (متد belonged به EscrowService)، reuse کلید Idempotency در اسکریپت (کلید یکتا بهازای هر درخواست)، `users.role` NOT NULL در insert E2E.

## ۱۳. چرخهٔ پنجم — UI اعلان‌ها، انتخاب بازارچه و وضعیت درگاه‌ها (۲۰۲۶-۰۹-۱۵)

- **UI اعلان‌ها**: کارت «اعلانها» در داشبورد خریدار (شمارنده، نقطه نخوانده، دکمه «خواندم»، پیام ورود برای مهمان) + `fetchNotifications`/`markNotificationRead` در marketplaceApi. تست مرورگر: مهمان → پیام ورود PASS.
- **انتخاب بازارچه در فرم فروشنده**: فیلد متنی شناسه با `<select>` واقعی (فید از `GET /marketplaces`) جایگزین شد + یادداشت «هنوز بازارچه‌ای ثبت نشده — اولین بازارچه را بسازید» با لینک. چرخهٔ «اول بازارچه ← بعد فروشگاه» کامل شد. تست: دروازه تعهد → تیک‌ها → فرم با select PASS.
- **وضعیت درگاه‌ها**: `GET /api/v1/marketplace/payments/status` (عمومی، بدون اسرار) + `fetchPaymentsStatus` — برای نشان «به‌زودی» روی درگاههای پیکربندینشده در checkout (گام بعدی UI).
- قراردادها: اسکریپت `deploy:amoy` به package.json اضافه شد (`npm run deploy:amoy`).
- باگ فرایند: تزریق block با depth-scan در BuyerDashboard خط `export default` را حذف کرد — با createProgram تشخیص دقیق و ترمیم جراحی؛ درس: برای درج بلوک JSX از اسکن عمق ساده استفاده نکن، با createProgram صحتسنجی کن.

## ۱۴. چرخهٔ ششم — درگاه دمو، حذف کامل سفید/خاکستری و آیتمهای جدید (۲۰۲۶-۰۹-۱۵)

- **درگاه «پرداخت آزمایشی (دمو)» همیشه فعال**: backend `demo` در VALID_GATEWAYS (initiate → awaiting_verification، confirm → escrow hold با هر ref) تا همهٔ دکمهها واقعاً کار کنند؛ تست API: create 200 / confirm 200 (escrow held).
- **اندپوینت `GET /payments/status`**: وضعیت پیکربندی هر درگاه (boolean بدون اسرار) — خروجی زنده: `{zarinpal:false, bank:false, international:false, demo:true}`.
- **CheckoutPage**: کارت چهارم دمو + نشان «حالت دمو» روی درگاههای پیکربندینشده + جریان کامل دمو (سفارش → دمو → confirm → اسکرو → موفقیت). تست مرورگر: **۴/۴ کارت + بنر اسکرو + نشان دمو PASS**.
- **VendorDashboard**: دکمهٔ «ثبت مرسوله» برای هر سفارش در انتظار (اتصال به POST /logistics/shipments) با وضعیت «ثبت شد ✓».
- **ProductPage**: انتخابگر تعداد (−/+) با جمع زنده، دکمهٔ «افزودن به علاقهمندی» (POST /wishlist)، ستارههای امتیاز.
- **حذف کامل سفید/خاکستری**: شمارش نهایی توکنهای bg-white/gray/slate/neutral در کل ناحیهٔ بازارگاه (۱۴ فایل + layout + dispute) = **۰**؛ پالت نهایی: فیلدها `#f6ecd6`، کارتهای کاغذی `#f7edd8`، بنرهای `#f3e8cf`، نوار کلیم روی ۶ کارت داشبورد/فهرست. تست مرورگر: پسزمینه فیلد `rgb(246,236,214)` ✅
- **مقاومسازی Idempotency**: بازنویسی تمیز middleware با fail-open هنگام در دسترس نبودن لجر (دیگر 500 در مسیر پرداخت رخ نمیدهد) + محافظت double-wrap حذف شد.
- باقیمانده (نیازمند تصمیم/کلید کاربر): ZARINPAL_MERCHANT_ID، INTL_PAYMENT_CHECKOUT_URL، کلید فاست Amoy.
