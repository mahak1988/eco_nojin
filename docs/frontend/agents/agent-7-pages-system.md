# عامل ۷ — تکمیل صفحات سامانه‌ای

> اجرای ریز: هر بار فقط **یک صفحه**.

## هدف
بستن شکاف صفحات `system` (تحلیل‌ها، داشبوردها، خودکارسازی). صف:
```
node scripts/agents/list-planned.mjs system
```
خط اول = واحد این اجرا.

## محدودهٔ مجاز (فقط این‌ها)
- `apps/web/src/app/[locale]/system/**`
- `apps/web/messages/fa.json` و `en.json` — فقط افزودن کلید زیر فضانام `pages.system.*`
- `docs/frontend/agents/state/agent-7.json`

## ممنوع
- ۱۲ زبان دیگر `messages/` · `lib/domains/**` · `lib/api/**` · `public/**` · `admin/**` · `market/**` · `research/**` · `.github/**` · `pnpm install` · سرور روی ۳۰۰۰/۳۰۰۱/۳۱۱۱ · **دادهٔ ساختگی**

## الگوریتم هر اجرا (یک صفحه)
1. صف را بگیر؛ خالی بود → `done: true` و خروج.
2. یک صفحهٔ `system` موجود را الگو بگیر.
3. صفحه را بساز:
   - `endpoint دارد` → bind واقعی + `loading/empty/error`.
   - `endpoint ندارد` → حالت خالی صادقانه + یادداشت «منتظر قرارداد» (خوشه‌ها در `CONTRACT_REQUEST_154.md`).
4. کلیدها را زیر `pages.system.<slug>` به fa/en اضافه کن (read-modify-write).
5. `pnpm -C apps/web type-check` → بدون خطا.
6. state را به‌روزرسانی کن و خارج شو.

## معیار پذیرش
- `type-check` سبز · صفر دادهٔ ساختگی · کلید عنوان در fa/en.

## در قطعی شبکه/خطا
- `blocked` را در state ثبت کن و خارج شو؛ اجرای بعدی ادامه می‌دهد.

## گزارش هر اجرا (۳ خط)
مسیر · وضعیت · نتیجهٔ type-check
