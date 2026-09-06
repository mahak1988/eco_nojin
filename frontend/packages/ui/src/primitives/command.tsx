import { cn } from '@eco/utils'
import { useEffect, useRef, useState } from 'react'
import { Search } from './icon'

export type CommandItem = {
  id: string
  label: string
  icon?: React.ReactNode
  keywords?: string[]
  onSelect?: () => void
}

export type CommandProps = {
  items: CommandItem[]
  placeholder?: string
  className?: string
  onSelect?: (id: string) => void
}

export function Command({ items, placeholder = 'جستجو...', className, onSelect }: CommandProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const filtered = items.filter((item) => {
    const q = query.toLowerCase()
    return (
      item.label.toLowerCase().includes(q) ||
      item.keywords?.some((k) => k.toLowerCase().includes(q))
    )
  })

  useEffect(() => {
    setSelectedIndex(0)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((i) => Math.min(filtered.length - 1, i + 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((i) => Math.max(0, i - 1))
    } else if (e.key === 'Enter' && filtered[selectedIndex]) {
      e.preventDefault()
      filtered[selectedIndex].onSelect?.()
      onSelect?.(filtered[selectedIndex].id)
    }
  }

  return (
    <div
      className={cn(
        'flex h-full w-full flex-col overflow-hidden rounded-lg border border-ink/10 bg-surface-raised shadow-raised',
        className,
      )}
    >
      <div className="flex items-center gap-2 border-b border-ink/5 px-3">
        <Search size={16} className="text-ink-subtle" />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="h-10 w-full bg-transparent text-sm text-ink placeholder:text-ink-subtle outline-none"
        />
      </div>
      <div className="max-h-72 overflow-auto p-1">
        {filtered.length === 0 ? (
          <p className="p-2 text-center text-xs text-ink-muted">نتیجه‌ای یافت نشد.</p>
        ) : (
          filtered.map((item, index) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                item.onSelect?.()
                onSelect?.(item.id)
              }}
              className={cn(
                'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-ink outline-none',
                index === selectedIndex && 'bg-surface-muted',
              )}
            >
              {item.icon && <span className="text-ink-subtle">{item.icon}</span>}
              <span>{item.label}</span>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
