# عامل ۹ — تکمیل صفحات پژوهش

> اجرای ریز: هر بار فقط **یک صفحه**.

## هدف
بستن شکاف صفحات `research` (hub/runs، science/datasets، citations، model-cards، zenodo). صف:
```
node scripts/agents/list-planned.mjs research
```
خط اول = واحد این اجرا. ستون دوم: `has-endpoint` یعنی در دروازهٔ زنده قابل bind است؛ `NO-ENDPOINT` یعنی منتظر قرارداد (خوشهٔ `research/experiments/*` در `CONTRACT_REQUEST_154.md`).

## محدودهٔ مجاز (فقط این‌ها)
- `apps/web/src/app/[locale]/research/**`
- `apps/web/messages/fa.json` و `en.json` — فقط افزودن کلید زیر فضانام `pages.research.*`
- `docs/frontend/agents/state/agent-9.json`

## ممنوع
- ۱۲ زبان دیگر `messages/` · `lib/domains/**` · `lib/api/**` · `admin/**` · `system/**` · `market/**` · `public/**` · `.github/**` · `pnpm install` · سرور روی پورت‌های dev · **دادهٔ ساختگی**

## الگوریتم هر اجرا (یک صفحه)
1. صف را بگیر؛ خالی بود → `done: true` و خروج.
2. یک صفحهٔ `research` موجود را الگو بگیر (لایهٔ `ResearchWorkspaceShell` را دوباره نساز).
3. صفحه را بساز:
   - `has-endpoint` → bind واقعی + `loading/empty/error`.
   - `NO-ENDPOINT` → حالت خالی صادقانه + یادداشت «منتظر قرارداد».
4. کلیدها را زیر `pages.research.<slug>` به fa/en اضافه کن (read-modify-write).
5. `pnpm -C apps/web type-check` → بدون خطا.
6. state را به‌روزرسانی کن و خارج شو.

## معیار پذیرش
- `type-check` سبز · صفر دادهٔ ساختگی · کلید عنوان fa/en.

## در قطعی شبکه/خطا
- `blocked` را ثبت و خارج شو.

## گزارش هر اجرا (۳ خط)
مسیر · وضعیت · نتیجهٔ type-check
