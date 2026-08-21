'use client';
import { useI18n } from '../lib/i18n-context';
import { useTheme } from '../lib/theme-context';

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
  const { colors } = useTheme();

  return (
    <select
      id="language-switcher"
      value={locale}
      onChange={(e) => setLocale(e.target.value)}
      aria-label={t('language_label')}
      title={t('language_label')}
      style={{
        padding: '8px 12px',
        borderRadius: '10px',
        border: `1px solid ${colors.border}`,
        background: colors.cardBg,
        color: colors.text,
        fontSize: '0.875rem',
        cursor: 'pointer',
        maxWidth: '180px',
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
