import { getTranslations, setRequestLocale } from 'next-intl/server';
import { Link } from '@/i18n/navigation';

export default async function NotFound({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main className="min-h-dvh flex flex-col items-center justify-center px-4 text-center">
      <h1 className="display text-5xl font-bold text-ink">404</h1>
      <p className="mt-4 text-lg text-ink-soft">
        {t('common.error')}: {t('home.landsEmpty')}
      </p>
      <Link
        href="/home"
        className="mt-6 rounded-[var(--radius-card)] bg-water px-5 py-3 text-sm font-semibold text-white hover:opacity-90"
      >
        {t('cover.enterPublic')}
      </Link>
    </main>
  );
}
