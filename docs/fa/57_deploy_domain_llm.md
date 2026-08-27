# فاز ۸-ج — راهنمای استقرار رایگان: دامنه + DNS + LLM

> تاریخ: 2026-08-27 · وضعیت DNS امروز (بررسی زنده): هر سه دامنه پیشنهادی (econojin.ir / .com / .land) **NXDOMAIN** هستند — هنوز ثبت نشده‌اند.

## ۰) وضعیت فعلی
- ✅ پاکسازی داده تستی: انجام شد (۳۱ رکورد حذف، فقط ادمین).
- ⬜ ثبت دامنه: نیازمند اقدام شما (زیر را ببینید).
- ⬜ کلید LLM رایگان: نیازمند اقدام شما (زیر را ببینید).

## ۱) ثبت دامنه
- ایران: `nic.ir` (irnic) برای `.ir` — ثبت‌کنندگان مجاز در سایت ایرنیک.
- بین‌الملل: هر رجیسترار (Cloudflare Registrar بدون مارک‌آپ برای `.com`).
- پیشنهاد: `econojin.ir` (برای بازار ایران) + `econojin.com` (بین‌الملل).

## ۲) DNS + ایمیل معتبر (SPF/DKIM/DMARC)
پس از ثبت دامنه، DNS را به **Cloudflare رایگان** منتقل کنید (فقط تغییر nameserver) — مزیت: TLS پساکوانتوم (X25519MLKEM768) در لبه بدون هزینه.

| نوع | نام | مقدار | هدف |
|---|---|---|---|
| A | @ | `76.76.21.21` | Vercel (frontend) |
| A | @ | `216.24.57.1` | Render (API) — یا CNAME ساب‌دامنه `api.` |
| CNAME | api | `api.your-render-service.onrender.com` | API |
| TXT | @ | `v=spf1 include:spf.zoho.com ~all` | SPF (مثال Zoho؛ برای سرویس‌دهنده خودتان تنظیم کنید) |
| TXT | _dmarc | `v=DMARC1; p=quarantine; rua=mailto:dmarc@econojin.ir; pct=100` | DMARC (بعد از چند هفته p=reject) |
| TXT | `zoho._domainkey` | `v=DKIM1; k=rsa; p=…` | DKIM (کلید از پنل سرویس ایمیل) |

> ⚠️ DKIM سِلکتور به سرویس‌دهنده ایمیل بستگی دارد (Zoho/Mailgun/Resend/Cloudflare Email Routing رایگان). کلید از پنل همان سرویس گرفته می‌شود.
> بررسی زنده: `POST /api/v1/security/anti-phishing {"domain":"econojin.ir"}` باید `verdict: protected` برگرداند.

## ۳) استقرار رایگان
1. **فرانت**: ریپو را به Vercel وصل کنید (فریم‌ورک Vite، build `pnpm build`، دایرکتوری `frontend`) — `frontend/vercel.json` از قبل هدرهای امنیتی را اعمال می‌کند.
2. **بک‌اند**: `render.yaml` را در Render (free) بزنید یا `railway.toml` در Railway — دستور شروع `python scripts/run_with_watchdog.py` (خودترمیمی + healthcheck).
3. **متغیرهای محیطی** (هر دو سرویس): `SUPABASE_URL`، `SUPABASE_ANON_KEY`، `SUPABASE_ACCESS_TOKEN`، `AI_LLM_KEY`، `TRUSTED_DOMAINS`، `APP_ENV=production`.

## ۴) اتصال LLM رایگان (Groq free tier)
1. در <https://console.groq.com> ثبت‌نام کنید → API Keys → ساخت کلید (رایگان، محدودیت روزانه).
2. کلید را در `.env` بگذارید:
   ```
   AI_LLM_KEY=gsk_…
   AI_LLM_URL=https://api.groq.com/openai/v1/chat/completions
   AI_LLM_MODEL=llama-3.3-70b-versatile
   ```
3. تست: `POST /api/v1/ai/advise {"question":"بندسار برای کاهش رواناب"}` → فیلد `provider` باید `llm:llama-3.3-70b-versatile` شود (فعلاً `local-nlg` است — صادقانه).
4. اگر Groq خطا داد، موتور به‌صورت خودکار به NLG محلی برمی‌گردد و `llm_error` را گزارش می‌کند (هرگز تظاهر به LLM نمی‌کند).

## ۵) چک‌لیست نهایی
- [ ] `https://دامنه/health` → 200 + هدرهای امنیتی
- [ ] `https://api.دامنه/ogc/features/v1/collections` → 200
- [ ] anti-phishing دامنه اصلی → `verdict: ok` و `email_auth: protected`
- [ ] `/api/v1/security/status` → همه لایه‌ها active
- [ ] `/api/v1/ai/advise` → provider=llm…
