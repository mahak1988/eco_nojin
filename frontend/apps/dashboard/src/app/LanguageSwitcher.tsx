import { useLocale, useSwitchLocale } from '@eco/i18n';
import { useTranslation } from 'react-i18next';

export function LanguageSwitcher() {
  const { t } = useTranslation(); const { locale, dir } = useLocale(); const switchTo = useSwitchLocale();;
  return (
    <button
      type="button"
      onClick={() => switchTo(locale === 'fa' ? 'en' : 'fa')}
      className="rounded-full border border-gray-300 dark:border-gray-700 px-3 py-1 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-green-500"
      aria-label={locale === 'fa' ? 'Switch to English' : 'تغییر زبان به فارسی'}
    >
      {locale === 'fa' ? 'EN' : 'فارسی'}
    </button>
  );
}
