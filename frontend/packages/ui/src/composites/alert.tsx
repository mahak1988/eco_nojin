import { cn } from '@eco/utils'
import type { HTMLAttributes, ReactNode } from 'react'

export type AlertTone = 'info' | 'success' | 'warning' | 'danger'

export type AlertProps = Omit<HTMLAttributes<HTMLDivElement>, 'children'> & {
  tone?: AlertTone
  variant?: 'soft' | 'solid' | 'outline'
  title?: ReactNode
  children?: ReactNode
  onClose?: () => void
}

const TONE_SOFT: Record<AlertTone, string> = {
  info: 'bg-info/10 text-info',
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  danger: 'bg-danger/10 text-danger',
}

const TONE_OUTLINE: Record<AlertTone, string> = {
  info: 'border border-info/40 text-info',
  success: 'border border-success/40 text-success',
  warning: 'border border-warning/40 text-warning',
  danger: 'border border-danger/40 text-danger',
}

const ICON: Record<AlertTone, string> = {
  info: 'ℹ',
  success: '✓',
  warning: '⚠',
  danger: '✕',
}

export function Alert({
  tone = 'success',
  variant = 'soft',
  title,
  children,
  onClose,
  className,
  ...rest
}: AlertProps) {
  const palette = variant === 'outline' ? TONE_OUTLINE : TONE_SOFT
  return (
    <div
      role="alert"
      className={cn('flex items-start gap-3 rounded-md p-3 text-sm', palette[tone], className)}
      {...rest}
    >
      <span aria-hidden className="font-bold">
        {ICON[tone]}
      </span>
      <div className="flex-1">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className="mt-0.5 text-xs opacity-90">{children}</div>}
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="opacity-60 hover:opacity-100"
        >
          ✕
        </button>
      )}
    </div>
  )
}
