# درخواست قرارداد — ۱۵۴ مسیر `unavailable`

**تاریخ:** 2026-09-26 · **مرجع:** کاتالوگ ۶۰۰ ورودی · **وضعیت:** منتظر پاسخ مالک بک‌اند

## چرا این سند وجود دارد

154 مسیر کاتالوگ `endpoint` ندارند یا endpoint‌شان در `openapi.json` منتشر نشده است. تا وقتی قراردادی منتشر نشود، ساختن صفحه برای این مسیرها یعنی ساختن داده؛ بنابراین این مسیرها `unavailable` و `noindex` می‌مانند و هیچ صفحه‌ای برایشان نوشته نمی‌شود.

این سند فهرست دقیق چیزی است که برای اتصال این مسیرها لازم است. هر ردیف یک خوشه API است، نه یک صفحه.

## خلاصه

| خوشه مسیر | تعداد | دامنه | دسترسی | متدها | نمونه |
|---|---:|---|---|---|---|
| `hydroma/tools` | 52 | hydroma | public | GET, POST | `/hydroma/tools/aquacrop-runner/execute` · `/hydroma/tools/carbon-calculator/execute` · `/hydroma/tools/climate-adaptive-phenology/execute` |
| `market/bazaars` | 19 | marketplace | public | GET | `/market/bazaars/{id}/analytics` · `/market/bazaars/{id}/disputes` · `/market/bazaars/{id}/finances` |
| `market/product` | 11 | marketplace | public | GET | `/market/product/{id}/bulk` · `/market/product/{id}/certifications` · `/market/product/{id}/compare` |
| `market/search` | 9 | marketplace | public | GET | `/market/search/autocomplete` · `/market/search/barcode` · `/market/search/history` |
| `research/experiments` | 6 | research | authenticated | GET | `/research/experiments/experiment-approval` · `/research/experiments/experiment-citations` · `/research/experiments/experiment-dataset` |
| `market/categories` | 4 | marketplace | public | GET | `/market/categories` · `/market/categories/{level1}` · `/market/categories/{level1}/{level2}` |
| `market/stores` | 4 | marketplace | public | GET | `/market/stores/create` · `/market/stores/create/step1` · `/market/stores/create/step2` |
| `public/education` | 4 | learning | public | GET | `/public/education/certifications` · `/public/education/courses` · `/public/education/video-player` |
| `about` | 1 | public | public | GET | `/about` |
| `ai` | 1 | public | public | GET | `/ai` |
| `ai/ethics` | 1 | public | public | GET | `/ai/ethics` |
| `ai/limits` | 1 | public | public | GET | `/ai/limits` |
| `design-system` | 1 | public | public | GET | `/design-system` |
| `developers/cookbooks` | 1 | public | public | GET | `/developers/cookbooks` |
| `prototype` | 1 | public | public | GET | `/prototype` |
| `public/visit-request-submit` | 1 | public | public | GET | `/public/visit-request-submit` |
| `services` | 1 | public | public | GET | `/services` |
| `statements` | 1 | public | public | GET | `/statements` |
| `trust` | 1 | public | public | GET | `/trust` |
| `trust/sanctions` | 1 | public | public | GET | `/trust/sanctions` |
| `market/bazaar-analytics` | 1 | marketplace | public | GET | `/market/bazaar-analytics` |
| `market/checkout` | 1 | marketplace | public | GET | `/market/checkout/ecowallet` |
| `market/escrow-dispute-arbitration` | 1 | marketplace | public | GET | `/market/escrow-dispute-arbitration` |
| `market/order-invoice` | 1 | marketplace | public | GET | `/market/order-invoice` |
| `market/orders` | 1 | marketplace | public | GET | `/market/orders/{id}/evidence` |
| `market/vendor-payouts` | 1 | marketplace | public | GET | `/market/vendor-payouts` |
| `market/{*segments}` | 1 | marketplace | public | GET | `/market/{*segments}` |
| `admin/audit-trail` | 1 | admin | role-gated | GET | `/admin/audit-trail` |
| `admin/automation-runs` | 1 | admin | role-gated | GET | `/admin/automation-runs` |
| `admin/channel-health` | 1 | admin | role-gated | GET | `/admin/channel-health` |
| `admin/message-catalogue-sync` | 1 | admin | role-gated | GET | `/admin/message-catalogue-sync` |
| `system/incident-timeline` | 1 | system | internal | GET | `/system/incident-timeline` |
| `system/migration-runner` | 1 | system | internal | GET | `/system/migration-runner` |
| `system/queue-inspector` | 1 | system | internal | GET | `/system/queue-inspector` |
| `workspace/audit` | 1 | workspace | role-gated | GET | `/workspace/audit` |
| `workspace/operations` | 1 | workspace | role-gated | GET | `/workspace/operations/events` |
| `workspace/report-export` | 1 | workspace | role-gated | GET | `/workspace/report-export` |
| `workspace/target-progress` | 1 | workspace | role-gated | GET | `/workspace/target-progress` |
| `accessibility` | 1 | inclusive | public | GET | `/accessibility` |
| `account/session` | 1 | inclusive | public | GET | `/account/session` |
| `auth/login` | 1 | inclusive | public | GET | `/auth/login` |
| `auth/signup` | 1 | inclusive | public | GET | `/auth/signup` |
| `inclusive/sms-delivery-receipt` | 1 | inclusive | public | GET | `/inclusive/sms-delivery-receipt` |
| `inclusive/ussd-session-audit` | 1 | inclusive | public | GET | `/inclusive/ussd-session-audit` |
| `inclusive/voice-call-record` | 1 | inclusive | public | GET | `/inclusive/voice-call-record` |
| `offline` | 1 | inclusive | public | GET | `/offline` |
| `simple` | 1 | inclusive | public | GET | `/simple` |
| `learn/assessment-submission` | 1 | learning | public | GET | `/learn/assessment-submission` |
| `learn/certificate-verify` | 1 | learning | public | GET | `/learn/certificate-verify` |
| `learn/course-enrolment` | 1 | learning | public | GET | `/learn/course-enrolment` |
| `learn/library-checkout` | 1 | learning | public | GET | `/learn/library-checkout` |
| `learn/video-caption-pack` | 1 | learning | public | GET | `/learn/video-caption-pack` |
| `learn/video-progress` | 1 | learning | public | GET | `/learn/video-progress` |

