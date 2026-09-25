import Link from 'next/link';
import type { ReactNode } from 'react';

export interface ResearchBreadcrumbItem {
  /** Stable key for the trail position. */
  id: string;
  /** Omitted on the current item, which is never a link. */
  href?: string;
  label: ReactNode;
  /** Marks the current page for assistive technology and styling. */
  current?: boolean;
}

/**
 * Primer-style breadcrumb: parent return path plus `aria-current` on the last
 * item. The accessible name is supplied by the caller so the landmark can be
 * distinguished from the site navigation without hard-coded copy.
 */
export function ResearchBreadcrumb({
  label,
  items,
}: {
  label: string;
  items: readonly ResearchBreadcrumbItem[];
}) {
  return (
    <nav aria-label={label}>
      <ol className="flex flex-wrap items-center gap-2 text-xs text-ink-soft">
        {items.map((item, index) => (
          <li key={item.id} className="flex items-center gap-2">
            {index > 0 ? (
              <span aria-hidden="true" className="text-ink-faint">
                /
              </span>
            ) : null}
            {item.href && !item.current ? (
              <Link
                href={item.href}
                className="underline decoration-dotted underline-offset-4 transition-micro hover:text-ink"
              >
                {item.label}
              </Link>
            ) : (
              <span aria-current={item.current ? 'page' : undefined} className="num text-ink">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
