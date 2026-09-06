import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type SpinnerProps = HTMLAttributes<HTMLSpanElement> & {
  size?: 'sm' | 'md' | 'lg'
  tone?: 'brand' | 'neutral' | 'inverse'
}

const SIZE = { sm: 'h-3 w-3 border-2', md: 'h-5 w-5 border-2', lg: 'h-8 w-8 border-[3px]' } as const

const TONE = {
  brand: 'border-brand-600 border-r-transparent',
  neutral: 'border-ink-muted border-r-transparent',
  inverse: 'border-white border-r-transparent',
} as const

export function Spinner({ size = 'md', tone = 'brand', className, ...rest }: SpinnerProps) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn('inline-block animate-spin rounded-full', SIZE[size], TONE[tone], className)}
      {...rest}
    />
  )
}
