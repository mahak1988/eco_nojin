# عامل ۲ — چندزبانگی (i18n)

> هر اجرا فقط **یک واحد** (یک فضانام در یک زبان) را انجام بده و خارج شو.

## هدف
پر کردن ۱۰ فضانام گمشده در ۱۲ زبان و بالا بردن پوشش کلیدها:
- فضانام‌ها: `admin`, `workspace`, `public`, `manual`, `help`, `layout`, `owner`, `why`, `surface`, `sponsors`
- زبان‌ها: `ar, ur, de, es, fr, hi, it, ms, pt, ru, zh, bn`
- هدف نهایی: موج ۰ (`ar, ur`) ≥ ۹۵٪ · موج ۱ (`de, es, fr, hi, pt, zh`) ≥ ۸۰٪ (فعلاً ۳۳–۴۶٪)

## محدودهٔ مجاز (فقط این‌ها)
- `apps/web/messages/<locale>.json` برای ۱۲ زبان بالا
- `docs/frontend/agents/state/agent-2.json`

## ممنوع
- تغییر `fa.json` یا `en.json` (مرجع‌اند) · حذف هیچ کلیدی · `apps/web/src/**` · `scripts/**` · `pnpm install` · سرور.

## الگوریتم هر اجرا (یک واحد)
1. `state/agent-2.json` را بخوان: `{ "done": ["<locale>:<namespace>", ...], "lastRun": ... }`
2. از زبان با **کمترین پوشش** شروع کن؛ اولین فضانام انجام‌نشده را انتخاب کن.
3. ساختار کلیدها را از `fa.json` بردار و همان ساختار را در فایل زبان مقصد بساز.
4. برای هر کلید **ترجمهٔ واقعی** بنویس؛ اگر ترجمهٔ مطمئن نداری، متن `fa` را نگه دار و `meta.machineTranslated: true` را حفظ کن (برچسب صادقانه لازم است).
5. فایل را UTF-8 بدون BOM بنویس؛ سپس معتبر بودن JSON را بررسی کن:
   `node -e "JSON.parse(require('fs').readFileSync('apps/web/messages/<locale>.json','utf8')); console.log('ok')"`
6. واحد را به `done` اضافه کن و خارج شو.

## معیار پذیرش
- `node scripts/check-locale-depth.mjs` → پوشش زبان انتخاب‌شده **افزایش** یابد.
- همهٔ ۱۴ فایل JSON معتبر بمانند.

## رفتار در قطعی شبکه/خطا
- کار به شبکه نیاز ندارد؛ اگر شکست خورد صرفاً `lastError` را در state ثبت کن و خارج شو.

## گزارش هر اجرا (کوتاه)
`<locale>:<namespace>` · پوشش قبل/بعد آن زبان · تعداد کلید افزوده
