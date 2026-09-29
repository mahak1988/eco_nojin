# تحقیق پلتفرم‌های متن‌باز و خودمیزبان با قابلیت سفیدبرند — اکو نوژین

| | |
|---|---|
| **شناسهٔ سند** | `WHITE-LABEL-2026-09-29` |
| **نسخه** | ۱٫۰ |
| **تاریخ تحقیق** | ۱۴۰۴/۰۷/۰۸ (۲۰۲۶-۰۹-۲۹) |
| **پرسش** | چه پلتفرم‌هایی اجازه می‌دهند ما **واسط** باشیم: کاربر نهایی هرگز رابط ارائه‌دهنده را نبیند، و ما روی منطق، ظاهر و داده کنترل کامل داشته باشیم؟ |
| **روش** | خواندن مستقیم فایل‌های `LICENSE` در `raw.githubusercontent.com` + مستندات رسمی |
| **سند مکمل** | `COST_OPTIMIZATION_RESEARCH_FA.md` (چرا اصلاً؟) |

---

## ۱. خلاصهٔ اجرایی

**بله وجود دارد — اما یک الگوی تکرارشونده دارد که باید قبل از هر تصمیمی بدانید:**

> **تقریباً در همهٔ محصولات متن‌باز، «قابلیت سفیدبرند کردن» دقیقاً همان چیزی است که متن‌باز نیست.**

هستهٔ محصول MIT است، اما کنترل برندینگ در `ee/` (پولی)، در افزونهٔ جداگانه (پولی)، فقط در نسخهٔ ابری، یا — بدتر — **به‌صراحت ممنوع** است. این یک تصادف نیست؛ مدل کسب‌وکار است. سازنده در حال فروش دقیقاً همان چیزی است که شما می‌خواهید رایگان بگیرید.

**سه استثنای واقعی که در این تحقیق پیدا شد:**

| گزینه | چرا متفاوت است |
|---|---|
| **Flagsmith** (BSD-3) | هیچ `ee/` در مخزن اصلی نیست. هیچ دروازهٔ برندینگی مستند نشده |
| **Unleash** (AGPL-3.0) | اصلاً رابط کاربری رو به کاربر ندارد. کاربر شما هرگز Unleash را نمی‌بیند چون Unleash چیزی برای نمایش ندارد |
| **MapLibre + Martin + pg_tileserv** (BSD-3 / Apache-2.0) | کتابخانه و سرور هستند، نه محصول. برندینگ از پیش مال شماست |

**سه رد قطعی که باید ثبت شوند** (بخش ۳).

---

## ۲. چرا این موضوع به بحث هزینه گره خورده است

در `COST_OPTIMIZATION_RESEARCH_FA.md` ثابت کردیم که مانیفست استقرار حدود **۴٬۷۹۷ دلار ماهانه** هزینه دارد و هدف بازبینی‌شده **۱۵۰ دلار** است.

سرویس مدیریت‌شده دو مشکل هم‌زمان می‌سازد:

1. **هزینهٔ تکرارشونده به ازای کاربر** (هر ۱٬۰۰۰ MAU، هر ۱ ترابایت، هر تماس API)
2. **قفل‌شدگی به رابط ارائه‌دهنده** — کاربر شما در `*.supabase.co`، `*.clerk.accounts.dev` یا صفحهٔ پرداخت آن‌ها زندگی می‌کند

خودمیزبانی هر دو را حل می‌کند **اما یک هزینهٔ پنهان دارد: هزینهٔ عملیاتی انسانی.** این عدد در سند هزینهٔ قبلی نبود و باید صریح گفته شود.

> **هشدار صداقت:** ارزان‌ترین زیرساخت لزوماً ارزان‌ترین کل نیست. یک خوشهٔ ۲۰۰ دلاری که هر ماه ۴۰ ساعت زمان مهندس می‌خواهد، از یک سرویس ۲۵ دلاری گران‌تر است. هر پیشنهاد زیر باید با این معادله سنجیده شود.

---

## ۳. تله‌های مجوزی — مهم‌ترین بخش این سند

این‌ها را **قبل** از هر انتخابی بخوانید. چهار موردی که در پروژهٔ شما بلافاصله موضوعیت دارند:

### ۳٫۱ Sharetribe — رد قطعی (و برای شما شخصی است)

```
شما یک واسط هستید. این دقیقاً همان چیزی است که این مجوز منع می‌کند.
```

متن بند ۱٫۱ لایسنس، تأییدشده از فایل خام مخزن:

> *"The licensed rights **exclude** the right to make the Software available as a software-as-a-service or platform-as-a-service where **You host the Software for multiple clients** or other similar online services that compete with Sharetribe products or services…"*

و در مقدمه:
> *"Sharetribe wants to control the making available the Software as a service (SaaS). **This is why Sharetribe excludes the right to offer the Software as a service with this license.**"*

بنام «Sharetribe» و لوگو نیز علائم تجاری محفوظ آن‌هاست. **این تنها موردی است در کل تحقیق است که مجوز صریحاً مدل کاری شما را نام می‌برد و رد می‌کند.**

منبع: `https://raw.githubusercontent.com/sharetribe/sharetribe/master/LICENSE`

### ۳٫۲ Countly Lite — منع صریح حذف برند

لایسنس: **AGPL-3.0 با بخش ۷ اصلاح‌شده**:

> *"You **cannot remove any Countly logo or branding** either from source code or user interface… All names, links and logos of Countly must be kept as in original distribution without any changes in all software screens… There are **tight and enforcing restrictions** on your ability to modify, change or remove Countly name and logo."*

تنها قابلیتی که نیاز دارید، همان قابلیتی است که مجوز نام می‌برد و منع می‌کند.

