import { cn } from '@eco/utils'
import { useEffect, useRef, useState } from 'react'
import { Button } from '../primitives'
import { Search, X } from '../primitives/icon'

export type SearchOverlayProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  placeholder?: string
  onSearch?: (query: string) => void
  recentSearches?: string[]
  className?: string
}

export function SearchOverlay({
  open,
  onOpenChange,
  placeholder = 'جستجو...',
  onSearch,
  recentSearches = [],
  className,
}: SearchOverlayProps) {
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50)
    } else {
      setQuery('')
    }
  }, [open])

  if (!open) return null

  return (
    <div
      className={cn('fixed inset-0 z-50 bg-ink/40 backdrop-blur-sm', className)}
      onClick={() => onOpenChange(false)}
    >
      <div className="mx-auto mt-20 max-w-lg" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 rounded-lg border border-ink/10 bg-surface-raised p-2 shadow-raised">
          <Search size={18} className="text-ink-subtle" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSearch?.(query)}
            placeholder={placeholder}
            className="flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-ink-subtle"
          />
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)} aria-label="بستن">
            <X size={16} />
          </Button>
        </div>
        {recentSearches.length > 0 && (
          <div className="mt-2 rounded-lg border border-ink/10 bg-surface-raised p-3 shadow-raised">
            <p className="mb-2 text-xs font-medium text-ink-muted">جستجوهای اخیر</p>
            <div className="flex flex-col gap-1">
              {recentSearches.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => {
                    setQuery(s)
                    onSearch?.(s)
                  }}
                  className="text-start text-sm text-ink hover:bg-surface-muted rounded px-2 py-1"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
