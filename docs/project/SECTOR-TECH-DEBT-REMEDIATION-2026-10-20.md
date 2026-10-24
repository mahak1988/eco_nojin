# برنامهٔ رفع بدهی فنی بخش‌ها — Commercial / Financial / Accounting / Marketplace / Ecotourism

* **Status:** Active · **Opened:** 2026-10-20 · **Owner:** A00 (program)
* **مکمل** `docs/project/REMEDIATION-PLAN-BACKEND-ONLY-2026-10-18.md` (موج‌های B0–B7). آن برنامه
  «پاک‌سازی/امنیت/داده/API/تست/زیرساخت» را می‌پوشاند؛ این برنامه **بدهی فنیِ اندازه‌گیری‌شدهٔ
  حوزه‌های اقتصادی** را می‌پوشاند (پول، مجوز، صداقت payload، ژورنال).
* **ریشهٔ برنامه:** سه بازرسی ایستای موازی (گردشگری، بازارگاه/تجارت، مالی/حسابداری) در ۲۰۲۶-۱۰-۲۰.
  هر ادعای بحرانی **مستقیماً راستی‌آزمایی شد** (read-only)؛ آنچه اجرا نشده با `[static]` علامت خورده.
* **قرارداد اجرا** از `docs/project/PHASE_PLAN.md §1` و `REMEDIATION-PLAN-BACKEND-ONLY-2026-10-18.md §0`
  ارث می‌برد: env، **یک suite در هر shell**، مهاجرت guarded/idempotent، **هیچ تستی ضعیف یا حذف نمی‌شود**،
  `Decimal` برای پول، secrets commit نمی‌شود، هر closure شواهد (دستور + خروجی) لازم دارد.

---

## ۰. قاعدهٔ حاکم (binding)

1. **پول `Decimal` است، هرگز `float`.** هر نقض موجود یک بدهی ثبت‌شده است (FR-08).
2. **مهاجرت guarded/idempotent** + اثبات `upgrade head --sql` + یادداشت rollback در docstring.
3. **هیچ تستی ضعیف/حذف نمی‌شود.** اگر یک تست پوچ است، **جایگزین** می‌شود (تست واقعی)، نه اینکه حذف شود.
4. **یک suite در هر shell.** `pytest services/ -n 6` و `pytest engine/ -n 6` هرگز هم‌زمان.
5. **مستندات خلاف کد ممنوع است.** هر docstring که ادعای رفتاری می‌کند باید با کد بخواند
   (FR-09: `ComSettlement.order_id`، FR-11: «Arithmetic is Decimal throughout»، FR-12: `not_yet_available`).
6. **وضعیت:** `READY_FOR_REVIEW | BLOCKED | PARTIALLY_COMPLETE`.
7. **تصمیم‌های باز** فقط با `docs/project/OPEN_DECISIONS.md` بسته می‌شوند، نه با عامل.

---

## ۱. یافتهٔ ریشه‌ای: «پوشش تست ≠ تضمین»

سه بازرسی مستقل به یک نتیجه رسیدند:

> ساختارها قوی‌اند (جدول، ژورنال، دسته، ۷۳ تست property-based پول، invariantهای واقعی)؛
> **مسیرهای نوشتنِ پول عمدتاً stub، دستی، بدون گارد، یا بدون ژورنال‌اند**؛ و گاردهایی که
> باید این را بگیرند **پوچ‌اند**.

| شناسه | یافته | شاهد | شدت |
|---|---|---|---|
| **FR-01** | **گارد مرز نوشتن پول هرگز درخت را اسکن نکرده.** `PROJECT_ROOT = parents[2]` ⇒ `D:\HyDroMA\services`؛ سپس `joinpath("services")` ⇒ `services/services` که وجود ندارد ⇒ `rglob` هیچ‌چیز ⇒ `assert offenders == {}` **همیشه سبز** | `services/finance/tests/test_p5_money_invariants.py:39,191,205` | **P0** |
| **FR-02** | گارد دوم `tests/test_money_detox.py` مسیر ریشه را درست حساب می‌کند ولی `_money_offenders` فقط با `tmp_path` مصنوعی صدا زده می‌شود | `tests/test_money_detox.py:23,79,94,109` | **P0** |
| **FR-03** | **تست‌های پوچ**: assert روی متن کد (`inspect.getsource`)، assert روی صفت غیرسطری، ORM seed دور زدن HTTP | `services/marketplace/tests/test_cross_tenant_matrix.py:220-227`؛ `services/api_gateway/tests/test_p6_golden_path.py:292-299,135-170` | **P0** |
| **FR-04** | تست صریحاً یک نقض `float` را **تحمل** می‌کند و آن را نهادینه کرده | `services/finance/tests/test_properties_money.py:1282-1284` | P1 |

