import { cn } from '@eco/utils'
import { forwardRef } from 'react'

export type DatePickerProps = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'value' | 'onChange'
> & {
  value?: string
  onChange?: (value: string) => void
}

export const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(function DatePicker(
  { className, value, onChange, ...rest },
  ref,
) {
  return (
    <div className={cn('relative', className)}>
      <input
        ref={ref}
        type="date"
        value={value}
        onChange={(e) => onChange?.((e.target as HTMLInputElement).value)}
        className={cn(
          'h-10 w-full rounded-md border border-ink/15 bg-surface-raised px-3 text-sm text-ink',
          'focus:outline-none focus:shadow-glow focus:border-brand-500',
          'disabled:cursor-not-allowed disabled:bg-surface-muted',
        )}
        {...rest}
      />
    </div>
  )
})
