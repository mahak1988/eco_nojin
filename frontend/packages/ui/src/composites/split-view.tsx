import { cn } from '@eco/utils'
import type { ReactNode } from 'react'
import { Separator } from '../primitives'

export type SplitViewProps = {
  primary: ReactNode
  secondary: ReactNode
  direction?: 'horizontal' | 'vertical'
  primarySize?: number
  className?: string
}

export function SplitView({
  primary,
  secondary,
  direction = 'horizontal',
  primarySize = 50,
  className,
}: SplitViewProps) {
  return (
    <div className={cn('flex', direction === 'horizontal' ? 'flex-row' : 'flex-col', className)}>
      <div style={{ flexBasis: `${primarySize}%`, flexShrink: 0 }}>{primary}</div>
      <Separator orientation={direction} />
      <div style={{ flexBasis: `${100 - primarySize}%`, flexShrink: 0 }}>{secondary}</div>
    </div>
  )
}