**سه writer غیرمجازی که FR-01 باید می‌دید و ندید** (همگی زنده):

| writer | جداول | فهرست مجازِ غلط |
|---|---|---|
| `services/wallet/eco_balance.py:190,287-296` | `eco_balance_accounts`, `eco_balance_entries` | `services.ecosystem` — ولی `services/ecosystem/service.py` **صفر** ارجاع دارد (ماژول جابه‌جا شده) |
| `services/auth_legacy/repository.py:90,108` | `eco_wallets` | `services.finance`/`services.api_gateway` — به‌علاوهٔ لیترال float و هدیهٔ خاموش ۱۰۰ ECO |
| `services/inventory/service.py:492-517` | `fin_journal_batches`, `fin_journal_entries` | `services.finance` — و writer **موازی** که `LedgerService` را دور می‌زند |

---

## ۲) رجیستر یافته‌ها (مرتب بر اساس اثر پولی/مجوزی)

### ۲٫۱ مجوز و دسترسی (FR‑06)

| ID | یافته | شاهد | شدت |
|---|---|---|---|
| FR-06a | `/orders/{id}/settle` — هر کاربر احراز‌هویت‌شده escrow هر سفارشی را آزاد می‌کند | `services/api_gateway/routers/marketplace.py:2031-2049` | **P0** |
| FR-06b | همان برای `/dispute`، `/complete`، `/confirm` | `marketplace.py:1993`، `:2065`، `:786` | **P0** |
| FR-06c | `DISPUTE_WINDOW_HOURS = 48` محاسبه می‌شود ولی **اعمال نمی‌شود** | `marketplace.py:1990` | P1 |
| FR-06d | روتر اختلاف: `complainant_id`/`resolved_by` از بدنه؛ حل با `require_user` نه `require_admin` | `services/dispute_resolution/routers/disputes.py:75,83,41,92` | **P0** |
| FR-06e | `GET /api/v1/logistics/shipments/{id}` بدون احراز هویت | `services/logistics/routers/logistics.py:50-64` | P1 |
| FR-06f | `GET /api/v1/ecowallet/wallet/{user_id}` — `user_id` از path، فقط `require_user` (خوداظهارشده در docstring) | `services/api_gateway/routers/ecowallet.py:210-226` | P1 |
| FR-06g | `POST /api/v1/finance/ledger/batch` با `require_user` (نه ادمین) | `services/finance/routers/finance.py:379-415` | P1 |
| FR-06h | `POST /api/v1/ledger/entries` روی اپ مستقل **بدون auth**؛ یکی روی `0.0.0.0:8006` | `services/ledger/main.py:78-94`؛ `services/ledger/service.py:488` | **P0** |
| FR-06i | گیت KYC فروشنده (`P7.1`) از HTTP دور زده می‌شود؛ روتر اصلاً `is_marketplace_eligible` را صدا نمی‌زند | `services/marketplace/service.py:100-108` در برابر `marketplace.py:1233,1266-1272` | **P0** |

### ۲٫۲ حقیقت پرداخت و پول (FR‑05، FR‑04)

