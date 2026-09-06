import { cn } from '@eco/utils'
import { type ReactNode, useMemo, useState } from 'react'
import { Card } from '../primitives'

export type DataGridColumn = {
  key: string
  header: string
  width?: string
  align?: 'start' | 'center' | 'end'
}

export type DataGridRow = Record<string, ReactNode>

export type DataGridProps = {
  data: DataGridRow[]
  columns: DataGridColumn[]
  pageSize?: number
  onRowClick?: (row: DataGridRow) => void
  className?: string
}

export function DataGrid({ data, columns, pageSize = 10, onRowClick, className }: DataGridProps) {
  const [page, setPage] = useState(0)
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const sorted = useMemo(() => {
    if (!sortKey) return data
    return [...data].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const cmp = String(av).localeCompare(String(bv), 'fa-IR')
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [data, sortKey, sortDir])

  const pages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const slice = sorted.slice(page * pageSize, (page + 1) * pageSize)

  const toggleSort = (key: string) => {
    setSortKey((prev) => {
      if (prev === key) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
        return key
      }
      setSortDir('asc')
      return key
    })
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-surface-muted text-start text-xs uppercase tracking-wide text-ink-muted">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  style={{ width: col.width }}
                  className={cn(
                    'px-4 py-3 font-medium',
                    col.align === 'end' && 'text-end',
                    col.align === 'center' && 'text-center',
                  )}
                >
                  <button
                    type="button"
                    onClick={() => toggleSort(col.key)}
                    className="inline-flex items-center gap-1 focus:outline-none focus:shadow-glow rounded"
                  >
                    {col.header}
                    <span className="text-ink-subtle">
                      {sortKey === col.key ? (sortDir === 'asc' ? '▲' : '▼') : '↕'}
                    </span>
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-ink/5">
            {slice.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                onClick={() => onRowClick?.(row)}
                className={cn(onRowClick && 'cursor-pointer hover:bg-surface-muted')}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(
                      'px-4 py-3 text-ink',
                      col.align === 'end' && 'text-end',
                      col.align === 'center' && 'text-center',
                    )}
                  >
                    {row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="flex items-center justify-between border-t border-ink/5 px-4 py-2 text-xs text-ink-muted">
          <span>
            صفحه {page + 1} از {pages}
          </span>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded px-2 py-1 hover:bg-surface-muted disabled:opacity-50"
            >
              قبلی
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
              disabled={page >= pages - 1}
              className="rounded px-2 py-1 hover:bg-surface-muted disabled:opacity-50"
            >
              بعدی
            </button>
          </div>
        </div>
      )}
    </Card>
  )
}
