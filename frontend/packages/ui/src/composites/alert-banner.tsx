import { cn } from '@eco/utils'
import type { ReactNode } from 'react'
import { Button } from '../primitives'
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from '../primitives/icon'

export type AlertBannerProps = {
  tone?: 'info' | 'success' | 'warning' | 'danger'
  title?: string
  children?: ReactNode
  onClose?: () => void
  className?: string
}

const ICONS: Record<string, ReactNode> = {
  info: <Info size={18} />,
  success: <CheckCircle2 size={18} />,
  warning: <AlertTriangle size={18} />,
  danger: <XCircle size={18} />,
}

export function AlertBanner({
  tone = 'info',
  title,
  children,
  onClose,
  className,
}: AlertBannerProps) {
  const palette: Record<string, string> = {
    info: 'border-info/40 bg-info/5 text-info',
    success: 'border-success/40 bg-success/5 text-success',
    warning: 'border-warning/40 bg-warning/5 text-warning',
    danger: 'border-danger/40 bg-danger/5 text-danger',
  }

  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 rounded-lg border px-4 py-3 text-sm',
        palette[tone],
        className,
      )}
    >
      <span aria-hidden="true" className="mt-0.5">
        {ICONS[tone]}
      </span>
      <div className="flex-1">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className="mt-0.5 text-xs opacity-90">{children}</div>}
      </div>
      {onClose && (
        <Button variant="ghost" size="sm" onClick={onClose} className="p-1" aria-label="بستن">
          <X size={14} />
        </Button>
      )}
    </div>
  )
}
