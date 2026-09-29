# عامل ۱ — شکاف‌های قرارداد (Contract Gaps)

> این فایل «دستور عملیاتی» است. هر اجرا فقط **یک واحد** را انجام بده و خارج شو.

## هدف
کاهش `missing` گیت قرارداد از ۱۴ به ۰، به یکی از این سه روش برای هر مسیر:
۱) اتصال به یک endpoint منتشرشدهٔ موجود، ۲) حذف فراخوانی از کد، ۳) افزودن به فهرست «اعلام‌شده» فقط اگر محتوای ثابت باشد.

## محدودهٔ مجاز (فقط این‌ها)
- `apps/web/src/lib/api/cart.ts`
- `apps/web/src/lib/api/escrow.ts`
- `apps/web/src/lib/api/manual.ts`
- `apps/web/src/lib/api/public.ts`
- `docs/frontend/CONTRACT_REQUEST_CODE_USED_37.md`
- `docs/frontend/agents/state/agent-1.json` (وضعیت خودت)

## ممنوع
- `apps/web/messages/**` · `apps/web/src/lib/domains/**` · `apps/web/tests/**` · `.github/**` · سرور روی پورت ۳۰۰۰/۳۰۰۱/۳۱۱۱ · `pnpm install` · هر دادهٔ ساختگی یا mock.

## ورودی‌ها
- `docs/frontend/contract-gaps.json` (خروجی گیت)
- `openapi.json` (۴۸۹ مسیر منتشرشده)
- اجرای گیت: `node scripts/check-api-contract.mjs`

## الگوریتم هر اجرا (یک واحد)
1. `node scripts/check-api-contract.mjs --json` را اجرا کن.
2. اولین مسیر در `missing` را بردار.
3. در `openapi.json` دنبال معادل منتشرشده بگرد (مثلاً `/api/v1/marketplace` → `/api/v1/marketplace/cart` یا `/api/v1/marketplace/orders`).
4. اگر معادل هست: فراخوانی را بازنویسی کن و `pnpm -C apps/web type-check` بگیر.
   اگر نیست: در `CONTRACT_REQUEST_CODE_USED_37.md` ردیف آن مسیر را با «وضعیت: بدون قرارداد» و اقدام پیشنهادی به‌روزرسانی کن.
5. `state/agent-1.json` را به‌روزرسانی کن: `{ "processed": [...], "remaining": N, "lastRun": "<ISO>", "blocked": [] }`
6. خارج شو.

## معیار پذیرش
- `node scripts/check-api-contract.mjs` → عدد `missing` نسبت به اجرای قبل **کمتر یا برابر** باشد (هرگز بیشتر).
- `pnpm -C apps/web type-check` بدون خطا.

## رفتار در قطعی شبکه/خطا
- اگر دستوری به شبکه نیاز داشت و شکست خورد: در state با کلید `blocked: ["network"]` ثبت کن، واحد را نیمه‌کاره رها کن و خارج شو. اجرای بعدی خودش ادامه می‌دهد.
- اگر گیت شکست خورد: هیچ تغییری اعمال نکن و فقط گزارش بده.

## گزارش هر اجرا (کوتاه)
مسیر پردازش‌شده · اقدام (اتصال/حذف/اعلام) · `missing` قبل/بعد · نتیجهٔ type-check