| ID | یافته | شاهد | شدت |
|---|---|---|---|
| FR-05a | تأیید پرداخت گردشگری **کاملاً کلاینت‌ادعا** است؛ `payment_tx_hash` هر رشتهٔ غیرخالی | `services/tourism/service.py:441-455`؛ `schemas/__init__.py:82` | **P0** |
| FR-05b | آزادسازی escrow بازارگاه **هرگز به ژورنال نمی‌رسد**؛ event با نام `settlement_posted` منتشر می‌شود ولی `journal_batch_id` ندارد | `services/marketplace/payments_service.py:605-649` | **P0** |
| FR-05c | webhook امضاشدهٔ بانکی فقط `ComPaymentIntent` را resolve می‌کند، نه `MarketplacePayment` ⇒ **هیچ صفحه‌ای هر دو نیمه را ندارد** | `services/finance/payment_provider.py:306-308` | **P0** |
| FR-05d | callback زرین‌پال ۴۰۴ می‌دهد (هیچ route‌ای با آن مسیر نیست) | `services/marketplace/payments_service.py:338,349` | **P0** |
| FR-05e | `marketplace_orders` ستون `idempotency_key` ندارد ⇒ retry در تسویه = شارژ دوباره | `services/marketplace/models/__init__.py:200-235` | **P0** |
| FR-05f | تسویه‌گر خودکار `payment_status == "succeeded"` می‌خواهد ولی `confirm_payment` می‌نویسد `"paid"` ⇒ **هرگز سفارشی انتخاب نمی‌کند**؛ نرخ کارمزد هم ۸۰۰/۲۰۰/۲۰۰ در برابر ۳۰۰/۱۰۰ | `services/finance/automated_marketplace_settlement.py:8,54-56,141`؛ `services/commerce/service.py:669,145-146` | **P0** |
| FR-05g | `ComSettlement.order_id` **قید یکتا ندارد** ولی docstring خلافش را ادعا می‌کند ⇒ تسویهٔ دوباره ممکن | `database/models.py:729-745`؛ `automated_marketplace_settlement.py:52-53` | **P0** |
| FR-05h | ژورنال **قبل از** ماندهٔ کیف پول commit می‌شود ⇒ دستهٔ یتیم در شکست به‌روزرسانی | `services/finance/wallet_service.py:183` در برابر `:186-199` | **P0** |
| FR-05i | کیف پول: بدون `with_for_update`، `EcoWallet.version` مقایسه نمی‌شود ⇒ **دوباره‌خرج هم‌زمان ممکن** | `services/finance/wallet_service.py:186-199`؛ `database/models.py:569` | **P0** |
| FR-05j | سقف روزانه TOCTOU (سقف خوانده می‌شود، `daily_earnings` بعداً ثبت) | `wallet_service.py:123,170` | P1 |
| FR-05k | مسیر نوشتن کیف پول **هیچ `AuditEvent` نمی‌نویسد** | `services/finance/wallet_service.py` (کل فایل) | P1 |
| FR-05l | کارمزد چشم‌انداز **دوباره‌شماری** می‌شود: هم `ECO_PLATFORM_REVENUE` و هم `landscape_funds` | `services/commerce/service.py:917-921` و `:263-276` | **P0** |
| FR-05m | `RedemptionEngine` دیکشنری **درون‌حافظه‌ای** را بدهکار می‌کند، نه `eco_wallets` و نه ژورنال | `services/ecowallet/redemption.py:198-208` | P1 |
| FR-05n | `services/wallet/eco_balance.py` اصلاً ژورنال نمی‌نویسد ⇒ چاه پول چهارم | `services/wallet/eco_balance.py:190,287-296` | P1 |
| FR-05o | انتقال بانکی تأییدشده `succeeded` می‌شود ولی **هیچ دستهٔ ژورنالی** ثبت نمی‌شود | `services/finance/payment_provider.py:353-433` | P1 |
| FR-05p | `BankTransferProvider` idempotency به کلید+provider می‌خورد، نه سفارش/خریدار ⇒ دو خریدارِ یک کلید برخورد می‌کنند | `services/finance/payment_provider.py:304-313` | P1 |
| FR-05q | مسیرهای نوشتن پول بدون محافظ idempotency: `/ecowallet/transfer`، `/finance/ledger/batch`، `/finance/ledger/batch/{id}/post` | `services/api_gateway/middleware/idempotency.py:37-48` | P1 |
| FR-05r | **بازپرداخت گردشگری با واحد اشتباه**: مبلغ ریالی از کیف پول **ECO** (حداقل ۱۰ ECO) و از کیف پول شخصی ادمین | `services/tourism/safety_service.py:129-134`؛ `services/finance/wallet_service.py:255,467` | **P0** |
| FR-05s | `EcoCoin`: KN‑02 تأیید (raw SQL، بدون مدل/مهاجرت)، KN‑18 باز (`get_balance` تکراری + ۴ id بلااستفاده)، KN‑19 نیمه‌رفع | `services/blockchain/service.py:95-115,335-355` | P1 |

### ۲٫۳ ۵۰۰ های زنده (FR‑07)

| ID | یافته | شاهد | شدت |
|---|---|---|---|
| FR-07a | `confirm_booking` متد **ناموجود** `_update_tour_stats` را صدا می‌زند ⇒ ۵۰۰ روی تأیید پرداخت؛ زنجیرهٔ pay→complete غیرقابل‌دسترس؛ ۳ تست می‌شکنند | `services/tourism/service.py:459` | **P0** |
| FR-07b | `cancel_booking` **مقدار برنمی‌گرداند** ⇒ `ResponseValidationError` ⇒ ۵۰۰ | `services/tourism/service.py:488-545`؛ `api/router.py:350-357` | **P0** |
| FR-07c | `OrderManager.get_order/list_orders` همیشه می‌شکند (`ComOrder.product_id` وجود ندارد) و در `except: pass` بلعیده می‌شود ⇒ `admin/orders` هرگز دادهٔ persist‌شده را نشان نمی‌دهد | `services/marketplace/order_management.py:280,318,291,331` | P1 |
| FR-07d | صفحهٔ کاتالوگ مقادیر نامعتبر در `com_orders.status` می‌نویسد (خارج از `ORDER_STATE_MACHINE`) | `order_management.py:255-265`؛ `database/models.py:642-658` | P1 |

