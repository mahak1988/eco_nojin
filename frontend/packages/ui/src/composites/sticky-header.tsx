import { cn } from '@eco/utils'
import type { ReactNode } from 'react'

export type StickyHeaderProps = {
  children: ReactNode
  className?: string
  offset?: number
}

export function StickyHeader({ children, className, offset = 0 }: StickyHeaderProps) {
  return (
    <div
      className={cn('sticky top-0 z-10 bg-surface/85 backdrop-blur-xl', className)}
      style={{ top: offset }}
    >
      {children}
    </div>
  )
}
