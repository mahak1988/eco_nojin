import { cn } from '@eco/utils'
import * as RT from '@radix-ui/react-toggle'
import { forwardRef } from 'react'

export type ToggleProps = Omit<RT.ToggleProps, 'onPressedChange'> & {
  onPressedChange?: (pressed: boolean) => void
}

export const Toggle = forwardRef<HTMLButtonElement, ToggleProps>(function Toggle(
  { className, pressed, onPressedChange, ...rest },
  ref,
) {
  return (
    <RT.Root
      ref={ref}
      pressed={pressed}
      onPressedChange={(v) => onPressedChange?.(v)}
      className={cn(
        'inline-flex h-9 items-center justify-center rounded-md border border-ink/10 bg-surface-raised px-3 text-sm text-ink',
        'hover:bg-surface-muted hover:text-ink focus:outline-none focus:shadow-glow',
        'data-[state=on]:bg-brand-50 data-[state=on]:text-brand-700 data-[state=on]:border-brand-400',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...rest}
    />
  )
})
