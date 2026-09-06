import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type BadgeTone =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'brand'
  | 'sky'
  | 'leaf'

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone
  variant?: 'soft' | 'solid' | 'outline'
}

const TONE_SOFT: Record<BadgeTone, string> = {
  neutral: 'bg-ink/5 text-ink-muted',
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  danger: 'bg-danger/10 text-danger',
  info: 'bg-info/10 text-info',
  brand: 'bg-brand-50 text-brand-700',
  sky: 'bg-sky-50 text-sky-700',
  leaf: 'bg-leaf-50 text-leaf-700',
}

const TONE_SOLID: Record<BadgeTone, string> = {
  neutral: 'bg-ink text-white',
  success: 'bg-success text-white',
  warning: 'bg-warning text-white',
  danger: 'bg-danger text-white',
  info: 'bg-info text-white',
  brand: 'bg-brand-600 text-white',
  sky: 'bg-sky-600 text-white',
  leaf: 'bg-leaf-600 text-white',
}

const TONE_OUTLINE: Record<BadgeTone, string> = {
  neutral: 'border border-ink/15 text-ink-muted',
  success: 'border border-success/40 text-success',
  warning: 'border border-warning/40 text-warning',
  danger: 'border border-danger/40 text-danger',
  info: 'border border-info/40 text-info',
  brand: 'border border-brand-400 text-brand-700',
  sky: 'border border-sky-400 text-sky-700',
  leaf: 'border border-leaf-400 text-leaf-700',
}

export function Badge({ tone = 'neutral', variant = 'soft', className, ...rest }: BadgeProps) {
  const map = variant === 'solid' ? TONE_SOLID : variant === 'outline' ? TONE_OUTLINE : TONE_SOFT
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
        map[tone],
        className,
      )}
      {...rest}
    />
  )
}
