import { type ReactNode, useEffect } from 'react';
import { isRTL } from './config';
import { useLocale } from './hooks';

/**
 * Sets <html dir> + <html lang> from the active i18n locale.
 * Wrap near the app root so all CSS logical props mirror correctly.
 */
export function DirectionProvider({ children }: { children: ReactNode }) {
  const { locale } = useLocale();
  useEffect(() => {
    const html = document.documentElement;
    html.setAttribute('lang', locale);
    html.setAttribute('dir', isRTL(locale) ? 'rtl' : 'ltr');
  }, [locale]);
  return <>{children}</>;
}