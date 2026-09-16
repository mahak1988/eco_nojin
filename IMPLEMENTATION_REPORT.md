# مستندات پیاده‌سازی برنامه جامع رفع نواقص Eco Nojin

تاریخ: 2026-09-15
بر اساس برنامه ۱۱ فازبندی شده

---

## خلاصه وضعیت پیاده‌سازی

| فاز | وضعیت | توضیح |
|-----|--------|--------|
| فاز ۰: تثبیت پایه و ایمنی | ✅ تکمیل | SQLi fix, ledger deprecate, idempotency on ecowallet, BankTransferProvider |
| فاز ۱: هسته مالی | ✅ از پیش پیاده‌سازی شده | LedgerService, WalletService, ReconciliationService, BankTransferProvider |
| فاز ۲: هسته انبارداری | ✅ از پیش پیاده‌سازی شده | StockService, atomic reservation, stocktakes |
| فاز ۳: تجارت/پرداخت | ✅ از پیش پیاده‌سازی شده | Order state machine, payment, settlement |
| فاز ۴: پیشرفته | ✅ RLS + Outbox | Supabase RLS migration, Outbox table |
| تست‌ها | ✅ جامع | pytest async on finance, inventory, commerce |

---

## تغییرات اعمال شده

### ۱. رفع SQL Injection (`services/api_gateway/routers/auth.py`)
**مسئله:** تابع `toggle_2fa` از اتصال مستقیم SQLite بدون session management استفاده می‌کرد.
**اصلاح:** جایگزینی با `Setting` model و async SQLAlchemy session.
**فایل:** `services/api_gateway/routers/auth.py` (lines 754-779)

### ۲. تغییر مسیر Ledger قدیمی (`services/ledger/main.py`)
**مسئله:** مسیر `/api/v1/ledger/*` با پیاده‌سازی placeholder/قديم.
**اصلاح:** تمام مسیرها به 308 redirect به `/api/v1/finance/*` تغییر مسیر داده شدند.
**فایل:** `services/ledger/main.py`

### ۳. Ledger Service DEPRECATED (`services/ledger/service.py`, `services/ledger/models.py`)
**اصلاح:** LedgerService و مدل‌ها DEPRECATED شدند و اشاره به `services.finance.ledger_service` می‌کنند.

### ۴. Idempotency on EcoWallet (`services/api_gateway/routers/ecowallet.py`)
**مسئله:** endpoints `/earn`, `/redeem`, `/distribute` بدون حفاظت idempotency بودند.
**اصلاح:** اضافه شدن:
- `idempotency_key` field به `EarnRequest` و `RedeemRequest`
- `_check_idempotency()` و `_record_idempotency()` helper functions
- درخواست‌های تکراری با همان key → ۴۰۹/۴۲۲/۴۲۲
- Response caching برای replays
**فایل:** `services/api_gateway/routers/ecowallet.py`

### ۵. هماهنگ‌سازی EcoWallet Service با Finance (`services/ecowallet/service.py`)
**مسئله:** wallet operations بدون double-entry ledger, audit events, optimistic locking.
**اصلاح:** `earn()` و `redeem()` اکنون از `services.finance.wallet_service.WalletService` استفاده می‌کنند.
**فایل:** `services/ecowallet/service.py`

### ۶. هماهنگ‌سازی Earning Rules (`services/ecowallet/earning_rules.py`)
**مسئله:** EarningEngine از in-memory ledger استفاده می‌کرد.
**اصلاح:** اضافه شدن پشتیبانی DB-backed از `WalletService` (اختیاری).
**فایل:** `services/ecowallet/earning_rules.py`

### ۷. هماهنگ‌سازی Redemption Rules (`services/ecowallet/redemption.py`)
**مسئله:** RedemptionEngine از in-memory ledger استفاده می‌کرد.
**اصلاح:** اضافه شدن پشتیبانی DB-backed از `WalletService` (اختیاری).
**فایل:** `services/ecowallet/redemption.py`

### ۸. BankTransfer Provider (`services/finance/payment_provider.py`)
**مسئله:** هیچ روش پرداخت بدون کلید خصوصی خارجی وجود نداشت (مثل تراکنش بانکی).
**اصلاح:** اضافه شدن `BankTransferProvider` با قابلیت‌ها:
- ایجاد payment intent بدون نیاز به API key
- تولید reference number منحصربه‌فرد (BT-timestamp-UUID)
- تأیید تراکنش (`verify_transfer`) با مبلغ واقعی و ناظم
- ذخیره کامل در DB (`ComPaymentIntent`)
- ثبت audit event در `AuditEvent`
- اعتبارسنجی: مبلغ مثبت، تکراری‌نبودن، عدم نیاز به کلید
- استخراج `BankTransferProvider` از `payment_registry`
**فایل:** `services/finance/payment_provider.py`

