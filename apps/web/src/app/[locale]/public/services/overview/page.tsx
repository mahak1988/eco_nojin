import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { toDataState } from '../../data-states';

export const dynamic = 'force-dynamic';

// Each health route is read directly so the page reports the gateway's own
// status value, never a locally derived "operational" guess.
const HEALTH_ENDPOINTS = [
  { path: '/api/v1/platform/health' },
  { path: '/api/v1/satellite/health' },
  { path: '/api/v1/voice/health' },
  { path: '/api/v1/ai/health' },
  { path: '/api/v1/land/health' },
  { path: '/api/v1/blockchain/health' },
  { path: '/api/v1/automation/health' },
  { path: '/api/v1/ecowallet/health' },
] as const;

type HealthPayload = {
  status?: string;
  service?: string;
  module?: string;
  cpp_available?: boolean;
  db_backend?: string;
  db_reachable?: boolean;
  profiles_count?: number;
  error?: string;
};

export default async function ServicesOverviewPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const servicesText = await getTranslations('services');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');

  const results = await Promise.all(
    HEALTH_ENDPOINTS.map((endpoint) => apiGet<HealthPayload>(endpoint.path)),
  );
  const rows = HEALTH_ENDPOINTS.map((endpoint, index) => ({
    path: endpoint.path,
    result: results[index],
  }));
  const reachable = rows.filter((row) => row.result.ok);
  const operational = reachable.filter(
    (row) => row.result.ok && row.result.data.status === 'operational',
  );
  const degraded = reachable.length - operational.length;
  const overviewState = toDataState(
    HEALTH_ENDPOINTS.map((endpoint) => endpoint.path).join(' '),
    reachable.length > 0
      ? { ok: true, data: null, status: 200 }
      : { ok: false, error: rows[0]?.result.ok === false ? rows[0].result.error : '', status: 503 },
    reachable.length,
  );

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={HEALTH_ENDPOINTS[0].path}
          label={servicesText('title')}
          verified={reachable.length > 0}
          method={HEALTH_ENDPOINTS[0].path}
        >
          <h1 className="display text-4xl font-bold text-ink">{servicesText('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{servicesText('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{servicesText('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{servicesText('audience')}</p>
        <ul className="mt-4 max-w-2xl list-inside list-disc space-y-1 text-sm text-ink-soft">
          {servicesText.raw('evidence').map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <ul className="mt-4 max-w-2xl list-inside list-disc space-y-1 text-sm text-ink-soft">
          {servicesText.raw('limits').map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <ul className="mt-4 max-w-2xl list-inside list-disc space-y-1 text-sm text-ink-soft">
          {servicesText.raw('next').map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-sm font-semibold text-ink-soft">{servicesText('title')}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <Card density="compact">
            <div className="text-sm text-ink-soft">{status('realData')}</div>
            <div className="num mt-1 text-3xl font-semibold text-ink">{reachable.length}</div>
          </Card>
          <Card density="compact">
            <div className="text-sm text-ink-soft">{common('live')}</div>
            <div className="num mt-1 text-3xl font-semibold text-forest">{operational.length}</div>
          </Card>
          <Card density="compact">
            <div className="text-sm text-ink-soft">{status('unavailable')}</div>
            <div className="num mt-1 text-3xl font-semibold text-copper">{degraded}</div>
          </Card>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-10">
        <h2 className="text-sm font-semibold text-ink-soft">{common('view')}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((row) => (
            <div key={row.path} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-ink">
                    {row.result.ok ? row.path : status('unavailable')}
                  </h3>
                  <p className="mt-1 font-mono text-xs text-ink-soft">{row.path}</p>
                </div>
                <ProvenanceStamp source={row.path} verified={row.result.ok} method={row.path} />
              </div>
              <div className="mt-3">
                <StatusDot
                  state={row.result.ok && row.result.data.status === 'operational' ? 'ok' : 'down'}
                  label={
                    row.result.ok && row.result.data.status
                      ? row.result.data.status
                      : row.result.ok
                        ? status('unavailable')
                        : status('unavailable')
                  }
                />
              </div>
              {row.result.ok && row.result.data.error ? (
                <p className="num mt-3 font-mono text-xs text-ink-soft">{row.result.data.error}</p>
              ) : null}
            </div>
          ))}
        </div>
        <p className="mt-6 flex flex-wrap items-center gap-2 text-xs text-ink-soft">
          <ProvenanceStamp
            source={HEALTH_ENDPOINTS[0].path}
            verified={overviewState.kind === 'ready'}
            method={HEALTH_ENDPOINTS[0].path}
          />
          <span>{status('realData')}</span>
          <span className="num">{reachable.length}</span>
        </p>
      </section>

      <OwnerFooter />
    </main>
  );
}
