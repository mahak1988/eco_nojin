import { useBilingual as useBilingualFull } from '../hooks/useBilingual';

/**
 * سازگاری با استفاده قبلی: useBilingual('فارسی', 'English')
 * استفاده توصیه‌شده: useBilingual().fa('فارسی', 'English')
 */
export function useBilingual(fa: string, en: string): string {
  const { fa: faHelper } = useBilingualFull();
  return faHelper(fa, en);
}

/** Returns array items filtered to active language key (fa/en/ur/ps). */
export function useBilingualList<T extends Record<string, string>>(items: T[]): T[] {
  const { lang } = useBilingualFull();
  return items.filter((item) => item[lang]);
}
