import { cn } from '@eco/utils'
import * as RD from '@radix-ui/react-dialog'
import type { ReactNode } from 'react'
import { Button } from '../primitives'

export type CartItem = {
  id: string
  title: string
  price: number
  quantity: number
  image?: ReactNode
}

export type CartDrawerProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  items: CartItem[]
  onRemove?: (id: string) => void
  onCheckout?: () => void
}

export function CartDrawer({ open, onOpenChange, items, onRemove, onCheckout }: CartDrawerProps) {
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0)

  return (
    <RD.Root open={open} onOpenChange={onOpenChange}>
      <RD.Portal>
        <RD.Overlay className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm" />
        <RD.Content
          className={cn(
            'fixed inset-y-0 start-0 z-50 w-80 border-e border-ink/10 bg-surface-raised shadow-elevated',
            'flex flex-col data-[state=open]:animate-slide-in-right data-[state=closed]:animate-slide-in-left',
          )}
        >
          <div className="flex items-center justify-between border-b border-ink/5 px-4 py-3">
            <h2 className="text-base font-semibold">سبد خرید</h2>
            <RD.Close asChild>
              <Button variant="ghost" size="sm">
                بستن
              </Button>
            </RD.Close>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {items.length === 0 ? (
              <p className="text-sm text-ink-muted">سبد خرید خالی است.</p>
            ) : (
              <div className="flex flex-col gap-3">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 rounded-lg border border-ink/5 p-2"
                  >
                    <div className="h-12 w-12 shrink-0 rounded-md bg-surface-muted">
                      {item.image}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-ink truncate">{item.title}</p>
                      <p className="text-xs text-ink-muted">
                        {item.quantity} × {item.price.toLocaleString('fa-IR')} تومان
                      </p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => onRemove?.(item.id)}>
                      ✕
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
          {items.length > 0 && (
            <div className="border-t border-ink/5 p-4">
              <div className="mb-3 flex items-center justify-between text-sm font-semibold">
                <span>جمع کل:</span>
                <span>{total.toLocaleString('fa-IR')} تومان</span>
              </div>
              <Button fullWidth onClick={onCheckout}>
                تکمیل خرید
              </Button>
            </div>
          )}
        </RD.Content>
      </RD.Portal>
    </RD.Root>
  )
}
