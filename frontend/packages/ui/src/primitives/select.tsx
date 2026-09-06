import { cn } from '@eco/utils'
import * as RS from '@radix-ui/react-select'
import { forwardRef } from 'react'
import { Check, ChevronDown } from './icon'

const _ITEM_HEIGHT = 'h-10'

export const Select = RS.Root
export const SelectTrigger = forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<typeof RS.Trigger>
>(function SelectTrigger({ className, children, ...rest }, ref) {
  return (
    <RS.Trigger
      ref={ref}
      className={cn(
        'flex h-10 w-full items-center justify-between rounded-md border border-ink/15 bg-surface-raised px-3 text-sm text-ink',
        'focus:outline-none focus:shadow-glow focus:border-brand-500',
        'disabled:cursor-not-allowed disabled:bg-surface-muted disabled:opacity-70',
        className,
      )}
      {...rest}
    >
      {children}
      <RS.Icon asChild>
        <span className="text-ink-muted">
          <ChevronDown size={16} />
        </span>
      </RS.Icon>
    </RS.Trigger>
  )
})

export const SelectContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RS.Content>
>(function SelectContent({ className, children, ...rest }, ref) {
  return (
    <RS.Portal>
      <RS.Content
        ref={ref}
        position="popper"
        sideOffset={4}
        className={cn(
          'z-50 max-h-64 overflow-auto rounded-md border border-ink/10 bg-surface-raised p-1 shadow-raised',
          className,
        )}
        {...rest}
      >
        {children}
      </RS.Content>
    </RS.Portal>
  )
})

export const SelectItem = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RS.Item>
>(function SelectItem({ className, children, ...rest }, ref) {
  return (
    <RS.Item
      ref={ref}
      className={cn(
        'flex cursor-pointer select-none items-center gap-2 rounded px-2 py-1.5 text-sm outline-none',
        'data-[highlighted]:bg-surface-muted data-[state=checked]:text-brand-700',
        className,
      )}
      {...rest}
    >
      <RS.ItemText>{children}</RS.ItemText>
      <RS.ItemIndicator className="ms-auto">
        <Check size={14} />
      </RS.ItemIndicator>
    </RS.Item>
  )
})

export const SelectValue = RS.Value