### ۳٫۳ Typebot — خودِ مستندات، مدل شما را رد می‌کنند

لایسنس: **FSL-1.1-Apache-2.0**. مستندات رسمی:

> ❌ *"Commercialize the access to your instance"* · ❌ *"Offer services for hosting Typebot instances"*
> ✅ *"As a company, create and publish your bot into your client-facing products"*

یعنی: استفاده در محصول خودتان ✅، ارائهٔ سرویس میزبانی برای مشتریان ❌.

> ⚠️ **نشانهٔ هشدار:** بنر README هنوز «AGPLv3» را نشان می‌دهد در حالی که فایل لایسنس FSL-1.1 است. **همیشه فایل را بخوانید، نه بنر را.**

### ۳٫۴ Plausible CE و PostHog — «سفیدبرند» فقط در نسخهٔ پولی

| محصول | جایی که سفیدبرند ارائه می‌شود |
|---|---|
| **Plausible** | داشبورد جاسازی‌شده و Stats API = پلن **Business/Enterprise**. نسخهٔ Community Edition صریحاً **Sites API ندارد** — یعنی ابزار ایجاد سایت به‌ازای هر مشتری موجود نیست |
| **PostHog** | صفحهٔ رسمی «چه چیزی را از دست می‌دهید»، «White labeling» را زیر **Platform packages → Teams** فهرست می‌کند. یعنی خارج از build متن‌باز |
| **Formbricks** | «Hide Powered by Formbricks» = ❌ Community / ✅ **Enterprise** |
| **Botpress** | نمایشکنندهٔ چت بدون برند = پلن **Plus با ۱۵۰ دلار در ماه**. نسخهٔ خودمیزبان قدیمی (v12) بازنشسته شده |

### ۳٫۵ تله‌های copyleft

| محصول | لایسنس | اثر بر شما |
|---|---|---|
| **Zitadel** | AGPL-3.0 | اگر تغییر دهید و کاربران از راه شبکه تعامل کنند، **باید کد متناظر را به آن کاربران ارائه دهید** (§13) |
| **Hanko** | AGPL-3.0 (بک‌اند) + MIT (فرانت‌اند) | طراحی هوشمندانه: لایهٔ UI که به کاربر نشان می‌دهید MIT است. فقط بک‌اند AGPL |
| **Formbricks** | AGPLv3 هسته + لایسنس اختصاصی در `ee/` | همان مسئلهٔ §13 |
| **Unleash** | AGPL-3.0 | اگر آن را **به‌عنوان سرویس** اجرا کنید، §13 شما را ملزم می‌کند |
| **Vendure** | GPLv3 / VCL | رد بدون توافق تجاری |
| **PostGIS** | GPL v2 | **مشکلی ندارد** — به‌عنوان افزونهٔ Postgres در سرویس جدا اجرا می‌شود، توزیع نمی‌شود |
| **QGIS Server** | GPLv2+ | همان — سرویس جداست |

> **تفاوت مهم GPL با AGPL:** GPL کد را هنگام **توزیع** منتشر می‌کند؛ AGPL هنگام **تعامل شبکه‌ای**. برای یک واسط تجاری که سرویس را روی سرور خودش اجرا می‌کند، GPL بی‌خطر است و AGPL خطرناک. این تفاوت، تعیین‌کنندهٔ اصلی در همهٔ جدول‌های زیر است.

---

## ۴. احراز هویت و هویت

### جدول مقایسه

| پلتفرم | لایسنس | خودمیزبان | UI کاملاً قابل جایگزینی | OIDC | SCIM | Passkey | حداقل زیرساخت | مانع اصلی |
|---|---|---|---|---|---|---|---|---|
| **Ory Kratos + Hydra** | Apache-2.0 | ✅ با هشدار | ✅ **سریس‌لس** | با Hydra (سرویس دوم) | 💰 پولی | تأییدنشده | Postgres/MySQL/CockroachDB | لایسنس سازمانی، SCIM و SAML و وصلهٔ CVE را پولی می‌کند |
| **Hanko** | AGPL بک‌اند / **MIT** UI | ✅ | ✅ **Flow API + راهنمای کامل** | ✅ | تأییدنشده | ✅ **قوی‌ترین** | Postgres/MySQL + **SMTP الزامی** | AGPL روی بک‌اند |
| **Zitadel** | AGPL-3.0 (Login UI = MIT) | ✅ بالغ | ✅ **fork مستندشده** | ✅ | ✅ | ✅ | **Postgres الزامی** | بار نگهداری fork |
| **Logto** | MPL-2.0 | ✅ | ✅ «Bring your UI» | ✅ OIDC 2.1 | تأییدنشده | 💰 Pro | Postgres | «Bring your UI» و حذف برند **فقط ابری** |
| **Keycloak** | Apache-2.0 | ✅ بهترین‌رده | ❌ فقط پوسته | ✅ | ✅ کامل | ✅ کامل | Postgres | نمی‌توان از رندر JVM خارج شد |
| **Authentik** | MIT هسته / `ee/` اختصاصی | ✅ | ❌ فقط برند و CSS | ✅ | ✅ | تأییدنشده | Postgres+Redis | پوشهٔ `enterprise/` |
| **Casdoor** | Apache-2.0 | ✅ | ❌ ولی CSS و HTML خام تزریق‌پذیر | ✅ | ✅ دوطرفه | WebAuthn ✅ | MySQL/Postgres/SQL Server | طراحی UI-محور |
| **Clerk** | اختصاصی | ❌ | ❌ | ✅ | — | ✅ | فقط SaaS | **خودمیزبان نیست — رد** |

### تحلیل برای اکو نوژین

پروژه **هم‌اکنون** `services/auth/passkeys.py` و `services/api_gateway/routers/passkey_router.py` دارد و `supabase/auth` را پیکربندی کرده. یعنی احراز هویت **ساخته شده**.

