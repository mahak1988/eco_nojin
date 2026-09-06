import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export function Divider({
  orientation = 'horizontal',
  className,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { orientation?: 'horizontal' | 'vertical' }) {
  return (
    <div
      role="separator"
      aria-orientation={orientation}
      className={cn(
        'bg-ink/10',
        orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
        className,
      )}
      {...rest}
    />
  )
}
