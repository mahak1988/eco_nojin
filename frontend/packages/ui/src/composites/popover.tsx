import { cn } from '@eco/utils'
import * as RP from '@radix-ui/react-popover'
import { forwardRef } from 'react'

export const Popover = RP.Root
export const PopoverTrigger = RP.Trigger

export const PopoverContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RP.Content>
>(function PopoverContent({ className, ...rest }, ref) {
  return (
    <RP.Portal>
      <RP.Content
        ref={ref}
        sideOffset={6}
        className={cn(
          'z-50 w-72 rounded-md border border-ink/10 bg-surface-raised p-4 shadow-raised focus:outline-none',
          className,
        )}
        {...rest}
      />
    </RP.Portal>
  )
})
