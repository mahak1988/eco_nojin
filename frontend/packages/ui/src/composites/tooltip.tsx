import { cn } from '@eco/utils'
import * as RT from '@radix-ui/react-tooltip'
import { forwardRef } from 'react'

export const TooltipProvider = RT.Provider
export const Tooltip = RT.Root
export const TooltipTrigger = RT.Trigger

export const TooltipContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RT.Content>
>(function TooltipContent({ className, ...rest }, ref) {
  return (
    <RT.Portal>
      <RT.Content
        ref={ref}
        sideOffset={6}
        className={cn(
          'z-50 max-w-xs rounded bg-ink px-2 py-1 text-xs text-white shadow-raised',
          className,
        )}
        {...rest}
      />
    </RT.Portal>
  )
})
