import { RTL_LOCALES, type Locale } from '@eco/config';
import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';
import ar from './locales/ar.json';
import en from './locales/en.json';
import fa from './locales/fa.json';
import ur from './locales/ur.json';

export const resources = {
  en: { translation: en },
  fa: { translation: fa },
  ar: { translation: ar },
  ur: { translation: ur },
} as const;

export type Namespace = keyof typeof resources.en;

export function isRTL(locale: Locale): boolean {
  return (RTL_LOCALES as readonly Locale[]).includes(locale);
}

let initialized = false;

export function setupI18n(defaultLocale: Locale = 'fa'): typeof i18n {
  if (initialized) return i18n;
  initialized = true;

  void i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      resources,
      fallbackLng: defaultLocale,
      supportedLngs: ['en', 'fa', 'ar', 'ur'],
      interpolation: { escapeValue: false },
      detection: {
        order: ['localStorage', 'navigator', 'htmlTag'],
        caches: ['localStorage'],
        lookupLocalStorage: 'eco.locale',
      },
    });

  return i18n;
}

export { i18n };