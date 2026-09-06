import { cn } from '@eco/utils'
import * as RS from '@radix-ui/react-switch'
import { forwardRef } from 'react'

export type SwitchProps = Omit<RS.SwitchProps, 'onCheckedChange'> & {
  onCheckedChange?: (checked: boolean) => void
}

export const Switch = forwardRef<HTMLButtonElement, SwitchProps>(function Switch(
  { className, checked, onCheckedChange, ...rest },
  ref,
) {
  return (
    <RS.Root
      ref={ref}
      checked={checked}
      onCheckedChange={(v) => onCheckedChange?.(Boolean(v))}
      className={cn(
        'peer inline-flex h-6 w-11 shrink-0 items-center rounded-full border border-ink/10 bg-ink/10 transition-colors',
        'focus:outline-none focus:shadow-glow',
        'data-[state=checked]:bg-brand-600 data-[state=checked]:border-brand-600',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...rest}
    >
      <RS.Thumb
        className={cn(
          'pointer-events-none block h-5 w-5 rounded-full bg-white shadow-md ring-0 transition-transform',
          'data-[state=checked]:translate-x-5',
        )}
      />
    </RS.Root>
  )
})
