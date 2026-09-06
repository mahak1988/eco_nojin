import { cn } from '@eco/utils'
import * as RP from '@radix-ui/react-progress'
import { forwardRef } from 'react'

export type ProgressProps = Omit<RP.ProgressProps, 'value'> & {
  value?: number
}

export const Progress = forwardRef<HTMLDivElement, ProgressProps>(function Progress(
  { className, value = 0, ...rest },
  ref,
) {
  return (
    <RP.Root
      ref={ref}
      value={value}
      className={cn('relative h-2 w-full overflow-hidden rounded-full bg-ink/10', className)}
      {...rest}
    >
      <RP.Indicator
        className="h-full rounded-full bg-brand-600 transition-all duration-300 ease-out"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </RP.Root>
  )
})
