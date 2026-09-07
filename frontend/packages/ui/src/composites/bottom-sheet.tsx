import { cn } from '@eco/utils'
import * as RD from '@radix-ui/react-dialog'
import { type ReactNode, useEffect, useRef, useState } from 'react'

export type BottomSheetProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: ReactNode
  snapPoints?: ('25%' | '50%' | '75%' | '90%')[]
  defaultSnapPoint?: '25%' | '50%' | '75%' | '90%'
  className?: string
}

export type BottomSheetContentProps = {
  children: ReactNode
  className?: string
}

export type BottomSheetHandleProps = {
  className?: string
}

const SNAP_HEIGHTS: Record<string, number> = {
  '25%': 25,
  '50%': 50,
  '75%': 75,
  '90%': 90,
}

export function BottomSheet({
  open,
  onOpenChange,
  children,
  snapPoints = ['25%', '50%', '90%'],
  defaultSnapPoint = '50%',
  className,
}: BottomSheetProps) {
  const [snapPoint, setSnapPoint] = useState(defaultSnapPoint)
  const [dragY, setDragY] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const sheetRef = useRef<HTMLDivElement>(null)
  const startY = useRef(0)
  const currentTranslateY = useRef(0)

  useEffect(() => {
    if (!open) {
      setDragY(0)
      setSnapPoint(defaultSnapPoint)
    }
  }, [open, defaultSnapPoint])

  useEffect(() => {
    if (!open) return
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  const handlePointerDown = (e: React.PointerEvent) => {
    if ((e.target as HTMLElement).closest('[data-no-drag]')) return
    setIsDragging(true)
    startY.current = e.clientY
    currentTranslateY.current = dragY
    ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return
    const delta = e.clientY - startY.current
    setDragY(currentTranslateY.current + delta)
  }

  const handlePointerUp = () => {
    if (!isDragging) return
    setIsDragging(false)
    const threshold = 80
    if (dragY > threshold) {
      const currentIndex = snapPoints.indexOf(snapPoint)
      const prev = currentIndex > 0 ? snapPoints[currentIndex - 1] : null
      if (prev) setSnapPoint(prev)
      else onOpenChange(false)
    } else if (dragY < -threshold) {
      const currentIndex = snapPoints.indexOf(snapPoint)
      const next =
        currentIndex >= 0 && currentIndex < snapPoints.length - 1
          ? snapPoints[currentIndex + 1]
          : null
      if (next) setSnapPoint(next)
    }
    setDragY(0)
  }

  const snapHeight = SNAP_HEIGHTS[snapPoint] || 50
  const dragOffset = isDragging ? dragY : 0

  return (
    <RD.Root open={open} onOpenChange={onOpenChange}>
      <RD.Portal>
        <RD.Overlay className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out" />
        <RD.Content
          ref={sheetRef}
          className={cn(
            'fixed inset-x-0 bottom-0 z-50 rounded-t-2xl bg-surface-raised shadow-elevated',
            'data-[state=open]:animate-slide-up data-[state=closed]:animate-slide-down',
            className,
          )}
          style={{ height: `calc(${snapHeight}vh - env(safe-area-inset-bottom, 0px))` }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={() => {
            setIsDragging(false)
            setDragY(0)
          }}
        >
          <div className="flex items-center justify-center border-b border-ink/5 py-3" data-no-drag>
            <div className="h-1.5 w-12 rounded-full bg-ink/15" />
          </div>
          <div className="h-full overflow-y-auto overscroll-y-contain p-4">{children}</div>
        </RD.Content>
      </RD.Portal>
    </RD.Root>
  )
}

export function BottomSheetContent({ children, className }: BottomSheetContentProps) {
  return <div className={cn('flex flex-col gap-4', className)}>{children}</div>
}

export function BottomSheetHandle({ className }: BottomSheetHandleProps) {
  return (
    <div className={cn('flex items-center justify-center border-b border-ink/5 py-3', className)}>
      <div className="h-1.5 w-12 rounded-full bg-ink/15" />
    </div>
  )
}
