import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { Link } from '@/i18n/navigation';
import { apiGet } from '@/lib/api/client';

export const dynamic = 'force-dynamic';

/**
 * Registry endpoints that are registered in the OpenAPI contract and readable
 * without a session. Each row reports the count the gateway returned for this
 * request — never a hard-coded figure.
 */
const REGISTRY_ENDPOINTS = [
  '/api/v1/models',
  '/api/v1/hydroma/models',
  '/api/v1/tool-registry',
  '/api/v1/science/citations/index',
  '/api/v1/science/datasets',
  '/api/v1/science/model-cards',
  '/api/v1/hydroma/validation',
] as const;

const SUB_ROUTES = [
  '/developers/api',
  '/developers/status-api',
  '/developers/playground',
  '/developers/webhooks',
  '/developers/sdks',
  '/developers/cookbooks',
  '/developers/changelog',
  '/developers/partners',
] as const;

type RegistryRow = { path: string; reachable: boolean; count: number | null };

function readCount(data: unknown): number | null {
  if (Array.isArray(data)) return data.length;
  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>;
    for (const key of ['count', 'total']) {
      const value = record[key];
      if (typeof value === 'number') return value;
    }
  }
  return null;
}

export default async function DevelopersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');

  const rows: RegistryRow[] = await Promise.all(
    REGISTRY_ENDPOINTS.map(async (path) => {
      const result = await apiGet<unknown>(path);
      return { path, reachable: result.ok, count: result.ok ? readCount(result.data) : null };
    }),
  );

  const reachable = rows.filter((row) => row.reachable).length;
  const state: DotState = reachable === 0 ? 'down' : reachable === rows.length ? 'ok' : 'warn';

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('developers.title')}
          lead={t('developers.lead')}
          what={t('developers.what')}
          audience={t('developers.audience')}
          evidence={t.raw('developers.evidence') as string[]}
          limits={t.raw('developers.limits') as string[]}
          next={t.raw('developers.next') as string[]}
        />

        <section className="mt-10" aria-labelledby="registry-heading">
          <h2 id="registry-heading" className="field-label">
            {statusPage('endpoint')}
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <StatusDot
              state={state}
              label={state === 'down' ? statusLine('unavailable') : statusLine('realData')}
            />
            <span className="num text-xs text-ink-soft">
              {common('total')}:{' '}
              {new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en').format(reachable)} /{' '}
              {rows.length}
            </span>
          </div>

          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-ink-soft">
                  <th className="py-2 pe-4 text-start font-medium">{statusPage('label')}</th>
                  <th className="py-2 text-start font-medium">{statusPage('result')}</th>
                  <th className="py-2 ps-4 text-start font-medium">{statusPage('state')}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.path} className="border-b border-line/50">
                    <td className="py-2 pe-4 font-mono text-xs text-ink">{row.path}</td>
                    <td className="num py-2 text-ink-soft">
                      {row.count === null ? '—' : row.count}
                    </td>
                    <td
                      className={`py-2 ps-4 text-xs ${row.reachable ? 'text-forest' : 'text-copper'}`}
                    >
                      {row.reachable ? common('live') : statusLine('unavailable')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-10" aria-labelledby="routes-heading">
          <h2 id="routes-heading" className="field-label">
            {statusPage('service')}
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
      </div>
    </main>
  );
}
