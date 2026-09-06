import { RTL_LOCALES, type Locale } from '@eco/config';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { isRTL } from './config';

export function useLocale(): { locale: Locale; dir: 'ltr' | 'rtl' } {
  const { i18n } = useTranslation();
  const locale = (i18n.language as Locale) ?? 'fa';
  return { locale, dir: isRTL(locale) ? 'rtl' : 'ltr' };
}

export function useRtlClass() {
  const { dir } = useLocale();
  return dir;
}

export function useDocumentDirection() {
  const { dir } = useLocale();
  useEffect(() => {
    document.documentElement.setAttribute('dir', dir);
    document.documentElement.setAttribute('lang', document.documentElement.lang || 'fa');
  }, [dir]);
}

export function useSwitchLocale(): (locale: Locale) => void {
  const { i18n } = useTranslation();
  return (locale: Locale) => {
    void i18n.changeLanguage(locale);
    document.documentElement.setAttribute('dir', (RTL_LOCALES as readonly Locale[]).includes(locale) ? 'rtl' : 'ltr');
  };
}

export function useIsRtl(): boolean {
  const { dir } = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted && dir === 'rtl';
}