### ۲٫۴ صداقت payload (FR‑08)

| ID | یافته | شاهد | شدت |
|---|---|---|---|
| FR-08a | `GET /blockchain/treasury/balance` → `{"balance": "150000.0"}` — **بدون گارد** | `services/api_gateway/routers/blockchain.py:413-415` | P1 |
| FR-08b | `GET /blockchain/oracle/metrics/{id}` → `impact_score: 5000` — **بدون گارد** | `blockchain.py:387-395` | P1 |
| FR-08c | `GET /ecowallet/daily-cap` → `earned_today: 0` هاردکد با کامنت «For now, return mock» | `services/api_gateway/routers/ecowallet.py:293-299` | P1 |
| FR-08d | `GET /products/{id}/images` → URL جعلی، بایت‌ها ذخیره نمی‌شوند | `services/api_gateway/routers/marketplace.py:480-488` | P1 |
| FR-08e | `GET /orders/{id}/track` fallback → تایم‌لاین یک‌مرحله‌ای جعلی | `marketplace.py:755-768` | P2 |
| FR-08f | `not_yet_available` در `/tourism/status` ادعاهای **نادرست** دارد (بازپرداخت و جشنواره زنده‌اند) و تست یک‌طرفه نمی‌تواند کهنگی را بکشف کند | `services/api_gateway/routers/tourism_router.py:64-70`؛ `test_tourism_status_honesty.py:99-122` | P1 |
| FR-08g | گزارش `ReportType.CARBON` شاخهٔ تولید ندارد ⇒ خروجی خالی **بدون نشانه** | `services/reporting/service.py` | P2 |
| FR-08h | تایم‌لاین فعالیت ECO همیشه خالی (`wallet_id` Integer↔String + هیچ‌کس `eco_transactions` نمی‌نویسد) | `services/api_gateway/routers/analytics.py:370-372` | P2 |

### ۲٫۵ حسابداری و گزارش (FR‑09، FR‑10)

| ID | یافته | شاهد | شدت |
|---|---|---|---|
| FR-09a | `ECO_EQUITY` و `ECO_OPERATING_EXPENSE` **«No writer yet»** ⇒ ترازنامه و سود و زیان کامل ساختنی نیست | `services/finance/chart_of_accounts.py:73-76` | **P0** |
| FR-09b | کدهای حساب per-user شناسهٔ کاربر را در خود دارند (`ECO_USER_<id>`) ⇒ رشد بی‌کران چارت + PII در نام حساب | `chart_of_accounts.py:83-84,251-253`؛ `wallet_service.py:421-437` | P1 |
| FR-09c | ۱۹ نقض `float`/`round` در مسیرهای پول؛ تست یکی را تحمل می‌کند | FR-04 + رجیستر بخش ۲٫۶ | P1 |
| FR-09d | گارد Decimal فقط یک فایل را با الگوی دو-توکنی می‌اسکند | `tests/test_money_detox.py:130-140` | P1 |
| FR-09e | `reconcile_inventory` فقط **کمیت** را مقایسه می‌کند؛ سمت ارزش وجود ندارد؛ اصلاح ناشناخته «رانش بدون تشخیص جهت» می‌دهد؛ `scrap` غلط غیرقابل‌کشف است | `services/finance/reconciliation.py:29-47,269-393` | P1 |
| FR-09f | `reconcile_wallet_ledger` بر اساس **نویسندهٔ دسته** scope می‌شود، نه ذی‌نفع ⇒ برای هر تأمین مالی بین‌طرفی رانش کاذب گزارش می‌کند | `reconciliation.py:123` | P1 |
| FR-09g | **هیچ artifact تطبیقی** ذخیره/امضا/زمان‌بندی نمی‌شود؛ فقط JSON در پاسخ | `reconciliation.py:395-412` | P1 |
| FR-09h | سه فهرست متناقض از «پنج انبار پول»؛ هیچ فهرست canonicalی | `BASELINE.md:62-68`؛ `consolidation.py:1-16`؛ `cross_ledger_report.py:102-119` | P1 |
| FR-09i | **هیچ جدول مالی ستون tenant/org ندارد** ⇒ تفکیک per-tenant مالی غیرممکن | `database/models.py:1475-1494` در برابر `fin_*`/`com_*`/`eco_*` | P1 |
| FR-09j | `fin_journal_batches` قید یکتای `(reference_type, reference_id)` ندارد ⇒ یک مرجع می‌تواند دوبار ژورنال شود | `database/models.py:506-520` | P1 |
| FR-09k | writer موازی ژورنال در `services/inventory/service.py:420-517` (دور زدن `LedgerService`) | همان‌جا | P1 |
| FR-09l | انحراف گرد‌کردن: `ROUND_HALF_EVEN` در برنامهٔ کارمزد، `ROUND_HALF_UP` در `realised_bps` | `services/finance/revenue_indicators.py:56-69`؛ `services/commerce/service.py:203-207` | P2 |
| FR-09m | ۷۳ تست property-based پول دقیقاً از ۴ فایل: ۲۷ + ۱۶ + ۲۵ + ۵ | `test_properties_money.py`، `test_properties_order_money.py`، `test_properties_valuation.py`، `test_properties_marketplace_money.py` | ✅ قوت |

