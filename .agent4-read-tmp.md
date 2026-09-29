# عامل ۴ — بازارگاه: از قرارداد تا قابلیت bind‌شده

> هر اجرا **یک واحد** (یک خوشهٔ API) را انجام بده و خارج شو.

## هدف
کاهش شکاف بازارگاه: از ۱۰۶ endpoint منتشرشده و ۴+۴۹ مورد `planned/unavailable` به سمت «قابلیت bind‌شده» حرکت کن.
مرجع خوشه‌ها: `docs/frontend/CONTRACT_REQUEST_154.md` (خوشه‌های `market/bazaars`، `market/product`، `market/search`، `market/categories`، `market/stores`).

## محدودهٔ مجاز (فقط این‌ها)
- `apps/web/src/app/[locale]/market/**`
- `apps/web/src/components/market/**`
- `docs/frontend/MARKETPLACE_IMPLEMENTATION.md` (به‌روزرسانی وضعیت)
- `docs/frontend/agents/state/agent-4.json`

## ممنوع
- `messages/**` · `lib/api/public.ts` · `lib/domains/**` · `tests/**` · `.github/**` · `pnpm install` · سرور روی پورت‌های dev · **هر دادهٔ ساختگی**.

## الگوریتم هر اجرا (یک واحد)
1. `state/agent-4.json` را بخوان: `{ "done": ["<cluster>", ...] }`
2. اولین خوشهٔ انجام‌نشده را بردار.
3. بررسی کن endpoint آن خوشه در دروازهٔ زنده هست یا نه (اگر دروازه بالا نیست: `curl http://127.0.0.1:8000/api/v1/platform/health`؛ در نبود دروازه، فقط با `openapi.json` کار کن).
4. اگر endpoint منتشر شده: صفحه/کامپوننت مربوطه را به آن bind کن، با حالت‌های `loading/empty/error` صادقانه.
   اگر منتشر نشده: در `MARKETPLACE_IMPLEMENTATION.md` وضعیت خوشه را «منتظر قرارداد» ثبت کن و صفحه را با **حالت خالی صادقانه** نگه دار.
5. `state/agent-4.json` را به‌روزرسانی کن و خارج شو.

## معیار پذیرش
- `pnpm -C apps/web type-check` بدون خطا
- هیچ صفحه‌ای دادهٔ ساختگی نشان ندهد؛ در نبود داده، متن صادقانه نمایش دهد.

## رفتار در قطعی شبکه/خطا
- اگر دروازه/شبکه در دسترس نبود، کار را روی `openapi.json` ادامه بده و در state `blocked: ["gateway"]` ثبت کن.

## گزارش هر اجرا (کوتاه)
خوشهٔ پردازش‌شده · وضعیت (bind شد / منتظر قرارداد) · فایل‌ها · نتیجهٔ type-check
