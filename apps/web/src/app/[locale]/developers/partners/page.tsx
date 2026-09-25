import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { SITE_URL as BASE_URL } from '@/config/site';
import { Link } from '@/i18n/navigation';
import { apiGet } from '@/lib/api/client';

const ROUTE = 'developers/partners';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('developers');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/${ROUTE}`,
      title: t('title'),
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/${ROUTE}`,
      languages: {
        fa: `${BASE_URL}/fa/${ROUTE}`,
        en: `${BASE_URL}/en/${ROUTE}`,
      },
    },
  };
}

export default async function PartnersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('developers');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const template = await getTranslations('market.template');

  // No partner registry is registered in the contract; probe the organization
  // surfaces instead of naming partners without a record.
  const surfaces = await Promise.all(
    ['/api/v1/organizations', '/api/v1/pilot/stats'].map(async (path) => ({
      path,
      reachable: (await apiGet<unknown>(path)).ok,
    })),
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <span className="chip num font-mono">{ROUTE}</span>
        <h1 className="display mt-3 text-4xl font-bold text-ink">{t('title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <StatusDot state="down" label={status('unavailable')} />
          <ProvenanceStamp
            source={statusPage('endpoint')}
            label={statusPage('endpoint')}
            method={statusPage('state')}
          />
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-semibold text-ink">{template('unavailableTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{template('unavailableDescription')}</p>
          <ul className="mt-4 grid gap-2">
            {surfaces.map((surface) => (
              <li key={surface.path} className="flex items-center justify-between gap-3 text-sm">
                <span className="font-mono text-xs text-ink-soft">{surface.path}</span>
                <span className={surface.reachable ? 'text-forest' : 'text-copper'}>
                  {surface.reachable ? common('live') : status('unavailable')}
                </span>
              </li>
            ))}
          </ul>
        </Card>

        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('contractTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('contractDescription')}</p>
          </div>
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('nextTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('nextDescription')}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4">
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
          <ListBlock title={common('next')} items={t.raw('next') as string[]} tone="moss" />
        </div>

        <nav className="mt-6">
          <Link href="/developers" className="text-sm text-water hover:underline">
            {common('back')}
          </Link>
        </nav>
      </div>
    </main>
  );
}
