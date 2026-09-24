import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export default async function DevelopersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const cards = [
    { title: t('developers.docsTitle'), desc: t('developers.docsDesc') },
    { title: t('developers.toolsTitle'), desc: t('developers.toolsDesc') },
    { title: t('developers.changesTitle'), desc: t('developers.changesDesc') },
  ];

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="display text-balance text-4xl font-bold text-ink sm:text-5xl">
          {t('developers.title')}
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('developers.lead')}</p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <section className="card p-5">
            <h2 className="field-label">{t('common.whatLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('developers.what')}</p>
          </section>
          <section className="card p-5">
            <h2 className="field-label">{t('common.audienceLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('developers.audience')}</p>
          </section>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {cards.map((card) => (
            <article key={card.title} className="card flex flex-col gap-2 p-5">
              <h2 className="text-base font-semibold text-ink">{card.title}</h2>
              <p className="text-sm text-ink-soft">{card.desc}</p>
            </article>
          ))}
        </div>

        <p className="mt-6 text-sm text-ink-soft">{t('developers.publicNote')}</p>

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={t('common.limitsLabel')}
            items={t.raw('developers.limits') as string[]}
            tone="clay"
          />
          <ListBlock
            title={t('common.nextLabel')}
            items={t.raw('developers.next') as string[]}
            tone="moss"
          />
        </div>
      </div>
    </main>
  );
}
