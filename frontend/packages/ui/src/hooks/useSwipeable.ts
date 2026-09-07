import { useRef, useState } from 'react'

export type SwipeableOptions = {
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
  onSwipeUp?: () => void
  onSwipeDown?: () => void
  threshold?: number
  preventScrollOnSwipe?: boolean
}

export type SwipeableResult = {
  handlers: {
    onTouchStart: (e: React.TouchEvent) => void
    onTouchMove: (e: React.TouchEvent) => void
    onTouchEnd: () => void
  }
  isSwiping: boolean
  direction: 'left' | 'right' | 'up' | 'down' | null
}

export function useSwipeable({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  preventScrollOnSwipe = false,
}: SwipeableOptions = {}): SwipeableResult {
  const [isSwiping, setIsSwiping] = useState(false)
  const [direction, setDirection] = useState<'left' | 'right' | 'up' | 'down' | null>(null)
  const startX = useRef(0)
  const startY = useRef(0)
  const currentX = useRef(0)
  const currentY = useRef(0)

  const handleTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0]?.clientX ?? 0
    startY.current = e.touches[0]?.clientY ?? 0
    currentX.current = startX.current
    currentY.current = startY.current
    setIsSwiping(true)
    setDirection(null)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isSwiping) return
    currentX.current = e.touches[0]?.clientX ?? 0
    currentY.current = e.touches[0]?.clientY ?? 0

    const deltaX = currentX.current - startX.current
    const deltaY = currentY.current - startY.current

    if (preventScrollOnSwipe && Math.abs(deltaX) > Math.abs(deltaY)) {
      e.preventDefault()
    }

    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      setDirection(deltaX > 0 ? 'right' : 'left')
    } else {
      setDirection(deltaY > 0 ? 'down' : 'up')
    }
  }

  const handleTouchEnd = () => {
    if (!isSwiping) return
    const deltaX = currentX.current - startX.current
    const deltaY = currentY.current - startY.current

    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > threshold) {
      if (deltaX > 0 && onSwipeRight) onSwipeRight()
      else if (deltaX < 0 && onSwipeLeft) onSwipeLeft()
    } else if (Math.abs(deltaY) > threshold) {
      if (deltaY > 0 && onSwipeDown) onSwipeDown()
      else if (deltaY < 0 && onSwipeUp) onSwipeUp()
    }

    setIsSwiping(false)
    setDirection(null)
  }

  return {
    handlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    },
    isSwiping,
    direction,
  }
}
