import { defineRouting } from 'next-intl/routing';

// The 14 official platform languages (aligned with docs/en/07_i18n_localization.md).
export const locales = [
  'fa',
  'en',
  'ar',
  'ur',
  'de',
  'es',
  'fr',
  'hi',
  'it',
  'ms',
  'pt',
  'ru',
  'zh',
  'bn',
] as const;

export type AppLocale = (typeof locales)[number];

export const rtlLocales: readonly AppLocale[] = ['fa', 'ar', 'ur'];
export const defaultLocale: AppLocale = 'fa';

export function isRtl(locale: string): boolean {
  return rtlLocales.includes(locale as AppLocale);
}

export const routing = defineRouting({
  locales,
  defaultLocale,
  localePrefix: 'always',
});
