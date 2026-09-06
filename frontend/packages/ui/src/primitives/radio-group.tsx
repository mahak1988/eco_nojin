import { cn } from '@eco/utils'
import * as RR from '@radix-ui/react-radio-group'
import { forwardRef } from 'react'

export type RadioGroupProps = RR.RadioGroupProps

export const RadioGroup = RR.Root

export const RadioGroupItem = forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<typeof RR.Item>
>(function RadioGroupItem({ className, ...rest }, ref) {
  return (
    <RR.Item
      ref={ref}
      className={cn(
        'h-4 w-4 shrink-0 rounded-full border border-ink/20 bg-surface-raised',
        'focus:outline-none focus:shadow-glow focus:border-brand-500',
        'data-[state=checked]:border-brand-600',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...rest}
    >
      <RR.Indicator className="flex items-center justify-center">
        <span className="h-2 w-2 rounded-full bg-brand-600" />
      </RR.Indicator>
    </RR.Item>
  )
})
