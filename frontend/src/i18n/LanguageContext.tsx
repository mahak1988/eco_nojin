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
const STORAGE_KEY = '***';

function readInitialLang(): Lang {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'fa' || stored === 'en') return stored;
  } catch (error) {
    console.warn('Could not read stored language preference', error);
  }
  return 'fa';
}

/**
 * Provides the active language, its text direction, and the typed content
 * dictionary. Mirrors state onto <html lang/dir>; page titles are owned by
 * the per-page <Seo> component, not here.
 */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readInitialLang);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (error) {
      console.warn('Could not persist language preference', error);
    }
  }, [lang]);

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

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang(): LanguageValue {
  const value = useContext(LanguageContext);
  if (!value) {
    throw new Error('useLang must be used within a LanguageProvider');
  }
  return value;
}
