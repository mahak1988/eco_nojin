'use client';

import { type ReactNode, useRef } from 'react';

/**
 * Breadcrumb trail.
 *
 * The current page is rendered as text with `aria-current="page"`, not as a
 * link. A link to the page you are already on invites a pointless request and
 * tells a screen reader there is somewhere to go.
 *
 * The separator is `aria-hidden` and comes from a logical property pair, so it
 * mirrors under RTL without a second rule.
 */

export interface Crumb {
  /** Route path without the locale prefix. The last crumb is ignored. */
  href: string;
  label: string;
}

export interface BreadcrumbProps {
  items: readonly Crumb[];
  /** Accessible name for the navigation landmark. */
  label: string;
  className?: string;
  /** Rendered instead of a link on the final crumb. */
  currentLabel?: string;
  children?: ReactNode;
}

export function Breadcrumb({
  items,
  label,
  className = '',
  currentLabel,
  children,
}: BreadcrumbProps) {
  const lastIndex = items.length - 1;
  return (
    <nav aria-label={label} className={className}>
      <ol
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 'var(--space-2)',
          listStyle: 'none',
          margin: 0,
          padding: 0,
          fontSize: '0.875rem',
        }}
      >
        {items.map((item, index) => {
          const isLast = index === lastIndex;
          return (
            <li
              key={item.href}
              style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}
            >
              {index > 0 ? (
                <span aria-hidden="true" style={{ color: 'var(--color-ink-faint)' }}>
                  /
                </span>
              ) : null}
              {isLast ? (
                <span aria-current="page" style={{ color: 'var(--color-ink)' }}>
                  {currentLabel ?? item.label}
                </span>
              ) : (
                <a
                  href={item.href}
                  style={{ color: 'var(--color-forest)', textDecoration: 'underline' }}
                >
                  {item.label}
                </a>
              )}
            </li>
          );
        })}
        {children}
      </ol>
    </nav>
  );
}

/**
 * Roving-focus-free pagination.
 *
 * Page numbers are real links with `rel="prev"` / `rel="next"`, so the control
 * works without JavaScript and search engines can follow it. The current page
 * is marked with `aria-current="page"` and is not a link.
 */

export interface PaginationProps {
  /** Zero-based current page. */
  page: number;
  pageCount: number;
  /** Builds the href for a zero-based page index. */
  hrefFor: (page: number) => string;
  label: string;
  previousLabel: string;
  nextLabel: string;
  className?: string;
}

export function Pagination({
  page,
  pageCount,
  hrefFor,
  label,
  previousLabel,
  nextLabel,
  className = '',
}: PaginationProps) {
  const listRef = useRef<HTMLUListElement>(null);
  if (pageCount <= 1) return null;

  const buttonStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    minInlineSize: '2.25rem',
    minBlockSize: '2.25rem',
    padding: 'var(--space-1) var(--space-2)',
    borderRadius: 'var(--radius-s)',
    border: '1px solid var(--color-line)',
    color: 'var(--color-ink)',
    textDecoration: 'none',
  };

  return (
    <nav aria-label={label} className={className}>
      <ul
        ref={listRef}
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 'var(--space-1)',
          listStyle: 'none',
          margin: 0,
          padding: 0,
        }}
      >
        <li>
          {page > 0 ? (
            <a rel="prev" href={hrefFor(page - 1)} style={buttonStyle}>
              <span aria-hidden="true">‹</span>
              <span>{previousLabel}</span>
            </a>
          ) : (
            <span aria-disabled="true" style={{ ...buttonStyle, opacity: 0.45 }}>
              <span aria-hidden="true">‹</span>
              <span>{previousLabel}</span>
            </span>
          )}
        </li>
        {Array.from({ length: pageCount }, (_, index) =>
          index === page ? (
            <li key={`current-${hrefFor(index)}`}>
              <span
                aria-current="page"
                className="num"
                style={{
                  ...buttonStyle,
                  backgroundColor: 'var(--color-forest)',
                  color: 'var(--color-on-action)',
                  borderColor: 'var(--color-forest)',
                }}
              >
                {index + 1}
              </span>
            </li>
          ) : (
            // Keyed by href rather than by index: the href is derived from the
            // page's identity, so it stays stable when the caller inserts or
            // removes a page, which an array index does not.
            <li key={hrefFor(index)}>
              <a href={hrefFor(index)} style={buttonStyle} className="num">
                {index + 1}
              </a>
            </li>
          ),
        )}
        <li>
          {page < pageCount - 1 ? (
            <a rel="next" href={hrefFor(page + 1)} style={buttonStyle}>
              <span>{nextLabel}</span>
              <span aria-hidden="true">›</span>
            </a>
          ) : (
            <span aria-disabled="true" style={{ ...buttonStyle, opacity: 0.45 }}>
              <span>{nextLabel}</span>
              <span aria-hidden="true">›</span>
            </span>
          )}
        </li>
      </ul>
    </nav>
  );
}

export default Breadcrumb;
