'use client';
import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { localesData } from './locales-data';

type Locale = string;
type Direction = 'ltr' | 'rtl';

interface I18nContextType {
  locale: Locale;
  direction: Direction;
  isRTL: boolean;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

/** RTL languages: Persian, Arabic, Urdu (mirrors lib/i18n.ts directions). */
const RTL_LOCALES: ReadonlySet<string> = new Set(['fa', 'ar', 'ur']);

/** Resolve the writing direction for a locale code. */
export function getDirection(locale: Locale): Direction {
  if (RTL_LOCALES.has(locale)) return 'rtl';
  const declared = localesData[locale]?.direction;
  return declared === 'rtl' ? 'rtl' : 'ltr';
}

export function I18nProvider({ children }: { children: ReactNode }) {
  // Start with 'en' for SSR consistency (no hydration mismatch).
  const [locale, setLocaleState] = useState<Locale>('en');
  const [isMounted, setIsMounted] = useState(false);

  // Restore saved locale after hydration.
  useEffect(() => {
    setIsMounted(true);
    const saved = localStorage.getItem('eco-nojin-locale');
    if (saved && localesData[saved]) {
      setLocaleState(saved);
    }
  }, []);

  // Keep <html lang> and <html dir> in sync with the active locale.
  // Runs after mount; SSR keeps the layout defaults (lang="en" dir="ltr").
  useEffect(() => {
    if (typeof document === 'undefined') return;
    document.documentElement.lang = locale;
    document.documentElement.dir = getDirection(locale);
  }, [locale]);

  const setLocale = useCallback((newLocale: Locale) => {
    if (!localesData[newLocale]) return;
    setLocaleState(newLocale);
    if (typeof window !== 'undefined') {
      localStorage.setItem('eco-nojin-locale', newLocale);
    }
  }, []);

  // Lookup: active locale first, then English, then the raw key as fallback
  // so a missing key never renders as an empty string.
  const t = useCallback(
    (key: string): string => {
      const current = localesData[locale]?.messages?.[key];
      if (current) return current;
      const fallback = localesData['en']?.messages?.[key];
      return fallback || key;
    },
    [locale]
  );

  // After mount, use the real locale; before that, keep SSR-safe ltr/en.
  const currentDirection: Direction = isMounted
    ? getDirection(locale)
    : 'ltr';

  return (
    <I18nContext.Provider
      value={{
        locale,
        direction: currentDirection,
        isRTL: currentDirection === 'rtl',
        setLocale,
        t,
      }}
    >
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useI18n must be used within I18nProvider');
  return context;
}
