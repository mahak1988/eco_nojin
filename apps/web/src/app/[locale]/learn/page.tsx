import { getTranslations, setRequestLocale } from 'next-intl/server';
import { EmptyState } from '@/components/EmptyState';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

/** T12 — honest empty library: content is pending, and we say so. */
export default async function LearnPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="display text-balance text-4xl font-bold text-ink">{t('learn.title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('learn.lead')}</p>
        <div className="mt-8">
          <EmptyState message={t('learn.emptyTitle')} detail={t('learn.emptyDesc')} />
        </div>
      </div>
    </main>
  );
}
