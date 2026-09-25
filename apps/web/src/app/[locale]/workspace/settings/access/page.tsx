import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { roleLabelKey } from '@/components/auth/role-label';
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
  getWorkspacePage,
  WORKSPACE_ORGANIZATIONS_ENDPOINT,
  WORKSPACE_ROLE_DESCRIPTORS,
} from '@/lib/workspaces/registry';
import { workspaceGet } from '@/lib/workspaces/server';

// Access state is read from the server session and the session-scoped
// organization route; nothing is read from browser storage and nothing is
// persisted from this surface.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('settings-access');
const MFA_STATE = PAGE.capabilities.find((capability) => capability.id === 'mfa-state');
const ROLE_ASSIGNMENT = PAGE.capabilities.find((capability) => capability.id === 'role-assignment');

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

export default async function SettingsAccessPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
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
  const sessionRoleKey = session ? roleLabelKey(session.user.role) : null;

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <WorkspaceContextCard
        id="workspace-access-session"
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

      <section className="card mt-6 p-4" aria-labelledby="workspace-role-state">
        <h2 id="workspace-role-state" className="field-label">
          {t('auth.session.role')}
        </h2>
        <p className="mt-2 flex flex-wrap items-center gap-2 text-sm text-ink">
          <StatusDot
            state="ok"
            label={sessionRoleKey === null ? t('auth.session.role') : t(sessionRoleKey)}
          />
          <span className="num">{session?.user.role ?? t('auth.session.unknown')}</span>
        </p>
        <p className="mt-2 text-xs text-ink-soft">{t('auth.session.lead')}</p>
      </section>

      {/*
        The registry documents the professional roles the design proposes. It
        grants nothing: a role the gateway does not issue is reported as
        unavailable, never as an option a reader could pick.
      */}
      <section className="mt-6" aria-labelledby="workspace-role-registry">
        <h2 id="workspace-role-registry" className="field-label">
          {t('market.template.contractTitle')}
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
                  {t('statusPage.state')}
                </th>
              </tr>
            </thead>
            <tbody>
              {WORKSPACE_ROLE_DESCRIPTORS.map((descriptor) => (
                <tr key={descriptor.id} className="border-b border-line last:border-0">
                  <th scope="row" className="px-4 py-2 text-start font-normal text-ink">
                    <span className="num">{descriptor.id}</span>
                    <span className="ms-2 text-xs text-ink-faint">{descriptor.kind}</span>
                  </th>
                  <td className="px-4 py-2">
                    <StatusDot
                      state={descriptor.issuedByGateway ? 'ok' : 'down'}
                      label={
                        descriptor.issuedByGateway ? t('common.live') : t('statusLine.unavailable')
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-6" aria-labelledby="workspace-access-state">
        <h2 id="workspace-access-state" className="field-label">
          {t('statusPage.state')}
        </h2>
        <ul className="mt-3 space-y-4">
          {[MFA_STATE, ROLE_ASSIGNMENT].map((capability) =>
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

      <WorkspaceSourceNote
        source={`${WORKSPACE_ORGANIZATIONS_ENDPOINT} · HttpOnly session cookie`}
        ok={organizations.ok}
      />
    </div>
  );
}
