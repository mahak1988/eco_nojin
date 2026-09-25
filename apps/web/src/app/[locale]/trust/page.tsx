import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Link } from '@/i18n/navigation';

export const dynamic = 'force-dynamic';

export default async function TrustPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const common = await getTranslations('common');

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
            <p className="mt-2 text-sm text-ink">{t('trust.what')}</p>
          </section>
          <section className="card p-5">
            <p className="mt-2 text-sm text-ink">{t('trust.audience')}</p>
          </section>
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Link href="/status" className="btn btn-primary">
            {t('statusPage.title')}
          </Link>
          <StatusDot state="down" label={t('statusLine.unavailable')} />
          <ProvenanceStamp
            source={t('market.template.source')}
            label={t('market.template.source')}
            verified={false}
            method={t('market.template.method')}
          />
        </div>

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={common('evidence')}
            items={t.raw('trust.evidence') as string[]}
            tone="neutral"
          />
          <ListBlock
            title={common('limits')}
            items={t.raw('trust.limits') as string[]}
            tone="clay"
          />
          <ListBlock title={common('next')} items={t.raw('trust.next') as string[]} tone="moss" />
        </div>
      </div>
    </main>
  );
}
