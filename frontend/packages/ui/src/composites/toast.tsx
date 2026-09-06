import { cn } from '@eco/utils'
import * as RT from '@radix-ui/react-toast'
import { type ReactNode, createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { BadgeTone } from '../primitives/badge'

export type ToastInput = {
  title: string
  description?: string
  tone?: BadgeTone
  duration?: number
}

type ToastRecord = ToastInput & { id: string }

type ToastContextValue = {
  notify: (toast: ToastInput) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastRecord[]>([])

  const notify = useCallback((toast: ToastInput) => {
    const id = crypto.randomUUID()
    setItems((prev) => [...prev, { ...toast, id }])
    setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id))
    }, toast.duration ?? 4500)
  }, [])

  const value = useMemo(() => ({ notify }), [notify])

  return (
    <ToastContext.Provider value={value}>
      <RT.Provider swipeDirection="right">
        {children}
        {items.map((t) => (
          <RT.Root
            key={t.id}
            onOpenChange={(open) => {
              if (!open) setItems((prev) => prev.filter((x) => x.id !== t.id))
            }}
            className={cn(
              'pointer-events-auto rounded-md border bg-surface-raised p-3 shadow-raised',
              t.tone === 'danger' && 'border-danger/40',
              t.tone === 'success' && 'border-success/40',
            )}
          >
            <RT.Title className="text-sm font-semibold text-ink">{t.title}</RT.Title>
            {t.description && (
              <RT.Description className="mt-0.5 text-xs text-ink-muted">
                {t.description}
              </RT.Description>
            )}
          </RT.Root>
        ))}
        <RT.Viewport className="fixed bottom-4 right-4 z-[60] flex w-80 max-w-[calc(100vw-32px)] flex-col gap-2" />
      </RT.Provider>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')
  return ctx
}
