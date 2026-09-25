import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import {
  WorkspaceDataGrid,
  type WorkspaceGridColumn,
} from '@/components/workspace/WorkspaceDataGrid';
import { WorkspacePageHeader } from '@/components/workspace/WorkspacePageHeader';
import {
  WorkspaceCapabilityTable,
  WorkspaceScopeNote,
  WorkspaceSourceNote,
  WorkspaceUnavailable,
} from '@/components/workspace/WorkspaceStates';
import { formatTimestamp, readAuditEvents } from '@/lib/workspaces/data';
import { accessRole, authorizeWorkspace, workspaceToken } from '@/lib/workspaces/guard';
import {
  getWorkspacePage,
  WORKSPACE_SECURITY_EVENTS_ENDPOINT,
  workspacePageHref,
} from '@/lib/workspaces/registry';
import { workspaceGet } from '@/lib/workspaces/server';

// The event stream is read from the gateway per request and never cached.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('operations-events');
const BRIDGE_EVENTS = PAGE.capabilities.find((capability) => capability.id === 'bridge-events');

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

export default async function OperationsEventsPage({
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
  const events = await workspaceGet<unknown>(
    workspaceToken(access.status === 'authorized' ? access.session : null),
    WORKSPACE_SECURITY_EVENTS_ENDPOINT,
  );
  const rows = events.ok ? readAuditEvents(events.data) : [];
  const notProvided = t('auth.session.unknown');

  const columns: readonly WorkspaceGridColumn<(typeof rows)[number]>[] = [
    {
      id: 'occurred',
      labelKey: 'auth.session.memberSince',
      search: (row) => row.occurredAt,
      compare: (a, b) => a.occurredAt.localeCompare(b.occurredAt),
      render: (row) => (
        <span className="num text-xs text-ink-soft">
          {formatTimestamp(row.occurredAt, locale, notProvided)}
        </span>
      ),
    },
    {
      id: 'kind',
      labelKey: 'statusPage.label',
      search: (row) => row.kind,
      compare: (a, b) => a.kind.localeCompare(b.kind),
      render: (row) => <span className="num text-xs text-ink-soft">{row.kind || notProvided}</span>,
    },
    {
      id: 'action',
      labelKey: 'common.open',
      search: (row) => row.action,
      compare: (a, b) => a.action.localeCompare(b.action),
      render: (row) => <span className="text-sm text-ink">{row.action}</span>,
    },
    {
      id: 'decision',
      labelKey: 'statusPage.state',
      search: (row) => row.decision,
      compare: (a, b) => a.decision.localeCompare(b.decision),
      render: (row) => <span className="num text-xs text-ink-soft">{row.decision}</span>,
    },
    {
      id: 'severity',
      labelKey: 'common.limits',
      search: (row) => row.severity,
      compare: (a, b) => a.severity.localeCompare(b.severity),
      render: (row) => (
        <span className="num text-xs text-ink-soft">{row.severity || notProvided}</span>
      ),
    },
  ];

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <section className="card mt-6 p-4" aria-labelledby="workspace-events-scope">
        <h2 id="workspace-events-scope" className="field-label">
          {t('common.limits')}
        </h2>
        <p className="mt-2 text-sm text-ink-soft">{t('market.template.unavailableDescription')}</p>
        <p className="num mt-2 break-words text-xs text-ink-faint">
          {`${WORKSPACE_SECURITY_EVENTS_ENDPOINT} · non-personal`}
        </p>
      </section>

      <section className="mt-6" aria-labelledby="workspace-events">
        <h2 id="workspace-events" className="field-label">
          {t('market.template.source')}
        </h2>
        <div className="mt-3">
          {events.ok ? (
            <WorkspaceDataGrid
              id="workspace-events-caption"
              caption={t('statusPage.subtitle')}
              source={WORKSPACE_SECURITY_EVENTS_ENDPOINT}
              basePath={workspacePageHref(locale, PAGE.path)}
              searchParams={query}
              columns={columns}
              rows={rows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <WorkspaceUnavailable
              source={WORKSPACE_SECURITY_EVENTS_ENDPOINT}
              status={events.status}
              detail={events.ok ? undefined : events.error}
            />
          )}
        </div>
      </section>

      {BRIDGE_EVENTS ? (
        <section className="mt-6" aria-labelledby="workspace-bridge-state">
          <h2 id="workspace-bridge-state" className="field-label">
            {t('statusPage.state')}
          </h2>
          <div className="mt-3">
            <WorkspaceUnavailable
              source={BRIDGE_EVENTS.gap}
              detail={t('market.template.unavailableDescription')}
            />
          </div>
        </section>
      ) : null}

      <WorkspaceScopeNote page={PAGE} role={accessRole(access)} id="workspace-scope" />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={PAGE.capabilities} />

      <WorkspaceSourceNote source={WORKSPACE_SECURITY_EVENTS_ENDPOINT} ok={events.ok} />
    </div>
  );
}
