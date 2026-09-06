import { cn } from '@eco/utils'
import * as RA from '@radix-ui/react-accordion'
import { forwardRef } from 'react'
import { ChevronDown } from './icon'

export type AccordionProps = RA.AccordionSingleProps | RA.AccordionMultipleProps

export const Accordion = RA.Root

export const AccordionItem = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RA.Item>
>(function AccordionItem({ className, ...rest }, ref) {
  return (
    <RA.Item
      ref={ref}
      className={cn('border-b border-ink/10 last:border-b-0', className)}
      {...rest}
    />
  )
})

export const AccordionTrigger = forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<typeof RA.Trigger>
>(function AccordionTrigger({ className, children, ...rest }, ref) {
  return (
    <RA.Header className="flex">
      <RA.Trigger
        ref={ref}
        className={cn(
          'flex flex-1 items-center justify-between py-4 text-sm font-medium text-ink transition-all',
          'hover:text-brand-700 focus:outline-none focus:shadow-glow',
          '[&[data-state=open]>svg]:rotate-180',
          className,
        )}
        {...rest}
      >
        {children}
        <ChevronDown size={16} className="text-ink-muted transition-transform duration-200" />
      </RA.Trigger>
    </RA.Header>
  )
})

export const AccordionContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RA.Content>
>(function AccordionContent({ className, children, ...rest }, ref) {
  return (
    <RA.Content
      ref={ref}
      className={cn(
        'overflow-hidden text-sm text-ink-muted data-[state=closed]:animate-slide-up data-[state=open]:animate-slide-down',
        className,
      )}
      {...rest}
    >
      <div className="pb-4 pt-0">{children}</div>
    </RA.Content>
  )
})
