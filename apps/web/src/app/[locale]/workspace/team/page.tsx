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
import { formatTimestamp, readOrganizations } from '@/lib/workspaces/data';
import { accessRole, authorizeWorkspace, workspaceToken } from '@/lib/workspaces/guard';
import {
  getWorkspacePage,
  WORKSPACE_ORGANIZATIONS_ENDPOINT,
  workspacePageHref,
} from '@/lib/workspaces/registry';
import { workspaceGet } from '@/lib/workspaces/server';

// Membership context comes from the session-scoped gateway route per request.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('team');
const MEMBER_INDEX = PAGE.capabilities.find((capability) => capability.id === 'member-index');
const MEMBER_INVITES = PAGE.capabilities.find((capability) => capability.id === 'member-invites');

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

export default async function TeamPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const access = await authorizeWorkspace();
  const organizations = await workspaceGet<unknown>(
    workspaceToken(access.status === 'authorized' ? access.session : null),
    WORKSPACE_ORGANIZATIONS_ENDPOINT,
  );
  const rows = organizations.ok ? readOrganizations(organizations.data) : [];
  const notProvided = t('auth.session.unknown');

  const columns: readonly WorkspaceGridColumn<(typeof rows)[number]>[] = [
    {
      id: 'name',
      labelKey: 'statusPage.label',
      search: (row) => row.name,
      compare: (a, b) => a.name.localeCompare(b.name),
      render: (row) => <span className="font-medium text-ink">{row.name}</span>,
    },
    {
      id: 'slug',
      labelKey: 'statusPage.endpoint',
      search: (row) => row.slug,
      compare: (a, b) => a.slug.localeCompare(b.slug),
      render: (row) => <span className="num break-all text-xs text-ink-soft">{row.slug}</span>,
    },
    {
      id: 'membership',
      labelKey: 'auth.session.role',
      search: (row) => row.membershipRole,
      compare: (a, b) => a.membershipRole.localeCompare(b.membershipRole),
      render: (row) => <span className="num text-xs text-ink-soft">{row.membershipRole}</span>,
    },
    {
      id: 'country',
      labelKey: 'auth.session.country',
      compare: (a, b) => (a.country ?? '').localeCompare(b.country ?? ''),
      render: (row) => <span className="text-xs text-ink-soft">{row.country ?? notProvided}</span>,
    },
    {
      id: 'created',
      labelKey: 'auth.session.memberSince',
      compare: (a, b) => (a.createdAt ?? '').localeCompare(b.createdAt ?? ''),
      render: (row) => (
        <span className="num text-xs text-ink-soft">
          {formatTimestamp(row.createdAt, locale, notProvided)}
        </span>
      ),
    },
  ];

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <section className="mt-6" aria-labelledby="workspace-organization">
        <h2 id="workspace-organization" className="field-label">
          {t('auth.roles.organization')}
        </h2>
        <div className="mt-3">
          {organizations.ok ? (
            <WorkspaceDataGrid
              id="workspace-organization-caption"
              caption={t('statusPage.subtitle')}
              source={WORKSPACE_ORGANIZATIONS_ENDPOINT}
              basePath={workspacePageHref(locale, PAGE.path)}
              searchParams={{}}
              columns={columns}
              rows={rows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <WorkspaceUnavailable
              source={WORKSPACE_ORGANIZATIONS_ENDPOINT}
              status={organizations.status}
              detail={organizations.ok ? undefined : organizations.error}
            />
          )}
        </div>
      </section>

      <section className="mt-6" aria-labelledby="workspace-member-state">
        <h2 id="workspace-member-state" className="field-label">
          {t('statusPage.state')}
        </h2>
        <ul className="mt-3 space-y-4">
          {[MEMBER_INDEX, MEMBER_INVITES].map((capability) =>
            capability ? (
              <li key={capability.id}>
                <WorkspaceUnavailable
                  source={capability.gap === '' ? capability.id : capability.gap}
                  detail={t('market.template.unavailableDescription')}
                />
              </li>
            ) : null,
          )}
        </ul>
      </section>

      <WorkspaceScopeNote page={PAGE} role={accessRole(access)} id="workspace-scope" />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={PAGE.capabilities} />

      <WorkspaceSourceNote source={WORKSPACE_ORGANIZATIONS_ENDPOINT} ok={organizations.ok} />
    </div>
  );
}
