import { cn } from '@eco/utils'
import * as RC from '@radix-ui/react-checkbox'
import { forwardRef } from 'react'
import { Check } from './icon'

export type CheckboxProps = Omit<RC.CheckboxProps, 'onCheckedChange'> & {
  onCheckedChange?: (checked: boolean) => void
}

export const Checkbox = forwardRef<HTMLButtonElement, CheckboxProps>(function Checkbox(
  { className, checked, onCheckedChange, ...rest },
  ref,
) {
  return (
    <RC.Root
      ref={ref}
      checked={checked}
      onCheckedChange={(v) => onCheckedChange?.(Boolean(v))}
      className={cn(
        'peer h-4 w-4 shrink-0 rounded border border-ink/20 bg-surface-raised',
        'focus:outline-none focus:shadow-glow focus:border-brand-500',
        'data-[state=checked]:bg-brand-600 data-[state=checked]:border-brand-600',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...rest}
    >
      <RC.Indicator className="flex items-center justify-center text-white">
        <Check size={12} />
      </RC.Indicator>
    </RC.Root>
  )
})
