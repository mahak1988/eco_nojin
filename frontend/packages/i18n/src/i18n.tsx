import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import fa from './locales/fa';
import en from './locales/en';

export type Lang = 'fa' | 'en';
type Dict = Record<string, unknown>;
const DICTS: Record<Lang, Dict> = { fa, en };

function lookup(dict: Dict, path: string): string | undefined {
  let cur: unknown = dict;
  for (const part of path.split('.')) {
    if (typeof cur !== 'object' || cur === null) return undefined;
    cur = (cur as Dict)[part];
  }
  return typeof cur === 'string' ? cur : undefined;
}

interface I18nValue { lang: Lang; dir: 'rtl' | 'ltr'; setLang: (l: Lang) => void; t: (key: string) => string; }
const Ctx = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() =>
    typeof window !== 'undefined' && window.localStorage.getItem('eco_lang') === 'en' ? 'en' : 'fa');
  const dir: 'rtl' | 'ltr' = lang === 'fa' ? 'rtl' : 'ltr';

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    window.localStorage.setItem('eco_lang', lang);
  }, [lang, dir]);

  const value = useMemo<I18nValue>(() => ({
    lang, dir, setLang,
    t: (key) => lookup(DICTS[lang], key) ?? lookup(DICTS.en, key) ?? key,
  }), [lang]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useI18n must be used within <I18nProvider>');
  return ctx;
}
