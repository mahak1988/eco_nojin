import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { WorkspacePageHeader } from '@/components/workspace/WorkspacePageHeader';
import {
  WorkspaceCapabilityTable,
  WorkspaceScopeNote,
  WorkspaceUnavailable,
} from '@/components/workspace/WorkspaceStates';
import { accessRole, authorizeWorkspace } from '@/lib/workspaces/guard';
import {
  findWorkspacePageByPath,
  getWorkspacePage,
  workspacePageHref,
} from '@/lib/workspaces/registry';

// A settings index has no store of its own: it is an honest index of the three
// registered settings surfaces and of the capability each one still needs.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('settings');
const CHILDREN = ['settings/notifications', 'settings/access'] as const;

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

export default async function SettingsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <section className="mt-6" aria-labelledby="workspace-settings-children">
        <h2 id="workspace-settings-children" className="field-label">
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

      <section className="mt-6" aria-labelledby="workspace-settings-state">
        <h2 id="workspace-settings-state" className="field-label">
          {t('statusPage.state')}
        </h2>
        <ul className="mt-3 space-y-4">
          {PAGE.capabilities.map((capability) => (
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

      <WorkspaceScopeNote
        page={PAGE}
        role={accessRole(await authorizeWorkspace())}
        id="workspace-scope"
      />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={PAGE.capabilities} />
    </div>
  );
}