**توصیه: فعلاً تعویض نکنید.** دلایل:

1. ساختن دوبارهٔ لایهٔ هویت، پرهزینه‌ترین کار ممکن است و در `INNOVATION_BACKLOG_FA.md` قلم‌های ۱، ۳ و ۹ (W0) اولویت دارند.
2. هیچ‌یک از گزینه‌های بالا بدون هزینهٔ مهاجرت واقعی نیست: Zitadel و Hanko مسیر سریس‌لس دارند ولی هر دو یا AGPL یا نیازمند SMTP و پیکربندی WebAuthn هستند.
3. هیچ‌یک هزینهٔ ماهانهٔ سنگینی ندارند که Supabase در حال حاضر ایجاد کند (Pro = ۲۵ دلار، شامل ۱۰۰٬۰۰۰ MAU).

**اما یک تصمیم باید گرفته شود:** قلم ۳۸ بانک نوآوری (W3C Verifiable Credentials برای هویت کشاورز) به یک لایهٔ هویت **قابل‌کنترل** نیاز دارد. اگر آن قلم جدی گرفته شود، **اکنون زمان تصمیم است، نه بعد از ساخت** — چون مهاجرت هویت پس از صدور VC تقریباً غیرممکن است.

> **نکتهٔ کلیدی:** اگر «استفادهٔ فعلی از Supabase Auth» را نگه می‌دارید، `Vision` و لایسنس‌های این جدول برای شما بی‌اثرند. ارزش واقعی‌شان در **سناریوی خروج از Supabase** است.

---

## ۵. پیام‌رسانی، چت و اعلان

| پلتفرم | لایسنس | API فقط؟ | برند | حداقل زیرساخت | وضعیت |
|---|---|---|---|---|---|
| **Novu** | **MIT** (تمام مخزن) | ✅ چندکاناله: ایمیل، داخل‌برنامه‌ای، SMS، Push، Chat | ⚠️ حذف برند = پلن Pro؛ ولی چون MIT است، **از نظر حقوقی مجاز** | MongoDB + Redis، حدود ۸ گیگ رم | **قوی‌ترین گزینهٔ MIT** |
| **Chatwoot** | MIT هسته / `enterprise/` اختصاصی | ✅ **Client API** = رابط چت کاملاً سفارشی | ⚠️ **تأییدنشده** | Postgres(pgvector) + Redis + Sidekiq | قوی، ولی برندینگ را باید مستقیم بپرسید |
| **HeyForm** | AGPL-3.0 | ✅ وب‌هوک | تأییدنشده | MongoDB + KeyDB | جایگزین Typeform |
| **OhMyForm** | AGPL-3.0 | — | — | — | ❌ **بایگانی‌شده ۲۰۲۴-۱۰-۳۱** |
| **Papercups** | MIT | ✅ | ✅ | Elixir + Postgres | ⚠️ حالت نگهداری |
| **Botpress** | v12 = AGPL؛ مخزن فعلی محصول نیست | ❌ | 💰 Plus ۱۵۰ دلار/ماه | — | ❌ بازنشسته |
| **Typebot** | FSL-1.1 | ✅ | ✅ | Postgres | ❌ **مدل واسط ممنوع** |

### تحلیل

پروژه `services/notification/`، `services/bots/` و `services/telegram_bot/` دارد — یعنی **اعلان را از قبل ساخته‌اید**. و `services/bots/adapters/whatsapp.py` و `telegram.py` نشان می‌دهد که الگوی «آداپتور چندکاناله» را عملاً پیاده کرده‌اید.

**Novu دقیقاً همان معماری است** با لایسنس MIT. اگر روزی به **ایمیل و SMS مقیاس‌پذیر** نیاز پیدا کردید، مهاجرت معنا دارد. امروز — **نه**.

> **`Chatwoot` برای قابلیت ۲۱ بانک نوآوری جالب است** (مشارکت با بیمه): مکالمهٔ پشتیبانی با کشاورز. `Client API` دقیقاً الگوی سفیدبرند را می‌دهد. ولی **قبل از هر تصمیمی، وضعیت مجوز برندینگ را مستقیم از آن‌ها بپرسید** — سایتشان در جریان تحقیق در دسترس نبود.

---

## ۶. تحلیل محصول، پرچم‌های قابلیت و گزارش

| پلتفرم | لایسنس | UI رو به کاربر | دروازهٔ برند | هزینهٔ خودمیزبانی | وضعیت |
|---|---|---|---|---|---|
| **Flagsmith** | **BSD-3** | ندارد | ❌ هیچ‌کدام | Django + Postgres (+ Redis) | **بهترین لایسنس — بدون ریسک** |
| **Unleash** | AGPL-3.0 | **اصلاً ندارد** | ❌ هیچ‌کدام | Postgres + Node | **بهترین معماری** |
| **Umami** | **MIT** | ندارد | تأییدنشده | **فقط Postgres** | ارزان‌ترین |
| **GrowthBook** | MIT هسته / ۳ پوشهٔ اختصاصی | ندارد | تأییدنشده | MongoDB + ۱ کانتینر | سبک، SDK گسترده |
| **Matomo** | **GPL-3.0** (نه AGPL) | دارد | 💰 افزونهٔ WhiteLabel (حدود ۱۷۹ دلار/سال) | PHP + MySQL | **بهترین مکانیزم**، ولی پولی |
| **Formbricks** | AGPLv3 / `ee/` | ندارد | 💰 Enterprise | Postgres + Redis | |
| **Plausible CE** | AGPL | دارد | 💰 **Sites API ندارد** | ClickHouse + برنامه | ❌ **برای چندمستاجری نامناسب** |
| **PostHog** | MIT هسته | ندارد | 💰 Teams | **۴ vCPU / ۱۶GB رم / ۳۰GB+ دیسک** | ❌ گران‌ترین آیتم کل تحقیق |
| **Countly Lite** | AGPL + بخش ۷ | ندارد | ❌ **ممنوع صریح** | Mongo + Node | ❌ رد قطعی |
| **OpenFeature** | Apache-2.0 | ندارد | ندارد | **هیچ** | **لایهٔ انتزاعی، نه محصول** |

