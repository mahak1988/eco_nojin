import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminDataGrid, type AdminGridColumn } from '@/components/admin/AdminDataGrid';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { AdminCapabilityTable, AdminSourceNote } from '@/components/admin/AdminStates';
import { type AdminCapability, getAdminSection } from '@/components/admin/admin-sections';
import type { AdminResult } from '@/components/admin/admin-server';
import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { StatusDot } from '@/components/StatusDot';

// Health is probed per request; nothing about this matrix may be cached.
export const dynamic = 'force-dynamic';

const section = getAdminSection('system-health');
const PROBED = section.capabilities.filter(
  (capability): capability is AdminCapability & { endpoint: string } =>
    capability.endpoint !== null,
);
const ENDPOINT_LIST = PROBED.map((capability) => capability.endpoint).join(' · ');

type HealthRow = {
  id: string;
  label: string;
  endpoint: string;
  state: 'live' | 'unavailable';
  http: number;
  detail: string;
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('statusPage.service'),
    description: t('statusPage.subtitle'),
    robots: { index: false, follow: false },
  };
}

/**
 * Derives the reported state from the payload itself. A 200 response is not
 * proof of health: a gateway that answers `status: "degraded"` or
 * `available: false` is reported as unavailable.
 */
function deriveState(payload: unknown): 'live' | 'unavailable' {
  if (!payload || typeof payload !== 'object') return 'unavailable';
  const record = payload as Record<string, unknown>;
  if (typeof record.status === 'string') {
    return ['operational', 'ok', 'healthy'].includes(record.status) ? 'live' : 'unavailable';
  }
  if (typeof record.available === 'boolean') return record.available ? 'live' : 'unavailable';
  if (typeof record.db_reachable === 'boolean') {
    return record.db_reachable ? 'live' : 'unavailable';
  }
  return 'live';
}

function detailOf(payload: unknown): string {
  if (!payload || typeof payload !== 'object') return '';
  const record = payload as Record<string, unknown>;
  const parts: string[] = [];
  for (const key of ['status', 'db_backend', 'note', 'version']) {
    const value = record[key];
    if (typeof value === 'string' && value !== '') parts.push(`${key}=${value}`);
  }
  return parts.join(' · ');
}

function rowFor(capability: AdminCapability, result: AdminResult<unknown>): HealthRow {
  const payload = result.ok ? result.data : null;
  return {
    id: capability.id,
    label: capability.labelKey,
    endpoint: capability.endpoint ?? '',
    state: result.ok ? deriveState(payload) : 'unavailable',
    http: result.status,
    detail: result.ok ? detailOf(payload) : result.error,
  };
}

export default async function SystemHealthPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  await params;
  const query = await searchParams;
  setRequestLocale(locale);
  const t = await getTranslations();

  const token = adminToken(await readAdminSession());
  const results = await Promise.all(
    PROBED.map(async (capability) =>
      rowFor(capability, await adminGet<unknown>(token, capability.endpoint)),
    ),
  );

  const rows: HealthRow[] = results.map((row) => ({ ...row, label: t(row.label) }));
  const degraded = rows.filter((row) => row.state === 'unavailable');
  const observedAt = new Date().toISOString();

  const columns: readonly AdminGridColumn<HealthRow>[] = [
    {
      id: 'service',
      labelKey: 'statusPage.service',
      search: (row) => row.label,
      compare: (a, b) => a.label.localeCompare(b.label),
      render: (row) => <span className="font-medium text-ink">{row.label}</span>,
    },
    {
      id: 'state',
      labelKey: 'statusPage.state',
      compare: (a, b) => a.state.localeCompare(b.state),
      render: (row) => (
        <StatusDot
          state={row.state === 'live' ? 'ok' : 'down'}
          label={row.state === 'live' ? t('common.live') : t('statusLine.unavailable')}
        />
      ),
    },
    {
      id: 'endpoint',
      labelKey: 'statusPage.endpoint',
      search: (row) => row.endpoint,
      compare: (a, b) => a.endpoint.localeCompare(b.endpoint),
      render: (row) => <span className="num break-all text-xs text-ink-soft">{row.endpoint}</span>,
    },
    {
      id: 'http',
      labelKey: 'statusPage.result',
      numeric: true,
      compare: (a, b) => a.http - b.http,
      render: (row) => <span className="num">{row.http === 0 ? '—' : row.http}</span>,
    },
  ];

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <section className="mt-6" aria-labelledby="admin-health-matrix">
        <h2 id="admin-health-matrix" className="field-label">
          {t('statusPage.service')}
        </h2>
        <div className="mt-3">
          <AdminDataGrid
            id="admin-health-caption"
            caption={t('statusPage.subtitle')}
            source={ENDPOINT_LIST}
            basePath={`/${locale}/admin/system/health`}
            searchParams={query}
            columns={columns}
            rows={rows}
            rowId={(row) => row.id}
            emptyMessage={t('statusLine.unavailable')}
          />
        </div>
      </section>

      <section className="mt-6" aria-labelledby="admin-health-failures">
        <h2 id="admin-health-failures" className="field-label">
          {t('statusPage.state')}
        </h2>
        {degraded.length === 0 ? (
          <p className="card mt-3 p-4 text-sm text-ink-soft">{t('statusLine.realData')}</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {degraded.map((row) => (
              <li key={row.id} className="card p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="text-sm font-medium text-ink">{row.label}</span>
                  <StatusDot state="down" label={t('statusLine.unavailable')} />
                </div>
                <p className="num mt-2 break-all text-xs text-ink-faint">
                  {row.endpoint}
                  {row.http === 0 ? '' : ` · ${row.http}`}
                </p>
                {row.detail ? <p className="mt-1 text-xs text-ink-soft">{row.detail}</p> : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <AdminCapabilityTable id="admin-health-contract" capabilities={section.capabilities} />

      <AdminSourceNote source={ENDPOINT_LIST} ok={degraded.length === 0} observedAt={observedAt} />
    </div>
  );
}
