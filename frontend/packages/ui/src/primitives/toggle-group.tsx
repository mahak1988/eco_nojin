import { cn } from '@eco/utils'
import * as RTG from '@radix-ui/react-toggle-group'
import { forwardRef } from 'react'

export type ToggleGroupProps = RTG.ToggleGroupSingleProps | RTG.ToggleGroupMultipleProps

export const ToggleGroup = RTG.Root

export const ToggleGroupItem = forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<typeof RTG.Item>
>(function ToggleGroupItem({ className, ...rest }, ref) {
  return (
    <RTG.Item
      ref={ref}
      className={cn(
        'inline-flex h-9 min-w-9 items-center justify-center rounded-md border border-ink/10 bg-surface-raised px-2 text-sm text-ink-muted',
        'hover:bg-surface-muted hover:text-ink focus:outline-none focus:shadow-glow',
        'data-[state=on]:bg-brand-50 data-[state=on]:text-brand-700 data-[state=on]:border-brand-400',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...rest}
    />
  )
})
