import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('trust');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/trust/report`,
      title: t('title'),
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/trust/report`,
      languages: {
        fa: `${BASE_URL}/fa/trust/report`,
        en: `${BASE_URL}/en/trust/report`,
      },
    },
  };
}

export default async function ReportPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('trust');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const template = await getTranslations('market.template');

  // No annual report resource is registered; the counter surfaces that could
  // carry one are probed so nothing is published from a guess.
  const probes = await Promise.all(
    ['/api/v1/pilot/stats', '/api/v1/mrv/public/dashboard-summary'].map(async (path) => {
      const result = await apiGet<unknown>(path);
      return { path, status: result.status, reachable: result.ok };
    }),
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <span className="chip num font-mono">trust/report</span>
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
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-ink-soft">
                  <th className="py-2 pe-4 text-start font-medium">{statusPage('endpoint')}</th>
                  <th className="py-2 text-start font-medium">{statusPage('result')}</th>
                  <th className="py-2 ps-4 text-start font-medium">{statusPage('state')}</th>
                </tr>
              </thead>
              <tbody>
                {probes.map((probe) => (
                  <tr key={probe.path} className="border-b border-line/50">
                    <td className="py-2 pe-4 font-mono text-xs text-ink">{probe.path}</td>
                    <td className="num py-2 text-ink-soft">
                      {probe.status === 0 ? '—' : probe.status}
                    </td>
                    <td
                      className={`py-2 ps-4 text-xs ${probe.reachable ? 'text-forest' : 'text-copper'}`}
                    >
                      {probe.reachable ? common('live') : status('unavailable')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <div className="mt-6 grid gap-4">
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
          <ListBlock title={common('next')} items={t.raw('next') as string[]} tone="moss" />
        </div>
      </div>
    </main>
  );
}
