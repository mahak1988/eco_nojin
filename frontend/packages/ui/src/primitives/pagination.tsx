import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type PaginationProps = HTMLAttributes<HTMLElement> & {
  page: number
  pageCount: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pageCount, onPageChange, className, ...rest }: PaginationProps) {
  const pages = Array.from({ length: pageCount }, (_, i) => i + 1)

  return (
    <nav aria-label="Pagination" className={cn('flex items-center gap-1', className)} {...rest}>
      <button
        type="button"
        onClick={() => onPageChange(Math.max(1, page - 1))}
        disabled={page === 1}
        className="rounded px-2 py-1 text-sm hover:bg-surface-muted disabled:opacity-50 disabled:cursor-not-allowed"
      >
        قبلی
      </button>
      {pages.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onPageChange(p)}
          aria-current={p === page ? 'page' : undefined}
          className={cn(
            'h-8 w-8 rounded text-sm font-medium',
            p === page
              ? 'bg-brand-600 text-white shadow-soft'
              : 'text-ink-muted hover:bg-surface-muted hover:text-ink',
          )}
        >
          {p}
        </button>
      ))}
      <button
        type="button"
        onClick={() => onPageChange(Math.min(pageCount, page + 1))}
        disabled={page === pageCount}
        className="rounded px-2 py-1 text-sm hover:bg-surface-muted disabled:opacity-50 disabled:cursor-not-allowed"
      >
        بعدی
      </button>
    </nav>
  )
}
