import { cn } from '@eco/utils'
import { type ReactNode, useMemo, useState } from 'react'

export type ColumnDef<T> = {
  id: string
  header: ReactNode
  cell: (row: T) => ReactNode
  sortBy?: (row: T) => string | number
  align?: 'start' | 'center' | 'end'
  width?: string
}

export type DataTableProps<T> = {
  data: readonly T[]
  columns: readonly ColumnDef<T>[]
  rowKey: (row: T) => string
  empty?: ReactNode
  onRowClick?: (row: T) => void
  pageSize?: number
  className?: string
  caption?: string
}

export function DataTable<T>({
  data,
  columns,
  rowKey,
  empty,
  onRowClick,
  pageSize = 25,
  className,
  caption,
}: DataTableProps<T>) {
  const [page, setPage] = useState(0)
  const [sort, setSort] = useState<{ id: string; dir: 'asc' | 'desc' } | null>(null)

  const sorted = useMemo(() => {
    if (!sort) return data
    const col = columns.find((c) => c.id === sort.id)
    if (!col?.sortBy) return data
    const out = [...data].sort((a, b) => {
      const va = col.sortBy?.(a)
      const vb = col.sortBy?.(b)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      if (va < vb) return sort.dir === 'asc' ? -1 : 1
      if (va > vb) return sort.dir === 'asc' ? 1 : -1
      return 0
    })
    return out
  }, [data, sort, columns])

  const pages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const slice = sorted.slice(page * pageSize, (page + 1) * pageSize)

  function toggleSort(id: string) {
    setSort((s) => {
      if (s?.id === id) return { id, dir: s.dir === 'asc' ? 'desc' : 'asc' }
      return { id, dir: 'asc' }
    })
  }

  if (data.length === 0 && empty) return <>{empty}</>

  return (
    <div
      className={cn('overflow-hidden rounded-lg border border-ink/10 bg-surface-raised', className)}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead className="bg-surface-muted text-start text-xs uppercase tracking-wide text-ink-muted">
            <tr>
              {columns.map((c) => {
                const isSorted = sort?.id === c.id
                const sortDir = isSorted ? sort.dir : undefined
                return (
                  <th
                    key={c.id}
                    style={{ width: c.width }}
                    scope="col"
                    aria-sort={
                      isSorted ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined
                    }
                    className={cn(
                      'px-4 py-3 font-medium',
                      c.align === 'end' && 'text-end',
                      c.align === 'center' && 'text-center',
                      !c.align && 'text-start',
                      c.sortBy && 'cursor-pointer select-none hover:text-ink',
                    )}
                  >
                    {c.sortBy ? (
                      <button
                        type="button"
                        onClick={() => toggleSort(c.id)}
                        className="inline-flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
                        aria-label={`مرتب‌سازی بر اساس ${typeof c.header === 'string' ? c.header : c.id} ${isSorted ? (sortDir === 'asc' ? 'صعودی' : 'نزولی') : ''}`}
                      >
                        <span>{c.header}</span>
                        <span aria-hidden="true" className="text-ink-subtle">
                          {isSorted ? (sortDir === 'asc' ? '▲' : '▼') : '↕'}
                        </span>
                      </button>
                    ) : (
                      c.header
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-ink/5">
            {slice.map((row, rowIndex) => {
              const clickable = Boolean(onRowClick)
              return (
                <tr
                  key={rowKey(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  onKeyDown={(e) => {
                    if (clickable && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault()
                      onRowClick?.(row)
                    }
                  }}
                  tabIndex={clickable ? 0 : undefined}
                  role={clickable ? 'button' : undefined}
                  aria-label={clickable ? `ردیف ${page * pageSize + rowIndex + 1}` : undefined}
                  className={cn(
                    clickable &&
                      'cursor-pointer hover:bg-surface-muted focus-visible:outline-none focus-visible:bg-surface-muted',
                  )}
                >
                  {columns.map((c) => (
                    <td
                      key={c.id}
                      className={cn(
                        'px-4 py-3 text-ink',
                        c.align === 'end' && 'text-end',
                        c.align === 'center' && 'text-center',
                      )}
                    >
                      {c.cell(row)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <nav
          aria-label="صفحه‌بندی جدول"
          className="flex items-center justify-between border-t border-ink/5 px-4 py-2 text-xs text-ink-muted"
        >
          <span aria-live="polite">
            صفحهٔ {page + 1} از {pages}
          </span>
          <div className="flex gap-1">
            <button
              type="button"
              className="rounded px-2 py-1 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              aria-label="صفحهٔ قبل"
            >
              قبلی
            </button>
            <button
              type="button"
              className="rounded px-2 py-1 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
              disabled={page >= pages - 1}
              aria-label="صفحهٔ بعد"
            >
              بعدی
            </button>
          </div>
        </nav>
      )}
    </div>
  )
}
