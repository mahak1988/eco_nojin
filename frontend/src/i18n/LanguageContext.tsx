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
export type LangExtended = 'fa' | 'en' | 'ur' | 'ps';

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
const SUPPORTED_LANGS: Lang[] = ['fa', 'en', 'ur', 'ps'];

function readInitialLang(): Lang {
  if (typeof window !== 'undefined') {
    try {
      const cookieLang = getCookie(COOKIE_NAME);
      if (SUPPORTED_LANGS.includes(cookieLang as Lang)) return cookieLang as Lang;
    } catch {
      // Ignore cookie parsing errors
    }
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (SUPPORTED_LANGS.includes(stored as Lang)) return stored as Lang;
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

  const value = useMemo<LanguageValue>(
    () => ({
      lang,
      dir: lang === 'fa' ? 'rtl' : 'ltr',
      t: content[lang] ?? content['fa'],
      setLang: setLangState,
      toggle: () => setLangState((current) => (current === 'fa' ? 'en' : 'fa')),
    }),
    [lang],
  );

  if (!mounted) {
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

export function detectLangFromRequest(
  headers: Headers | { get: (name: string) => string | null },
): Lang {
  const cookieHeader = headers.get('cookie') ?? '';
  const match = cookieHeader.match(new RegExp(`(^|; )${COOKIE_NAME}=([^;]+)`));
  if (match) {
    const val = match[2];
    if (SUPPORTED_LANGS.includes(val as Lang)) return val as Lang;
  }
  const acceptLang = headers.get('accept-language') ?? '';
  for (const l of SUPPORTED_LANGS) {
    if (acceptLang.includes(l)) return l;
  }
  return 'fa';
}
