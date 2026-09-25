import type { ReactNode } from 'react';
import type { WorkspaceNavigationGroup } from '@/lib/workspaces/registry';
import { WorkspaceNav } from './WorkspaceNav';

/**
 * Shared workspace shell: one persistent navigation landmark and one content
 * column. The `main` landmark and the deny-by-default session gate stay in
 * `workspace/layout.tsx`, so a page can never render outside the gate.
 *
 * The groups arrive from the server, already filtered for the session role. No
 * role, group or identity is ever read from browser storage.
 */
export function WorkspaceShell({
  groups,
  sessionRole,
  children,
}: {
  groups: readonly WorkspaceNavigationGroup[];
  /** Session role from the server record; used only to mark the visible scope. */
  sessionRole: string;
  children: ReactNode;
}) {
  return (
    <div className="grid gap-8 lg:grid-cols-[18rem_minmax(0,1fr)]">
      <WorkspaceNav groups={groups} sessionRole={sessionRole} />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
