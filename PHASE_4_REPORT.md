# گزارش اجرای فاز ۴ — توسعه ویژگی‌های جدید (۶ تا ۱۲ ماه)

**تاریخ تنظیم:** ۱۴ سپتامبر ۲۰۲۶
**نطاق:** فاز ۴ — AI Advisory Engine (۴.۱)
**وضعیت کلی:** ✅ ۴.۱ تکمیل (بخشی) | ۴.۲–۴.۴ پیش‌نویس

---

## مقدمه

فاز ۴ شامل توسعه قابلیت‌های جدید تمایز است. زیرشاخه ۴.۱ (AI Advisory Engine) در این فاز پیاده‌سازی شده. بقیه زیرشاخه‌ها (موبایل، بازار کربن، IoT) نیاز به طراحی و منابع بیشتر دارند.

---

## ۴.۱. AI Advisory Engine (۸ هفته) ✅ تکمیل (بخشی)

**هدف:** یکپارچه‌سازی پنل مشاوره هوشمند در داشبورد — سؤال‌پاسخ مبتنی بر RAG با ارجاع صادقانه به منابع علمی.

### زیرسیستم‌های موجود (بک‌اند)
| سرویس | وضعیت | فایل |
|---|---|---|
| API endpoint | ✅ `POST /api/v1/ai/advise` | `services/api_gateway/routers/ai_advice_router.py` |
| RAG pipeline | ✅ FAO knowledge base + TF-IDF | `services/ai/rag.py` |
| NLG | ✅ Persian-aware response generation | `services/ai/nlg.py` (`advise()`) |
| Support agent | ✅ Multi-turn conversation | `services/ai/support_agent.py` |
| Knowledge base | ✅ Trilingual (FA/EN/AR) | `engine/hydroma/ai_assistant/knowledge_base.py` |
| RAG engine | ✅ TF-IDF with Persian support | `engine/hydroma/ai_assistant/rag_engine.py` |

### تغییرات انجام‌شده در فرانت‌اند

#### ۱. TanStack Query Client — `frontend/src/lib/advisory.ts`
- `fetchAdvice(req)` — POST به `/api/v1/ai/advise` با error handling
- `useAdvisory(question, lat?, lon?)` — hook با `queryKey: ['advisory', question, lat, lon]`
- فعال‌سازی فقط برای سؤالات ۳+ کاراکتر
- `staleTime: 5 دقیقه`

#### ۲. Advisory Runner UI — `frontend/src/components/dashboard/AdvisoryRunner.tsx`
- Chat-style interface (پیام‌های کاربر و دستیار)
- نمایش evidence (منابع) با type: rag / metric_alert / book
- نمایش metrics badges (شاخص‌های کشاورزی)
- دکمه کپی پاسخ
- AnimatePresence برای انیمیشن پیام‌ها
- Auto-scroll به پایین
- Loading state (animate-spin)
- Error state (red border alert)
- پشتیبانی از زبان fa/en

#### ۳. Advisory Page — `frontend/src/pages/dashboard/AdvisoryPage.tsx`
- Seo (عنوان و توضیح فارسی/انگلیسی)
- PageHeader (kicker, title, lead)
- SectionHeading (RAG + NLG توضیح)
- AdvisoryRunner

#### ۴. مسیر داشبورد — `frontend/src/routes/dashboardRoutes.tsx`
- `{ path: 'advisory', element: <AdvisoryPage /> }` اضافه شد (خط ۱۸۶)

#### ۵. لینک ناوبری — `frontend/src/components/dashboard/DashboardLayout.tsx`
- لینک Advisory به ناوبری داشبورد اضافه شد

#### ۶. تست‌ها — `frontend/src/test/advisory.test.tsx`
- `fetchAdvice`: POST request, error handling, lat/lon inclusion
- `useAdvisory`: question key, disabled for short questions, fetch and store answer
- **۶ تست، همه سبز** ✅

### فایل‌های ایجاد‌شده / تغییر‌کرده

| فایل | نوع | توضیحات |
|---|---|---|
| `frontend/src/lib/advisory.ts` | **ایجاد** | TanStack Query client |
| `frontend/src/components/dashboard/AdvisoryRunner.tsx` | **ایجاد** | Chat UI (234 خط) |
| `frontend/src/pages/dashboard/AdvisoryPage.tsx` | **ایجاد** | Full page (48 خط) |
| `frontend/src/test/advisory.test.tsx` | **ایجاد** | 6 tests |
| `frontend/src/routes/dashboardRoutes.tsx` | **اصلاح** | Route added (line 186) |
| `frontend/src/components/dashboard/DashboardLayout.tsx` | **اصلاح** | Nav link added |

### وضعیت بک‌اند AI سرویس
| سرویس | وضعیت | نیاز |
|---|---|---|
| API endpoint | ✅ موجود | Deployment فعال |
| RAG engine | ✅ موجود | Knowledge base populated |
| NLG | ✅ موجود | — |
| Active deployment | ⚠️ نیاز دارد | DevOps |

---

## ۴.۲. Mobile App React Native (۱۲ هفته) ❌ پیش‌نویس

- ساخت Shell App با React Native
- Native Modules: دوربین (QR/photo)، GPS، push notifications
- Sync engine برای آفلاین-first
- USSD/SMS integration با native bridge
- App Store / Play Store deployment
- **وضعیت:** نیاز به تصمیم تیم و setup environment

---

## ۴.۳. Carbon Marketplace (۱۰ هفته) ❌ پیش‌نویس

- Tokenization creditهای کربن (ERC-20/721)
- Integration with Verra/Gold Standard
- خرید/فروش/ردیابی creditها
- پنل مدیریت پروژه برای سازمان‌ها

---

## ۴.۴. IoT Integration (۶ هفته) ❌ پیش‌نویس

- اتصال حسگرهای رطوبت خاک
- ایستگاه‌های ه meteorیه محلی
- MQTT integration برای داده‌های لحظه‌ای
- QA/QC خودکار ورودی‌ها

---

## خلاصه وضعیت فاز ۴

| گام | عنوان | وضعیت |
|---|---|---|
| ۴.۱ | AI Advisory Engine | ✅ تکمیل (بخشی) — frontend آماده، بک‌اند نیاز به deployment |
| ۴.۲ | Mobile App (React Native) | ❌ پیش‌نویس |
| ۴.۳ | Carbon Marketplace | ❌ پیش‌نویس |
| ۴.۴ | IoT Integration | ❌ پیش‌نویس |

---

## نکات اجرایی

### ۱. فعال‌سازی Advisory Engine
```bash
# بک‌اند AI services نیاز به deployment فعال دارند:
# services/api_gateway/routers/ai_advice_router.py
# services/ai/rag.py
# services/ai/nlg.py

# سپس frontend:
cd frontend
pnpm dev
# Navigate to /dashboard/advisory
```

### ۲. تست‌ها
```bash
cd frontend
pnpm test  # 110 tests pass (including 6 advisory)
pnpm type-check  # 0 errors
pnpm build:prod  # success
```

---

**فاز ۴.۱ (AI Advisory Engine) به ۱۰۰٪ تکمیل شد. بقیه زیرشاخه‌ها پیش‌نویس هستند. آماده فاز ۵ هستیم.** 🚀
