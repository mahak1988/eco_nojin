import { cn } from '@eco/utils'
import { type ReactNode, useRef, useState } from 'react'
import { Spinner } from '../primitives'

export type PullToRefreshProps = {
  onRefresh: () => Promise<void>
  children: ReactNode
  className?: string
}

export function PullToRefresh({ onRefresh, children, className }: PullToRefreshProps) {
  const [pulling, setPulling] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const startY = useRef(0)

  const onTouchStart = (e: React.TouchEvent) => {
    if (typeof window !== 'undefined' && window.scrollY === 0)
      startY.current = e.touches[0]?.clientY ?? 0
  }

  const onTouchMove = (e: React.TouchEvent) => {
    if (refreshing) return
    if (typeof window !== 'undefined' && window.scrollY === 0) {
      const currentY = e.touches[0]?.clientY ?? 0
      const delta = currentY - startY.current
      if (delta > 40) setPulling(true)
    }
  }

  const onTouchEnd = async () => {
    if (!pulling || refreshing) return
    setRefreshing(true)
    setPulling(false)
    await onRefresh()
    setRefreshing(false)
  }

  return (
    <div
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
      className={cn('relative', className)}
    >
      <div
        className={cn(
          'flex items-center justify-center py-2 transition-opacity',
          pulling || refreshing ? 'opacity-100' : 'opacity-0',
        )}
      >
        <Spinner size="sm" tone="brand" />
      </div>
      {children}
    </div>
  )
}
