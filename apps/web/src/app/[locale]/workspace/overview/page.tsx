import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { WorkspacePageHeader } from '@/components/workspace/WorkspacePageHeader';
import {
  WorkspaceCapabilityTable,
  WorkspaceContextCard,
  WorkspaceScopeNote,
  WorkspaceSourceNote,
  WorkspaceUnavailable,
} from '@/components/workspace/WorkspaceStates';
import { readOrganizations } from '@/lib/workspaces/data';
import { accessRole, authorizeWorkspace, workspaceToken } from '@/lib/workspaces/guard';
import {
  findWorkspacePageByPath,
  getWorkspacePage,
  WORKSPACE_ORGANIZATIONS_ENDPOINT,
  workspacePageHref,
} from '@/lib/workspaces/registry';
import { workspaceGet } from '@/lib/workspaces/server';

// Session, organization context and the capability matrix are read per request.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('overview');
const KPI = PAGE.capabilities.find((capability) => capability.id === 'workspace-kpis');
const NEXT_PATHS = ['assignments', 'cases', 'team', 'operations'] as const;

/**
 * The professional indicators a workspace lead would expect. None of them has a
 * registered endpoint, so every row reports the missing contract instead of a
 * number; the row set is fixed by the registry and never grows from a response.
 */
const KPI_ROWS = [
  { id: 'assignments', labelKey: 'common.pending' },
  { id: 'cases', labelKey: 'common.card' },
  { id: 'approvals', labelKey: 'market.bazaar.pending' },
  { id: 'targets', labelKey: 'statusPage.label' },
] as const;

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

export default async function OverviewPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const access = await authorizeWorkspace();
  const session = access.status === 'authorized' ? access.session : null;
  const organizations = await workspaceGet<unknown>(
    workspaceToken(session),
    WORKSPACE_ORGANIZATIONS_ENDPOINT,
  );
  const organizationRows = organizations.ok ? readOrganizations(organizations.data) : [];

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <WorkspaceContextCard
        id="workspace-context"
        session={
          session
            ? {
                email: session.user.email,
                fullName: session.user.full_name ?? null,
                role: session.user.role,
                isEmailVerified: session.user.is_email_verified,
                isActive: session.user.is_active,
                memberSince: session.user.created_at,
              }
            : null
        }
        organizations={organizationRows}
      />

      <section className="mt-6" aria-labelledby="workspace-kpis">
        <h2 id="workspace-kpis" className="field-label">
          {t('statusPage.label')}
        </h2>
        <div className="card mt-3 overflow-x-auto">
          <table className="w-full min-w-[30rem] border-collapse text-sm">
            <caption className="px-4 py-3 text-start text-xs text-ink-soft">
              {t('market.template.contractDescription')}
            </caption>
            <thead>
              <tr className="border-y border-line text-ink-soft">
                <th scope="col" className="px-4 py-2 text-start font-medium">
                  {t('statusPage.label')}
                </th>
                <th scope="col" className="px-4 py-2 text-start font-medium">
                  {t('statusPage.result')}
                </th>
                <th scope="col" className="px-4 py-2 text-start font-medium">
                  {t('statusPage.endpoint')}
                </th>
              </tr>
            </thead>
            <tbody>
              {KPI_ROWS.map((row) => (
                <tr key={row.id} className="border-b border-line last:border-0">
                  <th scope="row" className="px-4 py-2 text-start font-normal text-ink">
                    {t(row.labelKey)}
                  </th>
                  <td className="px-4 py-2">
                    <StatusDot state="down" label={t('statusLine.unavailable')} />
                  </td>
                  <td className="num px-4 py-2 break-words text-xs text-ink-faint">
                    {KPI?.gap ?? t('statusLine.unavailable')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-6" aria-labelledby="workspace-organization-state">
        <h2 id="workspace-organization-state" className="field-label">
          {t('auth.roles.organization')}
        </h2>
        <div className="mt-3">
          {organizations.ok ? (
            <p className="card p-4 text-sm text-ink-soft">
              {organizationRows.length === 0 ? t('statusLine.noData') : t('statusLine.realData')}
            </p>
          ) : (
            <WorkspaceUnavailable
              source={WORKSPACE_ORGANIZATIONS_ENDPOINT}
              status={organizations.status}
              detail={organizations.ok ? undefined : organizations.error}
            />
          )}
        </div>
      </section>

      <WorkspaceScopeNote page={PAGE} role={accessRole(access)} id="workspace-scope" />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={PAGE.capabilities} />

      <section className="mt-6" aria-labelledby="workspace-next">
        <h2 id="workspace-next" className="field-label">
          {t('market.template.nextTitle')}
        </h2>
        <p className="mt-2 text-sm text-ink-soft">{t('market.template.nextDescription')}</p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {NEXT_PATHS.map((path) => {
            const target = findWorkspacePageByPath(path);
            if (!target) return null;
            return (
              <li key={path}>
                <Link
                  href={workspacePageHref(locale, target.path)}
                  className="chip min-h-11 hover:bg-[var(--surface-2)]"
                >
                  {`/${target.path}`}
                </Link>
              </li>
            );
          })}
        </ul>
      </section>

      <WorkspaceSourceNote source={WORKSPACE_ORGANIZATIONS_ENDPOINT} ok={organizations.ok} />
    </div>
  );
}
