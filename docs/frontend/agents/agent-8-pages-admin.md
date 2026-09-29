# عامل ۸ — تکمیل صفحات ادمین

> اجرای ریز: هر بار فقط **یک صفحه**.

## هدف
بستن شکاف صفحات `admin` (ربات‌ها، محتوا، خطاها، مدل‌ها، امنیت، کاربران). صف:
```
node scripts/agents/list-planned.mjs admin
```

## محدودهٔ مجاز (فقط این‌ها)
- `apps/web/src/app/[locale]/admin/**`
- `apps/web/messages/fa.json` و `en.json` — فقط افزودن کلید زیر فضانام `pages.admin.*`
- `docs/frontend/agents/state/agent-8.json`

## ممنوع
- ۱۲ زبان دیگر `messages/` · `lib/domains/**` · `lib/api/**` · `public/**` · `system/**` · `market/**` · `research/**` · `.github/**` · `pnpm install` · سرور روی پورت‌های dev · **دادهٔ ساختگی**

## الگوریتم هر اجرا (یک صفحه)
1. صف را بگیر؛ خالی بود → `done: true` و خروج.
2. اگر صفحه نیازمند نقش/دسترسی است، همان الگوی محافظ موجود در `admin/layout.tsx` و `lib/auth/require-role.ts` را استفاده کن (هیچ محافظ تازه‌ای از خودت نساز).
3. صفحه را بساز:
   - `endpoint دارد` → bind واقعی + حالت‌های `loading/empty/error` + `Idempotency-Key` برای متدهای نوشتنی.
   - `endpoint ندارد` → حالت خالی صادقانه + یادداشت «منتظر قرارداد».
4. کلیدها را زیر `pages.admin.<slug>` به fa/en اضافه کن (read-modify-write).
5. `pnpm -C apps/web type-check` → بدون خطا.
6. state را به‌روزرسانی کن و خارج شو.

## معیار پذیرش
- `type-check` سبز · صفر دادهٔ ساختگی · محافظ نقش بدون تغییر باقی مانده · کلید عنوان fa/en.

## در قطعی شبکه/خطا
- `blocked` را ثبت و خارج شو.

## گزارش هر اجرا (۳ خط)
مسیر · وضعیت · نتیجهٔ type-check
