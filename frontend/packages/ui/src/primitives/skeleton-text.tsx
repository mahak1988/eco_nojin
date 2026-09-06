import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type SkeletonTextProps = HTMLAttributes<HTMLDivElement> & {
  lines?: number
  lineHeight?: number
}

export function SkeletonText({
  lines = 3,
  lineHeight = 12,
  className,
  ...rest
}: SkeletonTextProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)} {...rest} aria-hidden="true">
      {Array.from({ length: lines }, (_, i) => (
        <div
          key={i}
          className="animate-pulse rounded bg-ink/10"
          style={{
            width: i === lines - 1 ? '70%' : '100%',
            height: lineHeight,
          }}
        />
      ))}
    </div>
  )
}
