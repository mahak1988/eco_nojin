import { cn } from '@eco/utils'
import { type HTMLAttributes, forwardRef } from 'react'

export type CardElevation = 'flat' | 'soft' | 'raised' | 'elevated'

export type CardProps = HTMLAttributes<HTMLDivElement> & {
  elevation?: CardElevation
  interactive?: boolean
}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { elevation = 'soft', interactive = false, className, ...rest },
  ref,
) {
  return (
    <div
      ref={ref}
      className={cn(
        'rounded-lg border border-ink/5 bg-surface-raised',
        elevation === 'flat' && 'shadow-none',
        elevation === 'soft' && 'shadow-soft',
        elevation === 'raised' && 'shadow-raised',
        elevation === 'elevated' && 'shadow-elevated',
        interactive && 'transition hover:shadow-raised cursor-pointer',
        className,
      )}
      {...rest}
    />
  )
})

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  function CardHeader({ className, ...rest }, ref) {
    return (
      <div
        ref={ref}
        className={cn('flex flex-col gap-1 border-b border-ink/5 px-5 py-4', className)}
        {...rest}
      />
    )
  },
)

export const CardBody = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  function CardBody({ className, ...rest }, ref) {
    return <div ref={ref} className={cn('p-5', className)} {...rest} />
  },
)

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  function CardFooter({ className, ...rest }, ref) {
    return (
      <div
        ref={ref}
        className={cn('flex items-center gap-2 border-t border-ink/5 px-5 py-3', className)}
        {...rest}
      />
    )
  },
)
