'use client';
import { useI18n } from '../lib/i18n-context';

const languages = [
  { code: 'en', name: 'English' },
  { code: 'fa', name: 'فارسی' },
  { code: 'ar', name: 'العربية' },
  { code: 'fr', name: 'Français' },
  { code: 'es', name: 'Español' },
  { code: 'pt', name: 'Português' },
  { code: 'ru', name: 'Русский' },
  { code: 'hi', name: 'हिन्दी' },
  { code: 'zh', name: '中文' },
  { code: 'ur', name: 'اردو' },
  { code: 'bn', name: 'বাংলা' },
  { code: 'ms', name: 'Melayu' },
  { code: 'de', name: 'Deutsch' },
  { code: 'it', name: 'Italiano' },
];

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <select
      id="language-switcher"
      value={locale}
      onChange={(e) => setLocale(e.target.value)}
      aria-label={t('language_label')}
      title={t('language_label')}
      style={{
        padding: '8px',
        borderRadius: '4px',
        border: '1px solid #ccc',
        fontSize: '1rem',
        maxWidth: '160px',
      }}
    >
      {languages.map((lang) => (
        <option key={lang.code} value={lang.code} lang={lang.code}>
          {lang.name}
        </option>
      ))}
    </select>
  );
}
