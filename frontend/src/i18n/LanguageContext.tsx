import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { content, type Lang, type SiteContent } from '../content/site';

export type Dir = 'rtl' | 'ltr';

interface LanguageValue {
  lang: Lang;
  dir: Dir;
  t: SiteContent;
  setLang: (lang: Lang) => void;
  toggle: () => void;
}

const LanguageContext = createContext<LanguageValue | null>(null);
const STORAGE_KEY = 'eco_nojin_lang';
const COOKIE_NAME = 'lang';

function readInitialLang(): Lang {
  // SSR-safe: check cookie first (available during SSR via Next.js cookies())
  // then fallback to localStorage (client-only)
  if (typeof window !== 'undefined') {
    try {
      const cookieLang = getCookie(COOKIE_NAME);
      if (cookieLang === 'fa' || cookieLang === 'en') return cookieLang;
    } catch {
      // ignore cookie read errors
    }
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'fa' || stored === 'en') return stored;
    } catch (error) {
      console.warn('Could not read stored language preference', error);
    }
  }
  return 'fa';
}

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() ?? null;
  return null;
}

function setCookie(name: string, value: string, days = 365) {
  if (typeof document === 'undefined') return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
}

/**
 * Provides the active language, its text direction, and the typed content
 * dictionary. Mirrors state onto <html lang/dir>; page titles are owned by
 * the per-page <Seo> component, not here.
 */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readInitialLang);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
    try {
      localStorage.setItem(STORAGE_KEY, lang);
      setCookie(COOKIE_NAME, lang);
    } catch (error) {
      console.warn('Could not persist language preference', error);
    }
  }, [lang]);

  // Prevent hydration mismatch by rendering fallback until mounted
  const value = useMemo<LanguageValue>(
    () => ({
      lang,
      dir: lang === 'fa' ? 'rtl' : 'ltr',
      t: content[lang],
      setLang: setLangState,
      toggle: () => setLangState((current) => (current === 'fa' ? 'en' : 'fa')),
    }),
    [lang],
  );

  if (!mounted) {
    // SSR: render with initial lang but no children yet to avoid hydration mismatch
    return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
  }

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang(): LanguageValue {
  const value = useContext(LanguageContext);
  if (!value) {
    throw new Error('useLang must be used within a LanguageProvider');
  }
  return value;
}

/**
 * SSR helper: detect language from request headers or cookies.
 * Use in getServerSideProps or server components.
 */
export function detectLangFromRequest(
  headers: Headers | { get: (name: string) => string | null },
): Lang {
  // Check cookie header
  const cookieHeader = headers.get('cookie') ?? '';
  const match = cookieHeader.match(new RegExp(`(^|; )${COOKIE_NAME}=([^;]+)`));
  if (match) {
    const val = match[2];
    if (val === 'fa' || val === 'en') return val;
  }
  // Check Accept-Language header as fallback
  const acceptLang = headers.get('accept-language') ?? '';
  if (acceptLang.startsWith('fa') || acceptLang.includes(';q=') && acceptLang.includes('fa')) {
    return 'fa';
  }
  return 'en';
}
