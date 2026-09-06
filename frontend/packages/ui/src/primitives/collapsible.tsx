import { cn } from '@eco/utils'
import * as RC from '@radix-ui/react-collapsible'
import { forwardRef } from 'react'

export const Collapsible = RC.Root
export const CollapsibleTrigger = RC.Trigger
export const CollapsibleContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RC.Content>
>(function CollapsibleContent({ className, children, ...rest }, ref) {
  return (
    <RC.Content
      ref={ref}
      className={cn(
        'overflow-hidden text-sm text-ink-muted',
        'data-[state=closed]:animate-slide-up data-[state=open]:animate-slide-down',
        className,
      )}
      {...rest}
    >
      <div className="pb-2">{children}</div>
    </RC.Content>
  )
})
