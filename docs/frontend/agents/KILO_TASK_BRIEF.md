# بریف وظیفه برای Kilo Code

**هدف:** اجرای دقیق گیت‌های تأییدشدهٔ پروژه و ثبت یک checkpoint امن — بدون هیچ تغییری در کد محصول.

## یک خط که به Kilo بدهید

```
مهارت verify-and-checkpoint را از .kilo/skills/verify-and-checkpoint/SKILL.md اجرا کن
و نتیجه را دقیقاً در قالب «Report format» همان فایل برگردان.
```

## اگر Kilo مهارت‌ها را نمی‌خواند، همین را بدهید

```
در D:\eco_nojin دقیقاً این مراحل را به ترتیب اجرا کن و اعداد خام را گزارش بده:
۱) git status --short | Measure-Object -Line   و   git log -1 --oneline
۲) node scripts/check-api-contract.mjs
۳) node scripts/check-locale-depth.mjs
۴) pnpm -C apps/web type-check
۵) pnpm -C apps/web build
۶) فقط اگر در ۴۵ ثانیهٔ گذشته هیچ فایلی نوشته نشده بود:
   git checkout -b checkpoint/verified-<timestamp> && git add -A && git commit -m "checkpoint: verified state (build+tests green)"
   اگر نویسندهٔ فعالی بود، متوقف شو و فایل‌ها را گزارش بده.
۷) (اختیاری) CI=1 npx playwright test tests/cover.spec.ts tests/home.spec.ts tests/market.spec.ts tests/security.spec.ts tests/i18n.spec.ts --project=chromium --reporter=line
```

## مرزهای سخت (در همان مهارت هم قید شده)

1. هیچ دادهٔ ساختگی — نبود داده = حالت خالی صادقانه.
2. سرور dev دستی روی ۳۰۰۰/۳۰۰۱ بالا نیاور (Playwright خودش سرور می‌سازد).
3. به `apps/web/messages/*`، `apps/web/src/lib/domains/**` و `apps/web/src/lib/config/**` دست نزن، مگر وظیفه صریحاً بگوید.
4. تا وقتی نویسندهٔ دیگری فعال است، **کامیت نکن**.

## مقادیر مورد انتظار (وضعیت اندازه‌گیری‌شدهٔ ۲۰۲۶/۰۹/۲۹)

| گیت | مقدار درست |
|---|---|
| قرارداد | `missing: 1` · `declared content: 30` |
| i18n | `locale depth OK` · کلید غیرقابل‌دسترس = ۰ |
| type-check | exit 0 |
| build | `Compiled successfully` · exit 0 |
| E2E smoke | همه پاس (۳۸ تست در ۶ اسپک) |
