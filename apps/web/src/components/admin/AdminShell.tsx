import type { ReactNode } from 'react';
import { AdminNav } from './AdminNav';

/**
 * Shared console shell: one persistent navigation landmark and one content
 * column. The `main` landmark and the deny-by-default session gate stay in
 * `admin/layout.tsx`, so a page can never render outside the gate.
 */
export function AdminShell({ children }: { children: ReactNode }) {
  return (
    <div className="grid gap-8 lg:grid-cols-[17rem_minmax(0,1fr)]">
      <AdminNav />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
