import { cn } from '@eco/utils'
import { type ReactNode, useMemo } from 'react'

export type MasonryLayoutProps = {
  children: ReactNode
  columns?: 1 | 2 | 3 | 4 | 5 | 6
  gap?: 'sm' | 'md' | 'lg'
  className?: string
}

const COLUMN_CLASSES: Record<number, string> = {
  1: 'columns-1',
  2: 'columns-1 sm:columns-2',
  3: 'columns-1 sm:columns-2 lg:columns-3',
  4: 'columns-1 sm:columns-2 lg:columns-4',
  5: 'columns-1 sm:columns-2 lg:columns-3 xl:columns-5',
  6: 'columns-1 sm:columns-2 lg:columns-3 xl:columns-6',
}

const GAP_CLASSES: Record<string, string> = {
  sm: 'gap-3',
  md: 'gap-4',
  lg: 'gap-6',
}

export function MasonryLayout({
  children,
  columns = 3,
  gap = 'md',
  className,
}: MasonryLayoutProps) {
  const items = useMemo(() => {
    const childArray = Array.isArray(children) ? children : [children]
    return childArray.map((child, index) => (
      <div
        key={index}
        className={cn('mb-4 break-inside-avoid')}
        style={{ contain: 'layout style paint' }}
      >
        {child}
      </div>
    ))
  }, [children])

  return <div className={cn(COLUMN_CLASSES[columns], GAP_CLASSES[gap], className)}>{items}</div>
}

export type MasonryItemProps = {
  children: ReactNode
  className?: string
}

export function MasonryItem({ children, className }: MasonryItemProps) {
  return <div className={cn('mb-4 break-inside-avoid', className)}>{children}</div>
}