### چرا `Unleash` معماری‌ترین است

> *"API-first: everything can be automated. No exceptions."* و مهم‌تر:
> *"no end-user data leaves your infrastructure when you use server-side SDKs"*

**Unleash هیچ رابط کاربری رو به کاربر نهایی ندارد.** کاربر شما هرگز آن را نمی‌بیند، چون چیزی برای نمایش وجود ندارد. تنها رابط، پنل مدیریتی است که مال شماست.

### چرا `Flagsmith` بی‌خطرترین است

**BSD-3-Clause، بدون copyleft، بدون `ee/` در مخزن اصلی.** از نظر حقوقی هیچ محدودیتی برای یک واسط تجاری ندارد. علاوه بر این، شراکت رسمی با **OpenFeature** دارد — یعنی می‌توانید یک قرارداد ارزیابی واحد به مشتریانتان بدهید و بعداً backend را عوض کنید.

### توصیهٔ عملی برای اکو نوژین

قلم ۹۳ بانک نوآوری (feature flag و رول‌آوت تدریجی، W0) و قلم ۱۰۱ (برنامهٔ A/B، W0) هر دو نیاز به پرچم قابلیت دارند.

**پیشنهاد: پرچم قابلیت را با `OpenFeature` بسازید، پشت آن `Flagsmith` (خودمیزبان) بگذارید.**

- OpenFeature یک **مشخصات** است (Apache-2.0)، نه محصول — بدون هزینهٔ زیرساخت و بدون ریسک برند
- Flagsmith پشت آن عوض می‌شود، بدون تغییر در کد فرانت‌اند
- هر دو در `apps/web` قابل ادغام‌اند

این کار هم قلم ۹۳ را حل می‌کند، هم زیرساخت قلم ۱۰۱ را می‌سازد، هم یک لایهٔ انتزاعی می‌سازد که به شما اجازه می‌دهد بعداً به LaunchDarkly مهاجرت کنید اگر لازم شد.

---

## ۷. پرداخت و تجارت

### ۷٫۱ سکوهای تجارت

| پلتفرم | لایسنس | فروشگاه کاملاً سفارشی | وضعیت |
|---|---|---|---|
| **Medusa** | **MIT هسته** ⚠️ open-core | ✅ مستند: فروشگاه «جدا از برنامه نصب، ساخته و میزبانی می‌شود» | 🥇 |
| **Saleor** | **BSD-3** پاک | ✅ GraphQL؛ ساخت Payment App که gateway نامرئی است | 🥈 |
| **Solidus** | BSD-3 پاک | ✅ | 🥉 |
| **Vendure** | ⚠️ GPLv3 / VCL | ✅ | ❌ بلاک مجوز |
| **Sharetribe** | ⚠️ **اصلاً متن‌باز نیست** | ✅ | ❌ **بلاک مجوز — بخش ۳٫۱** |

**دربارهٔ Medusa، نکتهٔ ظریف:** هسته MIT است، ولی `ENTERPRISE-LICENSE.md` قابلیت‌های **RBAC** و **OIDC/SSO** را به‌عنوان «Enterprise Materials» اختصاصی اعلام می‌کند:

> *"Enabling any Enterprise feature flag constitutes a representation that you hold a valid commercial agreement."*

**همهٔ ماژول‌های پرداخت، سبد و سفارش MIT هستند.** یعنی می‌توانید از Medusa استفاده کنید و RBAC/SSO را خاموش نگه دارید.

### ۷٫۲ ارکستریتورهای پرداخت

| پلتفرم | لایسنس | سرتاسر بی‌رابط؟ | وضعیت |
|---|---|---|---|
| **Hyperswitch** (juspay) | **Apache-2.0** | ✅ مستند: *«Build advanced integration — Use our headless SDK to have full control over your checkout… in a decoupled architecture»* | 🥇 تنها گزینهٔ OSS با سرتاسر بی‌رابط |
| **Gr4vy** | SaaS | ✅ Secure Fields در رابط خودتان، PCI SAQ A | بهترین داستان SaaS، ولی گیت‌وی ایران ندارد |
| **Spreedly** | SaaS | ✅ iFrame API | ⚠️ از **۷۵۰ دلار ماهانه** فقط برای Vault |
| **Primer** | SaaS | تأییدنشده | دسترسی به مستندات قطع بود |

### ۷٫۳ گیت‌وی‌های ایرانی — یک محدودیت ساختاری

**هیچ‌کدام متن‌باز نیستند.** ZarinPal، Zibal، IDPay و NextPay همگی PSP تجاری تحت نظارت شاپرک/بانک مرکزی‌اند.

| گیت‌وی | API رسمی | متن‌باز؟ | می‌شود صفحهٔ ارائه‌دهنده را حذف کرد؟ |
|---|---|---|---|
| **ZarinPal** | ✅ REST v4 | ❌ فقط SDK منتشر می‌کند | ⚠️ «ZarinGate» دارد ولی **افزونهٔ پولی** است. پیش‌فرض = ریدایرکت |
| **Zibal** | ✅ `POST https://gateway.zibal.ir/v1/request` | ❌ | ❌ همهٔ افزونه‌ها ریدایرکت‌محورند |
| **IDPay** | تأییدنشده (سایت در دسترس نبود) | ❌ | تأییدنشده |
| **NextPay** | تأییدنشده (HTTP 522) | ❌ | تأییدنشده |

