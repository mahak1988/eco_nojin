# برنامه اجرایی توسعه فرانت‌اند اکو نوژین
## نقشه راه عملیاتی بر اساس چارچوب مدیریت بدهی فنی

| مورد | جزئیات |
|---|---|
| **تاریخ** | ۱۳ سپتامبر ۲۰۲۶ |
| **پروژه** | Eco Nojin Frontend |
| **نسخه** | 1.0 |
| **مبنی** | TECHNICAL_DEBT_MANAGEMENT.md |

---

## فهرست مطالب
1. [فوری — ایمن‌سازی و رفع بلاتکلیفی](#۱-فوری)
2. [کوتاه‌مدت — کیفیت کد و تست](#۲-کوتاه‌مدت)
3. [متوسط‌مدت — عملکرد و معماری](#۳-متوسط‌مدت)
4. [بلندمدت — ویژگی‌های جدید](#۴-بلندمدت)
5. [پایش و بازبینی](#۵-پایش)

---

## ۱. فوری (۰ تا ۲ هفته) — ایمن‌سازی و پایه‌سازی

### ۱.۱. مهم‌ترین اقدامات

| # | اقدام | جزئیات | زمان | وضعیت |
|---|---|---|---|---|
| 1.1 | `.env` ایمن‌سازی | `.env` در `.gitignore` ✓، `.env.example` ایجاد ✓، anti-leak hook تقویت ✓ | انجام شد | ✅ |
| 1.2 | Anti-leak hook | `pre-commit` با `secrets_audit.py` به‌روزرسانی ✓ | انجام شد | ✅ |
| 1.3 | حذف CSS تکراری | `--animate-shimmer` dup در `index.css` حذف شد ✓ | انجام شد | ✅ |
| 1.4 | اصلاح ProjectProperties | interface از داخل تابع خارج شد ✓ | انجام شد | ✅ |
| 1.5 | `vite-env.d.ts` | اعلان متغیرهای محیطی Vite ✓ | انجام شد | ✅ |
| 1.6 | `.npmrc` بهینه‌سازی | رجیستری به npmjs.org ✓ | انجام شد | ✅ |
| 1.7 | تکراری `useBilingual` | یکپارچه‌سازی دو نسخه | انجام شد | ✅ |

### ۱.۲. تکراری `useBilingual` — یکپارچه‌سازی

**مشکل:** دو تابع `useBilingual` با API متفاوت:
- `src/lib/i18n.ts`: `useBilingual(fa, en): string` — ساده
- `src/hooks/useBilingual.ts`: `useBilingual(): BilingualHelpers` — غنی

**راه‌حل:** حفظ نسخه غنی در `src/hooks/useBilingual.ts` و اضافه کردن wrapper در `src/lib/i18n.ts`:

```typescript
// src/lib/i18n.ts — بایگانی سازگاری
import { useBilingual as useBilingualFull } from '../hooks/useBilingual';

/**
 * سازگاری با استفاده قبلی: useBilingual('فارسی', 'English')
 * استفاده توصیه‌شده: useBilingual().fa('فارسی', 'English')
 */
export function useBilingual(fa: string, en: string): string {
  const { fa: faHelper } = useBilingualFull();
  return faHelper(fa, en);
}
```

**مالک:** توسعه‌دهنده فرانت‌اند

---

## ۲. کوتاه‌مدت (۱ تا ۴ هفته) — کیفیت کد و تست

### ۲.۱. تست‌ها

| # | اقدام | جزئیات | زمان |
|---|---|---|---|
| 2.1 | تست‌های واحد lib تابعی | `useBilingual`, `useAnimatedCounter`, format helpers | ۱ هفته |
| 2.2 | تست‌های کامپوننت | `EmptyState`, `UniversalCard`, `Reveal`, `SearchModal` | ۱ هفته |
| 2.3 | تست‌های یکپارچه dashboard | DashboardContext, DashboardLayout | ۱ هفته |
| 2.4 | E2E تست‌های کلیدی | RTL/LTR switch, Login flow, PWA install | ۱ هفته |

**هدف پوشش:** >20٪ کل کد، >40٪ کد داشبورد و lib

### ۲.۲. کیفیت کد

| # | اقدام | جزئیات | زمان |
|---|---|---|---|
| 2.3 | EmptyState component | موجود ✓ — بررسی استفاده در DashboardPage و صفحات بلاگ/FAQ | ۱ روز |
| 2.4 | Skip Navigation | موجود ✓ در Navbar — بررسی کامل عملکرد | ۱ روز |
| 2.5 | Prettier یکپارچه | `.prettierrc` + VSCode settings | انجام شد | ✅ |
| 2.6 | ESLint strict | `eslint.config.js` configured, `@eslint/js` installed, errors fixed | انجام شد | ✅ |
| 2.7 | TypeScript strict | `strict: true`, `noUnusedLocals/Parameters`, `lib: ES2022` | فعال | ✅ |

### ۲.۳. Error Boundary

```tsx
// frontend/src/components/ui/ErrorBoundary.tsx
'use client';

import { Component, type ReactNode } from 'react';

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div role="alert" className="p-6 text-center">
          <h2>خطا در بارگذاری بخش</h2>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
```

---

## ۳. متوسط‌مدت (۱ تا ۳ ماه) — عملکرد و معماری

### ۳.۱. بهبود عملکرد

| # | اقدام | جزئیات | زمان | وابستگی |
|---|---|---|---|---|
| 3.1 | SSR/SSG Migration | مهاجرت صفحات عمومی به Astro | ۳ هفته | Astro setup |
| 3.2 | PWA/Service Worker | `vite-plugin-pwa` + Cache strategies | ۲ هفته | Node 20+ |
| 3.3 | Bundle Optimization | Visualizer + Code splitting + Tree shaking | ۱ هفته | — |
| 3.4 | Critical CSS | Inline above-the-fold styles | ۱ هفته | — |
| 3.5 | Image Optimization | WebP/AVIF + Lazy loading + LQIP | ۲ هفته | — |
| 3.6 | MapLibre real tiles | NDVI/NDWI tiles from CDSE | ۳ هفته | CDSE credentials |
| 3.7 | Chart Library | Recharts or Chart.js integration | ۲ هفته | — |

### ۳.۲. بهبود دسترسی‌پذیری

| # | اقدام | جزئیات | زمان |
|---|---|---|---|
| 3.3 | Focus trap | `useFocusTrap.ts` — بررسی و تست | ۳ روز |
| 3.4 | ARIA labels | Audit کامل ARIA در کل کامپوننت‌ها | ۱ هفته |
| 3.5 | Color contrast | WCAG AA contrast check | ۳ روز |
| 3.6 | Keyboard navigation | تست کامل keyboard flow | ۱ هفته |

### ۳.۳. بهبود معماری

| # | اقدام | جزئیات | زمان |
|---|---|---|---|
| 3.7 | API client unify | `src/lib/api.ts` — واحد API | ۱ هفته |
| 3.8 | Context consolidation | بررسی `AuthContext` و `DashboardContext` | ۳ روز |
| 3.9 | Content modularization | `contentHelpers.ts` 36 accessors, `site.ts` 1903 lines (split in progress) | در حال انجام |

---

## ۴. بلندمدت (۳ تا ۱۲ ماه) — ویژگی‌های جدید

### ۴.۱. فناوری

| # | اقدام | جزئیات | زمان |
|---|---|---|---|
| 4.1 | React 19 Migration | بروزرسانی + types + hooks | ۴ هفته |
| 4.2 | TanStack Query | Cache + refetch + optimistic updates | ۲ هفته |
| 4.3 | Real-time Pipeline | WebSocket/SSE + polling | ۳ هفته |

### ۴.۲. ویژگی‌ها

| # | اقدام | زمان | اولویت |
|---|---|---|---|
| 4.4 | AI Advisory Engine | ۸ هفته | P2 |
| 4.5 | Mobile App (RN) | ۱۲ هفته | P3 |
| 4.6 | Carbon Marketplace | ۱۰ هفته | P2 |
| 4.7 | Digital Twin (3D) | ۱۶ هفته | P3 |
| 4.8 | IoT Dashboard | ۶ هفته | P2 |

### ۴.۳. استقرار

| # | اقدام | جزئیات | زمان |
|---|---|---|---|
| 4.4 | CI/CD Pipeline | GitHub Actions — lint, typecheck, test, build, lighthouse | ۲ هفته |
| 4.5 | Monitoring | RUM, Web Vitals, Error tracking | ۱ هفته |
| 4.6 | Security Audit | خارجی — ۶ ماهه | ۱ روز |

---

## ۵. پایش و بازبینی

### ۵.۱. چک‌لیست هر اسپرینت

- [ ] بدهی فنی جدید شناسایی و ثبت شد
- [ ] بودجه ۲۰٪ بدهی فنی اختصاص داده شد
- [ ] `npx tsc --noEmit` — صفر خطا
- [ ] `npx eslint src/` — صفر خطا
- [ ] `npx vitest run` — همه سبز
- [ ] `npx vite build` — موفق
- [ ] Lighthouse score > هدف فاز
- [ ] `pnpm audit` — صفر critical
- [ ] `.env` نه در git

### ۵.۲. چک‌لیست هر ماه

- [ ] بازبینی کامل بدهی فنی
- [ ] به‌روزرسانی داشبورد بدهی فنی
- [ ] رفع تمام P0 آتی‌ها
- [ ] بازبینی وابستگی‌ها
- [ ] بازبینی نقشه راه

### ۵.۳. چک‌لیست هر فاز

- [ ] ارزیابی عملکرد با Lighthouse CI
- [ ] بازبینی معماری
- [ ] بازنگری نقشه راه
- [ ] Security audit خارجی

### ۵.۴. ردیابی بدهی فنی

هر مورد بدهی فنی باید در فایل `TECHNICAL_DEBT.md` ثبت شود با:
- شناسه: TD-YYYY-NNN
- عنوان و توضیح
- نوع و اولویت
- امتیاز ماتریس
- فایل‌های مربوطه
- وضعیت و مالک
- پیوند به برنامه مرتبط

---

## ضمیمه: خلاصه تغییرات اعمال‌شده

### امنیت (P0)
- [x] `.env` محافظت‌شده در `.gitignore`
- [x] `.env.example` ایجاد شده با placeholders
- [x] `pre-commit` hook تقویت شده (secret scan + typecheck + lint + .env guard)
- [x] `secrets_audit.py` به همه فرمت‌ها گسترش یافت (JS/TS/JSON/YAML)
- [x] `.npmrc` به registry رسمی npmjs.org تغییر یافت

### کد (P1)
- [x] CSS `--animate-shimmer` تکراری حذف شد
- [x] `ProjectProperties` interface خارج از `addProjectMarkers` شد
- [x] `vite-env.d.ts` برای متغیرهای محیطی Vite

### مستندات
- [x] `TECHNICAL_DEBT_MANAGEMENT.md` — چارچوب جامع
- [x] `FRONTEND_DEVELOPMENT_PLAN.md` — برنامه اجرایی

### در انتظار تأیید
- [x] ErrorBoundary component
- [x] Bundle size budget optimization
- [x] Lighthouse CI config
- [x] Content modularization helpers

*این برنامه بر اساس چارچوب TECHNICAL_DEBT_MANAGEMENT.md تهیه شده و باید با تصمیم تیم فنی بازبینی و تأیید شود.*
