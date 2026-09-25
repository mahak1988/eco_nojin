import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import {
  findWorkspacePageByPath,
  type WorkspacePage,
  workspacePageHref,
} from '@/lib/workspaces/registry';
import { WorkspacePageHeader } from './WorkspacePageHeader';
import {
  WorkspaceCapabilityTable,
  WorkspaceScopeNote,
  WorkspaceSourceNote,
  WorkspaceUnavailable,
} from './WorkspaceStates';

/**
 * The honest state of a page whose capabilities have no registered endpoint.
 *
 * Every capability is reported individually with the contract that is missing, so
 * a reader learns which backend capability is absent without any internal detail
 * and without a single substitute record. Pages that do have a real endpoint are
 * written by hand instead of reusing this component.
 */
export async function WorkspaceUnavailablePage({
  locale,
  page,
  role,
  relatedPaths,
  sourceNote,
}: {
  locale: string;
  page: WorkspacePage;
  role: string;
  /** Sibling pages linked as the next step; only registered paths are passed. */
  relatedPaths?: readonly string[];
  sourceNote: string;
}) {
  const t = await getTranslations();

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={page} />

      <section className="mt-6" aria-labelledby="workspace-state">
        <h2 id="workspace-state" className="field-label">
          {t('statusPage.state')}
        </h2>
        <ul className="mt-3 space-y-4">
          {page.capabilities.map((capability) => (
            <li key={capability.id}>
              <WorkspaceUnavailable
                source={
                  capability.gap === '' ? (capability.endpoint ?? capability.id) : capability.gap
                }
                detail={t('market.template.unavailableDescription')}
              />
            </li>
          ))}
        </ul>
      </section>

      <section className="card mt-6 p-5" aria-labelledby="workspace-limits">
        <h2 id="workspace-limits" className="field-label">
          {t('common.limits')}
        </h2>
        <p className="mt-2 text-sm text-ink-soft">{t('market.template.unavailableDescription')}</p>
        <p className="mt-3 text-sm text-ink-soft">{t('statusLine.noData')}</p>
      </section>

      <WorkspaceScopeNote page={page} role={role} id="workspace-scope" />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={page.capabilities} />

      {relatedPaths && relatedPaths.length > 0 ? (
        <section className="mt-6" aria-labelledby="workspace-next">
          <h2 id="workspace-next" className="field-label">
            {t('market.template.nextTitle')}
          </h2>
          <p className="mt-2 text-sm text-ink-soft">{t('market.template.nextDescription')}</p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {relatedPaths.map((path) => {
              const target = findWorkspacePageByPath(path);
              if (!target) return null;
              return (
                <li key={path}>
                  <Link
                    href={workspacePageHref(locale, target.path)}
                    className="chip hover:bg-[var(--surface-2)]"
                  >
                    {`/${target.path}`}
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}

      <WorkspaceSourceNote source={sourceNote} ok={false} />
    </div>
  );
}
