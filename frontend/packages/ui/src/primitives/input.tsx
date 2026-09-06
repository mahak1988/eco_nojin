import { cn } from '@eco/utils'
import { type InputHTMLAttributes, type TextareaHTMLAttributes, forwardRef } from 'react'

type InputSize = 'sm' | 'md' | 'lg'

export type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> & {
  invalid?: boolean
  size?: InputSize
}

const SIZE: Record<InputSize, string> = {
  sm: 'h-8 px-2.5 text-sm',
  md: 'h-10 px-3 text-sm',
  lg: 'h-12 px-4 text-base',
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { invalid = false, size = 'md', className, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(
        'block w-full rounded-md border bg-surface-raised text-ink',
        'placeholder:text-ink-subtle focus:outline-none focus:shadow-glow',
        'disabled:cursor-not-allowed disabled:bg-surface-muted disabled:opacity-70',
        invalid ? 'border-danger focus:border-danger' : 'border-ink/15 focus:border-brand-500',
        SIZE[size],
        className,
      )}
      {...rest}
    />
  )
})

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { invalid = false, className, ...rest },
  ref,
) {
  return (
    <textarea
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(
        'block w-full rounded-md border bg-surface-raised px-3 py-2 text-sm text-ink',
        'placeholder:text-ink-subtle focus:outline-none focus:shadow-glow',
        'disabled:cursor-not-allowed disabled:bg-surface-muted',
        invalid ? 'border-danger' : 'border-ink/15 focus:border-brand-500',
        className,
      )}
      {...rest}
    />
  )
})
