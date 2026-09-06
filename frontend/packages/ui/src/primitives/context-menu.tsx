import { cn } from '@eco/utils'
import * as RC from '@radix-ui/react-context-menu'
import { forwardRef } from 'react'

export const ContextMenu = RC.Root
export const ContextMenuTrigger = RC.Trigger

export const ContextMenuContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RC.Content>
>(function ContextMenuContent({ className, ...rest }, ref) {
  return (
    <RC.Portal>
      <RC.Content
        ref={ref}
        className={cn(
          'z-50 min-w-[12rem] rounded-md border border-ink/10 bg-surface-raised p-1 shadow-raised',
          className,
        )}
        {...rest}
      />
    </RC.Portal>
  )
})

export const ContextMenuItem = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RC.Item>
>(function ContextMenuItem({ className, ...rest }, ref) {
  return (
    <RC.Item
      ref={ref}
      className={cn(
        'flex cursor-pointer select-none items-center gap-2 rounded px-2 py-1.5 text-sm outline-none',
        'text-ink data-[highlighted]:bg-surface-muted',
        className,
      )}
      {...rest}
    />
  )
})

export const ContextMenuSeparator = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RC.Separator>
>(function ContextMenuSeparator({ className, ...rest }, ref) {
  return <RC.Separator ref={ref} className={cn('my-1 h-px bg-ink/10', className)} {...rest} />
})
