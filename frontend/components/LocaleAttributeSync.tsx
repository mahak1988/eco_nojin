'use client';
import { useEffect } from 'react';
import { useI18n } from '../lib/i18n-context';

/**
 * Applies the active locale to <html lang> and <html dir> on the client.
 *
 * The root layout renders <html lang="en" dir="ltr" suppressHydrationWarning>
 * for SSR; after hydration this component (and the I18nProvider) push the
 * real locale/direction onto the document element.
 */
export default function LocaleAttributeSync() {
  const { locale, direction } = useI18n();

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = direction;
  }, [locale, direction]);

  return null;
}