**جمع: 154 مسیر در 53 خوشه.**

## آنچه برای باز شدن هر خوشه لازم است

| # | خواسته | چرا |
|---|---|---|
| 1 | مسیر و متد در `openapi.json` منتشر شود | بدون آن، کاتالوگ نمی‌تواند مسیر را به قرارداد وصل کند و تست کاتالوگ شکست می‌خورد |
| 2 | یک مدل پاسخ اعلام‌شده، نه `additionalProperties: true` | رابط کاربری نمی‌تواند فیلد را تایپ کند و ناچار نام فیلد خام را نمایش می‌دهد (B12) |
| 3 | برای متدهای نوشتنی: احراز هویت و نقش مشخص باشد | ساخت رابط نوشتنی پیش از تعیین نقح، بدهی امنیتی تولید می‌کند (B1 تا B4) |
| 4 | برای هر مقدار: مشخص شود اندازه‌گیری‌شده است یا ثابت | رابط کاربری نمی‌تواند مقدار گزارش‌شده را اندازه‌گیری‌شده معرفی کند (B18) |

## قواعدی که رعایت می‌شود

- تا وقتی بند ۱ برقرار نشده، مسیر در کاتالوگ `unavailable` می‌ماند و صفحه‌ای ساخته نمی‌شود.
- با انتشار هر قرارداد، وضعیت مسیر به‌طور خودکار به `planned` تبدیل می‌شود و وارد فاز ساخت می‌گردد.
- تست `apps/web/src/lib/domains/page-catalog.test.ts` هر endpoint اعلام‌نشده را رد می‌کند، پس این فهرست نمی‌تواند بی‌صدا کهنه شود.

## باقی‌مانده قراردادهای اعلام‌نشده — ۲۰۲۶-۰۹-۲۶

این سند فقط درباره ۱۵۴ مسیر `unavailable` بود. اندازه‌گیری کامل‌تر نشان داد مشکل بزرگ‌تر است: **۳۱۶ مسیر دیگر هم قرارداد دارند ولی قراردادشان چیزی اعلام نمی‌کند.**

| وضعیت قرارداد | تعداد |
|---|---:|
| اعلام‌شده (قابل تایپ) | ۱۱۱ |
| `additionalProperties: true` | ۸۱ |
| `{}` خالی | ۲۵۴ |

### توزیع باقی‌مانده به تفکیک روتر