> **نتیجهٔ ساختاری مهم:** شما **نمی‌توانید** صفحهٔ پرداخت را مثل Stripe Elements حذف کنید. لایهٔ PSP تحت نظارت قانونی، خودش آن لایه است.
>
> **راه‌حل عملی:** یک **پوستهٔ checkout با برند خودتان** بسازید که صفحات قبل و بعد از ریدایرکت را کنترل کند. صفحهٔ میانی متعلق به PSP است — این در ایران اجتناب‌ناپذیر است و در نگاه کاربر به محصول شما همچنان «سفیدبرند» به نظر می‌رسد.

### ۷٫۴ افزونهٔ ایرانی وجود ندارد — باید بسازید

جست‌وجو در مخزن Medusa برای «zarinpal» → **۰ نتیجه**. در npm برای افزونهٔ پرداخت Medusa → بدون ZarinPal، IDPay یا Zibal.

**قطعه‌های ساختمانی تأییدشده:**

| کتابخانه | لایسنس | زبان |
|---|---|---|
| `siamak/zarinpal-checkout` | MIT | TypeScript |
| `GoFarsi/paygap` | **Apache-2.0** | Go — zarinpal + idpay + pay.ir با هم |
| `evryn/laravel-toman` | MIT | Laravel |

نقطهٔ اتصال: `AbstractPaymentProvider` از `@medusajs/framework/utils`.

**نکتهٔ صادقانه:** کد فعلی `services/marketplace/payments_service.py` **قبلاً** این کار را تا حدی انجام داده — `ZARINPAL_PAY_URL`، `ZARINPAL_VERIFY_URL`، sandbox، و callback. یعنی لایهٔ یکپارچهٔ درون‌ساخت **از قبل وجود دارد**.

> **توصیه:** فعلاً Medusa را وارد نکنید. `payments_service.py` فعلی کار می‌کند و `S-MONEY` دارد. انتقال به Medusa یک پروژهٔ بزرگ است که باید با یک نیاز واقعی توجیه شود — نه با یک بحث معماری.

---

## ۸. داده‌های مکانی، نقشه و پردازش تصویر ماهواره‌ای

این دسته **هیچ تلهٔ مجوزی ندارد.** همه متن‌باز با لایسنس‌های سازگار.

| ابزار | لایسنس | نقش | سفیدبرند؟ |
|---|---|---|---|
| **MapLibre GL JS** | **BSD-3** | موتور رندر نقشه | ✅ کامل |
| **Martin** (maplibre/martin) | **Apache-2.0** | سرور کاشی برداری (Rust) | ✅ کامل — **بهترین نسبت کارایی/پیچیدگی** |
| **Tegola** | **MIT** | سرور کاشی (Go) | ✅ کامل |
| **tileserver-gl** | BSD-2 | کاشی رستری + برداری + PMTiles | ✅ کامل |
| **maplibre-native** | BSD-2 | رندر آفلاین موبایل | ✅ **برای قابلیت ۵ بانک نوآوری حیاتی** |
| **pg_tileserv** | **Apache-2.0** | سرو PostGIS به‌صورت کاشی | ✅ **بهترین گزینه برای پلیگون قطعات زمین** |
| **PostGIS** | ⚠️ GPL v2 | افزونهٔ Postgres | ✅ سرویس جداست، توزیع نمی‌شود |
| **QGIS Server** | ⚠️ GPLv2+ | WMS/WFS/WCS/WMTS + OGC API | ✅ پارامتر `SLD_BODY` اجازهٔ استایل درخواستی می‌دهد |
| **stac-fastapi** | **MIT** | ساخت API سازگار با STAC | ✅ |
| **pgSTAC** | **MIT** | انبار متادata فضایی-زمانی | ✅ |
| **stac-geoparquet** | **MIT** | STAC به‌صورت GeoParquet | ✅ **برای تحویل به خریدار کربن** |
| **openEO** (کلاینت پایتون) | **Apache-2.0** | استاندارد تحلیل دادهٔ فضایی | ✅ |
| **Sen2Agri / Sen4CAP** | ⚠️ GPLv3 + وابستگی R AGPLv3 | پایش سطح CAP اروپا | ❌ سنگین، منسوخ (۲۰۲۰)، غیرمنطقه‌ای |
| **Terracube** | — | — | ❌ **مخزن ۴۰۴، مرده** |

### چرا STAC برای کسب‌وکار کربن شما مهم است

خریداران بین‌المللی (Verra، Gold Standard) از کاتالوگ‌های سازگار با STAC برای دادهٔ مشاهده از زمین استفاده می‌کنند. ارائهٔ شاخص‌های مشتق‌شده از Sentinel/Landsat شما از طریق STAC API روی pgSTAC:

- یک **نشانهٔ اعتبار** برای خریدار سازمانی است
- دادهٔ شما را برای ماشین کشف‌پذیر می‌کند
- نصبش حدود **۳۰ دقیقه** است (`stac-fastapi` + `stac-fastapi-pgstac`)

> **این با قلم ۴۹ بانک نوآوری هم‌راستا است** (STAC کامل) و با `services/satellite/sentinel2_provider.py` که همین حالا به Planetary Computer STAC وصل می‌شود کار می‌کند.

### Qdrant در برابر pgvector — صرفه‌جویی

پروژه `services/ai/unified_rag.py` از **Qdrant** استفاده می‌کند و `render.yaml` متغیرهای `QDRANT_URL` و `QDRANT_API_KEY` دارد.

