import { cn } from '@eco/utils'
import * as DM from '@radix-ui/react-dropdown-menu'
import { forwardRef } from 'react'

export const Dropdown = DM.Root
export const DropdownTrigger = DM.Trigger

export const DropdownContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof DM.Content>
>(function DropdownContent({ className, ...rest }, ref) {
  return (
    <DM.Portal>
      <DM.Content
        ref={ref}
        sideOffset={6}
        className={cn(
          'z-50 min-w-[12rem] rounded-md border border-ink/10 bg-surface-raised p-1 shadow-raised',
          className,
        )}
        {...rest}
      />
    </DM.Portal>
  )
})

export type DropdownItemProps = React.ComponentPropsWithoutRef<typeof DM.Item> & {
  destructive?: boolean
}

export const DropdownItem = forwardRef<HTMLDivElement, DropdownItemProps>(function DropdownItem(
  { className, destructive, ...rest },
  ref,
) {
  return (
    <DM.Item
      ref={ref}
      className={cn(
        'flex cursor-pointer select-none items-center gap-2 rounded px-2 py-1.5 text-sm outline-none',
        destructive
          ? 'text-danger data-[highlighted]:bg-danger/10'
          : 'text-ink data-[highlighted]:bg-surface-muted',
        className,
      )}
      {...rest}
    />
  )
})

export const DropdownSeparator = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof DM.Separator>
>(function DropdownSeparator({ className, ...rest }, ref) {
  return <DM.Separator ref={ref} className={cn('my-1 h-px bg-ink/10', className)} {...rest} />
})
