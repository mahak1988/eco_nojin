import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { publicEnv } from '@/lib/config/public-env';

export const dynamic = 'force-dynamic';

type HttpMethod = 'GET';

/**
 * Read endpoints taken from the API gateway OpenAPI contract that answer
 * without a session. Nothing is listed that is not registered, and every row
 * below is probed per request so the state column is an observation rather
 * than a claim.
 */
const PUBLIC_READ_ENDPOINTS: { method: HttpMethod; path: string }[] = [
  { method: 'GET', path: '/api/v1/platform/health' },
  { method: 'GET', path: '/api/v1/platform/stats' },
  { method: 'GET', path: '/api/v1/platform/landscapes' },
  { method: 'GET', path: '/api/v1/health' },
  { method: 'GET', path: '/api/v1/models' },
  { method: 'GET', path: '/api/v1/models/cpp-status' },
  { method: 'GET', path: '/api/v1/models/pinn-status' },
  { method: 'GET', path: '/api/v1/hydroma/models' },
  { method: 'GET', path: '/api/v1/hydroma/validation' },
  { method: 'GET', path: '/api/v1/tool-registry' },
  { method: 'GET', path: '/api/v1/tool-registry/categories' },
  { method: 'GET', path: '/api/v1/tool-registry/domains' },
  { method: 'GET', path: '/api/v1/tool-registry/phases' },
  { method: 'GET', path: '/api/v1/science/citations/index' },
  { method: 'GET', path: '/api/v1/science/datasets' },
  { method: 'GET', path: '/api/v1/science/model-cards' },
  { method: 'GET', path: '/api/v1/science/zenodo/status' },
  { method: 'GET', path: '/api/v1/legal-texts' },
  { method: 'GET', path: '/api/v1/legal-texts/slugs' },
  { method: 'GET', path: '/api/v1/legal-texts/locales' },
  { method: 'GET', path: '/api/v1/marketplace/products' },
  { method: 'GET', path: '/api/v1/marketplace/stats' },
  { method: 'GET', path: '/api/v1/ai/health' },
  { method: 'GET', path: '/api/v1/voice/health' },
  { method: 'GET', path: '/api/v1/voice/status' },
  { method: 'GET', path: '/api/v1/voice/languages' },
  { method: 'GET', path: '/api/v1/support/personas' },
  { method: 'GET', path: '/api/v1/content/search' },
  { method: 'GET', path: '/api/v1/mrv/public/dashboard-summary' },
  { method: 'GET', path: '/api/v1/pilot/stats' },
  { method: 'GET', path: '/api/v1/manual/status' },
];

async function mapWithConcurrency<T, R>(
  items: T[],
  limit: number,
  mapper: (item: T) => Promise<R>,
): Promise<R[]> {
  const results = new Array<R>(items.length);
  let nextIndex = 0;
  async function worker(): Promise<void> {
    while (nextIndex < items.length) {
      const index = nextIndex++;
      results[index] = await mapper(items[index]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}

export default async function DevelopersApiPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);
  const t = await getTranslations('developers');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const template = await getTranslations('market.template');

  const probes = await mapWithConcurrency(PUBLIC_READ_ENDPOINTS, 4, async ({ method, path }) => {
    const result = await apiGet<unknown>(path, { method });
    return { method, path, status: result.status, reachable: result.ok };
  });

  const reachable = probes.filter((probe) => probe.reachable).length;
  const base = publicEnv.apiBaseUrl;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-balance text-4xl font-bold text-ink sm:text-5xl">
          {t('title')}
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <ProvenanceStamp
            source={publicEnv.apiBaseUrl}
            label={publicEnv.apiBaseUrl}
            method={statusPage('endpoint')}
          />
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="field-label">{statusPage('endpoint')}</h2>
          <code className="mt-2 block rounded border border-line bg-surface-2 px-3 py-2 font-mono text-sm text-ink">
            {base}
          </code>
          <p className="mt-2 text-sm text-ink-soft">
            {statusPage('rows')}:{' '}
            {new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en').format(reachable)} /{' '}
            {new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en').format(probes.length)} آ·{' '}
            {statusLine('realData')}
          </p>
        </Card>

        <Card density="cozy" className="mt-6">
          <h2 className="field-label">{template('contractTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{template('contractDescription')}</p>
        </Card>

        <Card density="compact" className="mt-6">
          <h2 className="field-label">{statusPage('label')}</h2>
          <div className="mt-3 overflow-x-auto">
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
                    <td className="py-2 pe-4">
                      <span className="me-2 rounded bg-water/10 px-2 py-0.5 font-mono text-xs font-semibold text-water">
                        {probe.method}
                      </span>
                      <span className="font-mono text-xs text-ink">{probe.path}</span>
                    </td>
                    <td className="num py-2 text-ink-soft">
                      {probe.status === 0 ? '—' : probe.status}
                    </td>
                    <td
                      className={`py-2 ps-4 text-xs ${probe.reachable ? 'text-forest' : 'text-copper'}`}
                    >
                      {probe.reachable ? common('live') : statusLine('unavailable')}
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