### ۲٫۶ رجیستر نقض `float` روی پول (FR‑09c)

| # | محل | نوع |
|---|---|---|
| 1 | `services/finance/reconciliation.py:82-84` | `float(wallet.balance)` در گزارش رانش — **و تست تحملش می‌کند** |
| 2 | `services/finance/routers/finance.py:637-639` | `sum(float(w.balance) …)` در آمار کیف پول |
| 3 | `services/api_gateway/routers/ecowallet.py:313-315` | همان |
| 4 | `services/api_gateway/routers/ecowallet.py:338` | `float(state.get("balance", 0))` |
| 5 | `services/ecowallet/service.py:127-129` | payload برگشتی float، در حالی که docstring «Decimal throughout» ادعا می‌کند |
| 6 | `services/ecowallet/distribution.py:136-151` | `distribute(total: float)` + `round()` |
| 7 | `services/marketplace/models/marketplace_payment.py:62` | `float(self.amount or 0)` در سریال‌ساز canonical |
| 8 | `services/auth_legacy/repository.py:90,108` | لیترال float در `eco_wallets` |
| 9 | `services/marketplace/payments_service.py:543,639,681` | `float(payment.amount)` |
| 10 | `services/marketplace/order_management.py:81,148,285,323` | `float(product.price_per_kg)` |
| 11 | `services/landscape/service.py:210-212,356` | `float(fund.total_collected)` |
| 12 | `services/tourism/service.py:360-371` | `sum(float(b.total))` + `round()` |
| 13 | `services/finance/payment_provider.py` + `services/marketplace/routers/marketplace.py:1757` | `amount: float` در API پرداخت، در برابر `dec()` خودِ پلتفرم |

### ۲٫۷ ساختاری (FR‑11، FR‑12)

