import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { WorkspacePageHeader } from '@/components/workspace/WorkspacePageHeader';
import {
  WorkspaceCapabilityTable,
  WorkspaceScopeNote,
  WorkspaceSourceNote,
  WorkspaceUnavailable,
} from '@/components/workspace/WorkspaceStates';
import { readSyncState } from '@/lib/workspaces/data';
import { accessRole, authorizeWorkspace, workspaceToken } from '@/lib/workspaces/guard';
import {
  findWorkspacePageByPath,
  getWorkspacePage,
  WORKSPACE_SYNC_STATUS_ENDPOINT,
  workspacePageHref,
} from '@/lib/workspaces/registry';
import { workspaceGet } from '@/lib/workspaces/server';

// The operations index reads the registered sync status and links the three
// registered operations surfaces.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('operations');
const OPERATIONS_JOBS = PAGE.capabilities.find((capability) => capability.id === 'operations-jobs');
const CHILDREN = ['operations/jobs', 'operations/events', 'operations/health'] as const;

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

export default async function OperationsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const access = await authorizeWorkspace();
  const sync = await workspaceGet<unknown>(
    workspaceToken(access.status === 'authorized' ? access.session : null),
    WORKSPACE_SYNC_STATUS_ENDPOINT,
  );
  const syncState = sync.ok ? readSyncState(sync.data) : null;

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <section className="card mt-6 p-4" aria-labelledby="workspace-operations-sync">
        <h2 id="workspace-operations-sync" className="field-label">
          {t('statusPage.supabase')}
        </h2>
        {syncState ? (
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <dt className="field-label">{t('statusPage.state')}</dt>
              <dd className="mt-1 text-sm text-ink">
                <StatusDot
                  state={syncState.status === 'disabled' ? 'warn' : 'ok'}
                  label={syncState.status ?? t('statusLine.unavailable')}
                />
              </dd>
            </div>
            <div>
              <dt className="field-label">{t('market.template.method')}</dt>
              <dd className="num mt-1 text-sm text-ink">
                {syncState.mode ?? t('auth.session.unknown')}
              </dd>
            </div>
            <div>
              <dt className="field-label">{t('common.total')}</dt>
              <dd className="num mt-1 text-sm text-ink">
                {syncState.pendingEvents === null
                  ? t('auth.session.unknown')
                  : new Intl.NumberFormat(locale).format(syncState.pendingEvents)}
              </dd>
            </div>
            <div>
              <dt className="field-label">{t('statusPage.dbReachable')}</dt>
              <dd className="mt-1 text-sm text-ink">
                <StatusDot
                  state={syncState.cloudConnected === true ? 'ok' : 'down'}
                  label={
                    syncState.cloudConnected === true
                      ? t('common.live')
                      : t('statusLine.unavailable')
                  }
                />
              </dd>
            </div>
          </dl>
        ) : (
          <div className="mt-3">
            <WorkspaceUnavailable
              source={WORKSPACE_SYNC_STATUS_ENDPOINT}
              status={sync.status}
              detail={sync.ok ? undefined : sync.error}
            />
          </div>
        )}
      </section>

      <section className="mt-6" aria-labelledby="workspace-operations-children">
        <h2 id="workspace-operations-children" className="field-label">
          {t('market.template.nextTitle')}
        </h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {CHILDREN.map((path) => {
            const child = findWorkspacePageByPath(path);
            if (!child) return null;
            return (
              <li key={child.id}>
                <Link
                  href={workspacePageHref(locale, child.path)}
                  className="chip min-h-11 hover:bg-[var(--surface-2)]"
                >
                  {t(child.labelKey)}
                  <span className="num ms-2 text-[0.65rem] text-[var(--ink-faint)]">
                    {`/${child.path}`}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </section>

      {OPERATIONS_JOBS ? (
        <section className="mt-6" aria-labelledby="workspace-operations-state">
          <h2 id="workspace-operations-state" className="field-label">
            {t('statusPage.state')}
          </h2>
          <div className="mt-3">
            <WorkspaceUnavailable
              source={OPERATIONS_JOBS.gap}
              detail={t('market.template.unavailableDescription')}
            />
          </div>
        </section>
      ) : null}

      <WorkspaceScopeNote page={PAGE} role={accessRole(access)} id="workspace-scope" />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={PAGE.capabilities} />

      <WorkspaceSourceNote source={WORKSPACE_SYNC_STATUS_ENDPOINT} ok={syncState !== null} />
    </div>
  );
}
