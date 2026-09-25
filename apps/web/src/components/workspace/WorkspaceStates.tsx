import { getTranslations } from 'next-intl/server';
import { roleLabelKey } from '@/components/auth/role-label';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { resolvePageScope } from '@/lib/workspaces/guard';
import {
  findWorkspaceRole,
  isWorkspaceCapabilitySourced,
  type WorkspaceCapability,
  type WorkspacePage,
  workspaceCapabilitySource,
} from '@/lib/workspaces/registry';

/**
 * Explicit unavailable state. `source` is always the contract that is missing or
 * the endpoint that did not answer, never a substitute data source.
 */
export async function WorkspaceUnavailable({
  source,
  detail,
  status,
}: {
  source: string;
  detail?: string;
  status?: number;
}) {
  const t = await getTranslations();

  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-ink">{t('market.template.status')}</h2>
        <StatusDot state="down" label={t('statusLine.unavailable')} />
      </div>
      <p className="mt-2 text-sm text-ink-soft">{t('market.template.unavailableDescription')}</p>
      <p className="num mt-3 break-words text-xs text-ink-faint">
        {source}
        {status === undefined ? '' : ` · ${status === 0 ? '—' : status}`}
        {detail ? ` · ${detail}` : ''}
      </p>
      <div className="mt-3">
        <ProvenanceStamp source={source} verified={false} method={source} />
      </div>
    </div>
  );
}

/**
 * Provenance footer for a real response. The live claim is made only when the
 * request actually succeeded.
 */
export async function WorkspaceSourceNote({
  source,
  ok,
  observedAt,
}: {
  source: string;
  ok: boolean;
  observedAt?: string;
}) {
  const t = await getTranslations();

  return (
    <p className="mt-6 flex flex-wrap items-center gap-2 text-xs text-ink-soft">
      <ProvenanceStamp
        source={source}
        verified={ok}
        method={source}
        timestamp={observedAt}
        labels={{
          heading: t('market.template.source'),
          source: t('statusPage.endpoint'),
          method: t('market.template.method'),
          verified: t('common.live'),
          unverified: t('statusLine.unavailable'),
        }}
      />
      <span>{ok ? t('statusLine.realData') : t('statusLine.unavailable')}</span>
    </p>
  );
}

/**
 * The per-page data contract. Every capability the page knows about is listed
 * with its method, its real source and whether the workspace may read it. A
 * capability without a registered endpoint is always shown as unavailable.
 */
