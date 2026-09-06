import { cn } from '@eco/utils'
import type { ReactNode } from 'react'

export type InlineValidationProps = {
  message: ReactNode
  tone?: 'success' | 'warning' | 'danger' | 'info'
  className?: string
}

const TONE: Record<string, string> = {
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
  info: 'text-info',
}

export function InlineValidation({ message, tone = 'danger', className }: InlineValidationProps) {
  return (
    <p className={cn('mt-1 flex items-center gap-1 text-xs', TONE[tone], className)} role="alert">
      <span aria-hidden="true">⚠</span>
      {message}
    </p>
  )
}
