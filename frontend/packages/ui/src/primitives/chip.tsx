import { cn } from '@eco/utils'
import { forwardRef } from 'react'
import { X } from './icon'

export type ChipProps = {
  label: string
  onRemove?: () => void
  tone?: 'neutral' | 'brand' | 'sky' | 'leaf' | 'success' | 'warning' | 'danger'
  className?: string
}

export const Chip = forwardRef<HTMLSpanElement, ChipProps>(function Chip(
  { label, onRemove, tone = 'neutral', className },
  ref,
) {
  const toneClass: Record<string, string> = {
    neutral: 'bg-ink/5 text-ink-muted',
    brand: 'bg-brand-50 text-brand-700',
    sky: 'bg-sky-50 text-sky-700',
    leaf: 'bg-leaf-50 text-leaf-700',
    success: 'bg-success/10 text-success',
    warning: 'bg-warning/10 text-warning',
    danger: 'bg-danger/10 text-danger',
  }

  return (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium',
        toneClass[tone],
        className,
      )}
    >
      <span>{label}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${label}`}
          className="rounded-full p-0.5 opacity-60 hover:opacity-100"
        >
          <X size={10} />
        </button>
      )}
    </span>
  )
})
