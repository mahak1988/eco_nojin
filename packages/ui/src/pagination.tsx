import { cn } from './cn';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  total: number;
  page: number;
  pageSize: number;
  onChange: (page: number) => void;
  showPageNumbers?: boolean;
  className?: string;
}

export function Pagination({
  total,
  page,
  pageSize,
  onChange,
  showPageNumbers = true,
  className,
}: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  const startPage = showPageNumbers ? Math.max(1, page - 2) : 1;
  const endPage = showPageNumbers ? Math.min(totalPages, page + 2) : totalPages;

  const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);

  return (
    <nav aria-label="Pagination" className="flex items-center gap-1">
      <button
        onClick={() => onChange(page - 1)}
        disabled={page === 1}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-line bg-white text-ink transition-colors hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      {startPage > 1 && (
        <>
          <button onClick={() => onChange(1)} className="h-9 min-w-9 px-3 text-sm font-medium text-ink-soft hover:text-ink">1</button>
          {startPage > 2 && <span className="px-2 text-ink-faint">…</span>}
        </>
      )}

      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={`h-9 min-w-9 px-3 text-sm font-medium rounded-md transition-colors ${
            p === page ? 'bg-water text-white' : 'text-ink hover:bg-muted'
          }`}
          aria-current={p === page ? 'page' : undefined}
        >
          {p}
        </button>
      ))}

      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && <span className="px-2 text-ink-faint">…</span>}
          <button onClick={() => onChange(totalPages)} className="h-9 min-w-9 px-3 text-sm font-medium text-ink-soft hover:text-ink">{totalPages}</button>
        </>
      )}

      <button
        onClick={() => onChange(page + 1)}
        disabled={page === totalPages}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-line bg-white text-ink transition-colors hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
}

export default Pagination;