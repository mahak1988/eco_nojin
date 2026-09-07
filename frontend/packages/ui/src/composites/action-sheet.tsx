import { cn } from '@eco/utils'
import * as RD from '@radix-ui/react-dialog'
import type { ReactNode } from 'react'

export type ActionSheetProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: ReactNode
  className?: string
}

export type ActionSheetContentProps = {
  children: ReactNode
  className?: string
}

export type ActionSheetGroupProps = {
  children: ReactNode
  className?: string
}

export type ActionSheetActionProps = {
  children: ReactNode
  icon?: ReactNode
  destructive?: boolean
  disabled?: boolean
  onSelect?: () => void
  className?: string
}

export type ActionSheetCancelProps = {
  children?: ReactNode
  className?: string
  onCancel?: () => void
}

export function ActionSheet({ open, onOpenChange, children, className }: ActionSheetProps) {
  return (
    <RD.Root open={open} onOpenChange={onOpenChange}>
      <RD.Portal>
        <RD.Overlay className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out" />
        <RD.Content
          className={cn(
            'fixed inset-x-0 bottom-0 z-50 rounded-t-2xl bg-surface-raised p-2 shadow-elevated',
            'data-[state=open]:animate-slide-up data-[state=closed]:animate-slide-down',
            className,
          )}
        >
          {children}
        </RD.Content>
      </RD.Portal>
    </RD.Root>
  )
}

export function ActionSheetContent({ children, className }: ActionSheetContentProps) {
  return <div className={cn('flex flex-col gap-1', className)}>{children}</div>
}

export function ActionSheetGroup({ children, className }: ActionSheetGroupProps) {
  return (
    <div className={cn('flex flex-col gap-1', className)} role="group">
      {children}
    </div>
  )
}

export function ActionSheetAction({
  children,
  icon,
  destructive = false,
  disabled = false,
  onSelect,
  className,
}: ActionSheetActionProps) {
  return (
    <button
      type="button"
      role="menuitem"
      disabled={disabled}
      onClick={() => {
        onSelect?.()
      }}
      className={cn(
        'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors',
        destructive ? 'text-danger hover:bg-danger/10' : 'text-ink hover:bg-surface-muted',
        disabled && 'opacity-50 cursor-not-allowed',
        className,
      )}
    >
      {icon && <span className="text-ink-muted">{icon}</span>}
      <span className="flex-1 text-start">{children}</span>
    </button>
  )
}

export function ActionSheetCancel({
  children = 'Cancel',
  className,
  onCancel,
}: ActionSheetCancelProps) {
  return (
    <RD.Close asChild>
      <button
        type="button"
        onClick={onCancel}
        className={cn(
          'mt-2 flex w-full items-center justify-center rounded-xl bg-surface-muted px-4 py-3 text-sm font-semibold text-ink',
          'hover:bg-surface-muted/80 active:bg-ink/5',
          className,
        )}
      >
        {children}
      </button>
    </RD.Close>
  )
}
