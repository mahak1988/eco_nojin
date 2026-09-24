import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Link } from '@/i18n/navigation';

export const dynamic = 'force-dynamic';

export default async function TrustPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const cards = [
    { title: t('trust.provenanceTitle'), desc: t('trust.provenanceDesc') },
    { title: t('trust.registryTitle'), desc: t('trust.registryDesc') },
    { title: t('trust.disclosureTitle'), desc: t('trust.disclosureDesc') },
  ];

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="display text-balance text-4xl font-bold text-ink sm:text-5xl">
          {t('trust.title')}
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('trust.lead')}</p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <section className="card p-5">
            <h2 className="field-label">{t('common.whatLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('trust.what')}</p>
          </section>
          <section className="card p-5">
            <h2 className="field-label">{t('common.audienceLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('trust.audience')}</p>
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

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Link href="/status" className="btn btn-primary">
            {t('trust.statusCta')}
          </Link>
          <ProvenanceStamp source={t('trust.provenanceTitle')}>
            {t('statusLine.realData')}
          </ProvenanceStamp>
        </div>

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={t('common.limitsLabel')}
            items={t.raw('trust.limits') as string[]}
            tone="clay"
          />
          <ListBlock
            title={t('common.nextLabel')}
            items={t.raw('trust.next') as string[]}
            tone="moss"
          />
        </div>
      </div>
    </main>
  );
}