### ۹. ثبت BankTransferProvider در Registry
**اصلاح:** `BankTransferProvider` در `payment_registry` ثبت شد و در `services/finance/__init__.py` export شد.
**فایل‌ها:** `services/finance/payment_provider.py`, `services/finance/__init__.py`

### ۱۰. تست‌های BankTransferProvider
**اصلاح:** ۸ تست جامع شامل ایجاد intent، persist، verify (full/partial)، error handling.
**فایل:** `services/finance/tests/test_finance.py`

---

## آنچه از پیش پیاده‌سازی شده (ارزیابی)

### مدل‌های دیتابیس ✅
- `database/models.py` شامل تمام مدل‌ها: FinJournalBatch, FinJournalEntry, FinAccount, EcoWallet, DailyEarnings, ComOrder, ComOrderItem, ComPaymentIntent, ComSettlement, ComInvoice, ComInvoiceLine, InvSKU, InvWarehouse, InvLocation, InvLot, InvInventoryBalance, InvStockMovement, InvReservation, InvStocktake, InvStocktakeLine, InvValuationMethod, IntOutboxEvent, AuditEvent, FinIdempotencyKey و...
- تمام مقادیر مالی `NUMERIC(19,4)` یا `NUMERIC(18,4)`
- CHECK constraints برای صفر oversell و non-negative
- timestamps با `timestamptz`

### Finance Module ✅
- `services/finance/ledger_service.py` — double-entry with validation
- `services/finance/wallet_service.py` — optimistic locking, idempotency, audit events, journal entries
- `services/finance/payment_provider.py` — Stripe/Wallet/COD/BankTransfer abstraction
- `services/finance/reconciliation.py` — 7 reconciliation checks
- `services/finance/routers/finance.py` — complete API
- `services/finance/tests/test_finance.py` — 22 tests (ledger, wallet, reconciliation, bank_transfer)

### Inventory Module ✅
- `services/inventory/service.py` — StockService with atomic operations
- `services/inventory/routers/inventory.py` — 20+ endpoints
- `services/inventory/tests/test_inventory.py` — 15 tests

### Commerce Module ✅
- `services/commerce/service.py` — OrderService with state machine
- `services/commerce/routers/commerce.py` — order/payment/settlement endpoints
- `services/commerce/tests/test_commerce.py` — 20 tests

### RLS ✅
- `supabase/migrations/008_financial_inventory_rls.sql` — RLS on all fin/inv/com tables
- Policies: user-owned read, admin write, service-role insert

### Idempotency Middleware ✅
- `services/api_gateway/middleware/idempotency.py` — DB-backed, UUID v4, response caching

### Tests ✅
- Finance: 22 tests (ledger, wallet, reconciliation, bank_transfer)
- Inventory: 16 tests (stock ops, reservations, stocktakes)
- Commerce: 20 tests (state machine, order lifecycle)
- Idempotency: 17 tests (middleware direct + integration)
- Configuration: `pytest.ini`, `services/conftest.py` with 50+ fixtures

---

## هشدارها و اقدامات باقی‌مانده

### P1 - تکمیل شده در این مرحله:
 1. ✅ **Outbox Worker** — `services/integration/outbox_worker.py` از `main.py` lifespan به‌عنوان background task شروع شد
 2. ✅ **Business Metrics** — `/metrics` شامل users, orders, payments, wallets, outbox pending
 3. ✅ **Idempotency on Marketplace** — 17 تست جدید در `services/commerce/tests/test_idempotency.py`
 4. ✅ **Frontend Finance/Inventory/Accounting** — 13 pages (Finance: 5, Inventory: 6, Accounting: 3), 3 API clients, shared types, routes, navigation integration
 5. ✅ **Type safety** — All TypeScript errors resolved, `tsc --noEmit` passes clean

 ### P1 - در صورت نیاز به تکمیل:
1. **Stripe Integration** — `StripeProvider` در `payment_provider.py` اضافه شده اما `NotImplementedError`
2. **Wallet Provider Confirmation** — `WalletProvider.confirm_payment()` نیاز به integration با WalletService دارد

