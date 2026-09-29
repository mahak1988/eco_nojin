'use client';

import { type CSSProperties, type ReactNode, useMemo, useState } from 'react';

/**
 * Sortable, filterable data grid for the admin and workspace tables (master plan
 * template T08).
 *
 * Two decisions worth stating. Column headers sort with `aria-sort`, and the
 * sort state lives in the caller rather than internally, so a table can be
 * driven by a URL query and stay shareable. And a number column is marked
 * `data-numeric`, which applies the platform's `.num` rule — tabular Latin digits
 * inside an RTL document, isolated with `unicode-bidi` so a value like
 * `1,204.5` does not reorder around the surrounding Persian text.
 */

export type SortDirection = 'ascending' | 'descending';
export type Align = 'start' | 'end' | 'center';

export interface Column<T> {
  key: string;
  header: string;
  /** Right-to-left aware alignment. Never `left` or `right`. */
  align?: Align;
  numeric?: boolean;
  sortable?: boolean;
  width?: string;
  render?: (row: T) => ReactNode;
}

export interface DataTableProps<T> {
  columns: readonly Column<T>[];
  rows: readonly T[];
  /** Stable row key. Without it, sorting re-mounts rows and loses focus. */
  rowKey: (row: T) => string;
  caption: string;
  /** `columns` and `rows` may be unfiltered; the table sorts what it is given. */
  sort?: { key: string; direction: SortDirection } | null;
  onSortChange?: (key: string, direction: SortDirection) => void;
  density?: 'cozy' | 'compact' | 'dense';
  emptyLabel?: string;
  className?: string;
  captionExtra?: ReactNode;
}

const CELL_PADDING = {
  cozy: 'var(--space-3) var(--space-4)',
  compact: 'var(--space-2) var(--space-3)',
  dense: 'var(--space-1) var(--space-2)',
} as const;

const FONT_SIZE = { cozy: '0.9375rem', compact: '0.875rem', dense: '0.8125rem' } as const;

/**
 * Alignment is expressed twice on purpose: a class for Tailwind's logical
 * utility and a style for the inline `text-align` the cell actually needs.
 * Spreading a Tailwind class into a style object is a type error, and using only
 * the class would leave the `<caption>` and fallback row unaligned.
 */
const ALIGN_CLASS: Record<Align, string> = {
  start: 'text-start',
  end: 'text-end',
  center: 'text-center',
};

const ALIGN_STYLE: Record<Align, CSSProperties> = {
  start: { textAlign: 'start' },
  end: { textAlign: 'end' },
  center: { textAlign: 'center' },
};

const alignOf = (column: Column<unknown>): Align =>
  column.align ?? (column.numeric === true ? 'end' : 'start');

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  caption,
  sort,
  onSortChange,
  density = 'cozy',
  emptyLabel,
  className = '',
  captionExtra,
}: DataTableProps<T>) {
  const [internalSort, setInternalSort] = useState<{
    key: string;
    direction: SortDirection;
  } | null>(null);
  const activeSort = sort === undefined ? internalSort : sort;

  const sorted = useMemo(() => {
    if (!activeSort) return rows;
    const column = columns.find((c) => c.key === activeSort.key);
    if (!column) return rows;
    const factor = activeSort.direction === 'ascending' ? 1 : -1;
    return [...rows].sort((a, b) => {
      const left = (a as Record<string, unknown>)[column.key];
      const right = (b as Record<string, unknown>)[column.key];
      if (typeof left === 'number' && typeof right === 'number') return (left - right) * factor;
      return String(left).localeCompare(String(right)) * factor;
    });
  }, [rows, activeSort, columns]);

  const handleSort = (key: string) => {
    const direction: SortDirection =
      activeSort?.key === key && activeSort.direction === 'ascending' ? 'descending' : 'ascending';
    const next = { key, direction };
    if (sort === undefined) setInternalSort(next);
    onSortChange?.(key, direction);
  };

  const ariaSortFor = (column: Column<T>): SortDirection | undefined => {
    if (!activeSort || activeSort.key !== column.key) return undefined;
    return activeSort.direction;
  };

  return (
    <div className={className} style={{ overflowX: 'auto' }}>
      <table
        style={{ inlineSize: '100%', borderCollapse: 'collapse', fontSize: FONT_SIZE[density] }}
      >
        <caption
          style={{
            textAlign: 'start',
            paddingBlockEnd: 'var(--space-2)',
            color: 'var(--color-ink-soft)',
          }}
        >
          {caption}
          {captionExtra ? (
            <span style={{ marginInlineStart: 'var(--space-2)' }}>{captionExtra}</span>
          ) : null}
        </caption>
        <thead>
          <tr>
            {columns.map((column) => {
              const ariaSort = ariaSortFor(column);
              return (
                <th
                  key={column.key}
                  scope="col"
                  aria-sort={ariaSort}
                  className={ALIGN_CLASS[alignOf(column as Column<unknown>)]}
                  style={{
                    ...ALIGN_STYLE[alignOf(column as Column<unknown>)],
                    inlineSize: column.width,
                    padding: CELL_PADDING[density],
                    borderBottom: '1px solid var(--color-line)',
                    color: 'var(--color-ink-soft)',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {column.sortable ? (
                    <button
                      type="button"
                      onClick={() => handleSort(column.key)}
                      style={{
                        background: 'none',
                        border: 0,
                        padding: 0,
                        font: 'inherit',
                        color: 'inherit',
                        fontWeight: 600,
                        cursor: 'pointer',
                        textAlign: 'inherit',
                      }}
                    >
                      {column.header}
                      <span aria-hidden="true" style={{ marginInlineStart: 'var(--space-1)' }}>
                        {ariaSort === 'ascending' ? '↑' : ariaSort === 'descending' ? '↓' : '↕'}
                      </span>
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{
                  padding: 'var(--space-8)',
                  textAlign: 'center',
                  color: 'var(--color-ink-soft)',
                }}
              >
                {emptyLabel ?? ''}
              </td>
            </tr>
          ) : (
            sorted.map((row) => (
              <tr key={rowKey(row)} style={{ borderBottom: '1px solid var(--color-line)' }}>
                {columns.map((column) => {
                  const isNumeric = column.numeric === true;
                  const value = column.render
                    ? column.render(row)
                    : String((row as Record<string, unknown>)[column.key] ?? '');
                  return (
                    <td
                      key={column.key}
                      className={`${isNumeric ? 'num ' : ''}${ALIGN_CLASS[alignOf(column as Column<unknown>)]}`}
                      style={{
                        ...ALIGN_STYLE[alignOf(column as Column<unknown>)],
                        padding: CELL_PADDING[density],
                        color: 'var(--color-ink)',
                      }}
                    >
                      {value}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