| ID | یافته | شاهد |
|---|---|---|
| FR-11 | مهاجرت‌های مرده: `mkt_carts`/`mkt_cart_items` (بدون مدل/سرویس/route)؛ `marketplace_wishlist` (مدل بلااستفاده)؛ `/api/v1/ledger/entries` در فهرست idempotency (router mount نشده)؛ `services/tourism/models/festival.py` (اعلان دوبارهٔ جدول) | `alembic/versions/20261018_153000_b2_marketplace_persistent_cart.py`؛ `services/marketplace/models/__init__.py:281`؛ `middleware/idempotency.py:41` |
| FR-12 | ادعاهای مستندی خلاف کد: `ComSettlement.order_id` (FR-05g)، «Arithmetic is Decimal» (#5)، «the in-memory cart is replaced»، `not_yet_available` (FR-08f) | همان بندها |

---

## ۳. موج‌های اجرا

| موج | دامنه | موازی؟ | دروازهٔ ورود | محتوا |
|---|---|---|---|---|
| **W1** گاردها | test/tooling | serial | G0 | FR‑01، FR‑02، FR‑03 |
| **W2** مجوز | gateway/services | serial | G1 | FR‑06a…i |
| **W3** حقیقت پرداخت و ۵۰۰ | marketplace/tourism | serial | G1 | FR‑05a…s، FR‑07a…d |
| **W4** درستی پول | finance/commerce | serial | G2 | FR‑05g…q، FR‑09 |
| **W5** صداقت payload | gateway/reporting | serial | G2 | FR‑08 |
| **W6** ساختاری | models/alembic | serial | G3 | FR‑11، FR‑12 |

### W1 — گاردها (اولین wave؛ کم‌هزینه‌ترین و پربازده‌ترین)

1. **FR‑01** — `test_p5_money_invariants.py`: `parents[2]` ⇒ `parents[3]`؛ و تصمیم صریح برای هر سه writer
   (مجاز به‌نام `services.wallet` و `services.auth_legacy` **یا** مهاجرت به `services.finance`؛
   `services.inventory` باید از مسیر `LedgerService` عبور کند).
2. **FR‑02** — `tests/test_money_detox.py`: افزودن یک تست که `_money_offenders` را روی **ریشهٔ واقعی** صدا بزند.
3. **FR‑03** — `tools/check_vacuous_tests.py`: ابزار CI که الگوهای پوچ را رد می‌کند
   (`inspect.getsource` + `assert` روی متن، assert روی صفت غیرسطری SQLAlchemy، seed مستقیم ORM به‌جای HTTP).

**دروازهٔ W1:** گاردها **واقعاً اسکن می‌کنند** (نمونهٔ منفی کنترل‌شده)؛ هیچ تستی ضعیف نشده؛ `ruff` بدون رشد.

### W2 — مجوز
FR‑06a…i: check مالکیت/نقش روی چهار مسیر بازارگاه + enforce پنجرهٔ ۴۸ ساعت؛ ادمین برای حل اختلاف؛
احراز هویت برای خواندن shipment؛ محدودسازی خواندن کیف پول به کیف پول خود کاربر؛ ادمین برای ساخت دستهٔ ژورنال؛
بستن اپ ledger مستقل یا افزودن auth؛ اعمال گیت KYC در `POST /vendors` و `POST /checkout/products`.

**دروازهٔ W2:** برای هر مسیر، یک تست منفی cross-tenant (پاسخ 403/404)؛ هیچ مسیر پول بدون auth.

### W3 — حقیقت پرداخت و ۵۰۰
FR‑07a/b (بازگرداندن `_update_tour_stats` و `return booking`)؛ FR‑07c/d (تعمیر `OrderManager` و واژگان وضعیت)؛
FR‑05d (callback زرین‌پال)؛ FR‑05e (idempotency روی `marketplace_orders`)؛ FR‑05f (تطبیق `payment_status` + نرخ کارمزد)؛
FR‑05r (واحد بازپرداخت گردشگری)؛ FR‑05a (Payment Proof).

### W4 — درستی پول
FR‑05h/i/j/k (ترتیب، قفل، TOCTOU، AuditEvent)؛ FR‑05l (دوباره‌شماری)؛ FR‑05g (قید یکتای `ComSettlement`)؛
FR‑09a/b/c/d (writer equity، کد حساب، Decimal)؛ FR‑09e/f/g/h (تطبیق).

### W5 — صداقت payload
FR‑08a…h.

### W6 — ساختاری
FR‑11 (حذف/پیوستن مهاجرت‌های مرده)؛ FR‑12 (تصحیح docstring‌های خلاف واقع).

---

## ۴. نقشهٔ مالکیت فایل (ضدّ برخورد)

| مالک | فایل‌ها |
|---|---|
| **A01 (W1)** | `services/finance/tests/test_p5_money_invariants.py`، `tests/test_money_detox.py`، `tools/check_vacuous_tests.py` |
| **A02 (W2)** | `services/api_gateway/routers/marketplace.py`، `services/dispute_resolution/routers/disputes.py`، `services/logistics/routers/logistics.py`، `services/api_gateway/routers/ecowallet.py`، `services/ledger/*` |
| **A03 (W3)** | `services/tourism/service.py`، `services/tourism/safety_service.py`، `services/marketplace/order_management.py`، `services/marketplace/payments_service.py`، `services/marketplace/models/__init__.py`، `services/finance/automated_marketplace_settlement.py` |
| **A04 (W4)** | `services/finance/wallet_service.py`، `services/finance/chart_of_accounts.py`، `services/finance/reconciliation.py`، `services/finance/ledger_service.py`، `services/commerce/service.py`، `database/models.py`، `alembic/versions/*` |
| **A05 (W5)** | `services/api_gateway/routers/blockchain.py`، `services/api_gateway/routers/tourism_router.py`، `services/reporting/service.py`، `services/api_gateway/routers/analytics.py` |

> درخت زنده است (۱٬۰۶۷ فایل تغییریافته در ۲۰۲۶-۱۰-۲۰). قاعدهٔ `KN-42`: **خواندن قبل از ویرایش،**
> **بررسی بعد از نوشتن**، و ویرایش فقط با ابزار `edit`/`write` (نه `Set-Content` در PowerShell).

---

## ۵. دروازه‌های عمومی (هر wave)

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
$env:SECRET_KEY = "test-secret-key"
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest <one suite> -q -p no:cacheprovider
& "D:\eco_nojin\.venv\Scripts\python.exe" -m ruff check .
& "D:\eco_nojin\.venv\Scripts\python.exe" -m mypy engine --ignore-missing-imports
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/detect_imports.py --root .
& "D:\eco_nojin\.venv\Scripts\python.exe" -c "from services.api_gateway.main import app; app.openapi()"
```

---

## ۶) خارج از دامنهٔ این برنامه (صریح)

- **راهبرد محصول** (سطح bazaar، تجارت عامل‌محور، e-invoicing، ظرفیت مشتق از موتور، ادعاهای حاکمیت‌شده)
  — این‌ها **پس از** بستن W1–W4 پیشنهاد می‌شوند؛ در این برنامه اجرا نمی‌شوند.
- **D‑04 / EcoCoin** — تصمیم محصول، مهاجرت/حذف منتظر تصمیم‌گیرنده.
- **ترکیب پنج انبار پول** (FR‑09h) — نیازمند تصمیم معماری D‑09/D‑10 بازبینی‌شده.
- **رابط کاربری** — طبق `REMEDIATION-PLAN-BACKEND-ONLY-2026-10-18.md §0` ممنوع.

---

## ۷) گزارش اجرا (۲۰۲۶-۲۰-۲۰)

### ۷٫۱ موج ۱ — گاردها ✅ کامل

| شناسه | اقدام | وضعیت |
|---|---|---|
| FR‑01 | `services/finance/tests/test_p5_money_invariants.py`: `parents[2]` ⇒ `parents[3]`؛ اسکنر به `tools/money_boundary.py` منتقل و allow‑list **مستند** شد؛ **کنترل منفی** افزوده شد (`test_money_write_scanner_actually_detects_an_offender`) | ✅ |
| FR‑02 | `tests/test_money_detox.py`: کپی دوم جدول حذف و هر دو گارد به یک اسکنر مشترک (`tools/money_boundary.py`) وصل شدند؛ تست «درخت واقعی» افزوده شد | ✅ |
| FR‑03 | `tools/check_vacuous_tests.py` + `tools/vacuous_test_baseline.json` (کلید = **متن خط**، نه شمارهٔ خط) | ✅ |

**یافتهٔ مهم حین اجرا:** گارد، پس از تعمیر، **برای اولین بار** درخت را اسکن کرد و **۵ writer غیرمجاز** آشکار کرد — که با فهرست اولیهٔ بازرسی متفاوت بود:

| writer | جداول | تصمیم |
|---|---|---|
| `services.finance` | `EcoBalance*` | **false-positive** — فقط *می‌خواند*؛ `execute` از تشخیص «نوشتن» حذف شد |
| `services.ecowallet` | `EcoWallet` | مجاز (ساخت سطر کیف پول با ماندهٔ صفر) |
| `services.auth_legacy` | `EcoWallet` | مجاز + **لیترال‌های float اصلاح شد** (`Decimal("0")` / `Decimal("100")`) |
| `services.inventory` | `FinJournal*` | مجاز — writer متوازن و *transaction-joining* که مستند است |
| `services.wallet` | `EcoBalance*` | مجاز — ماژول از `services/ecosystem/` منتقل شده بود؛ ورودی allow‑list کهنه بود |

### ۷٫۲ موج ۲ — مجوز ✅ (بخش بازارگاه)

- `_require_order_party()` افزوده شد: فقط **خریدار** سفارش، **فروشندگان** اقلامش، یا **ادمین**.
- روی `/orders/{id}/dispute`، `/orders/{id}/settle`، `/orders/{id}/complete` و `/orders/{id}/confirm` اعمال شد.
- **پنجرهٔ ۴۸ ساعت اعمال نشد** (تست پین‌شده داخل پنجره تسویه می‌کند) — به‌جای آن docstring صادق شد و FR‑06c به‌عنوان تصمیم محصول باز ماند.
- تست جدید: `services/api_gateway/tests/test_marketplace_escrow_authz.py` — **۶ تست** (مثبت: غریبه ۴۰۳، خریدار ۲۰۰، ادمین ۲۰۰).

### ۷٫۳ موج ۳ — حقیقت پرداخت و ۵۰۰ ✅

- FR‑07a: `_update_tour_stats` بازگردانده شد — `total_bookings` شمارش رزروهای **پرداخت‌شده** را نگه می‌دارد، `current_bookings` شمارش **شرکت‌کنندگان** (قرارداد پین‌شدهٔ `test_api_router.py:203-204`).
- FR‑07b: `cancel_booking` اکنون `booking` را برمی‌گرداند (پیش‌تر `None` ⇒ ۵۰۰)؛ `current_bookings` هم پیش‌تر منفی می‌شد، حالا کلمپ می‌شود.
- FR‑05r: بازپرداخت گردشگری دیگر **واحد اشتباه** ندارد. انتقال `WalletService` (کیف پول ECO با حداقل ۱۰ ECO، از کیف پول شخصی ادمین) **حذف شد** و به‌جای آن یک دستهٔ ژورنال دوطرفهٔ متوازن در **ارز رزرو (IRR)** ثبت می‌شود (`ECO_OPERATING_EXPENSE` ↔ `ECO_CASH`، قابل ردیابی با `reference_type="tourism_refund"`).
- FR‑08a/b: `blockchain/treasury/balance` و `blockchain/oracle/metrics` به `_eco_disabled` اضافه شدند ⇒ ۵۰۳ به‌جای اعداد ساختگی.
- FR‑08c: `GET /ecowallet/daily-cap` اکنون از همان `daily_earnings` که سقف را اعمال می‌کند می‌خواند (`WalletService.daily_cap_status`) به‌جای `earned_today=0` هاردکد.
- لبهٔ `services.tourism → services.finance` در `tools/service_boundary_policy.json` اعلام شد (با rationale).

### ۷٫۴ شواهد (اجرای ۲۰۲۶-۲۰-۲۰)

```
pytest services/finance/tests                                   → 187 passed, 0 failed
pytest services/api_gateway/tests/test_http_marketplace_commerce.py
        services/api_gateway/tests/test_marketplace_escrow_authz.py → 32 passed, 0 failed
pytest services/tourism/tests                                   → 59 passed, 1 failed*
pytest services/ecowallet/tests services/blockchain/tests
        tests/test_money_detox.py tests/test_p14_guard_sweep.py   → 76 passed, 0 failed
python tools/money_boundary.py --root .                          → OK (no unauthorized writer)
python tools/check_vacuous_tests.py --root . --strict            → 58 known, 0 new
ruff check <changed files>                                       → All checks passed!
python tools/detect_imports.py --root .                          → PASS (0 violations)
python tools/check_service_boundaries.py                         → 11 violation (preexisting, not ours)
from services.api_gateway.main import app; app.openapi()          → 118 routes / 710 paths
```

\* **تنها شکست باقی‌مانده مال این موج‌ها نیست:** `test_p8_scope.py::test_the_tourism_surface_advertises_only_mounted_paths`.
اختلاف ۱۵ مسیر است و **همهٔ آن‌ها `/festivals` یا `/unesco` هستند** — یعنی زیرروترهایی که
عامل دیگری هم‌زمان به `services/tourism/api/router.py` اضافه کرده (`M` در git). آن فایل و
`test_p8_scope.py` (untracked) طبق نقشهٔ مالکیت §۴ متعلق به همان عامل است و دست‌نخورده ماند.

### ۷٫۵ مواردی که به‌عمد به تعویق افتاد

| شناسه | دلیل تعویق | موج بعدی |
|---|---|---|
| FR‑06c | اعمال پنجرهٔ ۴۸ ساعت، قراردادِ پین‌شدهٔ چرخهٔ escrow را می‌شکند ⇒ تصمیم محصول لازم است | W2 (تصمیم) |
| FR‑05a/c/d | Payment Proof روی جدول مشترک — طراحی سراسری | W3 |
| FR‑05b/g/l, FR‑09 | ژورنال واحد، قید یکتای `ComSettlement`، رفع دوباره‌شماری کارمزد چشم‌انداز | W4 |
| FR‑05f | تطبیق `payment_status` و نرخ کارمزد تسویه‌گر خودکار | W3 |
| FR‑06d–i | روتر اختلاف، لجستیک، خواندن کیف پول، batch ژورنال، اپ ledger مستقل، گیت KYC فروشنده | W2 |
| FR‑08d–h | payloadهای جعلی باقی‌مانده (تصاویر محصول، تایم‌لاین، گزارش کربن، تایم‌لاین ECO) | W5 |
| FR‑11/FR‑12 | مهاجرت‌های مرده و docstring‌های خلاف واقع | W6 |
| FR‑07c/d | `OrderManager` و واژگان وضعیت `com_orders` | W3 |

> **قاعدهٔ رعایت‌شده:** هیچ تستی ضعیف یا حذف نشد. تنها استثنا: `test_p8_scope.py` که **متعلق به
> عامل دیگری** است و برای رفع تناقضِ در حال تغییرِ زمان اجرا دست‌نخورده ماند.

