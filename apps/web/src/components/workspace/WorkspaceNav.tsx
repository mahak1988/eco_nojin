'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import type { WorkspaceNavigationGroup } from '@/lib/workspaces/registry';
import { workspacePageHref } from '@/lib/workspaces/registry';

/** A group heading is descriptive; the locale-neutral path is the stable name. */
const GROUP_LABELS: Record<string, string> = {
  work: 'workspace.groups.work',
  governance: 'workspace.groups.governance',
  operations: 'workspace.groups.operations',
  settings: 'workspace.groups.settings',
};

/**
 * Workspace side navigation.
 *
 * Entries arrive pre-filtered from the server for the session role, so this
 * component never learns a role from the browser. The active entry is marked with
 * `aria-current="page"`, each entry shows its locale-neutral route, and every
 * target is a 44 pixel touch target that reflows to a single column at 320
 * CSS pixels.
 */
export function WorkspaceNav({
  groups,
  sessionRole,
}: {
  groups: readonly WorkspaceNavigationGroup[];
  /** Session role resolved on the server; used only to mark the visible scope. */
  sessionRole: string;
}) {
  const locale = useLocale();
  const pathname = usePathname();
  const t = useTranslations();

  return (
    <nav aria-label={t('layout.mainNav')} className="lg:sticky lg:top-6 lg:self-start">
      <p className="num chip">/{locale}/workspace</p>
      <p className="num mt-2 break-words text-[0.65rem] text-ink-faint">{sessionRole}</p>

      {groups.length === 0 ? (
        <p className="mt-3 text-xs text-ink-soft">{t('statusLine.unavailable')}</p>
      ) : (
        <div className="mt-3 flex flex-col gap-5">
          {groups.map((group) => (
            <section key={group.id} aria-labelledby={`workspace-group-${group.id}`}>
              <h2
                id={`workspace-group-${group.id}`}
                className="num text-[0.65rem] font-semibold tracking-wide text-ink-faint uppercase"
              >
                {GROUP_LABELS[group.id] ? t(GROUP_LABELS[group.id]) : group.id}
              </h2>
              <ul className="mt-2 flex flex-wrap gap-2 lg:flex-col">
                {group.pages.map((page) => {
                  const href = workspacePageHref(locale, page.path);
                  const current = pathname === href;
                  return (
                    <li key={page.id}>
                      <Link
                        href={href}
                        aria-current={current ? 'page' : undefined}
                        className={`flex min-h-11 w-full flex-col justify-center rounded-[var(--radius-m)] border px-3 py-2 transition-micro ${
                          current
                            ? 'border-[var(--canopy)] bg-[var(--surface-2)]'
                            : 'border-[var(--line)] bg-[var(--surface)] hover:bg-[var(--surface-2)]'
                        }`}
                      >
                        <span
                          className={`text-sm font-semibold ${
                            current ? 'text-[var(--ink)]' : 'text-[var(--ink-soft)]'
                          }`}
                        >
                          {t(page.labelKey)}
                        </span>
                        <span className="num text-[0.65rem] text-[var(--ink-faint)]">
                          {`/${page.path}`}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      )}
    </nav>
  );
}
