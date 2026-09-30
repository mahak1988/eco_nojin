# S-MONEY — قرارداد پول و کمیت

> پول `Decimal` است، کد ISO 4217 دارد، و **یک** قرارداد علامت در کل مخزن دارد.

**کد مرجع:** `services/_contracts/money.py`
**نسخه مرجع تطبیق‌پذیری:** `services/finance/ledger_service.py` (تنها نسخه با اعتبارسنجی توازن، علامت و فهرست دارایی)

## چرا این استاندارد

چهار `LedgerService` با سه قرارداد علامت متضاد:

| # | مکان | اعتبارسنجی | علامت موجودی |
|---|---|---|---|
| ۱ | `finance/ledger_service.py` | کامل | بستانکار مثبت، بدهکار منفی |
| ۲ | `finance/wallet_service.py` | **هیچ** | `بدهکار − بستانکار` (معکوس) |
| ۳ | `ledger/service.py` | هیچ | `func.sum` خام (بدون علامت) |
| ۴ | `ecowallet/ledger.py` | هیچ | `float` |

`reconcile_wallet_ledger` موجودی کیف پول را با موجودیِ محاسبه‌شده با قرارداد **معکوس** مقایسه می‌کرد، پس مغایرت کاذب روی هر حساب می‌ساخت.

## قرارداد علامت

**بستانکار مثبت، بدهکار منفی.** این قرارداد پیش‌تر در `finance/ledger_service.get_account_balance` پیاده و مستند شده بود؛ دو نسخه دیگر غلط‌اند، نه متفاوت.

## قواعد سخت

| قاعده | دلیل | ابزار |
|---|---|---|
| پول `Decimal`، هرگز `float` | `Decimal(0.1)` برابر `0.1000000000000000055…` است | `dec()` — `float` را رد می‌کند |
| یک قرارداد علامت واحد | سه قرارداد متضاد | `signed()` |
| واحد ISO 4217 | `IRT` کد پول نیست؛ `IRR` است | `require_asset()` |
| `IRT` و `fiat` ممنوع | `ledger/service.py:149` و `:30` | `ALLOWED_ASSETS` |
| خطا → استثنا، هرگز صفر خاموش | `ledger/service.py:93-95` صفر خاموش می‌داد | S-HONEST |
| دقت ≤ ۴ رقم اعشار | ستون `Numeric(19, 4)` | `Money.__post_init__` |
| توازن هر دسته پیش از ثبت | `wallet_service.create_journal_batch` هیچ بررسی نداشت | `balanced()` |

## دارایی‌های مجاز

```
IRR            ریال ایران (ISO 4217)
ECO            توکن اکو — داخلی
CARBON_tCO2e   تن CO2 معادل — کمیت، نه پول
USD            دلار آمریکا
```

افزودن دارایی جدید **تصمیم اسکیما و انطباق است، نه ویرایش یک ثابت.**

## `account_id` — قرارداد مرجع حساب

`FinJournalEntry.account_id` یک ستون `String` است، اما نویسندگان دو قرارداد متفاوت داشتند:

- `finance/wallet_service.py` می‌نوشت `FinAccount.id` (عدد صحیح)
- `commerce/service.py` می‌نوشت **کد حساب**، مثلاً `ECO_PLATFORM_REVENUE`

نتیجه: JOIN غیرممکن شد. `finance/reconciliation.py` روی `account_id == FinAccount.id` JOIN می‌کرد — **ستون String در برابر کلید اصلی Integer** — که هرگز مطابقت نمی‌کرد، پس هر کیف پول با موجودی صفر تطبیق داده می‌شد.

**قرارداد فعلی: کد حساب.** `services/finance/account_ref.py::account_join_condition` هر دو قرارداد تاریخی را تطبیق می‌دهد تا رکوردهای موجود از گزارش‌ها حذف نشوند.

## درست / نادرست

```python
# ✅ درست
Money.credit(Decimal("100.5000"), "IRR")
signed("credit", "100.50")  # ->  Decimal("100.50")
signed("debit", "100.50")  # ->  Decimal("-100.50")

# ❌ نادرست
Money.credit(0.1)  # MoneyError: float is refused
signed("debit", "100.50") * -1  # قرارداد علامت را دور می‌زند
total = func.sum(FinJournalEntry.amount)  # بدون علامت
```

## مهاجرت

ادغام چهار `LedgerService` در فاز ۴ بلوک ۳ انجام می‌شود (بالاترین ریسک). `finance/ledger_service.py` مقصد است. `services/ledger/` نسخه‌ای است که زمان‌بندی حذف آن به همان بلوک موکول است.
