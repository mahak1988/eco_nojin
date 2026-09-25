import { getTranslations } from 'next-intl/server';
import { roleLabelKey } from '@/components/auth/role-label';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { type GlobalRole, hasRole } from '@/lib/auth/roles';
import {
  type AdminCapability,
  adminCapabilitySource,
  isAdminCapabilitySourced,
} from './admin-sections';

/**
 * Explicit unavailable state. `source` is always the contract or the local
 * file that is missing — never a substitute data source.
 */
export async function AdminUnavailable({
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
 * Provenance footer for a real response. The "live data" claim is only made
 * when the request actually succeeded.
 */
export async function AdminSourceNote({
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
 * with its method, its real source, and whether the web layer may read it.
 */
export async function AdminCapabilityTable({
  capabilities,
  title,
  id,
}: {
  capabilities: readonly AdminCapability[];
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
              const sourced = isAdminCapabilitySourced(capability);
              const source = adminCapabilitySource(capability);
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

/** Resolves a role to its translated label, keeping the raw value when unknown. */
export function roleLabel(label: (key: string) => string, role: string): string {
  const key = roleLabelKey(role);
  return key === null ? role : label(key);
}

/**
 * Upstream role gate. The console gate lives in the layout; this reports the
 * narrower role the gateway itself requires, and whether the current session
 * already satisfies it.
 */
export async function AdminRoleGate({
  required,
  sessionRole,
  id,
}: {
  required: readonly GlobalRole[];
  sessionRole: string;
  id: string;
}) {
  if (required.length === 0) return null;
  const t = await getTranslations();
  const allowed = hasRole(sessionRole, required);

  return (
    <section className="card mt-6 p-4" aria-labelledby={id}>
      <h2 id={id} className="field-label">
        {t('auth.session.role')}
      </h2>
      <ul className="mt-2 flex flex-wrap gap-2">
        {required.map((role) => (
          <li key={role} className="chip">
            {roleLabel(t, role)}
          </li>
        ))}
      </ul>
      <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-ink-soft">
        <StatusDot state={allowed ? 'ok' : 'warn'} label={roleLabel(t, sessionRole)} />
        <span>{t('auth.session.title')}</span>
      </p>
      {allowed ? null : <p className="mt-1 text-xs text-ink-soft">{t('auth.errors.forbidden')}</p>}
    </section>
  );
}
