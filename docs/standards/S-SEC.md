# S-SEC — قرارداد امنیت

> هر مسیر: مجوزدهی صریح، دروازه خروجی، و میان‌افزار یا mount‌شده یا حذف‌شده.

**دروازه:** G1 + قرارداد مجوز — فاز ۳
**پایه:** `services/security/middleware.py` (تنها لایه دفاعی mount‌شده) + ۱۵۵ آزمون

## قواعد سخت

| قاعده | ابزار |
|---|---|
| هر endpoint: `require_user` + **بررسی مالکیت صریح** | آزمون AST: هر `router.post` باید `Depends(...)` داشته باشد |
| عملیات حساس: step-up با ۲FA واقعی | `services/security/tests/test_step_up.py` |
| مقایسه کلید/توکن: `hmac.compare_digest` | Ruff + آزمون |
| دروازه SSRF روی هر درخواست خروجی | `security/ssrf.py` باید به `httpx` transport وصل شود |
| هر میان‌افزار نوشته‌شده یا mount شود یا حذف شود | آزمون `test_middleware_mounted.py` |
| `X-Request-ID` اعتبارسنجی شود (طول + کاراکتر) | آزمون |
| `security_router` mount شود و وضعیت زنده گزارش کند | `test_firewall_wiring.py` |

## کد امنیتی نوشته‌شده اما نصب‌نشده

| فایل | خطوط | وضعیت |
|---|---|---|
| `security/ssrf.py` | ۱۰۹ | هرگز import نمی‌شود — **هیچ درخواست خروجی محافظت نمی‌شود** |
| `security/headers.py` | ۵۲ | هرگز import نمی‌شود — تنها CSP کل مخزن اینجاست |
| `security/slowloris.py` | ۱۵۹ | هرگز import نمی‌شود؛ **و منطقی هم خراب است** |
| `security/redis_rate_limit.py` | ۹۶ | هرگز import نمی‌شود؛ **و ضعیف‌تر** از `rate_limit.py` فعال |
| `routers/security_router.py` | ۱۴۳ | **هرگز mount نمی‌شود** — هیچ دیدی از وضعیت امنیتی در اجرا |
| `privacy/vault.py` | ۲۰۹ | غیرکارکردی: شناسه‌های متفاوت، Fernet با متن رمز، کنترل دسترسی `pass` |
| `session_manager.py` + `two_factor.py` | ۱۷۸ | کاملاً مرده — `KEYS "session:*"`، TOTP با SHA-256 بدون نمک |

## نقض‌های مجوزدهی ثبت‌شده (فاز ۱ رفع شد)

| مسیر | نقض قبلی |
|---|---|
| ۱۲ مسیر `compliance.py` | فقط `require_user` — خواندن KYC هر کاربر شامل تاریخ تولد، تأیید/رد هر کاربر، ساخت پرچم سبزنمایی برای رقیب |
| `carbon.py:tokenize/transfer/retire` | فقط `require_user` — **هر کاربر می‌توانست اعتبار کربن صادر کند** |
| `auth_supabase.py:oauth/callback` | `?mock=true` حساب می‌ساخت و توکن معتبر برمی‌گرداند |
| `passkey_router.py:step-up` | بدون اجرای ۲FA — `{"method":"totp"}` بدون هیچ کدی اثبات می‌ساخت |

## اصل تصمیم

مسیرهای انطباق و توکن‌سازی **مدیر-محور** شدند، نه کاربرمحور. دلیل: هیچ جدول مالکیت پروژه یا آدرس به این روترها وصل نیست. تا وقتی مدل مالکیت وجود ندارد، حداقل امن، انحصار مدیر است — و این در `docs/standards/S-HONEST.md` به‌عنوان تصمیم صریح ثبت شده، نه به‌عنوان راه‌حل دائمی.

## کد مرتبط

`services/security/middleware.py` — تنها لایه mount‌شده: honeypot → ضدربات → WAF → نرخ‌محدودسازی → امتیاز ناهنجاری. بهترین وضعیت مخزن (نسبت آزمون ۰٫۶۰) و الگوی بقیه لایه‌ها.
