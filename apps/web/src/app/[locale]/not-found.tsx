import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';

export default function NotFound() {
  const t = useTranslations('statusPage');

  return (
    <main className="mx-auto flex min-h-[50vh] max-w-2xl flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold text-ink">{t('notFoundTitle')}</h1>
      <p className="text-sm text-ink-soft">{t('notFoundDetail')}</p>
      <Link href="/" className="font-semibold text-[var(--color-forest)]">
        {t('notFoundHome')}
      </Link>
    </main>
  );
}
