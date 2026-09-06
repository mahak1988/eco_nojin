import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type SkeletonProps = HTMLAttributes<HTMLDivElement> & {
  rounded?: 'sm' | 'md' | 'lg' | 'full'
}

export function Skeleton({ rounded = 'md', className, ...rest }: SkeletonProps) {
  return (
    <div
      aria-hidden
      className={cn(
        'animate-pulse bg-ink/10',
        rounded === 'sm' && 'rounded-sm',
        rounded === 'md' && 'rounded-md',
        rounded === 'lg' && 'rounded-lg',
        rounded === 'full' && 'rounded-full',
        className,
      )}
      {...rest}
    />
  )
}