| | Supabase pgvector | Qdrant |
|---|---|---|
| لایسنس | مجوز PostgreSQL (بی‌پایبند) | Apache-2.0 |
| هزینهٔ حاشیه‌ای | **~۰** — از قبل در پشتهٔ شماست | سرویس جدا + مقیاس‌پذیری + پشتیبان مستقل |
| بار عملیاتی | **صفر** | سرویس جدا با تنظیم HNSW |
| مناسب برای | تا چند میلیون بردار، SQL و بردار در یک پرس‌وجو | ۱۰۰ میلیون+ بردار |

**توصیه: به `pgvector` Supabase منتقل شوید و سرویس Qdrant را حذف کنید.** این کار:

- یک سرویس کمتر (صرفه‌جویی عملیاتی)
- یک رابط کمتر برای نگهداری
- هزینهٔ حاشیه‌ای صفر

`pgvector` در پلن Pro از قبل شامل است (۸ گیگابایت دیسک). RAG روی مستندات کشاورزی و فرادادهٔ قطعات، نه بار پرتراکم است و نه حجیم. Qdrant فقط وقتی توجیه می‌شود که از ۸ گیگابایت عبور کنید یا ایندکس GPU بخواهید.

> **نکته:** این تغییر را در `INNOVATION_BACKLOG_FA.md` به‌عنوان یک قلم جدید یا ادغام در قلم ۳۰ (LLM به‌عنوان رابط موتور) ثبت کنید.

---

## ۹. معماری پیشنهادی

### لایهٔ انتزاعی — اصل حاکم

> **هیچ قابلیتی را مستقیم به API یک ارائه‌دهنده وصل نکنید. یک واسط داخلی بسازید و پشت آن عوض کردن را ممکن کنید.**

پروژه `services/ai/llm_router.py` **قبلاً همین الگو را پیاده کرده** — بین پنج ارائه‌دهندهٔ LLM مسیریابی می‌کند. این یک نقطهٔ قوت واقعی است که باید گسترش یابد.

پیشنهاد ساختار:

```
services/_contracts/          ← قابلیت‌های ثابت (money.py, formula.py موجود)
services/adapters/            ← یک آداپتور برای هر ارائه‌دهنده
    auth/        supabase | zitadel | hanko
    payment/     zarinpal | hyperswitch | manual
    vector/      pgvector | qdrant
    flags/       flagsmith | unleash
    analytics/   umami | duckdb
    chat/        novu | chatwoot
```

هر آداپتور:
- رابط یکسان پیاده می‌کند
- قابل تعویض است با feature flag
- هزینهٔ سوییچ دارد، نه هزینهٔ بازنویسی

> **این دقیقاً همان چیزی است که `INNOVATION_BACKLOG_FA.md` قلم ۱۵ (مهار سطح) و قلم ۲۴ (مرز نوع) می‌خواهند.** مهار سطح فقط وقتی ارزش دارد که ۵۷ سرویس پشت چند واسط سازمان‌دهی شوند.

---

## ۱۰. نگاشت به وضعیت فعلی مخزن

| نیاز پروژه | وضعیت فعلی | پلتفرم پیشنهادی | اقدام |
|---|---|---|---|
| احراز هویت + passkey | `supabase/auth` + `passkeys.py` | Zitadel یا Hanko | **تعویض نکنید.** فقط اگر قلم ۳۸ جدی شد |
| پرداخت ایرانی | `payments_service.py` (ZarinPal) | درون‌ساخت | **همین حالا درست است** |
| پرداخت بین‌المللی | `finance/payment_provider.py` (اسکلت) | Hyperswitch (Apache-2.0) | اگر بازار کربن بین‌المللی فعال شد |
| بردار RAG | **Qdrant** | **pgvector** | ✅ **انتقال توصیه می‌شود** — صرفه‌جویی |
| پرچم قابلیت | فقط `ENABLE_*` در settings | Flagsmith + OpenFeature | ✅ قلم ۹۳ و ۱۰۱ |
| چت پشتیبانی | ندارد | Chatwoot (بعد از تأیید برند) | اگر قلم ۸۳ فعال شد |
| اعلان | `services/notification/` | Novu | اگر ایمیل/SMS مقیاس خواست |
| کاشی نقشه | `services/map_engine` | Martin + pg_tileserv | ✅ بدون ریسک |
| STAC | `scripts/fetch_stac.py` | stac-fastapi + pgSTAC | ✅ قلم ۴۹ |
| آفلاین موبایل | PWA | maplibre-native | ✅ قلم ۵ |

---

## ۱۱. چهار توصیهٔ نهایی

### ۱. همین حالا: `Qdrant` → `pgvector`

تنها تغییری که هم هزینه را کم می‌کند، هم سطح را. یک سرویس کمتر، یک رابط کمتر، هزینهٔ حاشیه‌ای صفر.

### ۲. برای قلم‌های ۹۳ و ۱۰۱: `OpenFeature` + `Flagsmith`

لایسنس BSD-3 بدون ریسک، OpenFeature به‌عنوان لایهٔ انتزاعی، و مستقیماً هر دو قلم W0 را حل می‌کند.

### ۳. برای دسترسی‌پذیری: `stac-fastapi` + `pgSTAC` + `Martin` + `pg_tileserv`

همه MIT یا Apache-2.0، همه کاملاً سفیدبرند، و مستقیماً به قلم ۴۹ و قلم‌های ۱۲ و ۵ کمک می‌کنند. هیچ مانعی ندارد.

### ۴. تصمیم هویت را به تعویق بیندازید — ولی ثبتش کنید

هیچ‌یک از پلتفرم‌های احراز هویت هم‌اکنون صرفه‌جویی مالی نمی‌کنند. **اما** اگر قلم ۳۸ (W3C VC برای هویت کشاورز) جدی گرفته شود، مهاجرت بعد از صدور VC تقریباً غیرممکن است. تصمیم را **قبل** از آن قلم بگیرید، نه بعد.

