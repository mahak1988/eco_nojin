# Decision Freeze معماری Frontend

**تاریخ:** ۲۵ سپتامبر ۲۰۲۶
**وضعیت:** Wave 0 Research Gate
**دامنه:** `apps/web`، `packages/*`، CI/CD و قرارداد API
**مبنای تصمیم:** منابع رسمی W3C، OWASP، Next.js، Playwright، Unicode/ICU، Google Lighthouse، Serwist، Orval و next-intl

---

## ۱. نتیجه اجرایی

Wave 0 برای تثبیت baseline، بهداشت Git، اصلاح workflowهای stale و ثبت معماری مجاز است.

موارد زیر بدون ثبت ADR و عبور از gateهای وابسته مسدود هستند:

- Service Worker روی داده‌های authenticated یا مالی
- Offline payment، escrow، order و admin
- nonce سراسری CSP روی همه routeها
- نگهداری هم‌زمان دو OpenAPI schema
- endpoint جدید بدون `response_model` و typed error
- fallback خودکار و پنهان چندلایه
- ادعای WCAG AA فقط بر اساس axe
- ادعای INP فقط بر اساس Lighthouse lab
- بازسازی بزرگ Hydroma، Admin و Research پیش از تثبیت API، auth وDesign System

---

## ۲. ماتریس تصمیم

| حوزه | تصمیم قطعی | وضعیت | معیار عبور |
|---|---|---|---|
| CSP و Security Headers | هدر پایه برای همه routeها؛ CSP سخت با nonce فقط برای routeهای dynamic و BFF حساس | Adopt | report-only روی production build، سپس enforce؛ صفر CSP violation در login/cart/checkout |
| BFF و Session | Route Handlerهای Next روی same-origin؛ session فقط در cookie `HttpOnly`؛ بدون token در browser storage | Adopt | تست کامل login→session→cart→checkout→logout؛ rotation، fixation و Origin/CSRF تست شود |
| PWA | Serwist برای app-shell و GET عمومی؛ Dexie برای draft/outbox | Conditional | پس از Wave 1؛ cache هیچ API یا داده خصوصی ممنوع |
| WCAG و RTL | WCAG 2.2 AA؛ تست fa/ar/ur؛ reflow 320px؛ target داخلی 44px | Adopt | صفر axe violation در routeهای نماینده و stateهای اصلی |
| i18n | canonical=en؛ localeهای رسمی 14؛ ICU و Intl؛ parity در CI | Adopt با انتقال تدریجی | حذف hard-code و fallback پنهان؛ هر کلید جدید در هر 14 کاتالوگ |
| OpenAPI و Orval | یک schema canonical؛ validation و clean فعال؛ response_model الزامی | Adopt | `generate:api && git diff --exit-code` و contract test سبز |
| CI و CWV | gateهای مستقل؛ E2E روی production build؛ LCP/CLS در LHCI و INP در RUM | Adopt | branch protection و artifact coverage؛ Playwright با `next start` |

---

## ۳. تصمیم‌های تفصیلی

## ۳.۱ CSP و Security Headers

### سیاست

