import { useI18n } from '@eco/i18n';

export function LanguageSwitcher() {
  const { lang, setLang } = useI18n();
  return (
    <button
      type="button"
      onClick={() => setLang(lang === 'fa' ? 'en' : 'fa')}
      className="rounded-full border border-gray-300 dark:border-gray-700 px-3 py-1 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-green-500"
      aria-label={lang === 'fa' ? 'Switch to English' : 'تغییر زبان به فارسی'}
    >
      {lang === 'fa' ? 'EN' : 'فارسی'}
    </button>
  );
}
