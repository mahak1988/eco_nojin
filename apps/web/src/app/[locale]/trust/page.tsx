import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Link } from '@/i18n/navigation';

export const dynamic = 'force-dynamic';

const SUB_ROUTES = [
  '/trust/audits',
  '/trust/carbon-registry',
  '/trust/provenance',
  '/trust/disclosure',
  '/trust/report',
  '/trust/sanctions',
] as const;

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
            <h2 className="field-label">{common('whatLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('trust.what')}</p>
          </section>
          <section className="card p-5">
            <h2 className="field-label">{common('audienceLabel')}</h2>
            <p className="mt-2 text-sm text-ink">{t('trust.audience')}</p>
          </section>
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Link href="/status" className="btn btn-primary">
            {t('statusPage.title')}
          </Link>
          <StatusDot state="down" label={t('statusLine.unavailable')} />
          <ProvenanceStamp
            source={t('statusPage.endpoint')}
            label={t('statusPage.endpoint')}
            method={t('statusPage.state')}
          />
        </div>

        <section className="mt-10" aria-labelledby="trust-routes">
          <h2 id="trust-routes" className="field-label">
            {t('statusPage.service')}
          </h2>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {SUB_ROUTES.map((route) => (
              <li key={route} className="card flex items-center justify-between gap-3 p-4">
                <span className="font-mono text-xs text-ink">{route}</span>
                <Link href={route} className="text-sm text-water hover:underline">
                  {common('view')}
                </Link>
              </li>
            ))}
          </ul>
        </section>

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
