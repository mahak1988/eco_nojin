import { cn } from '@eco/utils'
import type { ReactNode } from 'react'
import { Card, CardBody, CardHeader } from '../primitives'

export type ChartCardProps = {
  title?: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
  loading?: boolean
}

export function ChartCard({
  title,
  subtitle,
  action,
  children,
  className,
  loading,
}: ChartCardProps) {
  return (
    <Card className={cn('flex flex-col', className)}>
      {(title || subtitle || action) && (
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              {title && <h3 className="text-base font-semibold text-ink">{title}</h3>}
              {subtitle && <p className="text-xs text-ink-muted">{subtitle}</p>}
            </div>
            {action && <div>{action}</div>}
          </div>
        </CardHeader>
      )}
      <CardBody className={cn(!title && !subtitle && 'p-0')}>
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-r-transparent" />
          </div>
        ) : (
          children
        )}
      </CardBody>
    </Card>
  )
}