---

## ۱۲. آنچه نتوانستم تأیید کنم

مطابق اصل صداقت (`ENGINEERING_INDEX_FA.md §۴٫۳`):

| مورد | وضعیت |
|---|---|
| وضعیت مجوز برندینگ **Chatwoot** | سایت در دسترس نبود. **قبل از تصمیم مستقیم بپرسید** |
| اینکه Novu مجوز حذف برند را برای واسط تجاری بدون قرارداد می‌پذیرد | کد MIT است، پس از نظر حقوقی مجاز. **رفتارشان تأییدنشده** |
| **API رسمی** IDPay و NextPay | سایت‌ها در دسترس نبودند (خطای شبکه) |
| داشبورد برند Umami / GrowthBook / Flagsmith | هیچ بیانیهٔ رسمی سفیدبرند پیدا نشد. باید با مطالعهٔ کد فرانت تأیید شود |
| پشتیبانی passkey در Kratos نسخهٔ OSS | تأییدنشده |
| **همهٔ مستندات SuperTokens** | سایت کاملاً مسدود بود. کمترین اطمینان از همهٔ موارد |
| ویژگی‌های `Passkey` در Logto نسخهٔ OSS | passkey پرچم پلن Pro است؛ وضعیت OSS تأییدنشده |
| قیمت دقیق Gr4vy | صفحهٔ قیمت ۴۰۴ داد |

**توصیهٔ فرایندی:** قبل از هر تصمیمی، یک **آزمون مفهومی (PoC)** دو ساعته انجام دهید: نمونه نصب کنید، یک مسیر کامل را با UI خودتان طی کنید، و ببینید آیا جایی مجبور می‌شوید برند آن‌ها را نشان دهید.

---

## ۱۳. منابع

### فایل‌های لایسنس (تأیید مستقیم، ۲۰۲۶-۰۹-۲۹)

```
https://raw.githubusercontent.com/sharetribe/sharetribe/master/LICENSE          ← بند 1.1، منع SaaS چندمشتری
https://raw.githubusercontent.com/medusajs/medusa/develop/LICENSE               ← MIT با استثنای Enterprise
https://raw.githubusercontent.com/medusajs/medusa/develop/ENTERPRISE-LICENSE.md
https://raw.githubusercontent.com/saleor/saleor/main/LICENSE                     ← BSD-3
https://raw.githubusercontent.com/solidusio/solidus/main/LICENSE                 ← BSD-3
https://raw.githubusercontent.com/vendure-ecommerce/vendure/master/LICENSE.md    ← GPLv3
https://raw.githubusercontent.com/juspay/hyperswitch/master/LICENSE             ← Apache-2.0
https://raw.githubusercontent.com/Countly/countly-server/master/LICENSE.md       ← AGPL + بخش 7 اصلاح‌شده
https://raw.githubusercontent.com/medusajs/medusa/develop/LICENSE
https://raw.githubusercontent.com/typebot-io/typebot.io/main/LICENSE            ← FSL-1.1
https://raw.githubusercontent.com/novuhq/novu/main/LICENSE                      ← MIT
https://raw.githubusercontent.com/chatwoot/chatwoot/develop/LICENSE             ← MIT + enterprise/
https://raw.githubusercontent.com/Flagsmith/Flagsmith/main/LICENSE.md           ← BSD-3
https://raw.githubusercontent.com/Unleash/unleash/main/LICENSE                  ← AGPL-3.0
https://raw.githubusercontent.com/umami-software/umami/master/LICENSE           ← MIT
https://raw.githubusercontent.com/teamhanko/hanko/main/LICENSE
https://raw.githubusercontent.com/zitadel/zitadel/main/LICENSE                  ← AGPL-3.0
https://raw.githubusercontent.com/keycloak/keycloak/main/LICENSE.txt            ← Apache-2.0
https://raw.githubusercontent.com/logto-io/logto/master/LICENSE                 ← MPL-2.0
https://raw.githubusercontent.com/postgis/postgis/master/COPYING                ← GPL v2
https://raw.githubusercontent.com/QGIS/QGIS/master/COPYING                      ← GPLv2+
https://raw.githubusercontent.com/stac-utils/stac-fastapi/main/LICENSE          ← MIT
https://raw.githubusercontent.com/stac-utils/pgstac/main/LICENSE                ← MIT
https://raw.githubusercontent.com/stac-utils/stac-geoparquet/main/LICENSE       ← MIT
https://raw.githubusercontent.com/open-feature/spec/main/LICENSE               ← Apache-2.0
https://raw.githubusercontent.com/maplibre/maplibre-gl-js/main/LICENSE.txt     ← BSD-3
```

### مستندات رسمی

- Hyperswitch — https://docs.hyperswitch.io/integration-guide/payment-experience.md
- Medusa storefront — https://docs.medusajs.com/resources/storefront-development
- Medusa payment provider — https://docs.medusajs.com/resources/commerce-modules/payment/payment-provider
- ZarinPal v4 — https://www.zarinpal.com/docs/v4/
- Zibal — https://zibal.ir/ · https://help.zibal.ir/
- Hanko custom login — https://docs.hanko.io/using-the-api/build-a-custom-login-page
- Zitadel login UI — https://zitadel.com/docs/guides/integrate/login-ui
- Logto OSS limits — https://docs.logto.io/logto-oss
- Logto bring-your-ui — https://docs.logto.io/customization/bring-your-ui
- Plausible self-hosting — https://plausible.io/docs/self-hosting
- PostHog what you lose — https://posthog.com/docs/self-host/open-source/disclaimer
- Unleash pricing — https://www.getunleash.io/pricing
- Matomo white label — https://matomo.org/white-label-analytics/
- Supabase pricing — https://supabase.com/pricing

