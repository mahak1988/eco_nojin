import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export function Kbd({ className, ...rest }: HTMLAttributes<HTMLElement>) {
  return (
    <kbd
      className={cn(
        'inline-flex h-5 min-w-5 items-center justify-center rounded border border-ink/15 bg-surface-muted px-1 font-mono text-[10px] text-ink-muted',
        className,
      )}
      {...rest}
    />
  )
}
