import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type AvatarGroupProps = HTMLAttributes<HTMLDivElement> & {
  children: React.ReactNode
  max?: number
}

export function AvatarGroup({ children, max = 4, className, ...rest }: AvatarGroupProps) {
  const childArray = Array.isArray(children) ? children : [children]
  const visible = childArray.slice(0, max)
  const remaining = childArray.length - max

  return (
    <div className={cn('flex items-center -space-x-2 rtl:space-x-reverse', className)} {...rest}>
      {visible}
      {remaining > 0 && (
        <div
          className={cn(
            'flex h-8 w-8 items-center justify-center rounded-full border-2 border-surface-raised bg-surface-muted text-xs font-semibold text-ink-muted',
          )}
          aria-label={`${remaining} more`}
        >
          +{remaining}
        </div>
      )}
    </div>
  )
}
