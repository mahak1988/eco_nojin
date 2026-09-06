import { cn } from '@eco/utils'
import * as RD from '@radix-ui/react-dialog'
import type { ReactNode } from 'react'
import { Button } from '../primitives'

export type OffCanvasProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  side?: 'left' | 'right' | 'top' | 'bottom'
  title?: string
  children: ReactNode
  className?: string
}

const SIDE: Record<string, string> = {
  left: 'inset-y-0 start-0 -translate-x-full data-[state=open]:translate-x-0',
  right: 'inset-y-0 end-0 translate-x-full data-[state=open]:translate-x-0',
  top: 'inset-x-0 top-0 -translate-y-full data-[state=open]:translate-y-0',
  bottom: 'inset-x-0 bottom-0 translate-y-full data-[state=open]:translate-y-0',
}

export function OffCanvas({
  open,
  onOpenChange,
  side = 'left',
  title,
  children,
  className,
}: OffCanvasProps) {
  return (
    <RD.Root open={open} onOpenChange={onOpenChange}>
      <RD.Portal>
        <RD.Overlay className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm" />
        <RD.Content
          className={cn(
            'fixed z-50 bg-surface-raised shadow-elevated transition-transform duration-300 ease-out-soft',
            SIDE[side],
            side === 'left' || side === 'right'
              ? 'h-full w-80 border-s border-ink/10'
              : 'w-full border-t border-ink/10',
            className,
          )}
        >
          {title && (
            <div className="flex items-center justify-between border-b border-ink/5 px-4 py-3">
              <h2 className="text-base font-semibold text-ink">{title}</h2>
              <RD.Close asChild>
                <Button variant="ghost" size="sm">
                  بستن
                </Button>
              </RD.Close>
            </div>
          )}
          <div className="p-4">{children}</div>
        </RD.Content>
      </RD.Portal>
    </RD.Root>
  )
}
