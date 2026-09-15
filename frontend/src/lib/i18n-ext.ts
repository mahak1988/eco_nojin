/** i18n utilities — extended language support for Phase 5.1. */

import { useBilingual as useBilingualFull } from '../hooks/useBilingual';
import { type Lang } from '../content/site';

/**
 * Extended language list for regional expansion (Phase 5.1).
 * Backend supports 14 languages; frontend currently supports 4 (fa, en, ur, ps).
 */
export const EXTENDED_LANGUAGES: Lang[] = ['fa', 'en', 'ur', 'ps'];

export function isLanguageSupported(lang: string): lang is Lang {
  return EXTENDED_LANGUAGES.includes(lang as Lang);
}

export function getLocaleString(lang: Lang): string {
  const localeMap: Record<Lang, string> = {
    fa: 'fa-IR',
    en: 'en-US',
    ur: 'ur-PK',
    ps: 'ps-AF',
  };
  return localeMap[lang] ?? 'en-US';
}

/**
 * Backward-compatible wrapper: useBilingualList(fa/en items)
 * Updated to filter by active language key.
 */
export function useBilingualList<T extends { fa: string; en: string }>(items: T[]): T[] {
  const { lang } = useBilingualFull();
  // If the active lang is ur or ps, fall back to fa or en
  if (lang === 'ur' || lang === 'ps') {
    return items.filter((item) => item.fa || item.en);
  }
  return items.filter((item) => item[lang]);
}