export async function WorkspaceCapabilityTable({
  capabilities,
  title,
  id,
}: {
  capabilities: readonly WorkspaceCapability[];
  title?: string;
  id: string;
}) {
  const t = await getTranslations();

  return (
    <section className="mt-6" aria-labelledby={id}>
      <h2 id={id} className="field-label">
        {title ?? t('market.template.contractTitle')}
      </h2>
      <div className="card mt-3 overflow-x-auto">
        <table className="w-full min-w-[34rem] border-collapse text-sm">
          <caption className="px-4 py-3 text-start text-xs text-ink-soft">
            {t('market.template.contractDescription')}
          </caption>
          <thead>
            <tr className="border-y border-line text-ink-soft">
              <th scope="col" className="px-4 py-2 text-start font-medium">
                {t('statusPage.label')}
              </th>
              <th scope="col" className="px-4 py-2 text-start font-medium">
                {t('statusPage.endpoint')}
              </th>
              <th scope="col" className="px-4 py-2 text-start font-medium">
                {t('statusPage.state')}
              </th>
            </tr>
          </thead>
          <tbody>
            {capabilities.map((capability) => {
              const sourced = isWorkspaceCapabilitySourced(capability);
              const source = workspaceCapabilitySource(capability);
              const state: DotState = sourced ? 'ok' : 'down';
              return (
                <tr key={capability.id} className="border-b border-line last:border-0">
                  <th scope="row" className="px-4 py-2 text-start font-normal text-ink">
                    {t(capability.labelKey)}
                    <span className="num ms-2 text-[0.65rem] text-ink-faint">
                      {capability.method}
                    </span>
                  </th>
                  <td className="num px-4 py-2 break-words text-xs text-ink-soft">
                    {source ?? t('statusLine.unavailable')}
                    {capability.projection === 'non-personal' && sourced ? (
                      <span className="block text-ink-faint">{capability.id}</span>
                    ) : null}
                    {!sourced && capability.gap ? (
                      <span className="block text-ink-faint">{capability.gap}</span>
                    ) : null}
                  </td>
                  <td className="px-4 py-2">
                    <StatusDot
                      state={state}
                      label={sourced ? t('common.live') : t('statusLine.unavailable')}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/**
 * Descriptive page scope.
 *
 * The layout gate is the only boundary. This reports the narrower professional
 * scope the page documents, whether the session already satisfies it, and that
 * the registry itself grants nothing. A reader outside the documented scope is
 * told so rather than silently given a page they do not own.
 */
export async function WorkspaceScopeNote({
  page,
  role,
  id,
}: {
  page: WorkspacePage;
  role: string;
  id: string;
}) {
  const t = await getTranslations();
  const scope = resolvePageScope(page, role);
  const descriptor = findWorkspaceRole(role);
  const sessionRoleKey = roleLabelKey(role);
  const sessionLabel = sessionRoleKey === null ? role : t(sessionRoleKey);

  return (
    <section className="card mt-6 p-4" aria-labelledby={id}>
      <h2 id={id} className="field-label">
        {t('auth.session.role')}
      </h2>
      <ul className="mt-2 flex flex-wrap gap-2">
        {page.roles.map((pageRole) => {
          const labelKey = roleLabelKey(pageRole);
          return (
            <li key={pageRole} className="num chip">
              {labelKey === null ? pageRole : t(labelKey)}
            </li>
          );
        })}
      </ul>
      <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-ink-soft">
        <StatusDot state={scope.status === 'in-scope' ? 'ok' : 'warn'} label={sessionLabel} />
        <span>{t('auth.session.lead')}</span>
      </p>
      <p className="mt-1 text-xs text-ink-soft">
        {descriptor?.issuedByGateway === false
          ? t('market.template.unavailableDescription')
          : t('statusLine.realData')}
      </p>
      {scope.status === 'outside-descriptive-scope' ? (
        <p className="mt-1 text-xs text-ink-soft">{t('auth.errors.forbidden')}</p>
      ) : null}
    </section>
  );
}

/**
 * Session and organization context, shown only when the backend actually
 * supplied it. A missing value is reported as "not provided" and never replaced
 * with a placeholder organization, team name or count.
 */
export async function WorkspaceContextCard({
  session,
  organizations,
  id,
}: {
  session: {
    email: string | null;
    fullName: string | null;
    role: string;
    isEmailVerified: boolean;
    isActive: boolean;
    memberSince: string | null;
  } | null;
  organizations: readonly {
    id: string;
    name: string;
    slug: string;
    membershipRole: string;
  }[];
  id: string;
}) {
  const t = await getTranslations();
  const notProvided = t('auth.session.unknown');
  const roleKey = session ? roleLabelKey(session.role) : null;

  return (
    <section className="card mt-6 p-4" aria-labelledby={id}>
      <h2 id={id} className="field-label">
        {t('auth.session.title')}
      </h2>
      <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <dt className="field-label">{t('auth.session.fullName')}</dt>
          <dd className="mt-1 text-sm text-ink">{session?.fullName ?? notProvided}</dd>
        </div>
        <div>
          <dt className="field-label">{t('auth.session.email')}</dt>
          <dd className="mt-1 break-all text-sm text-ink">{session?.email ?? notProvided}</dd>
        </div>
        <div>
          <dt className="field-label">{t('auth.session.role')}</dt>
          <dd className="num mt-1 text-sm text-ink">
            {roleKey === null ? (session?.role ?? notProvided) : t(roleKey)}
          </dd>
        </div>
        <div>
          <dt className="field-label">{t('auth.session.emailVerified')}</dt>
          <dd className="mt-1 text-sm text-ink">
            <StatusDot
              state={session?.isEmailVerified === true ? 'ok' : 'warn'}
              label={
                session?.isEmailVerified === true
                  ? t('auth.session.emailVerified')
                  : t('auth.session.emailNotVerified')
              }
            />
          </dd>
        </div>
        <div>
          <dt className="field-label">{t('auth.session.accountActive')}</dt>
          <dd className="mt-1 text-sm text-ink">
            <StatusDot
              state={session?.isActive === true ? 'ok' : 'down'}
              label={
                session?.isActive === true
                  ? t('auth.session.accountActive')
                  : t('auth.session.accountInactive')
              }
            />
          </dd>
        </div>
        <div>
          <dt className="field-label">{t('auth.session.memberSince')}</dt>
          <dd className="num mt-1 text-sm text-ink">{session?.memberSince ?? notProvided}</dd>
        </div>
      </dl>

      <h3 className="field-label mt-5">{t('auth.roles.organization')}</h3>
      {organizations.length === 0 ? (
        <p className="mt-2 text-sm text-ink-soft">{t('statusLine.noData')}</p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-2">
          {organizations.map((organization) => (
            <li key={organization.id} className="chip">
              <span className="font-semibold text-[var(--ink)]">{organization.name}</span>
              <span className="num ms-2 text-[0.65rem] text-[var(--ink-faint)]">
                {`${organization.slug} · ${organization.membershipRole}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
