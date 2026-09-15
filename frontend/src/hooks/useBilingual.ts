/** Bilingual content hook — replaces inline `lang === 'fa' ? ... : ...` patterns. */

import { useLang } from '../i18n/LanguageContext';
import { type SiteContent, type Lang } from '../content/site';

interface BilingualHelpers {
  /** Current language ('fa' | 'en') */
  lang: Lang;
  /** Text direction ('rtl' | 'ltr') */
  dir: 'rtl' | 'ltr';
  /** Full typed content dictionary for current language */
  t: SiteContent;
  /** True if current language is Persian */
  isFa: boolean;
  /** True if current language is English */
  isEn: boolean;
  /** Get Persian text if available, otherwise English */
  fa<T>(faValue: T, enValue: T): T;
  /** Format number according to current locale */
  formatNumber: (n: number, options?: Intl.NumberFormatOptions) => string;
  /** Format date according to current locale */
  formatDate: (date: Date | string | number, options?: Intl.DateTimeFormatOptions) => string;
  /** Get plural form for count (Persian doesn't have plural, English does) */
  plural: (count: number, singular: string, plural?: string) => string;
}

/**
 * Hook for bilingual content access.
 * Replaces inline `lang === 'fa' ? 'فارسی' : 'English'` patterns.
 * 
 * @example
 * ```tsx
 * const { t, lang, fa, formatNumber, isFa } = useBilingual();
 * 
 * // Direct access to typed content
 * <h1>{t.hero.title}</h1>
 * 
 * // Inline bilingual values
 * <span>{fa('فارسی', 'English')}</span>
 * 
 * // Number formatting
 * <span>{formatNumber(1234567)}</span> // "۱٬۲۳۴٬۵۶۷" or "1,234,567"
 * ```
 */
export function useBilingual(): BilingualHelpers {
  const { lang, dir, t } = useLang();
  
  const isFa = lang === 'fa';
  const isEn = lang === 'en';
  
  const fa = <T,>(faValue: T, enValue: T): T => (isFa ? faValue : enValue);
  
  const formatNumber = (n: number, options?: Intl.NumberFormatOptions): string => {
    const locale = isFa ? 'fa-IR' : 'en-US';
    return new Intl.NumberFormat(locale, options).format(n);
  };
  
  const formatDate = (date: Date | string | number, options?: Intl.DateTimeFormatOptions): string => {
    const locale = isFa ? 'fa-IR' : 'en-US';
    const dateObj = date instanceof Date ? date : new Date(date);
    return new Intl.DateTimeFormat(locale, options).format(dateObj);
  };
  
  const plural = (count: number, singular: string, plural?: string): string => {
    if (isFa) return singular; // Persian doesn't change form
    return count === 1 ? singular : (plural ?? `${singular}s`);
  };
  
  return {
    lang,
    dir,
    t,
    isFa,
    isEn,
    fa,
    formatNumber,
    formatDate,
    plural,
  };
}

/**
 * Hook for accessing specific content section with type safety.
 * 
 * @example
 * ```tsx
 * const hero = useContent('hero');
 * <h1>{hero.title}</h1>
 * ```
 */
export function useContent<K extends keyof SiteContent>(section: K): SiteContent[K] {
  const { t } = useBilingual();
  return t[section];
}

/**
 * Hook for accessing nested content with a path.
 * 
 * @example
 * ```tsx
 * const heroTitle = useContentPath('hero', 'title');
 * const firstStat = useContentPath('stats', 0, 'value');
 * ```
 */
export function useContentPath<T>(...path: (string | number)[]): T {
  const { t } = useBilingual();
  let current: any = t;
  for (const key of path) {
    current = current?.[key];
  }
  return current as T;
}