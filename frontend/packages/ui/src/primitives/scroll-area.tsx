import { cn } from '@eco/utils'
import * as RS from '@radix-ui/react-scroll-area'
import { forwardRef } from 'react'

export const ScrollArea = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RS.Root>
>(function ScrollArea({ className, children, ...rest }, ref) {
  return (
    <RS.Root ref={ref} className={cn('relative overflow-hidden', className)} {...rest}>
      <RS.Viewport className="h-full w-full rounded-[inherit]">{children}</RS.Viewport>
      <RS.Scrollbar
        orientation="vertical"
        className="flex touch-none select-none rounded bg-ink/5 p-0.5"
      >
        <RS.ScrollAreaThumb className="relative flex-1 rounded-full bg-ink/20" />
      </RS.Scrollbar>
      <RS.Scrollbar
        orientation="horizontal"
        className="flex touch-none select-none rounded bg-ink/5 p-0.5"
      >
        <RS.ScrollAreaThumb className="relative flex-1 rounded-full bg-ink/20" />
      </RS.Scrollbar>
    </RS.Root>
  )
})
