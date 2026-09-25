import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

export const dynamic = 'force-dynamic';

/**
 * Carbon registry reads exist in the contract but every one of them is
 * authenticated, so the public page has nothing it may show. Each candidate is
 * probed and the real status is rendered.
 */
const CARBON_SURFACES = [
  '/api/v1/carbon/verra/standards',
  '/api/v1/carbon/credits/balance',
  '/api/v1/carbon/credits/{token_id}/verify',
];

export default async function CarbonRegistryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('trust');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const template = await getTranslations('market.template');

  const probes = await Promise.all(
    CARBON_SURFACES.map(async (path) => {
      // Path templates are not callable; the concrete sibling is probed instead
      // and the registered path is what the table reports.
      const probePath = path.includes('{') ? path.replace('{token_id}', 'probe') : path;
      const result = await apiGet<unknown>(probePath);
      return { path, status: result.status, reachable: result.ok };
    }),
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <span className="chip num font-mono">trust/carbon-registry</span>
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
          <ListBlock
            title={common('evidence')}
            items={t.raw('evidence') as string[]}
            tone="neutral"
          />
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
          <ListBlock title={common('next')} items={t.raw('next') as string[]} tone="moss" />
        </div>
      </div>
    </main>
  );
}
