/** i18n helper — content accessors for regional expansion (Phase 5.1). */

import { type Lang } from '../content/site';

/** Maps extended language codes to content keys. */
export const LANGUAGE_CONTENT_MAP: Record<string, string> = {
  fa: 'fa',
  en: 'en',
  ur: 'ur',
  ps: 'ps',
};

/** Check if a language is a RTL language. */
export function isRTLLanguage(lang: Lang): boolean {
  return lang === 'fa' || lang === 'ur' || lang === 'ps';
}

/** Get the locale string for a language. */
export function getLocaleForLang(lang: Lang): string {
  const locales: Record<Lang, string> = {
    fa: 'fa-IR',
    en: 'en-US',
    ur: 'ur-PK',
    ps: 'ps-AF',
  };
  return locales[lang] ?? 'en-US';
}

/** Check if a language is newly added (Phase 5.1). */
export function isExtendedLanguage(lang: Lang): boolean {
  return lang === 'ur' || lang === 'ps';
}
