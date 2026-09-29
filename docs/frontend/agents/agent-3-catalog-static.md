# عامل ۳ — وضعیت `static` در کاتالوگ و خروج صفحات محتوایی از noindex

> هر اجرا **یک واحد** (یک گروه مسیر) را انجام بده و خارج شو.

## هدف
افزودن وضعیت `static` به کاتالوگ تا صفحات محتواییِ دارای route ولی بدون endpoint، **indexable** شوند.
۲۳ مسیر اعلام‌شده در `docs/frontend/contract-allowlist.json` مبنای این کارند.

## محدودهٔ مجاز (فقط این‌ها)
- `apps/web/src/lib/domains/page-catalog.ts`
- `apps/web/src/lib/domains/page-catalog*.test.ts`
- `scripts/**` فقط اگر **generator** کاتالوگ آنجا باشد
- `docs/frontend/agents/state/agent-3.json`

## ممنوع
- `apps/web/src/app/**` · `apps/web/messages/**` · `apps/web/src/lib/api/**` · `apps/web/tests/**` · `.github/**` · `pnpm install` · سرور.

## الگوریتم هر اجرا (یک واحد)
1. تعیین کن generator وجود دارد یا نه (کامنت سرصفحهٔ کاتالوگ + جست‌وجو در `scripts/`).
2. اگر generator هست: منطق وضعیت را در آن اضافه کن و فایل را بازتولید کن.
   اگر نیست: منطق تعیین وضعیت در `page-catalog.ts` را به‌روز کن:
   - `endpoint موجود + route فایل` → `live`
   - `endpoint نیست + route فایل + مسیر در contract-allowlist.json` → **`static`** با `indexable = true`
   - `endpoint نیست + route فایل` (و در allowlist نیست) → `unavailable` (بدون تغییر)
3. نوع `CatalogStatus` و تست‌های همان پوشه را هم‌راستا کن.
4. `state/agent-3.json` را به‌روزرسانی کن (شمارش وضعیت‌ها قبل/بعد).
5. خارج شو.

## معیار پذیرش
- `pnpm -C apps/web exec vitest run src/lib/domains --reporter=basic` → همه سبز
- `pnpm -C apps/web type-check` → بدون خطا
- شمارش `unavailable` نسبت به قبل **کاهش** یابد (هدف: ۱۵۴ → ۱۳۱).

## رفتار در قطعی شبکه/خطا
- کار به شبکه نیاز ندارد. اگر تست شکست خورد، تغییر را برنگردان ولی در state با `needsFix: true` ثبت کن تا اجرای بعدی کامل کند.

## گزارش هر اجرا (کوتاه)
شمارش وضعیت‌ها قبل/بعد · فایل‌های تغییر‌یافته · نتیجهٔ تست و type-check
