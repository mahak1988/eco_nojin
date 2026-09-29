# شکاف‌های قرارداد — مسیرهای مصرف‌شده ولی منتشرنشده

**تاریخ:** ۲۰۲۶/۰۹/۲۸ · **ابزار:** `scripts/check-api-contract.mjs` (گیت فاز B3)
**خلاصه:** ۵۰۳ مسیر مصرف‌شده در کد · ۴۶۴ تطبیق · **۳۹ شکاف**

> نمونه‌های شاخص زنده آزمایش شدند (۹ مسیر): ۸ مورد **۴۰۴** (endpoint وجود ندارد) و ۱ مورد **۴۰۱** (`/api/v1/farms` نیازمند نشست). ۳۰ مسیر دیگر در همان خوشه‌ها هستند و به‌صورت جداگانه آزمون نشده‌اند.

```
published paths : 489
used paths      : 503
matched         : 464
missing         : 39

Used but NOT published:
  /api/v1/ecowallet
      apps\web\src\app\[locale]\market\wallet\page.tsx
      apps\web\src\lib\domains\page-catalog.ts
  /api/v1/farms
      apps\web\src\app\[locale]\hydroma\farms\page.tsx
      apps\web\src\lib\domains\page-catalog.ts
      packages\api-client\src\generated.ts
  /api/v1/lms/courses
      apps\web\src\app\[locale]\public\education\courses\page.tsx
  /api/v1/manual
      apps\web\src\lib\api\manual.ts
  /api/v1/marketplace
      apps\web\src\lib\api\cart.ts
      apps\web\src\lib\api\escrow.ts
  /api/v1/public/api/endpoints
      apps\web\src\lib\api\public.ts
  /api/v1/public/api/schema
      apps\web\src\lib\api\public.ts
  /api/v1/public/components
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/api-playground
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/dispute-resolution
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/ecowallet
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/hydroma-engine
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/land-profiler
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/marketplace
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/mrv-dashboard
      apps\web\src\lib\api\public.ts
  /api/v1/public/components/satellite-view
      apps\web\src\lib\api\public.ts
  /api/v1/public/education/certifications
      apps\web\src\app\[locale]\public\education\certifications\page.tsx
      apps\web\src\lib\api\public.ts
  /api/v1/public/education/courses
      apps\web\src\lib\api\public.ts
  /api/v1/public/education/video
      apps\web\src\app\[locale]\public\education\video-player\page.tsx
  /api/v1/public/education/video/{param}
      apps\web\src\lib\api\public.ts
  /api/v1/public/education/videos
      apps\web\src\lib\api\public.ts
  /api/v1/public/education/workshops
      apps\web\src\app\[locale]\public\education\workshops\page.tsx
  /api/v1/public/policy/accessibility
      apps\web\src\lib\api\public.ts
  /api/v1/public/policy/cookies
      apps\web\src\lib\api\public.ts
  /api/v1/public/policy/governance
      apps\web\src\lib\api\public.ts
  /api/v1/public/policy/licensing
      apps\web\src\lib\api\public.ts
  /api/v1/public/policy/privacy
      apps\web\src\lib\api\public.ts
  /api/v1/public/policy/terms
      apps\web\src\lib\api\public.ts
  /api/v1/public/policy/{param}/versions
      apps\web\src\lib\api\public.ts
  /api/v1/public/science/data-sources
      apps\web\src\lib\api\public.ts
  /api/v1/public/science/evidence-base
      apps\web\src\lib\api\public.ts
  /api/v1/public/science/methodology
      apps\web\src\lib\api\public.ts
  /api/v1/public/science/reproducibility
      apps\web\src\lib\api\public.ts
  /api/v1/public/science/uncertainty
      apps\web\src\lib\api\public.ts
  /api/v1/public/science/validation
      apps\web\src\lib\api\public.ts
  /api/v1/security/status
      apps\web\src\lib\workspaces\registry.ts
  /api/v1/soil
      packages\api-client\src\generated.ts
  /api/v1/{param}/health
      apps\web\src\app\[locale]\system\page.tsx
  /api/{param}{param}
      apps\web\src\app\api\[...path]\route.ts
```