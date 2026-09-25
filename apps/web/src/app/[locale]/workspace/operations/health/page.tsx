import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import {
  WorkspaceDataGrid,
  type WorkspaceGridColumn,
} from '@/components/workspace/WorkspaceDataGrid';
import { WorkspacePageHeader } from '@/components/workspace/WorkspacePageHeader';
import {
  WorkspaceCapabilityTable,
  WorkspaceScopeNote,
  WorkspaceSourceNote,
} from '@/components/workspace/WorkspaceStates';
import { readHealthDetail, readHealthState } from '@/lib/workspaces/data';
import { accessRole, authorizeWorkspace, workspaceToken } from '@/lib/workspaces/guard';
import {
  getWorkspacePage,
  type WorkspaceCapability,
  workspacePageHref,
} from '@/lib/workspaces/registry';
import { workspaceGet } from '@/lib/workspaces/server';

// Health is probed per request through the BFF; nothing in this matrix is cached.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('operations-health');
const PROBED = PAGE.capabilities.filter(
  (capability): capability is WorkspaceCapability & { endpoint: string } =>
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
    title: t(PAGE.labelKey),
    description: t(PAGE.leadKey),
    robots: { index: false, follow: false },
  };
}

export default async function OperationsHealthPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const query = await searchParams;
  setRequestLocale(locale);
  const t = await getTranslations();

  const access = await authorizeWorkspace();
  const token = workspaceToken(access.status === 'authorized' ? access.session : null);

  // Only endpoints the gateway really registers are probed, each through the BFF
  // with the server session. Nothing is invented for a missing contract.
  const results = await Promise.all(
    PROBED.map(async (capability) => {
      const result = await workspaceGet<unknown>(token, capability.endpoint);
      return {
        id: capability.id,
        label: t(capability.labelKey),
        endpoint: capability.endpoint,
        state: result.ok ? readHealthState(result.data) : ('unavailable' as const),
        http: result.status,
        detail: result.ok ? readHealthDetail(result.data) : result.error,
      } satisfies HealthRow;
    }),
  );

  const rows: HealthRow[] = results;
  const degraded = rows.filter((row) => row.state === 'unavailable');
  const observedAt = new Date().toISOString();

  const columns: readonly WorkspaceGridColumn<HealthRow>[] = [
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
      search: (row) => row.state,
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
    {
      id: 'detail',
      labelKey: 'market.template.method',
      search: (row) => row.detail,
      render: (row) => <span className="num break-all text-xs text-ink-faint">{row.detail}</span>,
    },
  ];

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <section className="mt-6" aria-labelledby="workspace-health-matrix">
        <h2 id="workspace-health-matrix" className="field-label">
          {t('statusPage.service')}
        </h2>
        <div className="mt-3">
          <WorkspaceDataGrid
            id="workspace-health-caption"
            caption={t('statusPage.subtitle')}
            source={ENDPOINT_LIST}
            basePath={workspacePageHref(locale, PAGE.path)}
            searchParams={query}
            columns={columns}
            rows={rows}
            rowId={(row) => row.id}
            emptyMessage={t('statusLine.unavailable')}
          />
        </div>
      </section>

      <section className="mt-6" aria-labelledby="workspace-health-failures">
        <h2 id="workspace-health-failures" className="field-label">
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

      <WorkspaceScopeNote page={PAGE} role={accessRole(access)} id="workspace-scope" />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={PAGE.capabilities} />

      <WorkspaceSourceNote
        source={ENDPOINT_LIST}
        ok={degraded.length === 0}
        observedAt={observedAt}
      />
    </div>
  );
}
