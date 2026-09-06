import { cn } from '@eco/utils'
import { useState } from 'react'

export type SegmentedOption = {
  label: string
  value: string
}

export type SegmentedControlProps = {
  options: SegmentedOption[]
  value: string
  onChange: (value: string) => void
  className?: string
}

export function SegmentedControl({ options, value, onChange, className }: SegmentedControlProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const activeIndex = options.findIndex((o) => o.value === value)

  return (
    <div
      className={cn('relative inline-flex items-center rounded-lg bg-surface-muted p-1', className)}
      role="tablist"
    >
      <div
        className="absolute top-1 bottom-1 rounded-md bg-surface-raised shadow-soft transition-all duration-200 ease-out-soft"
        style={{
          left: `calc(${(activeIndex / options.length) * 100}% + 4px)`,
          width: `calc(${100 / options.length}% - 8px)`,
        }}
      />
      {options.map((option, index) => (
        <button
          key={option.value}
          type="button"
          role="tab"
          aria-selected={value === option.value}
          onClick={() => onChange(option.value)}
          onMouseEnter={() => setHoveredIndex(index)}
          onMouseLeave={() => setHoveredIndex(null)}
          className={cn(
            'relative z-10 h-8 flex-1 rounded-md text-sm font-medium transition-colors',
            value === option.value ? 'text-ink' : 'text-ink-muted hover:text-ink',
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
