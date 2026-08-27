# فاز ۸-ج — امنیت عنکبوتی (۱۰+ لایه) + استانداردهای باز + AI (تکمیل‌شده)

> تاریخ: 2026-08-27 · همه لایه‌ها رایگان، تست‌شده زنده روی سرور محلی (پورت 8011).

## ۱) فایروال عنکبوتی — `services/security/` (۱۱ لایه)
| لایه | پیاده‌سازی | تست زنده |
|---|---|---|
| ۱. WAF (ruleset) | ۱۹ قاعده (SQLi/XSS/مسیر/دستور/اسکنر) + امتیازدهی | SQLi → 403، XSS → 403 |
| ۲. Rate limiting هوشمند | پنجره لغزان IP (120/دقیقه) + مسیر auth سخت‌گیر (10/دقیقه) + سهمیه کاربر | 14× 429 در 130 درخواست |
| ۳. هدرهای امنیتی | CSP+HSTS+frame+referrer+permissions | هدرها روی همه پاسخ‌ها |
| ۴. JWT/RLS | Supabase (قبلاً) + تأیید Bearer در میان‌افزار | — |
| ۵. ضد فیشینگ | سکوت‌سازی دامنه (لون‌اشتاین) + SPF/DKIM/DMARC زنده (dnspython) + امضای کلون صفحه | `econojin.co` → suspicious؛ `econojin.com` → ok (ایمیل unprotected صادقانه) |
| ۶. پساکوانتوم | CRYSTALS-Kyber/Dilithium (هیبرید X25519/Ed25519) — ماژول آماده؛ ⚠️ liboqs روی ویندوز باینری pip ندارد → وضعیت صادقانه `not_installed` + مسیر رایگان: TLS پساکوانتوم Cloudflare در لبه یا نصب روی Linux/Docker | status → not_installed + note |
| ۷. خودترمیمی | watchdog (poll /health + restart) + مدارشکن (5 بلاک WAF در 60 ثانیه → بلاک 10 دقیقه) | `scripts/run_with_watchdog.py` |
| ۸. Honeypot | تله‌های /admin.php ،/.env ،/wp-login.php → بلاک خودکار IP + رویداد | /admin.php → 404 + رویداد ثبت شد |
| ۹. رفتارشناسی | نمره آنومالی (حجم، نسبت 4xx، آنتروپی payload) | فعال |
| ۱۰. رمزنگاری | at-rest (Supabase + helper فیلد-سطح) + in-transit (TLS) | — |
| ۱۱. Zero-trust RBAC + audit | رویدادهای امنیتی → جدول `security_events` (یا JSONL محلی صادقانه) | رویدادها در /api/v1/security/events |

- میان‌افزار بدنه را کامل بافر می‌کند، اسکن می‌کند، سپس به اپ پخش می‌کند (WAF واقعی).
- همه درخواست‌ها هدر `x-econojin-firewall: active` دارند.

## ۲) استانداردهای باز
- **OGC API — Features (Part 1 Core)**: `/ogc/features/v1/` (landing, conformance, collections, items GeoJSON) — داده واقعی از ویو `ogc_landscape_points` (PostGIS) با پالیسی خواندن عمومی (migration 0007). تست: ۵ feature واقعی.
- **WaterML 2.0 (زیرمجموعه)**: `/ogc/waterml/1.0/timeseries` — سری واقعی SPI/SPEI (ERA5) به‌صورت om:Observation/wml2:MeasurementTimeseries؛ NaNها صادقانه حذف می‌شوند. تست: ۲۳۰ نقطه، بدون NaN.

## ۳) AI — RAG → NLG/LLM
- `services/ai/rag.py`: شاخص BM25 (بدون وابستگی) روی `docs/fa/*.md` — ۳۳۶ سند.
- `services/ai/nlg.py`: موتور توصیه فارسی قطعی + آداپتر LLM (BYO key: AI_LLM_KEY) — فیلد provider همیشه صادقانه.
- `POST /api/v1/ai/advise`: تست زنده — «بندسار برای کاهش رواناب» → ۳ جمله توصیه + SPI زنده -0.812 + ۳ مدرک.

## ۴) استقرار رایگان
- `frontend/vercel.json` (Vercel رایگان): SPA + هدرهای امنیتی (CSP/HSTS).
- `render.yaml` (Render رایگان) + `railway.toml` (Railway رایگان): API با watchdog و healthcheck.
- پساکوانتوم رایگان در لبه: Cloudflare (X25519MLKEM768) هنگام اتصال دامنه.

## ۵) دیتابیس (migration 0007 — اعمال‌شده زنده)
- `security_events` / `audit_log` / `blocked_ips` (RLS: مالک + ادمین) + ویو `ogc_landscape_points` + خواندن عمومی `platform_landscapes`.

## قدم بعدی
- ✅ پاک‌سازی داده تستی انجام شد (۳۱ رکورد: ۲۱ نقطه منظره + ۱۰ پروژه کربن تستی حذف، فقط حساب ادمین باقی ماند).
- اتصال دامنه واقعی + تنظیم SPF/DKIM/DMARC، و ارتقای AI به LLM رایگان (مثلاً Groq free tier با AI_LLM_KEY) — نیازمند اقدام کاربر.
