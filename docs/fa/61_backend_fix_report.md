# گزارش اجرای Backend Fix Request — ۴/۴ تست PASS

> تاریخ: 2026-08-28 · نتیجه نهایی: `tests/integration/test_admin_finalize.py` → **4 passed in 9.02s**

## خلاصه اجرا (طبق دستور)
| # | مشکل گزارش | اقدام واقعی | وضعیت |
|---|---|---|---|
| 1 | ImportError در auth.py:11 | `from database.models import AuditLog, EcoWallet, PasswordResetToken, User` | ✅ رفع |
| 2 | AuditLog در login نوشته نمیشد | helper `_write_auth_audit` اصلاح شد (`models.AuditLog`→`AuditLog`) و هر سه شاخه login (موفق/رمز اشتباه/غیرفعال) آن را صدا میزنند؛ مرجعهای خراب `request`/`email` حذف شدند؛ signature بدون تغییر | ✅ رفع |
| 3 | فرمت detail در AuditOut | از قبل درست بود (`ok: email` / `failed: email` از details.result) — تأیید شد | ✅ تأیید |
| 4 | UserResponse schema | واقعاً اصلاح نشده بود → پچ شد: `id: str`، `full_name/language: Optional`، `ConfigDict(from_attributes=True)` | ✅ رفع |

## 🔴 دو ریشه کشفشده خارج از گزارش (حلشده)
1. **passlib 1.7.4 با bcrypt 5.0.0 کاملاً خراب بود** — `verify_password` برای رمز اشتباه هم True برمیگرداند (هر لاگینی موفق!). جایگزینی با فراخوانی مستقیم bcrypt (`hashpw`/`checkpw`) در `services/api_gateway/auth.py` — سازگار با هشهای `$2b$` موجود.
2. **conftest پچ میکرد**: `tests/conftest.py` تابعهای hash/verify را بازنویسی میکرد (`verify→True`، `hash→"dummyhash"`) — با انتظارات تست جدید در تضاد بود. پچها حذف شدند (رفتار واقعی رمز).

## ✅ شواهد تست
- هدف: **4 passed, 2 warnings in 9.02s** — هر ۴: overview_counts، overview_error_counts، security_login_history، security_requires_admin_role
- سویت اصلی services: **79 passed** (بدون تغییر)
- A/B برای رگرسیون: ۶ فایل دیگر tests/ با conftest اصلی و conftex جدید **دقیقاً یکسان** (14 failed/14 passed در هر دو) — ۱۴ fail پیش-existing است (مدلهای ContentItem/Setting در database.models تعریف نشدهاند؛ جدا از این درخواست)

## نکته حاشیهای
- یک `main.py.bak.*` ناخواسته وارد commit شد → از git خارج و `*.bak.*` به gitignore اضافه شد.

## قدم بعدی پیشنهادی
- تعریف `ContentItem` و `Setting` در `database/models.py` (یا اصلاح admin.py) تا ۱۴ fail پیش-existing tests/ هم سبز شود — خارج از محدوده این درخواست.