| روتر | کل | `open` | خالی | مالک |
|---|---:|---:|---:|---|
| `marketplace.py` | ۵۵ | ۰ | ۵۵ | `marketplace` |
| `blockchain.py` | ۲۵ | ۰ | ۲۵ | `platform` |
| `platform.py` | ۲۴ | ۰ | ۲۴ | `platform` |
| `auth.py` | ۲۲ | ۰ | ۲۲ | `security` |
| `science.py` | ۲۰ | ۰ | ۲۰ | `science` |
| `village_hub.py` | ۱۶ | ۹ | ۷ | `marketplace` |
| `legal_texts.py` | ۱۴ | ۴ | ۱۰ | `content-platform` |
| `carbon.py` | ۱۱ | ۰ | ۱۱ | `hydroma` |
| بقیه (۲۲ روتر) | ۱۲۹ | ۶۸ | ۶۱ | متعدد |

### چه چیزی انجام شد و چه چیزی نه

**انجام شد:** ۱۹ روتر رابط + ۵۷ سطح `tool-registry` = **۷۶ مسیر** از حالت بی‌فایده خارج شدند. برای `tool-registry` یک تست قرارداد پنج‌تستی نوشته شد که مدل را به سریالایزر، به schema منتشرشده و به پاسخ زنده قفل می‌کند.

**انجام نشد و چرا:** ۳۱۶ مسیر باقی‌مانده در ۳۰ روتر پخش‌اند و بخش بزرگی از آن‌ها (`auth`، `blockchain`، `compliance`) مسیرهای امنیتی‌اند. اعلام مدل برای این‌ها فقط وقتی درست است که شکل واقعی پاسخ خوانده و آزموده شود؛ حدس زدن مدل یعنی انتشار میدان‌هایی که مسیر برنمی‌گرداند — بدتر از `{}` فعلی. این کار برای هر تیم، با دانش همان دامنه، انجام‌شدنی است.

**قانون:** `ShapeView` در فرانت‌اند می‌ماند تا وقتی قراردادها اعلام شوند.

## فهرست کامل ۱۵۴ مسیر