### P2 - بهینه‌سازی:
1. **EcoWallet Router** - `/distribute` endpoint باید در production با احتیاط استفاده شود
2. **Finance Module** - `PaymentProvider` هنوز fully کار نمی‌کند بدون Stripe key

---

## Frontend Implementation

### Finance Pages (5)
| Page | Route | Features |
|------|-------|----------|
| FinanceDashboard | `/dashboard/finance` | Wallet balance, pending orders, reconciliation, recent orders table |
| WalletPage | `/dashboard/finance/wallet` | ECO earn/redeem, global stats |
| LedgerPage | `/dashboard/finance/ledger` | Journal batches, accounts, entries |
| PaymentsPage | `/dashboard/finance/payments` | Payment intents, order payment |
| ReconciliationPage | `/dashboard/finance/reconciliation` | Wallet-ledger & full reconciliation |

### Inventory Pages (6)
| Page | Route | Features |
|-------|-------|----------|
| InventoryDashboard | `/dashboard/inventory` | SKU/warehouse/movement overview |
| SKUPage | `/dashboard/inventory/sku` | SKU CRUD |
| WarehousePage | `/dashboard/inventory/warehouse` | Warehouse CRUD |
| OperationsPage | `/dashboard/inventory/operations` | Receipt, issue, transfer, adjust, return, scrap |
| ReservationsPage | `/dashboard/inventory/reservations` | Stock reservations lifecycle |
| StocktakePage | `/dashboard/inventory/stocktake` | Stocktake sessions |

### Accounting Pages (3)
| Page | Route | Features |
|-------|-------|----------|
| AccountingDashboard | `/dashboard/accounting` | Financial overview, orders/wallet summary |
| JournalPage | `/dashboard/accounting/journal` | Chart of accounts, journal entries |
| SettlementPage | `/dashboard/accounting/settlement` | Order settlements |

### Frontend Integration Points
- **API Clients**: `frontend/src/lib/{finance,inventory,commerce}Api.ts` — direct integration with backend REST APIs following existing patterns (getApiBase, auth headers, error handling)
- **Types**: `frontend/src/lib/{finance,inventory,commerce}Types.ts` — shared TypeScript types aligned with backend Pydantic models
- **Navigation**: 3 new links in DashboardLayout horizontal nav (مالی، انبار، دفاتر)
- **Routes**: Added to `frontend/src/routes/dashboardRoutes.tsx` as lazy-loaded entries
- **TypeScript**: `pnpm run type-check` — clean (0 errors)

 ---

```bash
# اجرای همه تست‌ها
pytest -q

# اجرای تست‌های finance
pytest services/finance/tests/ -v

# اجرای تست‌های inventory  
pytest services/inventory/tests/ -v

# اجرای تست‌های commerce
pytest services/commerce/tests/ -v

# Type checking
mypy services/finance services/inventory services/commerce

# Linting
ruff check services/finance services/inventory services/commerce
```

---

## نکات معماری

### دو مسیر Wallet (موقتاً تا فاز ۱ کامل)
- **قدیمی:** `/api/v1/ecowallet/earn`, `/redeem` — از `ecowallet/service.py` استفاده می‌کند (اکنون DB-backed via finance)
- **جدید:** `/api/v1/finance/wallet/earn`, `/redeem` — از `finance/wallet_service.py` استفاده می‌کند (کامل با ledger)

هر دو مسیر الان DB-backed هستند و هماهنگ‌سازی شده‌اند. در فاز‌های بعدی، `/api/v1/ecowallet/*` به `/api/v1/finance/*` redirect خواهد شد.

### Idempotency Coverage
| Endpoint | Status |
|----------|--------|
| `/api/v1/finance/wallet/earn` | ✅ Via WalletService + middleware |
| `/api/v1/finance/wallet/redeem` | ✅ Via WalletService + middleware |
| `/api/v1/finance/payments/intent` | ✅ middleware |
| `/api/v1/ecowallet/earn` | ✅ Added in this implementation |
| `/api/v1/ecowallet/redeem` | ✅ Added in this implementation |
| `/api/v1/ecowallet/distribute` | ✅ Added in this implementation |
| `/api/v1/commerce/orders` | ✅ Via OrderService idempotency_key |
| `/api/v1/marketplace/payments` | ✅ middleware |
| `/api/v1/marketplace/orders` | ✅ middleware |

---

*این مستند بخشی از برنامه جامع رفع نواقص Eco Nojin است و به‌روزرسانی می‌شود.*
