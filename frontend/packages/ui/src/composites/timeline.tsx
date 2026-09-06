import { cn } from '@eco/utils'
import type { ReactNode } from 'react'

export type TimelineItem = {
  id: string
  title: string
  description?: string
  time?: string
  icon?: ReactNode
  status?: 'completed' | 'active' | 'pending'
}

export type TimelineProps = {
  items: TimelineItem[]
  className?: string
}

export function Timeline({ items, className }: TimelineProps) {
  const statusColor: Record<string, string> = {
    completed: 'bg-success',
    active: 'bg-brand-600',
    pending: 'bg-ink/20',
  }

  return (
    <div className={cn('flex flex-col gap-0', className)}>
      {items.map((item, index) => (
        <div key={item.id} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div
              className={cn(
                'h-3 w-3 rounded-full border-2 border-white',
                statusColor[item.status ?? 'pending'],
              )}
            />
            {index < items.length - 1 && <div className="h-full w-px bg-ink/10" />}
          </div>
          <div className="pb-6">
            <div className="flex items-center gap-2">
              {item.icon && <span className="text-ink-subtle">{item.icon}</span>}
              <h4 className="text-sm font-semibold text-ink">{item.title}</h4>
            </div>
            {item.description && <p className="mt-1 text-sm text-ink-muted">{item.description}</p>}
            {item.time && <p className="mt-1 text-xs text-ink-subtle">{item.time}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}
