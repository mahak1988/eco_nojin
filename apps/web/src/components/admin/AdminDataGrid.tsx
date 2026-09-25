import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import type { ReactNode } from 'react';

export type AdminSearchParams = Record<string, string | string[] | undefined>;

export interface AdminGridColumn<Row> {
  id: string;
  /** Existing `namespace.key` message key for the column header. */
  labelKey: string;
  /** Plain-text projection used by the toolbar search. Omit to exclude. */
  search?: (row: Row) => string;
  /** Provide to make the column sortable with a keyboard-operable header. */
  compare?: (a: Row, b: Row) => number;
  render: (row: Row) => ReactNode;
  /** Right-aligns a numeric column. */
  numeric?: boolean;
}

export interface AdminDataGridProps<Row> {
  /** Unique id for the caption, also used to name the scrollable region. */
  id: string;
  /** Accessible caption, already translated. */
  caption: string;
  /** Real source path or endpoint shown as provenance. */
  source: string;
  basePath: string;
  searchParams: AdminSearchParams;
  columns: readonly AdminGridColumn<Row>[];
  rows: readonly Row[];
  rowId: (row: Row) => string;
  /** Shown when the grid has no rows at all, or no row matches the search. */
  emptyMessage: string;
  pageSize?: number;
}

const DEFAULT_PAGE_SIZE = 25;

function firstValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? '';
  return value ?? '';
}

function buildHref(basePath: string, params: URLSearchParams): string {
  const query = params.toString();
  return query === '' ? basePath : `${basePath}?${query}`;
}

/**
 * Shared admin data grid.
 *
 * Follows the Carbon data-table contract the benchmark names: a real caption, a
 * search toolbar, sortable headers with `aria-sort`, a result summary in a live
 * region (WCAG 2.2 · 4.1.3) and predictable pagination.
 *
 * Sorting, search and paging are plain links and a GET form, so the table is
 * fully operable with the keyboard, needs no client JavaScript, never steals
 * focus, and keeps its state in a shareable URL.
 */
export async function AdminDataGrid<Row>({
  id,
  caption,
  source,
  basePath,
  searchParams,
  columns,
  rows,
  rowId,
  emptyMessage,
  pageSize = DEFAULT_PAGE_SIZE,
}: AdminDataGridProps<Row>) {
  const t = await getTranslations();

  const query = firstValue(searchParams.q).trim();
  const sort = firstValue(searchParams.sort);
  const dir: 'asc' | 'desc' = firstValue(searchParams.dir) === 'desc' ? 'desc' : 'asc';
  const pageParam = Number.parseInt(firstValue(searchParams.page), 10);
  const requestedPage = Number.isFinite(pageParam) && pageParam > 0 ? pageParam : 1;

  const needle = query.toLowerCase();
  const filtered =
    needle === ''
      ? [...rows]
      : rows.filter((row) =>
          columns.some((column) => column.search?.(row).toLowerCase().includes(needle)),
        );

  const activeColumn = columns.find((column) => column.id === sort);
  const compare = activeColumn?.compare;
  if (compare) {
    const direction = dir === 'desc' ? -1 : 1;
    filtered.sort((a, b) => direction * compare(a, b));
  }

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const page = Math.min(requestedPage, pageCount);
  const visible = filtered.slice((page - 1) * pageSize, page * pageSize);

  const linkFor = (next: { sort?: string; dir?: 'asc' | 'desc'; page?: number }) => {
    const params = new URLSearchParams();
    const nextSort = next.sort ?? sort;
    const nextDir = next.dir ?? dir;
    if (query !== '') params.set('q', query);
    if (nextSort !== '') {
      params.set('sort', nextSort);
      params.set('dir', nextDir);
    }
    const nextPage = next.page ?? 1;
    if (nextPage > 1) params.set('page', String(nextPage));
    return buildHref(basePath, params);
  };

  if (rows.length === 0) {
    return (
      <div className="card p-5">
        <p className="text-sm text-ink">{emptyMessage}</p>
        <p className="num mt-2 break-words text-xs text-ink-faint">{source}</p>
      </div>
    );
  }

  return (
    <div className="card p-4 sm:p-5">
      <search>
        <form method="get" className="flex flex-wrap items-end gap-3">
          <div className="min-w-48 flex-1">
            <label htmlFor={`${id}-search`} className="field-label">
              {t('admin.grid.search')}
            </label>
            <input
              id={`${id}-search`}
              type="search"
              name="q"
              defaultValue={query}
              className="mt-1 w-full rounded-[var(--radius-m)] border border-[var(--line-strong)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--ink)]"
            />
          </div>
          <button type="submit" className="btn btn-ghost text-sm">
            {t('admin.grid.submit')}
          </button>
          {query !== '' || sort !== '' || requestedPage > 1 ? (
            <Link href={basePath} className="btn btn-ghost text-sm">
              {t('admin.grid.clear')}
            </Link>
          ) : null}
        </form>
      </search>

      <p role="status" className="num mt-3 text-xs text-ink-soft">
        {t('admin.grid.results', { filtered: filtered.length, total: rows.length })}
      </p>

      {visible.length === 0 ? (
        <p className="mt-4 text-sm text-ink">{emptyMessage}</p>
      ) : (
        // biome-ignore lint/a11y/noNoninteractiveTabindex: a horizontally scrollable data region must stay reachable by keyboard (WCAG 2.2 · 2.1.1)
        <section aria-labelledby={id} tabIndex={0} className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[36rem] border-collapse text-sm">
            <caption id={id} className="text-start text-xs text-ink-soft">
              {caption}
            </caption>
            <thead>
              <tr className="border-y border-line text-ink-soft">
                {columns.map((column) => {
                  const active = compare !== undefined && activeColumn?.id === column.id;
                  const ariaSort = column.compare
                    ? active
                      ? dir === 'desc'
                        ? 'descending'
                        : 'ascending'
                      : 'none'
                    : undefined;
                  return (
                    <th
                      key={column.id}
                      scope="col"
                      aria-sort={ariaSort}
                      className={`px-3 py-2 font-medium ${
                        column.numeric ? 'text-end' : 'text-start'
                      }`}
                    >
                      {column.compare ? (
                        <Link
                          href={linkFor({
                            sort: column.id,
                            dir: active && dir === 'asc' ? 'desc' : 'asc',
                            page: 1,
                          })}
                          className="inline-flex min-h-11 items-center gap-1 hover:underline"
                        >
                          {t(column.labelKey)}
                          <span aria-hidden="true">
                            {active ? (dir === 'asc' ? '▲' : '▼') : '↕'}
                          </span>
                        </Link>
                      ) : (
                        t(column.labelKey)
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={rowId(row)} className="border-b border-line last:border-0">
                  {columns.map((column) => (
                    <td
                      key={column.id}
                      className={`px-3 py-2 align-top text-ink ${column.numeric ? 'num text-end' : ''}`}
                    >
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {pageCount > 1 ? (
        <ul className="mt-4 flex flex-wrap items-center gap-3 text-xs">
          {page > 1 ? (
            <li>
              <Link href={linkFor({ page: page - 1 })} className="btn btn-ghost text-sm">
                {`← ${t('common.back')}`}
              </Link>
            </li>
          ) : null}
          <li className="num text-ink-soft">{`${page} / ${pageCount}`}</li>
          {page < pageCount ? (
            <li>
              <Link href={linkFor({ page: page + 1 })} className="btn btn-ghost text-sm">
                {`${t('common.next')} →`}
              </Link>
            </li>
          ) : null}
        </ul>
      ) : null}
    </div>
  );
}
