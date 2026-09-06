import { cn } from '@eco/utils'
import type { HTMLAttributes, ReactNode } from 'react'

export type FieldProps = Omit<HTMLAttributes<HTMLDivElement>, 'children'> & {
  label: ReactNode
  hint?: ReactNode
  error?: ReactNode
  children: ReactNode
}

/**
 * Generic labeled field. Renders a label above an input slot, with optional
 * hint or error text below. Does not impose any specific input type.
 */
export function Field({ label, hint, error, children, className, ...rest }: FieldProps) {
  return (
    <div className={cn('flex flex-col gap-1 text-xs text-ink-muted', className)} {...rest}>
      <span className="font-medium">{label}</span>
      {children}
      {error ? (
        <span className="text-danger">{error}</span>
      ) : hint ? (
        <span className="text-ink-subtle">{hint}</span>
      ) : null}
    </div>
  )
}