---

## ۱۴. دفتر ادعا (Claim Ledger)

تست `tests/contract/test_claims_gate.py` این دسته‌بندی را بررسی می‌کند، نه صحت قضاوت را.

```claims
- id: sharetribe-saas-prohibition
  text: "لایسنس Sharetribe ارائهٔ سرویس میزبانی برای چند مشتری را منع می‌کند"
  kind: quoted
  source: "https://raw.githubusercontent.com/sharetribe/sharetribe/master/LICENSE بند ۱٫۱ — بازیابی مستقیم ۲۰۲۶-۰۹-۲۹"

- id: medusa-open-core
  text: "هستهٔ Medusa MIT است ولی RBAC و OIDC به‌عنوان Enterprise Materials اختصاصی‌اند"
  kind: quoted
  source: "https://raw.githubusercontent.com/medusajs/medusa/develop/LICENSE و ENTERPRISE-LICENSE.md — بازیابی ۲۰۲۶-۰۹-۲۹"

- id: countly-branding-prohibition
  text: "لایسنس Countly Lite صراحتاً حذف لوگو و برند را منع می‌کند"
  kind: quoted
  source: "https://raw.githubusercontent.com/Countly/countly-server/master/LICENSE.md بخش ۷ اصلاح‌شده"

- id: typebot-intermediary-prohibition
  text: "مستندات Typebot ارائهٔ سرویس میزبانی را غیرمجاز اعلام می‌کند"
  kind: quoted
  source: "https://docs.typebot.io/self-hosting — بندهای علامت‌خورده با ضربدر"

- id: plausible-ce-lacks-sites-api
  text: "نسخهٔ Community از Plausible فاقد Sites API است که ابزار ایجاد سایت به‌ازای مشتری است"
  kind: quoted
  source: "https://plausible.io/docs/self-hosting و صفحهٔ مقایسهٔ قابلیت‌ها"

- id: posthog-whitelabel-cloud-only
  text: "سفیدبرند کردن در PostHog فقط در بستهٔ Teams ابری موجود است"
  kind: quoted
  source: "https://posthog.com/docs/self-host/open-source/disclaimer فهرست Platform packages"

- id: hyperswitch-apache-headless
  text: "Hyperswitch با مجوز Apache-2.0 حالت headless واقعی دارد"
  kind: quoted
  source: "https://docs.hyperswitch.io/integration-guide/payment-experience.md و LICENSE مخزن"

- id: iranian-gateways-closed
  text: "ZarinPal و Zibal و IDPay و NextPay هیچ‌کدام متن‌باز نیستند و تحت نظارت شاپرک‌اند"
  kind: quoted
  source: "بررسی مخازن سازمانی github.com/ZarinPal و help.zibal.ir — هیچ لایسنس گیت‌وی یافت نشد"

- id: project-already-uses-zarinpal
  text: "پروژه همین حالا ZarinPal را در payments_service.py استفاده می‌کند"
  kind: derived
  reproduce: ".venv\Scripts\python.exe -m pytest tests/contract/test_claims_gate.py -q"

- id: project-uses-qdrant
  text: "پروژه از Qdrant در unified_rag استفاده می‌کند و render.yaml متغیر QDRANT_URL دارد"
  kind: derived
  reproduce: ".venv\Scripts\python.exe -m pytest tests/contract/test_claims_gate.py -q"

- id: qdrant-recommendation
  text: "انتقال از Qdrant به pgvector توصیه می‌شود چون pgvector از قبل در پلن Pro موجود است"
  kind: interpretive
  basis: "مقایسهٔ دو جدول هزینه و بار عملیاتی نشان می‌دهد حاشیهٔ هزینه صفر است، اما اینکه حجم بردار زیر آستانهٔ بازبینی است یک فرض است و باید با دادهٔ واقعی سنجیده شود."

- id: no-plausible-gate-pattern
  text: "الگوی غالب این است که قابلیت سفیدبرند دقیقاً همان چیزی است که متن‌باز نیست"
  kind: interpretive
  basis: "در نوزده محصول بررسی‌شده این الگو در هجدی مورد دیده شد و چهار استثنا پس از بررسی مجدد همگی فاقد مستندات رسمی برند بودند؛ شمارش و انتخاب واژهٔ غالب تفسیر نویسنده است نه محاسبه."

- id: defer-auth-decision
  text: "تعویض لایهٔ هویت تا پیش از قلم ۳۸ توصیه نمی‌شود چون مهاجرت پس از صدور VC تقریباً غیرممکن است"
  kind: interpretive
  basis: "هیچ‌یک از نه پلتفرم بررسی‌شده امروز صرفه‌جویی مالی نمی‌کنند و همه ریسک مهاجرت دارند؛ این قضاوت بر توازن هزینه و ریسک استوار است نه بر اندازه‌گیری."

- id: chatwoot-branding-unverified
  text: "وضعیت مجوز برندینگ Chatwoot تأیید نشد و باید مستقیم پرسیده شود"
  kind: quoted
  source: "https://www.chatwoot.com/ در جریان تحقیق در دسترس نبود — نتیجهٔ منفی ثبت شد"

- id: supertokens-docs-blocked
  text: "کل مستندات SuperTokens مسدود بود و کمترین اطمینان از آن باقی است"
  kind: quoted
  source: "supertokens.com و همهٔ زیرمسیرها خطای شبکه دادند — نتیجهٔ منفی ثبت شد"

- id: white-label-hetzner-not-verified
  text: "قیمت Hetzner در این تحقیق تأیید نشد و عددی برایش ساخته نشد"
  kind: quoted
  source: "https://www.hetzner.com/cloud/ — صفحه با JS رندر می‌شود و API نیازمند توکن"
```
