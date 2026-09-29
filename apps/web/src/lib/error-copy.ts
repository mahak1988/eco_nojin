/**
 * Copy for the error boundaries.
 *
 * An error boundary is the one place in the app that cannot rely on the message
 * provider. `app/global-error.tsx` replaces the root layout, so
 * `NextIntlClientProvider` is gone, and the boundary that lives above the locale
 * segment would fail if it called `useTranslations`. Reading the catalogue from
 * inside the component is therefore not an option here.
 *
 * Rather than hard-code English inside the components — which
 * `I18N_AND_RTL.md` forbids for visible text — this module resolves the copy
 * from the locale in the URL. It is deliberately tiny, holds no state, and is
 * unit tested, so the constraint is visible and verifiable instead of implicit.
 */
import { type AppLocale, defaultLocale, isRtl } from '@/i18n/routing';

export type ErrorBoundaryKind = 'global' | 'segment';

type Copy = {
  title: string;
  description: string;
  retry: string;
  home: string;
  /** The support reference shown to the reader, without inventing an address. */
  reference: string;
};

/**
 * `en` and `fa` are the two catalogs the project maintains by hand; the other
 * twelve fall back to `en` today, exactly as the locale catalogs do. Writing a
 * separate string per language here would create a second source of truth that
 * no translation tool can see.
 *
 * The fallback target must be `en`, never `fa`. An error boundary is exactly
 * where a reader is most likely to be a non-Persian speaker, and falling back to
 * the default locale would hand Arabic and Urdu readers a Persian error page —
 * the one place in the app where a wrong-language message is least forgivable,
 * because it replaces the surface they asked for.
 *
 * `ar` and `ur` are hand-written because they are the two RTL locales whose
 * readers are most likely to hit a crash, and because a wrongly-directed error
 * page hides its own reason from a screen reader user.
 */
const COPY: Partial<Record<AppLocale, Copy>> = {
  en: {
    title: 'Something went wrong',
    description: 'The page could not be loaded. Nothing was changed on the server.',
    retry: 'Try again',
    home: 'Return home',
    reference: 'If this keeps happening, quote the reference below when you report it.',
  },
  fa: {
    title: 'خطایی رخ داد',
    description: 'این صفحه بارگذاری نشد. هیچ تغییری روی سرور ایجاد نشده است.',
    retry: 'تلاش دوباره',
    home: 'بازگشت به خانه',
    reference: 'اگر این خطا تکرار شد، هنگام گزارش، شناسه زیر را ذکر کنید.',
  },
  ar: {
    title: 'حدث خطأ ما',
    description: 'تعذّر تحميل الصفحة. لم يتغيّر أي شيء على الخادم.',
    retry: 'أعد المحاولة',
    home: 'العودة إلى الصفحة الرئيسية',
    reference: 'إذا تكرر هذا الخطأ، فاذكر المرجع أدناه عند الإبلاغ عنه.',
  },
  ur: {
    title: 'خرابی پیش آئی',
    description: 'یہ صفحہ لوڈ نہیں ہو سکا۔ سرور پر کوئی تبدیلی نہیں ہوئی۔',
    retry: 'دوبارہ کوشش کریں',
    home: 'مرکزی صفحے پر واپس جائیں',
    reference: 'اگر یہ خرابی بار بار ہو تو رپورٹ کرتے وقت نیچے دیا گیا حوالہ لکھیں۔',
  },
};

const FALLBACK = COPY.en as Copy;

export function copyFor(locale: string | undefined | null, _kind: ErrorBoundaryKind): Copy {
  const key = (locale ?? defaultLocale) as AppLocale;
  return COPY[key] ?? FALLBACK;
}

export function localeFromPath(pathname: string): string | null {
  const segment = pathname.split('/').filter(Boolean)[0];
  return segment ?? null;
}

export function directionFor(locale: string | undefined | null): 'rtl' | 'ltr' {
  return isRtl(locale ?? defaultLocale) ? 'rtl' : 'ltr';
}
