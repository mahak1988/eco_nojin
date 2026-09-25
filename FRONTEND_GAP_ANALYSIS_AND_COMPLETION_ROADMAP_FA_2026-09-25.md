# گزارش جامع ممیزی فرانت‌اند، شکاف‌ها و نقشه راه تکمیل پروژه

**تاریخ ممیزی:** ۲۵ سپتامبر ۲۰۲۶
**مخزن:** `D:\eco_nojin`
**شاخه:** `main`
**HEAD:** `5f9aa44`
**رابط فعوب:** `apps/web`
**زبان گزارش:** فارسی

---

## فهرست مطالب

1. [دامنه و روش ممیزی](#۱-دامنه-و-روش-ممیزی)
2. [وضعیت اجرایی و اعتبار اسناد](#۲-وضعیت-اجرایی-و-اعتبار-اسناد)
3. [وضعیت موجود فرانت‌اند](#۳-وضعیت-موجود-فرانتاند)
4. [فهرست دقیق صفحات موجود](#۴-فهرست-دقیق-صفحات-موجود)
5. [فایل‌های تولیدشده و Build Artifactها](#۵-فایلهای-تولیدشده-و-build-artifactها)
6. [تحلیل شکاف‌ها](#۶-تحلیل-شکافها)
7. [ناسازگاری مستندات](#۷-ناسازگاری-مستندات)
8. [نقشه راه تکمیل پروژه](#۸-نقشه-راه-تکمیل-پروژه)
9. [Definition of Done نهایی](#۹-definition-of-done-نهایی)

---

# ۱. دامنه و روش ممیزی

این گزارش حاصل تحلیل ایستای موارد زیر است:

- کل فایل‌های frontend در `apps/web`
- بسته‌های مشترک `packages/*`
- فایل‌های جانبی `mobile`
- مستندات معماری، توسعه، طراحی و فازبندی
- فایل‌های تولیدشده OpenAPI و API Client
- build، cache و گزارش‌های تست
- workflowهای CI/CD و فایل‌های استقرار
- قراردادهای frontend با backend موجود

روش بررسی شامل موارد زیر بوده است:

- شمارش و طبقه‌بندی فایل‌های route
- خواندن تنظیمات package، Next.js، TypeScript، Tailwind، Vitest و Playwright
- تطبیق routeهای واقعی با route manifest و مستندات
- بررسی i18n، RTL، دسترس‌پذیری و Design System
- بررسی Auth، session، guard و جریان‌های مالی
- تطبیق endpointهای frontend با routerهای backend
- بررسی PWA، service worker، IndexedDB و sync
- بررسی فایل‌های generated و stale
- بررسی deployment و health probeها

در این ممیزی build، test، lint یا type-check مجدداً اجرا نشده است. بنابراین وضعیت runtime و سبز بودن commandها باید در مرحله بعد با اجرای واقعی تأیید شود.

---

# ۲. وضعیت اجرایی و اعتبار اسناد

## ۲.۱ سلسله‌مراتب اعتبارسناد

1. `hydroma-nojin-master-plan.md:3-7` — نسخه ۲.۱ و مرجع معماری و استاندارد نهایی.
2. `DESIGN_SYSTEM_ART_AND_VISUALS_2026.md:6` — مرجع رسمی بصری، حرکت و دسترس‌پذیری.
3. `FRONTEND_AGENT_ROADMAP.md:52-120` — فازهای اجرایی و معیار پذیرش.
4. `FRONTEND_ALIGNMENT_GAP_ANALYSIS.md:4-6` — مرجع رسمی مقایسه سند و کد.
5. `AGENTS.md` و `CLAUDE.md` — الزامات رویه‌ای و کیفیت.
6. طرح‌های `.kilo/plans/*` — پیشنهادی و منتظر تأیید، نه استاندارد نهایی.

## ۲.۲ وضعیت Git

working tree بسیار dirty است:

- تعداد زیادی فایل frontend_modified وجود دارد.
- فایل‌های مهم جدید untracked هستند.
- تمام پوشه `docs/` deleted است.
- سه سند مرجع اصلی در ریشه untracked هستند:
  - `DESIGN_SYSTEM_ART_AND_VISUALS_2026.md`
  - `FRONTEND_AGENT_ROADMAP.md`
  - `FRONTEND_ALIGNMENT_GAP_ANALYSIS.md`

بنابراین نتایج این گزارش، وضعیت فعلی working tree را توصیف می‌کند و یک snapshot قابل بازتولید از HEAD نیست.

## ۲.۳ خلاصه سازگاری حوزه‌ها

| حوزه | وضعیت | نتیجه |
|---|---|---|
| Next.js/React/TypeScript | موجود و نسبتاً منطبق | پشته اصلی با سند اصلی سازگار است، اما تغییرات commit نشده‌اند. |
| Tailwind 4 و CSS مدرن | موجود و نسبتاً منطبق | `oklch`، font-face، motion و ابزارهای RTL پیاده‌سازی شده‌اند. |
| i18n چهاردوزبانه | ناقص | ۱۴ locale وجود دارد، اما hard-code، fallback پنهان و عدم تقارن ترجمه باقی است. |
| Design System | ناقص | بخشی از توکن‌ها و حرکت پیاده‌سازی شده، ولی چند مؤلفه و قالب اصلی غایب است. |
| صفحات عمومی | ناقص | تعداد زیادی صفحه وجود دارد، اما بسیاری نمونه، قدیمی یا متصل به API غیرفعال هستند. |
| بازارگاه | ناقص | ۷۲ صفحه فیزیکی؛ بخشی scaffold/mock و بخشی از قرارداد backend ناسازگار است. |
| Hydroma tools | ناقص | فقط صفحات `hydroma` و `scientific-models`؛ ساختار ۱۷۴ صفحه‌ای وجود ندارد. |
| Admin | غایب | مسیر و middleware ادمین وجود ندارد. |
| Research | غایب | مسیر پژوهش و DOI/preprint وجود ندارد. |
| Auth/Session | غایب | login، session، guard و cookie forwarding وجود ندارد. |
| PWA واقعی | غایب | فقط manifest؛ service worker، cache، IndexedDB و sync وجود ندارند. |
| تست | ناقص | ۱۴ تست unit/component و ۸ تست E2E موجود است، اما coverage و fixture قطعی وجود ندارد. |
| CI/CD | ناقص | workflow وجود دارد، اما بخشی از مسیرها و artifactهای آن stale یا مفقود است. |
| Deploy فرانت | ناقص | image، Dockerfile و manifestهای پایه Kubernetes کامل نیستند. |
| Observability | غایب | Sentry، OpenTelemetry، Web Vitals و telemetry سراسری وجود ندارند. |
| Mobile | ناقص | importها و dependencyهای `mobile` ناسازگار هستند. |

---

# ۳. وضعیت موجود فرانت‌اند

## ۳.۱ فناوری و پیکربندی فعال

پیاده‌سازی فعال از این فناوری‌ها استفاده می‌کند:

- Next.js 15 App Router
- React 19
- TypeScript 5.9 strict
- Tailwind CSS 4
- next-intl
- TanStack Query
- React Hook Form
- Zod 4
- MapLibre
- Orval
- Vitest
- Playwright
- Biome
- pnpm workspace
- Turborepo

## ۳.۲ فایل‌های پایه و پیکربندی ریشه

```text
package.json
pnpm-workspace.yaml
pnpm-lock.yaml
biome.json
orval.config.ts
turbo.json
.pre-commit-config.yaml
openapi.json
openapi_schema.json
mkdocs.yml
```

## ۳.۳ فایل‌های پیکربندی وب

```text
apps/web/package.json
apps/web/next.config.ts
apps/web/tsconfig.json
apps/web/tailwind.config.ts
apps/web/postcss.config.mjs
apps/web/vitest.config.ts
apps/web/playwright.config.ts
apps/web/next-env.d.ts
apps/web/src/middleware.ts
apps/web/scripts/i18n-check.mjs
apps/web/src/app/globals.css
apps/web/tokens/dtcg.json
apps/web/tokens/variables.css
apps/web/src/app/robots.ts
apps/web/src/app/sitemap.ts
apps/web/src/app/manifest.ts
apps/web/src/app/manifest.test.ts
```

نکات مهم:

- `apps/web/package.json:6-17` اسکریپت‌های `dev`، `build`، `start`، `type-check`، `generate:api`، `lint`، `format`، `test`، `test:e2e` و `i18n:compile` را دارد.
- اسکریپت `test:coverage` در نسخه فعلی package وجود ندارد.
- `apps/web/tsconfig.json:8-11` حالت strict را فعال می‌کند.
- `apps/web/next.config.ts:7-13` rewrite را از `API_PROXY_TARGET` می‌خواند.
- `apps/web/next.config.ts:21-29` چند security header پایه دارد.
- `apps/web/vitest.config.ts:7-11` فقط `src/**/*.test.{ts,tsx}` را اجرا می‌کند و threshold یا coverage provider ندارد.
- `apps/web/playwright.config.ts:19-40` پنج project دارد: Chromium، Firefox، WebKit، Mobile Chrome و Mobile Safari.
- Playwright فعلاً projectهای جداگانه RTL برای `fa`، `ar` و `ur` ندارد.
- `apps/web/src/app/manifest.ts` و تست آن در Git untracked هستند.

## ۳.۴ زیرساخت i18n

```text
apps/web/src/i18n/routing.ts
apps/web/src/i18n/request.ts
apps/web/src/i18n/navigation.ts
apps/web/src/i18n/routing.test.ts
apps/web/src/i18n/messages.test.ts
apps/web/src/lib/i18n/messages.ts
apps/web/scripts/i18n-check.mjs
apps/web/src/middleware.ts
```

کاتالوگ‌های رسمی موجود:

```text
apps/web/messages/fa.json
apps/web/messages/en.json
apps/web/messages/ar.json
apps/web/messages/ur.json
apps/web/messages/de.json
apps/web/messages/es.json
apps/web/messages/fr.json
apps/web/messages/hi.json
apps/web/messages/it.json
apps/web/messages/ms.json
apps/web/messages/pt.json
apps/web/messages/ru.json
apps/web/messages/zh.json
apps/web/messages/bn.json
```

کاتالوگ‌های legacy/duplicate در ریشه:

```text
messages/fa.json
messages/en.json
messages/ar.json
messages/ur.json
messages/de.json
messages/es.json
messages/fr.json
messages/hi.json
messages/it.json
messages/ms.json
messages/pt.json
messages/ru.json
messages/zh.json
messages/bn.json
```

موجود:

- locale prefix اجباری
- default locale برابر فارسی
- fallback و merge کاتالوگ
- تعریف `fa`، `ar` و `ur` به‌عنوان RTL
- locale switcher
- `lang/dir` پویا

ناقص:

- ترجمه‌های سخت‌کدشده در صفحات
- fallback پنهان در برخی localeها
- عدم تقارن واقعی همه کاتالوگ‌ها
- نبود تست per-locale
- استفاده ناقص از ICU و `Intl`

## ۳.۵ Design System و توکن‌ها

```text
apps/web/tokens/dtcg.json
apps/web/tokens/variables.css
apps/web/src/app/globals.css
```

موارد پیاده‌سازی‌شده:

- پالت `oklch`
- تم روشن/تیره
- پالت نمودار
- فونت‌های محلی
- شبکه فاصله
- motion زمان‌دار
- `prefers-reduced-motion`
- ابزارهای منطقی RTL
- contour و scroll timeline
- ProvenanceStamp
- صفحه نمونه `/[locale]/design-system`

## ۳.۶ مؤلفه‌های داخلی UI

```text
apps/web/src/components/ui/Button.tsx
apps/web/src/components/ui/Card.tsx
apps/web/src/components/ui/CommandPalette.tsx
apps/web/src/components/ui/Dialog.tsx
apps/web/src/components/ui/ErrorBoundary.tsx
apps/web/src/components/ui/Input.tsx
apps/web/src/components/ui/OfflineBanner.tsx
apps/web/src/components/ui/Select.tsx
apps/web/src/components/ui/Skeleton.tsx
apps/web/src/components/ui/Stat.tsx
apps/web/src/components/ui/Switch.tsx
apps/web/src/components/ui/Textarea.tsx
apps/web/src/components/ui/Toast.tsx
```

## ۳.۷ مؤلفه‌های سطح صفحه

```text
apps/web/src/components/BazaarEstablishmentWizard.tsx
apps/web/src/components/BazaarSteps.tsx
apps/web/src/components/CoverPageClient.tsx
apps/web/src/components/EmptyState.tsx
apps/web/src/components/FivePart.tsx
apps/web/src/components/LanguageMenu.tsx
apps/web/src/components/ListBlock.tsx
apps/web/src/components/LocaleSwitcher.tsx
apps/web/src/components/MarketMap.tsx
apps/web/src/components/OwnerFooter.tsx
apps/web/src/components/ProvenanceStamp.tsx
apps/web/src/components/Providers.tsx
apps/web/src/components/SiteFooter.tsx
apps/web/src/components/SiteNav.tsx
apps/web/src/components/StatusDot.tsx
apps/web/src/components/SustainabilityDashboardPrototype.tsx
apps/web/src/components/SustainabilityPreview.tsx
apps/web/src/components/layout/PublicLayout.tsx
apps/web/src/components/layout/index.ts
```

## ۳.۸ مؤلفه‌های بازار

```text
apps/web/src/components/market/BazaarStepRenderer.tsx
apps/web/src/components/market/MarketplaceTemplatePage.tsx
apps/web/src/components/market/bazaar-wizard/Step1Form.tsx
apps/web/src/components/market/bazaar-wizard/Step2Form.tsx
apps/web/src/components/market/bazaar-wizard/Step3Form.tsx
apps/web/src/components/market/bazaar-wizard/Step4Form.tsx
apps/web/src/components/market/bazaar-wizard/Step5Form.tsx
apps/web/src/components/market/bazaar-wizard/Step6Form.tsx
apps/web/src/components/market/bazaar-wizard/Step7Form.tsx
apps/web/src/components/market/bazaar-wizard/Step8Form.tsx
apps/web/src/components/market/bazaar-wizard/Step9Form.tsx
apps/web/src/components/market/bazaar-wizard/Step10Form.tsx
apps/web/src/components/market/store-wizard/StoreStep1Form.tsx
apps/web/src/components/market/store-wizard/StoreStep2Form.tsx
```

## ۳.۹ بسته مشترک UI

```text
packages/ui/package.json
packages/ui/tsconfig.json
packages/ui/src/index.ts
packages/ui/src/avatar.tsx
packages/ui/src/badge.tsx
packages/ui/src/breadcrumb.tsx
packages/ui/src/button.tsx
packages/ui/src/card.tsx
packages/ui/src/checkbox.tsx
packages/ui/src/cn.ts
packages/ui/src/dialog.tsx
packages/ui/src/dropdown-menu.tsx
packages/ui/src/input.tsx
packages/ui/src/label.tsx
packages/ui/src/pagination.tsx
packages/ui/src/select.tsx
packages/ui/src/switch.tsx
packages/ui/src/table.tsx
packages/ui/src/tabs.tsx
packages/ui/src/textarea.tsx
packages/ui/src/toast.tsx
packages/ui/src/tooltip.tsx
```

## ۳.۱۰ دارایی‌های برند و PWA

```text
apps/web/public/favicon.ico
apps/web/public/brand/platform-logo.webp
apps/web/public/brand/platform-logo.png
apps/web/public/brand/platform-logo-transparent.webp
apps/web/public/brand/platform-logo-transparent.png
apps/web/public/brand/platform-icon.png
apps/web/public/brand/platform-icon-512.png
apps/web/public/brand/platform-icon-32.png
apps/web/public/brand/platform-icon-192.png
apps/web/public/brand/platform-icon-180.png
apps/web/public/brand/owner-narvan-logo.png
apps/web/public/brand/owner-narvan-logo-transparent.png
apps/web/src/app/icon.png
apps/web/src/app/apple-icon.png
apps/web/src/app/opengraph-image.png
```

فونت‌های محلی موجود:

```text
apps/web/public/fonts/vazirmatn-latin-ext-800-normal-BzH3Tiwu.woff2
apps/web/public/fonts/vazirmatn-latin-ext-700-normal-BfoXmNMx.woff2
apps/web/public/fonts/vazirmatn-latin-ext-500-normal-CgxvvVrG.woff2
apps/web/public/fonts/vazirmatn-latin-ext-400-normal-BdGhO0lm.woff2
apps/web/public/fonts/vazirmatn-latin-800-normal-e0EQwLmk.woff2
apps/web/public/fonts/vazirmatn-latin-700-normal-9BlbvDRV.woff2
apps/web/public/fonts/vazirmatn-latin-500-normal-6zZzgpg4.woff2
apps/web/public/fonts/vazirmatn-latin-400-normal-BT_DHTc7.woff2
apps/web/public/fonts/vazirmatn-arabic-800-normal-Bwnt96zj.woff2
apps/web/public/fonts/vazirmatn-arabic-700-normal-Dge_DOjm.woff2
apps/web/public/fonts/vazirmatn-arabic-500-normal-C_lbnnKa.woff2
apps/web/public/fonts/vazirmatn-arabic-400-normal-DMZFCm7K.woff2
apps/web/public/fonts/markazi-text-latin-ext-600-normal-qy7x9MPE.woff2
apps/web/public/fonts/markazi-text-latin-ext-400-normal-JAGQHsuk.woff2
apps/web/public/fonts/markazi-text-latin-600-normal-Ck2duw3u.woff2
apps/web/public/fonts/markazi-text-latin-400-normal-ShOarP0H.woff2
apps/web/public/fonts/markazi-text-arabic-600-normal-BvUjLBiD.woff2
apps/web/public/fonts/markazi-text-arabic-400-normal-Cn7gGLcu.woff2
apps/web/public/fonts/jetbrains-mono-latin-ext-600-normal-BfB_LPfz.woff2
apps/web/public/fonts/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2
apps/web/public/fonts/jetbrains-mono-latin-600-normal-C8RAYTDA.woff2
apps/web/public/fonts/jetbrains-mono-latin-400-normal-V6pRDFza.woff2
```

## ۳.۱۱ API، type و validation

```text
apps/web/src/lib/api/client.ts
apps/web/src/lib/api/client.test.ts
apps/web/src/lib/api/typed-client.ts
apps/web/src/lib/api/hooks.ts
apps/web/src/lib/api/market.ts
apps/web/src/lib/api/cart.ts
apps/web/src/lib/api/escrow.ts
apps/web/src/lib/api/escrow.test.ts
apps/web/src/lib/api/public.ts
apps/web/src/lib/route-manifest.ts
apps/web/src/lib/route-manifest.test.ts
apps/web/src/lib/marketplace-routes.ts
apps/web/src/lib/marketplace-routes.test.ts
apps/web/src/lib/query-client.ts
apps/web/src/lib/utils.ts
apps/web/src/lib/validation/bazaar-establishment.ts
apps/web/src/lib/validation/store-creation.ts
apps/web/src/types/bazaar-types.ts
apps/web/src/types/data-envelope.ts
apps/web/src/types/data-envelope.test.ts
apps/web/src/types/escrow.ts
apps/web/src/types/escrow.test.ts
apps/web/src/types/maplibre-stub.d.ts
apps/web/src/types/market.ts
```

بسته‌های مشترک:

```text
packages/api-client/package.json
packages/api-client/tsconfig.json
packages/api-client/src/index.ts
packages/api-client/src/generated.ts
packages/api-client/src/mutator.ts
packages/api-client/src/global.d.ts
packages/api-client/src/types/bazaar.ts

packages/types/package.json
packages/types/tsconfig.json
packages/types/src/index.ts
packages/types/src/market.ts
packages/types/src/public.ts
packages/types/src/schemas.ts

packages/config/package.json
packages/config/tsconfig/base.json
```

پوشه `packages/config/biome/` خالی است، درحالی‌که package export مسیر `biome.json` را معرفی می‌کند.

## ۳.۱۲ فایل‌های تست

### Unit/Component

```text
apps/web/src/app/manifest.test.ts
apps/web/src/content/public-pages.test.ts
apps/web/src/components/ProvenanceStamp.test.tsx
apps/web/src/components/SustainabilityDashboardPrototype.test.tsx
apps/web/src/components/SustainabilityPreview.test.tsx
apps/web/src/i18n/messages.test.ts
apps/web/src/i18n/routing.test.ts
apps/web/src/lib/api/client.test.ts
apps/web/src/lib/api/escrow.test.ts
apps/web/src/lib/marketplace-routes.test.ts
apps/web/src/lib/route-manifest.test.ts
apps/web/src/types/data-envelope.test.ts
apps/web/src/types/escrow.test.ts
```

### E2E/Playwright

```text
apps/web/tests/a11y.spec.ts
apps/web/tests/cover.spec.ts
apps/web/tests/home.spec.ts
apps/web/tests/hydroma.spec.ts
apps/web/tests/i18n.spec.ts
apps/web/tests/market.spec.ts
apps/web/tests/marketplace.spec.ts
apps/web/tests/prototype.spec.ts
```

نقص مهم: چند فایل تست و کامپوننت جدید untracked هستند و بخش بزرگی از صفحات اصلی فاقد تست مستقیم هستند.

---

# ۴. فهرست دقیق صفحات موجود

Snapshot فعلی شامل **۱۷۷ فایل `page.tsx`** است: ۱۷۶ صفحه قابل route و یک مسیر ویژه `_not-found`.

## ۴.۱ مسیرهای مستقیم ـ ۱۹ فایل

```text
apps/web/src/app/[locale]/page.tsx
apps/web/src/app/[locale]/_not-found/page.tsx
apps/web/src/app/[locale]/about/page.tsx
apps/web/src/app/[locale]/accessibility/page.tsx
apps/web/src/app/[locale]/design-system/page.tsx
apps/web/src/app/[locale]/evidence/page.tsx
apps/web/src/app/[locale]/home/page.tsx
apps/web/src/app/[locale]/hydroma/page.tsx
apps/web/src/app/[locale]/learn/page.tsx
apps/web/src/app/[locale]/legal/page.tsx
apps/web/src/app/[locale]/offline/page.tsx
apps/web/src/app/[locale]/platform/page.tsx
apps/web/src/app/[locale]/prototype/page.tsx
apps/web/src/app/[locale]/references/page.tsx
apps/web/src/app/[locale]/scientific-models/page.tsx
apps/web/src/app/[locale]/services/page.tsx
apps/web/src/app/[locale]/statements/page.tsx
apps/web/src/app/[locale]/status/page.tsx
apps/web/src/app/[locale]/validation/page.tsx
```

صفحات `design-system`، `offline`، `prototype`، loading/error/not-found و catch-all بازار در Git untracked هستند.

## ۴.۲ AI ـ ۸ فایل

```text
apps/web/src/app/[locale]/ai/page.tsx
apps/web/src/app/[locale]/ai/agents/page.tsx
apps/web/src/app/[locale]/ai/assistant/page.tsx
apps/web/src/app/[locale]/ai/ethics/page.tsx
apps/web/src/app/[locale]/ai/feedback/page.tsx
apps/web/src/app/[locale]/ai/glossary/page.tsx
apps/web/src/app/[locale]/ai/limits/page.tsx
apps/web/src/app/[locale]/ai/voice/page.tsx
```

## ۴.۳ Developers ـ ۹ فایل

```text
apps/web/src/app/[locale]/developers/page.tsx
apps/web/src/app/[locale]/developers/api/page.tsx
apps/web/src/app/[locale]/developers/changelog/page.tsx
apps/web/src/app/[locale]/developers/cookbooks/page.tsx
apps/web/src/app/[locale]/developers/partners/page.tsx
apps/web/src/app/[locale]/developers/playground/page.tsx
apps/web/src/app/[locale]/developers/sdks/page.tsx
apps/web/src/app/[locale]/developers/status-api/page.tsx
apps/web/src/app/[locale]/developers/webhooks/page.tsx
```

## ۴.۴ Trust ـ ۷ فایل

```text
apps/web/src/app/[locale]/trust/page.tsx
apps/web/src/app/[locale]/trust/audits/page.tsx
apps/web/src/app/[locale]/trust/carbon-registry/page.tsx
apps/web/src/app/[locale]/trust/disclosure/page.tsx
apps/web/src/app/[locale]/trust/provenance/page.tsx
apps/web/src/app/[locale]/trust/report/page.tsx
apps/web/src/app/[locale]/trust/sanctions/page.tsx
```

## ۴.۵ Public ـ ۶۲ فایل

```text
apps/web/src/app/[locale]/public/audiences/cooperatives/page.tsx
apps/web/src/app/[locale]/public/audiences/farmers/page.tsx
apps/web/src/app/[locale]/public/audiences/government/page.tsx
apps/web/src/app/[locale]/public/audiences/investors/page.tsx
apps/web/src/app/[locale]/public/audiences/ngos/page.tsx
apps/web/src/app/[locale]/public/audiences/researchers/page.tsx
apps/web/src/app/[locale]/public/channels/page.tsx
apps/web/src/app/[locale]/public/components/api-playground/page.tsx
apps/web/src/app/[locale]/public/components/dispute-resolution/page.tsx
apps/web/src/app/[locale]/public/components/ecowallet/page.tsx
apps/web/src/app/[locale]/public/components/hydroma-engine/page.tsx
apps/web/src/app/[locale]/public/components/land-profiler/page.tsx
apps/web/src/app/[locale]/public/components/marketplace/page.tsx
apps/web/src/app/[locale]/public/components/mrv-dashboard/page.tsx
apps/web/src/app/[locale]/public/components/satellite-view/page.tsx
apps/web/src/app/[locale]/public/cta/page.tsx
apps/web/src/app/[locale]/public/education/advanced-search/page.tsx
apps/web/src/app/[locale]/public/education/certifications/page.tsx
apps/web/src/app/[locale]/public/education/courses/page.tsx
apps/web/src/app/[locale]/public/education/glossary/page.tsx
apps/web/src/app/[locale]/public/education/library-advanced/page.tsx
apps/web/src/app/[locale]/public/education/library/page.tsx
apps/web/src/app/[locale]/public/education/video-player/page.tsx
apps/web/src/app/[locale]/public/education/workshops/page.tsx
apps/web/src/app/[locale]/public/goals/impact/page.tsx
apps/web/src/app/[locale]/public/goals/manifesto/page.tsx
apps/web/src/app/[locale]/public/goals/mission/page.tsx
apps/web/src/app/[locale]/public/goals/roadmap/page.tsx
apps/web/src/app/[locale]/public/goals/values/page.tsx
apps/web/src/app/[locale]/public/goals/vision/page.tsx
apps/web/src/app/[locale]/public/home/page.tsx
apps/web/src/app/[locale]/public/model-count/page.tsx
apps/web/src/app/[locale]/public/policy/accessibility/page.tsx
apps/web/src/app/[locale]/public/policy/cookies/page.tsx
apps/web/src/app/[locale]/public/policy/governance/page.tsx
apps/web/src/app/[locale]/public/policy/licensing/page.tsx
apps/web/src/app/[locale]/public/policy/privacy/page.tsx
apps/web/src/app/[locale]/public/policy/terms/page.tsx
apps/web/src/app/[locale]/public/science/benchmarks/page.tsx
apps/web/src/app/[locale]/public/science/case-studies/page.tsx
apps/web/src/app/[locale]/public/science/data-sources/page.tsx
apps/web/src/app/[locale]/public/science/evidence-base/page.tsx
apps/web/src/app/[locale]/public/science/gap-analysis/page.tsx
apps/web/src/app/[locale]/public/science/limitations/page.tsx
apps/web/src/app/[locale]/public/science/methodology/page.tsx
apps/web/src/app/[locale]/public/science/peer-review/page.tsx
apps/web/src/app/[locale]/public/science/reproducibility/page.tsx
apps/web/src/app/[locale]/public/science/uncertainty/page.tsx
apps/web/src/app/[locale]/public/science/validation-methods/page.tsx
apps/web/src/app/[locale]/public/science/validation/page.tsx
apps/web/src/app/[locale]/public/services/ai-advisor/page.tsx
apps/web/src/app/[locale]/public/services/api-access/page.tsx
apps/web/src/app/[locale]/public/services/carbon-registry/page.tsx
apps/web/src/app/[locale]/public/services/land-intelligence/page.tsx
apps/web/src/app/[locale]/public/services/marketplace-access/page.tsx
apps/web/src/app/[locale]/public/services/mrv-verification/page.tsx
apps/web/src/app/[locale]/public/services/offline-tools/page.tsx
apps/web/src/app/[locale]/public/services/overview/page.tsx
apps/web/src/app/[locale]/public/services/satellite-intelligence/page.tsx
apps/web/src/app/[locale]/public/services/water-management/page.tsx
apps/web/src/app/[locale]/public/visit/page.tsx
apps/web/src/app/[locale]/public/why/page.tsx
```

## ۴.۶ Market ـ ۷۲ فایل

```text
apps/web/src/app/[locale]/market/page.tsx
apps/web/src/app/[locale]/market/[...segments]/page.tsx
apps/web/src/app/[locale]/market/cart/page.tsx
apps/web/src/app/[locale]/market/compare/page.tsx
apps/web/src/app/[locale]/market/wallet/page.tsx
apps/web/src/app/[locale]/market/bazaars/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/analytics/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/disputes/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/finances/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/governance/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/map/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/settings/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/stores/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/supervision/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step1/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step2/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step3/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step4/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step5/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step6/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step7/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step8/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step9/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step10/page.tsx
apps/web/src/app/[locale]/market/categories/page.tsx
apps/web/src/app/[locale]/market/categories/[level1]/page.tsx
apps/web/src/app/[locale]/market/categories/[level1]/[level2]/page.tsx
apps/web/src/app/[locale]/market/categories/[level1]/[level2]/[level3]/page.tsx
apps/web/src/app/[locale]/market/checkout/page.tsx
apps/web/src/app/[locale]/market/checkout/card/page.tsx
apps/web/src/app/[locale]/market/checkout/cart-review/page.tsx
apps/web/src/app/[locale]/market/checkout/confirmation/page.tsx
apps/web/src/app/[locale]/market/checkout/contract/page.tsx
apps/web/src/app/[locale]/market/checkout/ecowallet/page.tsx
apps/web/src/app/[locale]/market/checkout/escrow-setup/page.tsx
apps/web/src/app/[locale]/market/checkout/transaction-key/page.tsx
apps/web/src/app/[locale]/market/escrow/[id]/page.tsx
apps/web/src/app/[locale]/market/orders/page.tsx
apps/web/src/app/[locale]/market/orders/[id]/dispute/page.tsx
apps/web/src/app/[locale]/market/orders/[id]/evidence/page.tsx
apps/web/src/app/[locale]/market/orders/[id]/timeline/page.tsx
apps/web/src/app/[locale]/market/orders/[id]/tracking/page.tsx
apps/web/src/app/[locale]/market/product/[id]/page.tsx
apps/web/src/app/[locale]/market/product/[id]/bulk/page.tsx
apps/web/src/app/[locale]/market/product/[id]/certifications/page.tsx
apps/web/src/app/[locale]/market/product/[id]/compare/page.tsx
apps/web/src/app/[locale]/market/product/[id]/eco-impact/page.tsx
apps/web/src/app/[locale]/market/product/[id]/pricing-history/page.tsx
apps/web/src/app/[locale]/market/product/[id]/qa/page.tsx
apps/web/src/app/[locale]/market/product/[id]/reviews/page.tsx
apps/web/src/app/[locale]/market/product/[id]/shipping/page.tsx
apps/web/src/app/[locale]/market/product/[id]/similar/page.tsx
apps/web/src/app/[locale]/market/product/[id]/specs/page.tsx
apps/web/src/app/[locale]/market/product/[id]/traceability/page.tsx
apps/web/src/app/[locale]/market/product/[id]/warranty/page.tsx
apps/web/src/app/[locale]/market/search/page.tsx
apps/web/src/app/[locale]/market/search/advanced/page.tsx
apps/web/src/app/[locale]/market/search/autocomplete/page.tsx
apps/web/src/app/[locale]/market/search/barcode/page.tsx
apps/web/src/app/[locale]/market/search/filters/page.tsx
apps/web/src/app/[locale]/market/search/history/page.tsx
apps/web/src/app/[locale]/market/search/image/page.tsx
apps/web/src/app/[locale]/market/search/nfc/page.tsx
apps/web/src/app/[locale]/market/search/semantic/page.tsx
apps/web/src/app/[locale]/market/search/suggestions/page.tsx
apps/web/src/app/[locale]/market/search/visual/page.tsx
apps/web/src/app/[locale]/market/search/voice/page.tsx
apps/web/src/app/[locale]/market/stores/[id]/page.tsx
apps/web/src/app/[locale]/market/stores/create/page.tsx
apps/web/src/app/[locale]/market/stores/create/step1/page.tsx
apps/web/src/app/[locale]/market/stores/create/step2/page.tsx
```

وجود `page.tsx` به معنی تکمیل کار نیست؛ تعدادی از این فایل‌ها mock، scaffold یا صرفاً پوسته هستند.

---

# ۵. فایل‌های تولیدشده و Build Artifactها

| مسیر | وضعیت | نتیجه |
|---|---|---|
| `pnpm-lock.yaml` | tracked | lockfile واقعی monorepo؛ حدود ۵۵۰KB |
| `apps/web/.next/` | ignored | کش dev ناقص؛ بدون `BUILD_ID` و build قابل استقرار |
| `apps/web/.next-phase1check/**` | tracked | build تولیدی اشتباهاً commit‌شده؛ حدود ۱۸۰ فایل و حداقل ۷۳MB |
| `apps/web/playwright-report/index.html` | ignored | گزارش E2E قبلی |
| `apps/web/test-results/**` | ignored | ۳۷ `error-context.md` و چند artifact خالی |
| `apps/web/tsconfig.tsbuildinfo` | ignored | cache افزایشی TypeScript |
| `.turbo/cache/**` | ignored | cache Turbo |
| `packages/api-client/src/generated.ts` | tracked | حدود ۲.۶MB و ۶۰٬۴۹۱ خط؛ تولید Orval |
| `openapi.json` | tracked | snapshot جدیدتر، حدود ۹۸۵KB |
| `openapi_schema.json` | tracked | snapshot قدیمی‌تر، حدود ۹۲۲KB |
| `apps/web/src/app/manifest.ts` | untracked | manifest PWA |
| `apps/web/src/app/manifest.test.ts` | untracked | تست manifest |
| `reports/frontend_layers_i18n.json` | موجود | گزارش تولیدی با مسیرهای قدیمی `frontend/` |
| `reports/design_analysis.json` | موجود | تحلیل تولیدی طراحی |
| `reports/browser-test-2026-09-15/**` | موجود | خروجی قدیمی آزمون مرورگر |
| coverage | غایب | هیچ پوشه `coverage/` وجود ندارد |

## ۵.۱ مشکلات artifactهای تولیدشده

1. `apps/web/.next-phase1check/` کهنه است:
   - `icon.svg` قدیمی دارد.
   - manifest route ندارد.
   - صفحات جدید بازار و سامانه را ندارد.
   - نباید در Git باشد.
2. دو snapshot متفاوت OpenAPI وجود دارد، ولی Orval از `openapi_schema.json` قدیمی‌تر استفاده می‌کند.
3. آخرین Playwright report ثبت‌شده شکست مرورگر را نشان می‌دهد:
   - `chromium_headless_shell ... chrome-headless-shell.exe` نصب نبوده است.
   - این گزارش اثبات موفقیت E2E نیست.
4. `next-env.d.ts` generated و tracked است؛ در clone تازه تا پیش از build به مسیر ignored زیر `.next/types` اشاره می‌کند.
5. هیچ coverage report یا coverage directory وجود ندارد.
6. `apps/web/src/app/manifest.ts` و تست آن untracked هستند.
7. اسناد production مربوط به local-first و frontend در working tree حذف شده‌اند.

---

# ۶. تحلیل شکاف‌ها

## ۶.۱ P0 ـ ناسازگاری environment و proxy

شواهد:

- کلاینت `API_BASE_URL` یا `NEXT_PUBLIC_API_BASE_URL` را می‌خواند: `apps/web/src/lib/api/client.ts:3-4`
- Next rewrite از `API_PROXY_TARGET` استفاده می‌کند: `apps/web/next.config.ts:7-13`
- Helm متغیر `NEXT_PUBLIC_API_URL` را تعریف می‌کند: `helm/eco-nojin/values.yaml:144-149`
- هیچ‌کدام نام canonical مشترک ندارند.
- fallback داخل pod به `127.0.0.1:8000` می‌رسد.

پیامد:

- frontend در deployment نمی‌تواند به gateway واقعی متصل شود.
- health، data و auth همگی وابسته به همین wiring هستند.

وضعیت لازم:

- یک نام متغیر canonical
- Zod validation برای env
- BFF same-origin
- health probe واقعی

## ۶.۲ P0 ـ ناسازگاری قرارداد endpointها

| Frontend | Backend |
|---|---|
| `/api/v1/market/*` | `/api/v1/marketplace/*` |
| `/api/ai/assistant` | `/api/v1/ai/chat` |
| `data.response` | `data.answer` |
| `/api/v1/bazaars/establish` | router فعال marketplace |
| `/api/v1/public/**` | router فعال متناظر پیدا نشد |
| `/api/trust/**` | router فعال متناظر پیدا نشد |
| `/api/developers/**` | router فعال متناظر پیدا نشد |

شواهد:

- `apps/web/src/lib/api/market.ts:14-15,128-138`
- `services/api_gateway/routers/marketplace.py:37`
- `apps/web/src/app/[locale]/ai/assistant/page.tsx:53-68`
- `services/api_gateway/routers/ai_chat.py:206-224`
- `apps/web/src/app/[locale]/market/bazaars/[id]/wizard/page.tsx:138-144`

پیامد:

- بسیاری از صفحاتی که «API-connected» نامیده می‌شوند در runtime به سرویس اشتباه یا route غیرفعال متصل می‌شوند.

## ۶.۳ P0 ـ نبود Auth و Session

موجود نیست:

- login
- signup
- callback
- session provider
- refresh/logout
- route guard
- role guard
- cookie forwarding

شواهد:

- `apps/web/src/lib/api/client.ts:44-51,74-77,176-184` cookie ارسال نمی‌کند.
- backend cookieهای httpOnly ایجاد می‌کند: `services/api_gateway/auth.py:360-388`
- cart/payment/escrow به کاربر معتبر نیاز دارند: `services/api_gateway/routers/marketplace.py:555-559,592-596`

پیامد:

- جریان‌های cart، checkout، payment و escrow قابل استفاده واقعی نیستند.

## ۶.۴ P0 ـ ارسال داده mock به جریان مالی

نمونه‌ها:

- `apps/web/src/app/[locale]/market/cart/page.tsx:23-44`
- `apps/web/src/app/[locale]/market/checkout/page.tsx:25-44,79-107`
- `apps/web/src/app/[locale]/market/escrow/[id]/page.tsx:43-119`
- `apps/web/src/app/[locale]/market/wallet/page.tsx:29-78`
- `apps/web/src/app/[locale]/market/search/page.tsx:24-91`

در checkout، شناسه سفارش از داده mock تولید می‌شود و به payment ارسال می‌گردد.

این برخلاف الزام `FRONTEND_AGENT_ROADMAP.md:20` است: هر داده disconnected باید `unavailable` یا صریحاً `demo` باشد.

## ۶.۵ P0 ـ schema و client کهنه و کم‌نوع

- `orval.config.ts:5` از `openapi_schema.json` استفاده می‌کند.
- `openapi.json` جدیدتر است.
- `packages/api-client/src/generated.ts` در برخی پاسخ‌ها `unknown` تولید کرده است.
- `clean: false` در Orval احتمال نگهداری توابع stale را افزایش می‌دهد.
- backend در بسیاری از routeها `response_model` ندارد.

پیامد:

- Type safety ظاهری وجود دارد، اما قرارداد واقعی API قابل اعتماد نیست.

## ۶.۶ P0 ـ CI و کیفیت قابل بازتولید نیست

workflowهای موجود:

```text
.github/workflows/ci.yml
.github/workflows/ci-cd.yml
.github/workflows/i18n-ci.yml
.github/workflows/security.yml
```

نقص‌ها:

- `ci.yml` به `apps/web/.lighthouserc.json` مفقود اشاره می‌کند.
- E2E build را دانلود می‌کند، ولی `webServer` دستور `pnpm dev` را اجرا می‌کند.
- `ci-cd.yml` به `apps/web/pnpm-lock.yaml` مفقود اشاره می‌کند.
- `i18n-ci.yml` به `frontend/src/paraglide`، `check-rtl-mapping.js` و اسکریپت‌های غایب متکی است.
- `.github/dependabot.yml` هنوز `/frontend` را هدف گرفته است.
- pre-commit از Biome قدیمی `1.9.4` استفاده می‌کند، درحالی‌که پروژه `2.5.14` دارد.
- lint فقط `apps/web/src/` را بررسی می‌کند؛ `packages/*`، testها، scripts و configها خارج از gate هستند.

## ۶.۷ شکاف مسیرها و صفحات

### مقایسه کمی

- هدف master plan: ۹۸۵ صفحه منطقی.
- route manifest داخلی: ۹۸۷.
- snapshot فعلی: ۱۷۷ فایل صفحه.
- نسبت صرفاً بر اساس تعداد فایل: حدود ۱۸٪.
- catch-all و صفحات mock نباید معادل صفحه واقعی محاسبه شوند.

| حوزه | هدف | موجود |
|---|---:|---:|
| Public | ۷۰ | عمدتاً ۶۲ صفحه، بخشی mock |
| Market | ۴۴۴ | ۷۲ صفحه فیزیکی + catch-all |
| Hydroma | ۱۷۴ | فقط صفحات shallow |
| Admin | ۱۳۴ | صفر مسیر واقعی |
| Research | ۷۲ | صفر مسیر واقعی |
| System | ۳۰ | فقط `status` و `offline` |

### مسیرهای مشخص غایب

```text
apps/web/src/app/[locale]/hydroma/tools/**
apps/web/src/app/[locale]/hydroma/map-studio/**
apps/web/src/app/[locale]/hydroma/uncertainty/**
apps/web/src/app/[locale]/hydroma/mrv/**
apps/web/src/app/[locale]/admin/**
apps/web/src/app/[locale]/research/**
apps/web/src/app/[locale]/system/pwa-update/page.tsx
apps/web/src/app/[locale]/system/webgpu-fallback/page.tsx
apps/web/src/app/[locale]/simple/page.tsx
apps/web/src/app/[locale]/telecom/page.tsx
apps/web/src/app/[locale]/market/finance/escrow-ledger/page.tsx
```

### route registry ناسازگار

- `apps/web/src/lib/route-manifest.ts:3-4` عدد ۱۷۵ را ذخیره می‌کند؛ snapshot فعلی ۱۷۷ است.
- `FRONTEND_ALIGNMENT_GAP_ANALYSIS.md:66` عدد ۷۳ صفحه market را ذکر می‌کند؛ شمارش فعلی ۷۲ است.
- مانیفست دستی است و تست آن فقط constant را با خودش مقایسه می‌کند.
- سطح دسترسی `authenticated` و `role-gated` تعریف شده، ولی guard پیاده‌سازی نشده است.
- sitemap فقط چهار مسیر دارد: `apps/web/src/app/sitemap.ts:4-8`

### dead linkهای مشخص

```text
/fa/validation/results
/fa/scientific-models/catalog
/fa/references/library
```

شواهد:

- `apps/web/src/app/[locale]/validation/page.tsx:207-225`
- `apps/web/src/app/[locale]/scientific-models/page.tsx:213-233`
- `apps/web/src/app/[locale]/references/page.tsx:219-237`

## ۶.۸ شکاف i18n و RTL

- تست با نام «All 14 locales» فقط ۸ locale را بررسی می‌کند: `apps/web/tests/i18n.spec.ts:3-21`
- تست واحد `pt` را جا انداخته است: `apps/web/src/i18n/messages.test.ts:5-15`
- صفحات validation، scientific models، references و market search به `fa` یا فقط `fa/en` محدود شده‌اند.
- `PublicLayout` متن انگلیسی و alt ثابت فارسی دارد: `apps/web/src/components/layout/PublicLayout.tsx:29-49`
- loading/error متن ثابت انگلیسی دارند: `apps/web/src/app/[locale]/loading.tsx:7-11` و `apps/web/src/app/[locale]/error.tsx:10-19`
- کلاس‌های فیزیکی مانند `ml-*`، `mr-*`، `text-left` و `text-right` وجود دارند.
- `MarketMap.tsx:95-107` زبان `ur` را در محاسبه جهت نقشه LTR در نظر می‌گیرد.
- هیچ Playwright project مستقلی برای `fa/ar/ur` وجود ندارد.
- قاعده ICU و `Intl` به‌صورت سراسری enforce نشده است.

## ۶.۹ شکاف Design System

مرجع components در `hydroma-nojin-master-plan.md:234-236` حدود ۵۰ مؤلفه را تعیین می‌کند.

### مؤلفه‌های کلیدی مفقود

```text
IconButton
DatePicker شمسی/میلادی
RadioGroup
Accordion
Drawer
DataGrid
Tag
Chip
Progress
Spinner
ErrorState
Stepper/Wizard عمومی
CurrencyUnitToggle
NumberFlow
MapView پایه
ChartFrame
MediaUploader
FileDrop
Sheet
SegmentedControl
Slider/Range
SearchFilter
EmptyRegionMapPlaceholder
PrintHeader
```

### قالب‌های مفقود

```text
T06 — DashboardLayout
T07 — ScientificToolLayout
T08 — AdminTableLayout
T09 — LegalDocumentLayout
T10 — ReportPrintLayout
T11 — SystemStatusLayout کامل
T12 — LearningLayout
```

شاهد:

- `FRONTEND_AGENT_ROADMAP.md:63-71`
- `hydroma-nojin-master-plan.md:238-267`

### سه منبع موازی token

1. `apps/web/tokens/dtcg.json`
2. `apps/web/tokens/variables.css`
3. tokenهای دستی داخل `apps/web/src/app/globals.css`

نقص:

- `globals.css:1` فقط Tailwind را import می‌کند.
- `tokens/variables.css` در runtime به‌صورت مطمئن وارد نمی‌شود.
- کامپوننت‌هایی مانند Button و Card از متغیرهایی استفاده می‌کنند که ممکن است unresolved باشند.
- هیچ Style Dictionary generation یا token drift check وجود ندارد.
- `packages/ui` و `components/ui` دو سیستم کامپوننت موازی هستند.
- نام‌هایی مانند `bg-primary`، `bg-muted` و `ring-border` در theme جاری تعریف نشده‌اند.

## ۶.۱۰ شکاف stateهای صفحه

الزام `hydroma-nojin-master-plan.md:255-257` برای هر صفحه:

- loading
- empty
- error
- partial
- offline
- degraded

وضعیت فعلی:

- loading/error عمومی وجود دارد.
- empty state به‌صورت پراکنده وجود دارد.
- partial/degraded state استاندارد و سراسری وجود ندارد.
- stateها در Storybook مستقل نیستند.
- بسیاری از صفحات فقط static UI هستند.

## ۶.۱۱ شکاف PWA و Local-first

موجود:

```text
apps/web/src/app/manifest.ts
apps/web/src/app/[locale]/offline/page.tsx
apps/web/src/components/ui/OfflineBanner.tsx
```

غایب:

```text
Service Worker
Serwist
Workbox
IndexedDB
Dexie
Yjs/CRDT
OPFS
background sync
outbox
conflict resolution
cache policy
offline form persistence
WASM
```

`OfflineBanner` هیچ‌جا mount نشده است. manifest، app را standalone اعلام می‌کند ولی هیچ service workerی وجود ندارد؛ بنابراین قابلیت آفلاین واقعی نیست.

## ۶.۱۲ شکاف تست و کیفیت

- coverage tool/provider نصب نشده است.
- threshold ۸۰٪ وجود ندارد.
- `test:coverage` در package فعلی وجود ندارد.
- `apps/web/tests/home.spec.ts` به داده واقعی وابسته است.
- `apps/web/tests/hydroma.spec.ts` وضعیت شکست C++ را ثابت انتظار می‌کند.
- a11y فقط ۸ route و فقط critical را بررسی می‌کند.
- صفحات checkout، cart، auth، payment و escrow تست کامل ندارند.
- MSW/fixture backend وجود ندارد.
- تست‌های منفی 401/403/409/422/429/500 وجود ندارند.
- حالت offline و reconnect تست نشده است.
- نتیجه artifactشده E2E شکست missing Chromium را نشان می‌دهد.
- build/lint/type-check موفق فعلاً اثبات نشده است.

## ۶.۱۳ شکاف دسترس‌پذیری

- دکمه‌های `−` و `+` سبد ۲۴×۲۴ هستند: `apps/web/src/app/[locale]/market/cart/page.tsx:184-199`
- input/select جست‌وجو label یا `aria-label` ندارند: `apps/web/src/app/[locale]/market/search/page.tsx:161-189`
- `LanguageMenu` الگوی listbox را بدون keyboard navigation کامل پیاده کرده است: `apps/web/src/components/LanguageMenu.tsx:112-165`
- skip-link به landmark واقعی همه routeها متصل نیست.
- loading/error متن محلی ندارند.
- `MarketMap` از `role="application"` استفاده می‌کند.
- پوشش WCAG 2.2 AA همه routeها و stateها را پوشش نمی‌دهد.

## ۶.۱۴ شکاف امنیت و حریم خصوصی

- CSP و HSTS در Next وجود ندارد.
- `X-Frame-Options`/frame policy کامل وجود ندارد.
- CSP Kubernetes دارای `unsafe-inline` و `unsafe-eval` است.
- `Permissions-Policy`، microphone و camera را برای همه routeها می‌بندد: `apps/web/next.config.ts:22-28`
- playground به دامنه hard-codeشده درخواست می‌فرستد: `apps/web/src/app/[locale]/developers/playground/page.tsx:29-41`
- cookie policy و Google Analytics نمایش‌داده‌شده با پیاده‌سازی واقعی هم‌خوان نیست.
- wallet و escrow داده mock را verified نشان می‌دهند.
- هیچ BFF برای جلوگیری از ارسال مستقیم header/token دلخواه وجود ندارد.
- secret scanning و dependency/SAST فرانت در gate یکپارچه نشده است.

## ۶.۱۵ شکاف performance

نقاط مثبت:

- فونت محلی
- `next/image`
- lazy import نقشه
- WebP/AVIF برای برخی برندها

نقاط منفی:

- layout به‌صورت کلی `force-dynamic` است: `apps/web/src/app/[locale]/layout.tsx:20-21`
- کاتالوگ پیام در هر request خوانده می‌شود: `apps/web/src/lib/i18n/messages.ts:52-70`
- همه namespaceهای پیام ارسال می‌شوند.
- API reads عمدتاً `cache: 'no-store'` دارند.
- bundle analyzer فعال نیست.
- budget برای JS وجود ندارد.
- Lighthouse CI وجود ندارد.
- Web Vitals/RUM وجود ندارد.
- هیچ gateای برای LCP/INP/CLS وجود ندارد.

## ۶.۱۶ شکاف deployment

موارد مفقود:

```text
apps/web/Dockerfile
apps/web/.dockerignore
apps/web/.lighthouserc.json
k8s/base/frontend-deployment.yaml
k8s/base/frontend-service.yaml
```

ناساسگاری‌ها:

- Helm probe از `/health` و `/ready` استفاده می‌کند، ولی این routeهای frontend وجود ندارند.
- Helm `NEXT_PUBLIC_API_URL` می‌دهد، ولی کد آن را نمی‌خواند.
- `API_PROXY_TARGET` در deploy تنظیم نشده است.
- overlayهای Kubernetes یک Deployment با نام frontend را patch می‌کنند که در base وجود ندارد.
- CI فقط image مربوط به API را build می‌کند.
- image `ghcr.io/eco-nojin/frontend` ارجاع می‌شود ولی frontend image build نمی‌شود.

## ۶.۱۷ شکاف mobile

- `mobile/App.tsx` از `./screens/...` import می‌کند، ولی screenها در `mobile/src/screens` هستند.
- `AdvisoryChatScreen.tsx` وجود ندارد.
- `I18nProvider` mount نشده است.
- `AsyncStorage` import شده ولی dependency وجود ندارد.
- `useCallback` استفاده شده ولی import نشده است.
- token امن ذخیره نمی‌شود.
- `tsconfig.json` فقط `**/*.ts` را include می‌کند و TSXها را پوشش نمی‌دهد.

---

# ۷. ناسازگاری مستندات

| موضوع | تعارض |
|---|---|
| مسیر frontend | `apps/web` واقعی؛ `frontend/` در README، CLAUDE و گزارش‌های قدیمی |
| framework | مستند قدیمی Vite؛ پیاده‌سازی فعلی Next.js |
| PWA | AGENTS: Workbox؛ Roadmap/Master plan: Serwist |
| زبان‌ها | استاندارد ۱۴؛ برخی اسناد ۶ یا ۱۲ |
| تعداد route | ۹۸۵ در master plan؛ ۹۸۷ در route manifest؛ ۱۷۵ در کد؛ ۱۷۷ واقعی |
| بازار | ۷۳ در gap analysis؛ ۷۲ فایل فعلی |
| docs | `mkdocs.yml` و README به `docs/` ارجاع می‌دهند؛ پوشه deleted است |
| quality script | README از `pnpm quality` نام می‌برد؛ script وجود ندارد |
| i18n CI | workflow به پروژه قدیمی و مسیرهای حذف‌شده اشاره می‌کند |
| گزارش RTL قدیمی | layout ثابت RTL را گزارش کرده، ولی layout فعلی per-locale است |

---

# ۸. نقشه راه تکمیل پروژه

## Wave 0 — تثبیت baseline و بهداشت مخزن

### اقدامات

1. تعیین تکلیف تمام تغییرات untracked/deleted.
2. commit یا انتقال اسناد مرجع:
   - `DESIGN_SYSTEM_ART_AND_VISUALS_2026.md`
   - `FRONTEND_AGENT_ROADMAP.md`
   - `FRONTEND_ALIGNMENT_GAP_ANALYSIS.md`
3. بازیابی یا جایگزینی کنترل‌شده `docs/`؛ حذف نیمه‌کاره docs قابل قبول نیست.
4. حذف build از Git:
   - `apps/web/.next-phase1check/**`
5. اصلاح `.gitignore` برای تمام distهای سفارشی:
   ```gitignore
   **/.next/
   **/.next-*/
   **/playwright-report/
   **/test-results/
   **/coverage/
   ```
6. حذف کاتالوگ duplicate ریشه `messages/*.json` یا Mark کردن آن به‌عنوان legacy.
7. انتخاب `openapi.json` به‌عنوان منبع canonical.
8. حذف یا generation-based کردن `openapi_schema.json`.
9. تنظیم Orval روی schema canonical و `clean: true`.
10. افزودن `response_model` در backend و regenerate کردن client.
11. اصلاح README/CLAUDE/mkdocs و حذف ارجاع‌های `frontend/`، Vite و ۶/۱۲ زبان.

### معیار پذیرش

- clone تازه ساختار frontend و docs را بدون اصلاح دستی پیدا کند.
- هیچ build artifact در Git نباشد.
- `openapi.json` و client generated از یک commit مشترک باشند.
- routeهای فعلی از route registry تولید شوند.

---

## Wave 1 — قرارداد API، environment و Auth

### فایل‌های جدید

```text
apps/web/src/lib/config/env.ts
apps/web/src/lib/config/env.test.ts
apps/web/src/lib/api/errors.ts
apps/web/src/lib/api/query-keys.ts
apps/web/src/lib/auth/session.ts
apps/web/src/lib/auth/permissions.ts
apps/web/src/lib/auth/session.test.ts
apps/web/src/lib/auth/permissions.test.ts

apps/web/src/app/api/auth/login/route.ts
apps/web/src/app/api/auth/signup/route.ts
apps/web/src/app/api/auth/refresh/route.ts
apps/web/src/app/api/auth/logout/route.ts
apps/web/src/app/api/auth/session/route.ts

apps/web/src/app/[locale]/auth/login/page.tsx
apps/web/src/app/[locale]/auth/signup/page.tsx
apps/web/src/app/[locale]/auth/callback/page.tsx
apps/web/src/app/[locale]/account/session/page.tsx
```

### فایل‌های نیازمند تغییر

```text
apps/web/next.config.ts
apps/web/src/middleware.ts
apps/web/src/lib/api/client.ts
apps/web/src/lib/api/typed-client.ts
apps/web/src/lib/api/hooks.ts
apps/web/src/lib/api/market.ts
apps/web/src/lib/api/cart.ts
apps/web/src/lib/api/escrow.ts
apps/web/src/app/[locale]/ai/assistant/page.tsx
apps/web/src/app/[locale]/ai/voice/page.tsx
apps/web/src/app/[locale]/ai/feedback/page.tsx
apps/web/src/app/[locale]/market/checkout/page.tsx
apps/web/src/app/[locale]/market/bazaars/[id]/wizard/page.tsx
```

### کارهای دقیق

- استفاده از یک نام env canonical.
- حذف fallback localhost در production.
- ارسال cookie only در same-origin.
- refresh خودکار session.
- guard برای routeهای authenticated/role-gated.
- حذف order/payment mock.
- تطبیق `/market` با `/marketplace`.
- تطبیق AI request/response با `/api/v1/ai/chat`.
- حذف endpointهای public/trust/developers غیرفعال یا فعال‌سازی آنها در backend.
- افزودن timeout، abort، retry و typed error مشترک.
- تست E2E مسیر login → cart → checkout → payment → escrow.

### معیار پذیرش

- هیچ endpointی fallback به localhost نداشته باشد.
- هیچ داده مالی mock به API واقعی ارسال نشود.
- session و RBAC در server و client هر دو enforce شوند.
- تمام pageهای API از client/hook canonical استفاده کنند.

---

## Wave 2 — i18n، Design System و Accessibility

### توکن و Style Dictionary

```text
packages/tokens/package.json
packages/tokens/src/dtcg.json
packages/tokens/src/config.json
packages/tokens/src/typescript.ts
packages/tokens/style-dictionary.config.mjs
packages/tokens/src/generated/css/tokens.css
packages/tokens/src/generated/typescript/tokens.ts
apps/web/tokens/dtcg.json
apps/web/tokens/variables.css
```

- یک منبع canonical برای primitive و semantic tokens.
- حذف توکن‌های موازی.
- تست unresolved CSS variables.
- CI برای token diff.

### مؤلفه‌های مفقود `packages/ui`

```text
packages/ui/src/icon-button.tsx
packages/ui/src/date-picker.tsx
packages/ui/src/radio-group.tsx
packages/ui/src/accordion.tsx
packages/ui/src/drawer.tsx
packages/ui/src/data-grid.tsx
packages/ui/src/tag.tsx
packages/ui/src/chip.tsx
packages/ui/src/progress.tsx
packages/ui/src/spinner.tsx
packages/ui/src/error-state.tsx
packages/ui/src/stepper.tsx
packages/ui/src/currency-unit-toggle.tsx
packages/ui/src/number-flow.tsx
packages/ui/src/map-view.tsx
packages/ui/src/chart-frame.tsx
packages/ui/src/media-uploader.tsx
packages/ui/src/file-drop.tsx
packages/ui/src/sheet.tsx
packages/ui/src/segmented-control.tsx
packages/ui/src/slider.tsx
packages/ui/src/search-filter.tsx
packages/ui/src/empty-region-map-placeholder.tsx
packages/ui/src/print-header.tsx
```

### قالب‌های مفقود

```text
apps/web/src/components/layout/DashboardLayout.tsx
apps/web/src/components/layout/ScientificToolLayout.tsx
apps/web/src/components/layout/AdminTableLayout.tsx
apps/web/src/components/layout/LegalDocumentLayout.tsx
apps/web/src/components/layout/ReportPrintLayout.tsx
apps/web/src/components/layout/SystemStatusLayout.tsx
apps/web/src/components/layout/LearningLayout.tsx
```

### Storybook

```text
apps/web/.storybook/main.ts
apps/web/.storybook/preview.ts
apps/web/.storybook/test-runner.ts
packages/ui/src/**/*.stories.tsx
```

### i18n و accessibility

- حذف hard-codeهای `fa/en`.
- تست هر ۱۴ locale.
- تست جداگانه RTL برای `fa/ar/ur`.
- تکمیل labelها و keyboard navigation.
- touch target حداقل ۴۴px.
- حذف کلاس‌های فیزیکی RTL.
- تعریف stateهای loading/empty/error/partial/offline/degraded.
- axe برای همه routeهای نماینده و همه stateها.

### معیار پذیرش

- WCAG 2.2 AA بدون violation جدی/بحرانی.
- هر ۵۰ مؤلفه در Storybook و design-system page قابل مشاهده باشد.
- هیچ متغیر CSS unresolved وجود نداشته باشد.
- ترجمه‌ها دارای برچسب کیفیت باشند.

---

## Wave 3 — تکمیل حوزه‌های صفحه

### Hydroma

```text
apps/web/src/app/[locale]/hydroma/layout.tsx
apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx
apps/web/src/app/[locale]/hydroma/map-studio/page.tsx
apps/web/src/app/[locale]/hydroma/uncertainty/page.tsx
apps/web/src/app/[locale]/hydroma/mrv/page.tsx
apps/web/src/app/[locale]/hydroma/calibration/page.tsx
apps/web/src/app/[locale]/hydroma/run-queue/page.tsx
apps/web/src/lib/hydroma/tool-registry.ts
apps/web/src/lib/hydroma/tool-registry.test.ts
apps/web/src/lib/hydroma/types.ts
```

- registry ۶۲ ابزار به‌جای ۶۲ صفحه تکراری scaffold.
- ScientificToolLayout برای همه ابزارها.
- Zod validation.
- model version/calibration/uncertainty/run ID.
- replay با همان input.
- fallback صریح `demo/unavailable`.

### Admin

```text
apps/web/src/app/[locale]/admin/layout.tsx
apps/web/src/app/[locale]/admin/loading.tsx
apps/web/src/app/[locale]/admin/error.tsx
apps/web/src/app/[locale]/admin/disputes/page.tsx
apps/web/src/app/[locale]/admin/system/health/page.tsx
apps/web/src/app/[locale]/admin/localization/translations/page.tsx
apps/web/src/app/[locale]/admin/feature-flags/page.tsx
apps/web/src/app/[locale]/admin/event-bus/page.tsx
apps/web/src/app/[locale]/admin/jobs/page.tsx
apps/web/src/app/[locale]/admin/workers/page.tsx
apps/web/src/app/[locale]/admin/design-tokens/page.tsx
apps/web/src/middleware/admin-auth.ts
```

- deny-by-default.
- RBAC سمت server.
- T08 با bulk action و DataGrid.

### Research

```text
apps/web/src/app/[locale]/research/layout.tsx
apps/web/src/app/[locale]/research/page.tsx
apps/web/src/app/[locale]/research/workspace/[experimentId]/page.tsx
apps/web/src/app/[locale]/research/datasets/[datasetId]/page.tsx
apps/web/src/app/[locale]/research/preprints/page.tsx
apps/web/src/app/[locale]/research/pipelines/page.tsx
apps/web/src/app/[locale]/research/federated/page.tsx
apps/web/src/app/[locale]/research/ethics/page.tsx
apps/web/src/lib/research/doi.ts
apps/web/src/lib/research/immutable-record.ts
```

### System و inclusive

```text
apps/web/src/app/[locale]/system/layout.tsx
apps/web/src/app/[locale]/system/pwa-update/page.tsx
apps/web/src/app/[locale]/system/webgpu-fallback/page.tsx
apps/web/src/app/[locale]/system/locale-fallback/page.tsx
apps/web/src/app/[locale]/simple/page.tsx
apps/web/src/app/[locale]/telecom/page.tsx
```

### Market

```text
apps/web/src/app/[locale]/market/finance/escrow-ledger/page.tsx
apps/web/src/app/[locale]/market/orders/[id]/page.tsx
apps/web/src/app/[locale]/market/stores/page.tsx
apps/web/src/app/[locale]/market/product/[id]/buy-box.tsx
apps/web/src/app/[locale]/market/product/[id]/seller-ranking.tsx
```

---

## Wave 4 — PWA و Local-first

### فایل‌های جدید

```text
apps/web/src/app/sw.ts
apps/web/src/lib/offline/db.ts
apps/web/src/lib/offline/schema.ts
apps/web/src/lib/offline/outbox.ts
apps/web/src/lib/offline/sync.ts
apps/web/src/lib/offline/conflicts.ts
apps/web/src/lib/offline/cache-policy.ts
apps/web/src/lib/offline/connectivity.ts
apps/web/src/lib/offline/db.test.ts
apps/web/src/lib/offline/outbox.test.ts
apps/web/src/lib/offline/sync.test.ts
apps/web/src/components/providers/OfflineProvider.tsx
```

### تغییرات

- افزودن Serwist، Dexie و Yjs طبق master plan.
- ثبت service worker در build production.
- cache کردن app shell و routeهای عمومی.
- cache فرم‌های ناقص.
- outbox برای writeهای مجاز.
- reconnect/retry.
- conflict resolution با Lamport clock.
- mount کردن `OfflineBanner` در layout.
- پاک‌کردن cache و outbox هنگام logout.
- تست واقعی airplane mode.

### معیار پذیرش

- بدون شبکه، صفحات اصلی باز شوند.
- فرم قابل ویرایش باشد.
- پس از reconnect در outbox قرار گیرد.
- داده حساس/admin cache نشود.
- Lighthouse PWA و update flow عبور کند.

---

## Wave 5 — کیفیت، Observability، Security و Performance

### تست

```text
apps/web/vitest.config.ts
apps/web/vitest.setup.ts
apps/web/src/test/msw/handlers.ts
apps/web/src/test/msw/server.ts
apps/web/src/test/factories/*.ts
apps/web/playwright.config.ts
apps/web/tests/rtl-fa.spec.ts
apps/web/tests/rtl-ar.spec.ts
apps/web/tests/rtl-ur.spec.ts
apps/web/tests/auth.spec.ts
apps/web/tests/checkout.spec.ts
apps/web/tests/offline.spec.ts
apps/web/tests/api-errors.spec.ts
apps/web/.lighthouserc.json
```

- افزودن `@vitest/coverage-v8`.
- threshold حداقل ۸۰٪؛ برای auth/money/state machine صددرصد branch هدف.
- تست API با MSW، نه داده developer.
- projectهای per-locale.
- regression تست برای ۳۲۰px.
- lint تمام `apps/web` و `packages/*`.

### Observability

```text
apps/web/src/lib/observability/client.ts
apps/web/src/lib/observability/errors.ts
apps/web/src/components/WebVitals.tsx
apps/web/src/app/health/route.ts
apps/web/src/app/ready/route.ts
apps/web/src/app/metrics/route.ts
```

- Sentry یا OpenTelemetry.
- source map release.
- PII scrubbing.
- request ID و backend correlation.
- Web Vitals.
- alert برای error rate، API failure و Core Web Vitals.

### Security

- CSP با nonce.
- HSTS در production.
- `frame-ancestors`.
- Permissions-Policy per route.
- حذف direct playground request.
- BFF برای auth/API حساس.
- cookie policy واقعی.
- secret/dependency/SAST scan.

### Performance

- حذف `force-dynamic` سراسری.
- cache ایستا صفحات محتوایی.
- namespace-level i18n loading.
- cache policy برای API reads.
- فعال‌سازی bundle analyzer.
- lazy load MapLibre/ECharts/Three.js.
- budget:
  - LCP ≤ ۲.۵ ثانیه
  - INP ≤ ۲۰۰ms
  - CLS ≤ ۰.۱
  - initial JS ≤ ۲۰۰KB gzip

---

## Wave 6 — Deployment و زیرساخت

### فایل‌های جدید

```text
apps/web/Dockerfile
apps/web/.dockerignore
deploy/nginx/frontend.conf
k8s/base/frontend-deployment.yaml
k8s/base/frontend-service.yaml
k8s/base/frontend-hpa.yaml
```

### اصلاح فایل‌های موجود

```text
.github/workflows/ci.yml
.github/workflows/ci-cd.yml
.github/workflows/i18n-ci.yml
.github/dependabot.yml
helm/eco-nojin/values.yaml
helm/eco-nojin/templates/deployment-frontend.yaml
helm/eco-nojin/templates/service-frontend.yaml
k8s/base/kustomization.yaml
```

### اقدامات

- build واقعی frontend image.
- استفاده از build artifact در E2E، نه `pnpm dev`.
- lockfile root در cache dependency path.
- تعریف `API_PROXY_TARGET`.
- افزودن routeهای `/health` و `/ready`.
- هماهنگی port با Helm.
- build واقعی `ghcr.io/eco-nojin/frontend`.
- حذف placeholderهای deploy staging/production.
- تعریف resource limit، probe و security context.

---

## Wave 7 — تعمیر mobile و بستن پروژه

### اصلاح mobile

```text
mobile/App.tsx
mobile/src/screens/*
mobile/src/context/I18nContext.tsx
mobile/src/hooks/useBilingual.ts
mobile/src/services/api.ts
mobile/package.json
mobile/tsconfig.json
```

موارد مشخص:

- اصلاح import از `./screens` به `./src/screens`.
- افزودن `AdvisoryChatScreen`.
- mount کردن `I18nProvider`.
- افزودن `AsyncStorage`.
- import کردن `useCallback`.
- پیاده‌سازی SecureStore برای token.
- include کردن TSX در tsconfig.
- افزودن test و scripts.

### مستندسازی نهایی

```text
docs/frontend/ARCHITECTURE.md
docs/frontend/API_AND_QUERY.md
docs/frontend/AUTH_AND_RBAC.md
docs/frontend/I18N_AND_RTL.md
docs/frontend/PWA_AND_OFFLINE.md
docs/frontend/TESTING.md
docs/frontend/DEPLOYMENT.md
docs/adr/0002-auth-bff.md
docs/adr/0003-pwa-local-first.md
docs/adr/0004-design-tokens.md
docs/adr/0005-api-contract.md
```

---

# ۹. Definition of Done نهایی

پروژه زمانی مطابق استاندارد نهایی است که همه موارد زیر برقرار باشند:

1. تمام commandهای زیر در CI سبز باشند:
   ```bash
   pnpm -C apps/web lint
   pnpm -C apps/web type-check
   pnpm -C apps/web test
   node apps/web/scripts/i18n-check.mjs
   pnpm -C apps/web build
   pnpm -C apps/web test:e2e
   ```
2. coverage واقعی و threshold فعال باشد.
3. route crawler هیچ لینک داخلی شکسته یا 404 نداشته باشد.
4. هر ۱۴ locale در i18n و Playwright پوشش داده شوند.
5. هیچ متن hard-code در `src/app` و `src/components` باقی نماند.
6. هیچ raw color یا فاصله خارج از token وجود نداشته باشد.
7. هر عدد `ProvenanceStamp` یا وضعیت `unavailable/demo` داشته باشد.
8. تمام صفحات stateهای loading/empty/error/partial/offline/degraded داشته باشند.
9. auth/session/RBAC و جریان checkout واقعی با session و API معتبر کار کند.
10. PWA پس از قطع شبکه، فرم و outbox واقعی داشته باشد.
11. frontend image و Kubernetes deployment/health probe واقعی داشته باشد.
12. route registry، OpenAPI، generated client و مستندات از یک منبع canonical تغذیه شوند.
13. تمام فایل‌های untracked و deleted تعیین تکلیف شده و baseline Git قابل بازتولید باشد.
14. WCAG 2.2 AA، performance budget و observability در gateهای CI enforce شوند.

---

## جمع‌بندی

زیرساخت Next.js، i18n، بخشی از Design System، API tooling و اسکلت صفحات بازارگاه وجود دارد؛ اما پروژه هنوز «استاندارد نهایی» نیست. مهم‌ترین مسیر تکمیل به ترتیب عبارت است از:

1. تثبیت Git و اسناد مرجع
2. یکسان‌سازی OpenAPI و environment
3. پیاده‌سازی Auth/Session/RBAC
4. اصلاح جریان‌های مالی و حذف mock
5. تکمیل i18n، Design System و accessibility
6. تکمیل Hydroma، Admin، Research و System
7. پیاده‌سازی PWA و Local-first
8. stabilization کیفیت، امنیت، observability و performance
9. تکمیل deployment و production gates
10. بستن gaps مستندسازی و رسیدن به Definition of Done

---

# ۱۰. گزارش اجرای Wave 1 و Wave 2

## Wave 1 — قرارداد، Auth و Release

انجام‌شده:

- BFF same-origin با routeهای زیر ایجاد شد:
  - `apps/web/src/app/api/auth/login/route.ts`
  - `apps/web/src/app/api/auth/signup/route.ts`
  - `apps/web/src/app/api/auth/refresh/route.ts`
  - `apps/web/src/app/api/auth/logout/route.ts`
  - `apps/web/src/app/api/auth/session/route.ts`
  - `apps/web/src/app/api/[...path]/route.ts`
- session به یک شناسهٔ opaque در Redis تبدیل شد؛ access/refresh token در cookie مرورگر نیست.
- Redis session store، TTL، rotation، logout و fallback حافظه‌ای توسعه اضافه شد.
- Origin، `X-CSRF-Intent` و `Sec-Fetch-Site` برای mutationهای BFF اعمال شد.
- RBAC به roleهای واقعی backend محدود شد؛ permission اختراعی منتشر نشد.
- اصلاح JTI refresh token، commit رکورد register، revoke در logout و محدودیت self-assign شدن role مدیریتی در backend انجام شد.
- checkout، cart، wallet، escrow و search از داده mock به API واقعی یا وضعیت unavailable منتقل شدند.
- endpointهای AI به قرارداد `/api/v1/ai/chat` و voice به `answer`/`text` منتقل شدند.
- `openapi.json` منبع canonical شد، `openapi_schema.json` حذف و Orval client بازتولید شد.
- `API_PROXY_TARGET`، `REDIS_URL`، `SESSION_SECRET` و `NEXT_PUBLIC_APP_URL` در Helm/env نمونه هم‌تراز شدند.
- workflowهای CI، release و branch model روی `main` و semver tag محدود شدند.
- deploy placeholder staging/production خاموش نگه داشته شد.

## Wave 2 — Design System، i18n، Accessibility و PWA

انجام‌شده:

- `tokens/variables.css` به runtime متصل و مقادیر Tailwind به semantic tokenها متحد شدند.
- tokenهای action/ink/contrast اصلاح شدند و WCAG 2.2 AA تست جدی روی ۱۱ مسیر عبور کرد.
- مؤلفه‌های مشترک جدید به `packages/ui` اضافه و export شدند:
  - `IconButton`
  - `Progress`
  - `Spinner`
  - `ErrorState`
  - `Tag`
  - `CurrencyUnitToggle`
  - `DataGrid`
  - `ChartFrame`
  - `Stepper`
- `OfflineBanner`، `ErrorBoundary` و `OfflineProvider` در layout mount شدند.
- canonical i18n به en تغییر کرد، fallback چندلایه حذف و localeهای ۱۴گانه parity شدند.
- Serwist 9.5.12 و Dexie اضافه شدند.
- `sw.ts` فقط app-shell و asset عمومی را cache می‌کند و `/api/*` را Network-only نگه می‌دارد.
- `tests/offline.spec.ts` اضافه و عبور آفلاین بعد از اولین بازدید آنلاین اثبات شد.

## Wave 4 — PWA Baseline

انجام‌شده:

- Serwist 9.5.12 و Dexie به workspace اضافه شدند.
- `apps/web/src/app/sw.ts` فقط app-shell و assetهای عمومی را cache می‌کند.
- `/api/*`، session، داده خصوصی و عملیات مالی در cache policy مسدود هستند.
- `OfflineBanner`، `ErrorBoundary` و `OfflineProvider` در layout mount شدند.
- تست E2E آفلاین پس از اولین بازدید آنلاین موفق است.

PWA اکنون یک پوستهٔ آفلاین و draft/outbox عمومی است؛ ledger مالی، پرداخت، escrow و order همچنان online-only باقی می‌مانند.

## اعتبارسنجی نهایی این مرحله

| بررسی | نتیجه |
|---|---|
| frontend quality gate | موفق؛ ۲۹۸ فایل، ۶۷ تست |
| TypeScript app | موفق |
| Vitest | ۱۸ فایل و ۶۷ تست موفق |
| i18n parity | هر ۱۴ locale موفق |
| Next production build | موفق؛ خروجی routeها و service worker تولید شد |
| Playwright i18n | ۱۹ تست موفق |
| Playwright WCAG 2.2 AA | ۱۱ تست موفق |
| Playwright PWA offline | ۱ تست موفق |
| packages/ui TypeScript | موفق |
| Ruff auth files | موفق |
| auth unit tests | ۷ تست موفق |
| auth refresh integration | ۴ تست موفق در SQLite ایزوله |
| OpenAPI contract test | ۱ تست موفق |
| version check | `0.2.0` برای VERSION/package/pyproject |

## موارد باقی‌مانده پیش از تکمیل نهایی

- UI صفحه‌های login/signup و کنترل‌های session در UI هنوز به Wave 2 تکمیلی نیاز دارند؛ API و provider آماده‌اند.
- production باید `REDIS_URL` و `SESSION_SECRET` واقعی را در Secret ارائه کند.
- cache/query persistence سراسری و outbox برای فرم عمومی باید به فرم واقعی متصل شود.
- بسیاری از صفحات عمومی قدیمی هنوز محتوای scaffold/demo دارند و باید به محتوای canonical و ProvenanceStamp منتقل شوند.
- image/Docker/deploy واقعی frontend و GitHub environments/rulesets هنوز نیازمند دسترسی مدیر و قرارداد نهایی هستند.
- تغییرات Wave 1 و Wave 2 فعلاً uncommitted هستند و باید پیش از merge بازبینی و commit شوند.
