import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';

export default async function OfflinePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('offline');

  return (
    <main className="mx-auto flex min-h-[60vh] max-w-2xl flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="font-mono text-sm text-ink-soft">{t('code')}</p>
      <h1 className="text-2xl font-semibold text-ink">{t('title')}</h1>
      <p className="text-ink-soft">{t('description')}</p>
      <Link href={`/${locale}/home`} className="font-semibold text-[var(--color-forest)]">
        {t('retry')}
      </Link>
    </main>
  );
}
