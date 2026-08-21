'use client';
import { createContext, useContext, useEffect, useState } from 'react';
import en from '../locales/en.json';
import fa from '../locales/fa.json';
import ar from '../locales/ar.json';
import fr from '../locales/fr.json';
import es from '../locales/es.json';
import pt from '../locales/pt.json';
import ru from '../locales/ru.json';
import hi from '../locales/hi.json';
import zh from '../locales/zh.json';
import ur from '../locales/ur.json';
import bn from '../locales/bn.json';
import de from '../locales/de.json';
import it from '../locales/it.json';
import ms from '../locales/ms.json';

const locales: Record<string, any> = { en, fa, ar, fr, es, pt, ru, hi, zh, ur, bn, de, it, ms };

// Font mapping per language
export const fonts = {
  en: "'Inter', 'Segoe UI', sans-serif",
  fa: "'Vazirmatn', 'Tahoma', sans-serif",
  ar: "'Cairo', 'Tahoma', sans-serif",
  ur: "'Noto Nastaliq Urdu', 'Tahoma', sans-serif",
  hi: "'Noto Sans Devanagari', sans-serif",
  zh: "'Noto Sans SC', sans-serif",
  bn: "'Noto Sans Bengali', sans-serif",
  ru: "'Inter', sans-serif",
  fr: "'Inter', sans-serif",
  es: "'Inter', sans-serif",
  pt: "'Inter', sans-serif",
  de: "'Inter', sans-serif",
  it: "'Inter', sans-serif",
  ms: "'Inter', sans-serif",
};

const rtlLanguages = ['fa', 'ar', 'ur'];

interface I18nContextType {
  t: (key: string) => string;
  locale: string;
  setLocale: (l: string) => void;
  direction: 'ltr' | 'rtl';
  font: string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState('fa');

  useEffect(() => {
    const saved = localStorage.getItem('locale');
    if (saved && locales[saved]) setLocaleState(saved);
  }, []);

  const setLocale = (l: string) => {
    setLocaleState(l);
    localStorage.setItem('locale', l);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('locale-change', { detail: l }));
    }
  };

  const t = (key: string): string => {
    const msg = locales[locale]?.messages?.[key] || locales['en']?.messages?.[key] || key;
    return msg;
  };

  const direction = rtlLanguages.includes(locale) ? 'rtl' : 'ltr';
  const font = fonts[locale as keyof typeof fonts] || fonts.en;

  useEffect(() => {
    document.documentElement.setAttribute('dir', direction);
    document.documentElement.setAttribute('lang', locale);
    document.body.style.fontFamily = font;
  }, [locale, direction, font]);

  const exposedLocale = locale;
  return (
    <I18nContext.Provider value={{ t, locale, setLocale, direction, font }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
