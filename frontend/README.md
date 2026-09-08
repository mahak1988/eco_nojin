# Eco Nojin — Frontend (وب‌سایت عمومی)

وب‌سایت رسمی و مدرن پلتفرم **اکو نوژین** (احیای اکوسیستم، کشاورزی هوشمند، اقتصاد کربن).

- **پشته:** Vite 5 · React 18 · TypeScript (strict) · Tailwind CSS v4 · Framer Motion · lucide-react · React Router 7
- **زبان:** فارسی-اول (RTL) با سوییچ fa/en — فونت وزیرمتن به‌صورت محلی باندل شده (بدون نیاز به اینترنت)
- **بدون Docker** — فقط Node 20+ و pnpm 9+

## اجرا

```bash
# از ریشهٔ مونوریپو (D:\eco_nojin)
pnpm install          # یک بار برای کل workspace
pnpm dev              # سرور توسعه روی http://localhost:5173

# بیلد production و پیش‌نمایش
pnpm build            # tsc --noEmit + vite build → خروجی در frontend/dist
pnpm start            # سرو کردن بیلد روی http://localhost:4173
```

اسکریپت‌های معادل داخل `frontend/`:

| فرمان | کار |
|---|---|
| `pnpm dev` | سرور توسعه (HMR) روی 5173 |
| `pnpm build` | چک تایپ + بیلد production |
| `pnpm start` / `pnpm preview` | سرو بیلد روی 4173 |
| `pnpm lint` | ESLint (flat config) |
| `pnpm test` | تست‌های Vitest + Testing Library |
| `pnpm type-check` | فقط چک تایپ TypeScript |

## ساختار

```
frontend/
├─ index.html                  # شل HTML (fa/RTL پیش‌فرض)
├─ public/favicon.svg          # نشان برند (برگ + مدار ماهواره)
└─ src/
   ├─ main.tsx                 # نقطهٔ ورود
   ├─ App.tsx                  # Router + chrome مشترک (lazy routes)
   ├─ index.css                # Tailwind v4 + توکن‌های تم (پالت شب‌جنگلی/سبز)
   ├─ content/site.ts          # تک‌منبع محتوا (fa/en، تایپ‌شده)
   ├─ i18n/LanguageContext.tsx # زبان + جهت (RTL/LTR) + ماندگاری در localStorage
   ├─ public/robots.txt + sitemap.xml + og.png   # سئوی فنی
├─ content/pages/*.ts       # محتوای صفحات جدید (تقسیم‌شده بر اساس صفحه)
├─ content/menus.ts         # گروه‌های لینک فوتر (دوزبانه)
├─ lib/api.ts + lib/contact.ts  # کلاینت API (تماس، خبرنامه، پایلوت)
├─ components/
   │  ├─ layout/               # Navbar، Footer
   │  ├─ sections/             # Hero، Stats، Capabilities، ScienceChain، Channels، Carbon، CTA، …
   │  ├─ ui/                   # Icon، Reveal، SectionHeading، RouteFallback
   │  └─ visuals/              # Logo، Backdrop، FieldScene (صحنهٔ ماهواره‌ای SVG)
   ├─ pages/                   # ۲۳ صفحه: Home، Platform، Hydroma، About، Blog، FAQ، Contact، Transparency، Developers، Support، Status، Impact، Carbon، Partners، Careers، Investors، PilotIran، Academia، Marketplace، Resources، Terms، Rules، Privacy، 404
   └─ test/                    # setup + smoke tests (7)
```

هر فایل از `main.tsx` قابل ردیابی است (قاعدهٔ zero-orphan). تصاویر همه SVG/CSS محلی‌اند؛ هیچ منبع ریموتی وجود ندارد.

## تغییرات رایج

- **متن‌ها (فارسی/انگلیسی):** فقط `src/content/site.ts` — همهٔ برچسب‌ها، آمار، کارت‌ها و مدل‌ها از همین فایل خوانده می‌شوند.
- **رنگ و تم:** توکن‌های `@theme` در `src/index.css` (پالت leaf/sand/aqua/night).
- **صفحهٔ جدید:** فایل در `src/pages/` + مسیر در `App.tsx` + لینک در `Navbar` و `content/site.ts`.
- **زبان پیش‌فرض:** `readInitialLang` در `LanguageContext.tsx` (فعلاً `fa`).

## کیفیت

- `tsc --noEmit` سبز (strict) · ESLint: ۰ خطا · Vitest: ۱۵/۱۵ سبز (smoke + contact/status libs)
- ۲۶ مسیر فعال (+dashboard/declaration/eco-coin) (از جمله Developers/Support/Status/Impact/Carbon/Investors/Pilot/Academia/Marketplace/Resources) · سئو کامل · فرم تماس/پایلوت/خبرنامه متصل به درگاه API · sitemap/robots · ریسپانسیو موبایل/دسکتاپ · احترام به `prefers-reduced-motion` · ناوبری با کیبورد و aria-label
- اعداد فارسی در نسخهٔ فارسی، لاتین در انگلیسی (Intl.NumberFormat)

## اتصال به بک‌اند (فعال)

- **فرم تماس** به `POST /api/v1/contact`، **فرم پایلوت** به `POST /api/v1/pilot/apply`، **خبرنامه** به `POST /api/v1/newsletter/subscribe` و **محاسبه‌گرهای داشبورد** به `POST /api/v1/hub/runs` (مرکز تجمیع) وصل‌اند (مدل‌های ContactMessage/PilotApplication/NewsletterSubscriber؛ بدون ذخیرهٔ IP؛ هانی‌پات).
- `VITE_API_BASE_URL` را در `.env.local` فرانت‌اند تنظیم کنید (پیش‌فرض `http://localhost:8000`).
- CORS: `.env` ریشه باید پرت‌های 5173 (dev) و 4173 (preview) را در `CORS_ORIGINS` داشته باشد — اضافه شده.
- تست بک‌اند: `tests/unit/test_contact_router.py` (۶ تست، دیتابیس درون‌حافظه‌ای).
- برای داشبورد داده‌محور بعدی، یک کلاینت با TanStack Query روی همین درگاه اضافه کنید.
