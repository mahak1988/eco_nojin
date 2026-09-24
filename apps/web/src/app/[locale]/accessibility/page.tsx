import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export default async function AccessibilityPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="display text-balance text-4xl font-bold text-ink sm:text-5xl">
          {t('accessibility.title')}
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('accessibility.lead')}</p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <section className="card p-5">
            <h2 className="field-label">{t('common.whatLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('accessibility.what')}</p>
          </section>
          <section className="card p-5">
            <h2 className="field-label">{t('common.audienceLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('accessibility.audience')}</p>
          </section>
          <section className="card p-5">
            <h2 className="field-label">{t('accessibility.standardTitle')}</h2>
            <p className="mt-2 text-sm text-ink">{t('accessibility.standardDesc')}</p>
          </section>
          <section className="card p-5">
            <h2 className="field-label">{t('accessibility.feedbackTitle')}</h2>
            <p className="mt-2 text-sm text-ink">{t('accessibility.feedbackDesc')}</p>
          </section>
        </div>

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={t('common.limitsLabel')}
            items={t.raw('accessibility.limits') as string[]}
            tone="clay"
          />
          <ListBlock
            title={t('common.nextLabel')}
            items={t.raw('accessibility.next') as string[]}
            tone="moss"
          />
        </div>
      </div>
    </main>
  );
}
