import { cn } from '@eco/utils'
import { Card, CardBody, CardHeader } from '../primitives'
import { Badge } from '../primitives'

export type NotificationCenterProps = {
  notifications: {
    id: string
    title: string
    description?: string
    time: string
    read?: boolean
    tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info'
  }[]
  onMarkRead?: (id: string) => void
  className?: string
}

export function NotificationCenter({
  notifications,
  onMarkRead,
  className,
}: NotificationCenterProps) {
  const unread = notifications.filter((n) => !n.read).length
  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-ink">اعلان‌ها</h3>
          {unread > 0 && (
            <Badge tone="brand" variant="solid">
              {unread} جدید
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardBody className="flex flex-col gap-3">
        {notifications.length === 0 ? (
          <p className="text-sm text-ink-muted">اعلان جدیدی نیست.</p>
        ) : (
          notifications.map((n) => (
            <button
              key={n.id}
              type="button"
              onClick={() => onMarkRead?.(n.id)}
              className={cn(
                'flex flex-col gap-1 rounded-lg border border-ink/5 p-3 text-start transition-colors hover:bg-surface-muted',
                !n.read && 'border-brand-400/40 bg-brand-50/50',
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-ink">{n.title}</span>
                <span className="text-[10px] text-ink-subtle">{n.time}</span>
              </div>
              {n.description && <p className="text-xs text-ink-muted">{n.description}</p>}
            </button>
          ))
        )}
      </CardBody>
    </Card>
  )
}