- هدرهای پایه در `apps/web/next.config.ts`:
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy` حداقلی و per-route
  - `Cross-Origin-Opener-Policy: same-origin`
  - `Cross-Origin-Resource-Policy: same-site`
  - HSTS در edge/production
- CSP پایه:
  - `default-src 'self'`
  - `object-src 'none'`
  - `base-uri 'self'`
  - `form-action 'self'`
  - `frame-ancestors 'none'`
  - `connect-src 'self'`
  - `worker-src 'self' blob:`
  - `manifest-src 'self'`
- nonce و `strict-dynamic` فقط برای auth، account، checkout، admin و BFF.
- rollout نخست با `Content-Security-Policy-Report-Only` روی production build است.

### ممنوع

- `unsafe-inline` و `unsafe-eval` در production
- nonce سراسری که ISR/CDN را نابود کند
- SRI به‌عنوان راهکار production در Next 15.5
- اتکا به `X-Frame-Options` بدون `frame-ancestors`

---

## ۳.۲ BFF و Session

- BFF با Route Handlerهای Next و prefix `/api/*` پیاده می‌شود.
- cookie نشست:
  - نام: `__Host-eco_session`
  - `HttpOnly`
  - `Secure`
  - `SameSite=Lax`
  - `Path=/`
  - بدون `Domain`
- session فقط server-side نگهداری می‌شود.
- login و تغییر نقش باید session را rotate کنند.
- logout باید session و داده محلی حساس را پاک کند.
- mutationها باید Origin و `Sec-Fetch-Site` را بررسی کنند.
- هیچ state change با GET انجام نشود.
- RBAC در DAL یا handler نزدیک داده enforce شود؛ middleware به‌تنهایی کافی نیست.
- `credentials: 'include'` فقط برای same-origin.

### ممنوع

- token در `localStorage` یا `sessionStorage`
- `Authorization: Bearer` از مرورگر
- `SameSite=None`
- `Domain=.eco-nojin...`
- CORS باز همراه credentials

---

## ۳.۳ PWA و Local-first

- Serwist انتخاب رسمی Wave 4 است.
- `next-pwa` و Workbox wiring دستی برای Next رد شدند.
- precache فقط app-shell و assetهای public.
- `NetworkFirst` فقط برای GET عمومی.
- `StaleWhileRevalidate` فقط برای asset ایستا.
- Dexie فقط برای draft و outbox.
- `persistQueryClient` فقط برای queryهای عمومی، با `buildHash` و `maxAge`.
- payment، escrow، order و admin همیشه online هستند.

### ممنوع

- cache کردن `/api/*`
- cache پاسخ‌های `Set-Cookie`، private یا `no-store`
- cache یا IndexedDB برای secret/PII
- Yjs/Lamport برای ledger مالی
- Service Worker پیش از تثبیت BFF و session

---

## ۳.۴ WCAG 2.2 AA و RTL

- هدف انطباق: WCAG 2.2 AA.
- axe tags:
  - `wcag2a`
  - `wcag2aa`
  - `wcag21a`
  - `wcag21aa`
  - `wcag22aa`
- فیلتر critical-only حذف می‌شود.
- Playwright جدا برای `fa`، `ar` و `ur`.
- reflow در 320×256.
- تست keyboard، focus، skip-link، zoom 200٪ و reduced motion.
- CSS فقط منطقی: `ms`, `me`, `ps`, `pe`, `start`, `end`, `text-start`, `text-end`.
- اعداد و bidi با `dir="ltr"` یا `<bdi>` ایزوله شوند.
- target داخلی لمسی: 44×44.

---

## ۳.۵ i18n

- localeهای رسمی:
  - `fa`, `en`, `ar`, `ur`, `de`, `es`, `fr`, `hi`, `it`, `ms`, `pt`, `ru`, `zh`, `bn`
- prefix همیشه اجباری است.
- `fa`, `ar`, `ur` RTL هستند.
- canonical catalog: `messages/en.json`
- fallback اصلی: locale درخواستی → en
- fallback خودکار به fa فقط در دوره انتقال و با config صریح مجاز است؛ پس از تکمیل parity باید حذف شود.
- ICU MessageFormat برای plural/select با شاخه `other`.
- `Intl.NumberFormat` و `Intl.DateTimeFormat` با locale و timeZone صحیح.
- هیچ متن قابل مشاهده نباید hard-code شود.
- key جدید بدون parity در هر 14 کاتالوگ مجاز نیست.
- ترجمه ماشینی باید برچسب کیفیت داشته باشد.

### اقدام Wave 2

- حذف `deepMerge(fa, en, over)` و `noStore()` پس از مهاجرت namespaceها.
- افزودن fallback موقت fa فقط با config صریح و گزارش fallback.
- حذف duplicateهای `messages/*.json` در ریشه.

---

## ۳.۶ OpenAPI و Orval

- `openapi.json` منبع canonical است.
- `openapi_schema.json` حذف یا کاملاً generated می‌شود.
- `validate: true`
- `clean: true`
- client: `react-query`
- query version: 5
- هر endpoint جدید به `response_model`، status code و typed error envelope نیاز دارد.
- BFF خروجی backend را به DTO پایدار نگاشت می‌کند.
- endpoint غیرفعال frontend نباید صرفاً با DTO mock حفظ شود.
- CI باید generate و سپس drift check اجرا کند.
- Node runtime باید با نسخه Orval انتخاب‌شده هماهنگ شود.

---

## ۳.۷ CI و Core Web Vitals

Required checks:

1. Biome check بدون write
2. TypeScript type-check
3. Unit test + coverage threshold 80٪
4. i18n parity
5. Orval drift
6. Next production build
7. Playwright روی production start
8. Lighthouse CI
9. security scan

Performance gates:

- LCP ≤ 2500ms
- CLS ≤ 0.1
- INP ≤ 200ms در RUM
- initial JS ≤ 200KB gzip
- TBT می‌تواند guard آزمایشگاهی باشد، اما جایگزین INP نیست.
- LHCI با چند اجرا و median اجرا می‌شود.

---

## ۴. وضعیت Waves

| Wave | وضعیت | شرط شروع |
|---|---|---|
| Wave 0 | مجاز | در حال اجرا |
| Wave 1: API/BFF/Auth | مجاز | تکمیل Decision Freeze و baseline |
| Wave 2: tokens/i18n/a11y | مجاز | تثبیت canonical schema و test baseline |
| Wave 3: Hydroma/Admin/Research | مشروط | عبور Wave 1 و Wave 2 |
| Wave 4: PWA | مشروط | عبور کامل Wave 1 |
| Wave 5: security/observability/performance | مجاز | rollout report-only برای CSP |
| Wave 6: deployment | مشروط | وجود health/ready و frontend image |
| Wave 7: mobile/docs | مجاز | تثبیت frontend baseline |

---

## ۵. منابع رسمی

همه منابع در ۲۵ سپتامبر ۲۰۲۶ بررسی شده‌اند:

- Next.js CSP: https://nextjs.org/docs/15/app/guides/content-security-policy
- Next.js Headers: https://nextjs.org/docs/15/app/api-reference/config/next-config-js/headers
- Next.js Authentication: https://nextjs.org/docs/15/app/guides/authentication
- OWASP Session Management: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP CSRF: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP HTTP Headers: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
- OWASP CSP: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Playwright Accessibility: https://playwright.dev/docs/accessibility-testing
- W3C RTL scripts: https://www.w3.org/International/questions/qa-scripts/
- ICU MessageFormat: https://unicode-org.github.io/icu/userguide/format_parse/messages/
- Unicode CLDR plural rules: http://cldr.unicode.org/index/cldr-spec/plural-rules
- next-intl middleware: https://next-intl.dev/docs/routing/middleware
- next-intl configuration: https://next-intl.dev/docs/usage/configuration
- Serwist: https://github.com/serwist/serwist
- Workbox: https://registry.npmjs.org/workbox-build/latest
- next-pwa: https://registry.npmjs.org/next-pwa/latest
- TanStack persistQueryClient: https://tanstack.com/query/latest/docs/framework/react/plugins/persistQueryClient
- Orval: https://github.com/orval-labs/orval
- Google Web Vitals: https://github.com/GoogleChrome/web-vitals
- Lighthouse CI: https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md
- Biome CI: https://biomejs.dev/guides/ci/
- IETF OAuth Browser-Based Apps: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps

---

## ۶. اقدامات فوری ثبت‌شده

- حذف `apps/web/.next-phase1check` از tracked build artifacts
- ignore کردن `**/.next-*` و `.lighthouseci/`
- افزودن `format:check` و `quality`
- انتقال Dependabot به `/apps/web`
- اصلاح lockfile cache path
- اصلاح workflow قدیمی i18n
- همگام‌سازی pre-commit با Biome 2.5.14
- افزودن LHCI config
- افزودن public env example بدون secret
- گسترش Playwright i18n به ۱۴ locale
- اجرای production server در Playwright CI

این تصمیم‌ها پس از پیاده‌سازی هر Wave باید در `docs/adr/` حفظ و نسخه‌بندی شوند.

---

## ۷. نتیجه اجرای Wave 0

### ۷.۱ تغییرات تکمیل‌شده

- build کهنه `apps/web/.next-phase1check` از Git حذف شد.
- `**/.next-*` و `.lighthouseci/` به `.gitignore` اضافه شدند.
- scriptهای `format:check` و `quality` به root و `apps/web` اضافه شدند.
- Dependabot به `/apps/web` منتقل شد.
- lockfile cache در workflow به `pnpm-lock.yaml` ریشه منتقل شد.
- workflow قدیمی i18n به `apps/web`، ۱۴ locale و production Playwright منتقل شد.
- pre-commit با Biome `2.5.14` و بدون `--write` همگام شد.
- LHCI config و public env example جدید اضافه شدند.
- Playwright اکنون production build را روی پورت ۳۰۰۱ اجرا می‌کند.
- تست i18n از ۸ به ۱۴ locale گسترش یافت و locator واقعی LanguageMenu را استفاده می‌کند.
- `orval.config.ts` به `openapi.json` canonical تغییر کرد و validation فعال شد.
- API client از schema جدید بازتولید و wrapper دستی با نام‌های canonical هماهنگ شد.
- `science.modelsPublicNote` به کاتالوگ‌های فارسی و انگلیسی اضافه شد.
- ارجاع dependency نامعتبر `cpp-build` از graph داخل `ci-cd.yml` حذف شد.
- jobهای placeholder استقرار staging/production تا تثبیت quality gate غیرفعال شدند.
- E2E اکنون build artifact واقعی را مصرف می‌کند و build تکراری نمی‌سازد.
- Orval drift check به CI اضافه شد.

### ۷.۲ اعتبارسنجی اجراشده

| اعتبارسنجی | نتیجه |
|---|---|
| `pnpm -C apps/web quality` | موفق |
| Biome check برای فایل‌های تغییریافته | موفق |
| TypeScript type-check | موفق |
| Vitest | ۱۳ فایل و ۵۳ تست موفق |
| i18n parity | هر ۱۴ locale موفق |
| Next production build | موفق؛ ۱۷۷ مسیر page و shared JS حدود ۱۰۳KB |
| Playwright i18n روی production build | ۱۹ تست موفق |
| Playwright a11y فعلی | ۱۱ تست موفق؛ فعلاً critical-only |
| YAML syntax | ۵ workflow/config موفق |
| JSON syntax | package و LHCI موفق |
| Orval determinism | hash قبل و بعد generation یکسان |
| scoped `git diff --check` | موفق؛ فقط هشدار line ending |
| build کامل E2E | build قبلی Chromium نصب نبود؛ تست با Edge و production build موفق شد |

### ۷.۳ محدودیت‌ها و کارهای باقی‌مانده

- `clean: true` در Orval هنوز فعال نیست؛ خروجی و فایل‌های دستی در یک پوشه قرار دارند و فعال‌کردن آن manual sourceها را حذف کرد. ابتدا باید generated output به پوشه مستقل منتقل شود.
- build یک warning مربوط به `metadataBase` برای static social image دارد.
- `docs/` همچنان deleted است و باید تعیین تکلیف شود.
- remote فقط GitHub است؛ GitLab یا remote دوم وجود ندارد.
- branch واقعی remote فقط `main` و `security` است؛ branch `develop` مستندشده وجود ندارد.
- GitHub Releases، Environments و Rulesets عمومی خالی هستند.
- آخرین runهای frontend، C++ و security روی HEAD شکست خورده‌اند.
- workflow `cpp-build.yml` هنوز publish به PyPI را از push روی `main` آغاز می‌کند و باید به semver tag محدود شود.
- image namespace میان `ghcr.io/mahak1988/eco_nojin` و Helm فعلی ناسازگار است.
- release به tag immutable، digest promotion، attestation و reviewer انسانی هنوز پیاده‌سازی نشده است.
- Wave 1 باید پیش از PWA یا بازسازی بزرگ، env/BFF/session و قراردادهای مالی را اصلاح کند.
