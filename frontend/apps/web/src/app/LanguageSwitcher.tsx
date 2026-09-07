import { useLocale, useSwitchLocale } from '@eco/i18n';
import { useTranslation } from 'react-i18next';

const LANGS = [
  { code: 'fa', label: 'فارسی' },
  { code: 'en', label: 'English' },
  { code: 'ar', label: 'العربية' },
  { code: 'ur', label: 'اردو' },
] as const;

export function LanguageSwitcher() {
  const { locale } = useLocale();
  const switchTo = useSwitchLocale();
  const { t } = useTranslation();

  return (
    <label className="flex items-center gap-1">
      <span className="sr-only">{t('common.language', 'Language')}</span>
      <select
        value={locale}
        onChange={(e) => {
          e.preventDefault();
          switchTo(e.target.value as typeof locale);
        }}
        className="rounded-lg border border-ink/10 bg-surface px-2 py-1.5 text-sm text-ink focus:border-brand-400 focus:outline-none"
        aria-label={t('common.language', 'Language')}
      >
        {LANGS.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  );
}