```
GET    /about
GET    /ai
GET    /ai/ethics
GET    /ai/limits
GET    /design-system
GET    /developers/cookbooks
GET    /prototype
GET    /public/visit-request-submit
GET    /services
GET    /statements
GET    /trust
GET    /trust/sanctions
GET    /market/bazaar-analytics
GET    /market/bazaars/{id}/analytics
GET    /market/bazaars/{id}/disputes
GET    /market/bazaars/{id}/finances
GET    /market/bazaars/{id}/governance
GET    /market/bazaars/{id}/map
GET    /market/bazaars/{id}/settings
GET    /market/bazaars/{id}/stores
GET    /market/bazaars/{id}/supervision
GET    /market/bazaars/{id}/wizard
GET    /market/bazaars/{id}/wizard/step1
GET    /market/bazaars/{id}/wizard/step10
GET    /market/bazaars/{id}/wizard/step2
GET    /market/bazaars/{id}/wizard/step3
GET    /market/bazaars/{id}/wizard/step4
GET    /market/bazaars/{id}/wizard/step5
GET    /market/bazaars/{id}/wizard/step6
GET    /market/bazaars/{id}/wizard/step7
GET    /market/bazaars/{id}/wizard/step8
GET    /market/bazaars/{id}/wizard/step9
GET    /market/categories
GET    /market/categories/{level1}
GET    /market/categories/{level1}/{level2}
GET    /market/categories/{level1}/{level2}/{level3}
GET    /market/checkout/ecowallet
GET    /market/escrow-dispute-arbitration
GET    /market/order-invoice
GET    /market/orders/{id}/evidence
GET    /market/product/{id}/bulk
GET    /market/product/{id}/certifications
GET    /market/product/{id}/compare
GET    /market/product/{id}/eco-impact
GET    /market/product/{id}/pricing-history
GET    /market/product/{id}/qa
GET    /market/product/{id}/reviews
GET    /market/product/{id}/shipping
GET    /market/product/{id}/similar
GET    /market/product/{id}/specs
GET    /market/product/{id}/warranty
GET    /market/search/autocomplete
GET    /market/search/barcode
GET    /market/search/history
GET    /market/search/image
GET    /market/search/nfc
GET    /market/search/semantic
GET    /market/search/suggestions
GET    /market/search/visual
GET    /market/search/voice
GET    /market/stores/create
GET    /market/stores/create/step1
GET    /market/stores/create/step2
GET    /market/stores/{id}
GET    /market/vendor-payouts
GET    /market/{*segments}
POST   /hydroma/tools/aquacrop-runner/execute
POST   /hydroma/tools/carbon-calculator/execute
POST   /hydroma/tools/climate-adaptive-phenology/execute
POST   /hydroma/tools/crop-scenarios/execute
POST   /hydroma/tools/crop-water-requirement/execute
POST   /hydroma/tools/decision-support/execute
POST   /hydroma/tools/dynamic-stress-engine/execute
POST   /hydroma/tools/et0-calculator/execute
POST   /hydroma/tools/gaussian-process-surrogate/execute
POST   /hydroma/tools/groundwater-model/execute
POST   /hydroma/tools/groundwater-service/execute
POST   /hydroma/tools/hecras-simulation/execute
POST   /hydroma/tools/hydrology-fallback/execute
POST   /hydroma/tools/hydrology-fast/execute
POST   /hydroma/tools/hydroma-core/execute
POST   /hydroma/tools/indices-fallback/execute
POST   /hydroma/tools/indices-fast/execute
POST   /hydroma/tools/irrigation-scheduler/execute
POST   /hydroma/tools/modflow6/execute
POST   /hydroma/tools/monte-carlo-scenarios/execute
POST   /hydroma/tools/mrv-iot-ingest/execute
POST   /hydroma/tools/mrv-metrics/execute
POST   /hydroma/tools/mrv-nojin/execute
POST   /hydroma/tools/mrv-quality-assurance/execute
POST   /hydroma/tools/multi-stress-engine/execute
POST   /hydroma/tools/ndvi-analysis/execute
POST   /hydroma/tools/optimization-optimizer/execute
POST   /hydroma/tools/physics-informed-network/execute
POST   /hydroma/tools/rothc-runner/execute
POST   /hydroma/tools/scenario-manager/execute
POST   /hydroma/tools/seed-optimization/execute
POST   /hydroma/tools/soil-chemistry/execute
POST   /hydroma/tools/soil-degradation-model/execute
POST   /hydroma/tools/soil-health/execute
POST   /hydroma/tools/soil-pedotransfer/execute
POST   /hydroma/tools/soil-physics-fallback/execute
POST   /hydroma/tools/soil-physics-fast/execute
POST   /hydroma/tools/soil-physics/execute
POST   /hydroma/tools/soil-recommendations/execute
POST   /hydroma/tools/soil-salinity/execute
POST   /hydroma/tools/soil-taxonomy/execute
POST   /hydroma/tools/soil-texture/execute
POST   /hydroma/tools/soil-water-retention/execute
POST   /hydroma/tools/swat-plus/execute
POST   /hydroma/tools/swat-runner/execute
POST   /hydroma/tools/topographic-calculations/execute
POST   /hydroma/tools/uncertainty-knowledge/execute
POST   /hydroma/tools/water-quality/execute
POST   /hydroma/tools/watershed-calculator/execute
POST   /hydroma/tools/weap-simulation/execute
POST   /hydroma/tools/what-if-engine/execute
GET    /hydroma/tools/{toolId}
GET    /admin/audit-trail
GET    /admin/automation-runs
GET    /admin/channel-health
GET    /admin/message-catalogue-sync
GET    /research/experiments/experiment-approval
GET    /research/experiments/experiment-citations
GET    /research/experiments/experiment-dataset
GET    /research/experiments/experiment-run
GET    /research/experiments/lab-protocol
GET    /research/experiments/review-queue
GET    /system/incident-timeline
GET    /system/migration-runner
GET    /system/queue-inspector
GET    /workspace/audit
GET    /workspace/operations/events
GET    /workspace/report-export
GET    /workspace/target-progress
GET    /accessibility
GET    /account/session
GET    /auth/login
GET    /auth/signup
GET    /inclusive/sms-delivery-receipt
GET    /inclusive/ussd-session-audit
GET    /inclusive/voice-call-record
GET    /offline
GET    /simple
GET    /learn/assessment-submission
GET    /learn/certificate-verify
GET    /learn/course-enrolment
GET    /learn/library-checkout
GET    /learn/video-caption-pack
GET    /learn/video-progress
GET    /public/education/certifications
GET    /public/education/courses
GET    /public/education/video-player
GET    /public/education/workshops
```
