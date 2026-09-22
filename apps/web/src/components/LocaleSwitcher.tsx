import { Link } from '@/i18n/navigation';
import { locales, isRtl, type AppLocale } from '@/i18n/routing';

const LABELS: Record<AppLocale, string> = {
  fa: 'فارسی',
  en: 'English',
  ar: 'العربية',
  ur: 'اردو',
  de: 'Deutsch',
  es: 'Español',
  fr: 'Français',
  hi: 'हिन्दी',
  it: 'Italiano',
  ms: 'Bahasa Melayu',
  pt: 'Português',
  ru: 'Русский',
  zh: '中文',
  bn: 'বাংলা',
};

export function LocaleSwitcher({ current, label }: { current: string; label: string }) {
  return (
    <nav aria-label={label} className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      {locales.map((locale) => {
        const active = locale === current;
        return (
          <Link
            key={locale}
            href="/"
            locale={locale}
            hrefLang={locale}
            dir={isRtl(locale) ? 'rtl' : 'ltr'}
            aria-current={active ? 'true' : undefined}
            className={
              active
                ? 'font-semibold text-water underline underline-offset-4'
                : 'text-ink-soft hover:text-ink'
            }
          >
            {LABELS[locale]}
          </Link>
        );
      })}
    </nav>
  );
}
