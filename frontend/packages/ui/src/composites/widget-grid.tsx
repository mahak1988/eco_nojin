import { cn } from '@eco/utils'
import type { ReactNode } from 'react'

export type WidgetGridProps = {
  children: ReactNode
  columns?: 1 | 2 | 3 | 4 | 6 | 12
  gap?: 'sm' | 'md' | 'lg'
  className?: string
}

const COLUMNS: Record<number, string> = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 md:grid-cols-2',
  3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  6: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6',
  12: 'grid-cols-4 md:grid-cols-6 lg:grid-cols-12',
}

const GAP: Record<string, string> = {
  sm: 'gap-3',
  md: 'gap-4',
  lg: 'gap-6',
}

export function WidgetGrid({ children, columns = 3, gap = 'md', className }: WidgetGridProps) {
  return <div className={cn('grid', COLUMNS[columns], GAP[gap], className)}>{children}</div>
}
