import { cn } from '@eco/utils'
import * as RD from '@radix-ui/react-dialog'
import { type ComponentPropsWithoutRef, forwardRef } from 'react'

export type DialogProps = RD.DialogProps

export const Dialog = RD.Root
export const DialogTrigger = RD.Trigger
export const DialogClose = RD.Close

export const DialogContent = forwardRef<
  HTMLDivElement,
  ComponentPropsWithoutRef<typeof RD.Content>
>(function DialogContent({ className, children, ...rest }, ref) {
  return (
    <RD.Portal>
      <RD.Overlay className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=open]:fade-in" />
      <RD.Content
        ref={ref}
        className={cn(
          'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
          'w-[min(560px,calc(100vw-32px))] max-h-[85vh] overflow-auto rounded-lg',
          'bg-surface-raised p-6 shadow-raised focus:outline-none',
          className,
        )}
        {...rest}
      >
        {children}
      </RD.Content>
    </RD.Portal>
  )
})

export function DialogHeader({ className, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mb-4 flex flex-col gap-1', className)} {...rest} />
}

export const DialogTitle = forwardRef<
  HTMLHeadingElement,
  ComponentPropsWithoutRef<typeof RD.Title>
>(function DialogTitle({ className, ...rest }, ref) {
  return (
    <RD.Title ref={ref} className={cn('text-lg font-semibold text-ink', className)} {...rest} />
  )
})

export const DialogDescription = forwardRef<
  HTMLParagraphElement,
  ComponentPropsWithoutRef<typeof RD.Description>
>(function DialogDescription({ className, ...rest }, ref) {
  return <RD.Description ref={ref} className={cn('text-sm text-ink-muted', className)} {...rest} />
})

export function DialogFooter({ className, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mt-6 flex items-center justify-end gap-2', className)} {...rest} />
}
