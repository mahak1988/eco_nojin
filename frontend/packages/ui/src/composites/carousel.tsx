import { cn } from '@eco/utils'
import { type ReactNode, useEffect, useId, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight } from '../primitives/icon'

export type CarouselProps = {
  children: ReactNode
  className?: string
  autoPlay?: boolean
  interval?: number
  loop?: boolean
  onSlideChange?: (index: number) => void
}

export type CarouselContentProps = {
  children: ReactNode
  className?: string
}

export type CarouselItemProps = {
  children: ReactNode
  className?: string
}

export type CarouselDotsProps = {
  count: number
  current: number
  onDotClick?: (index: number) => void
  className?: string
}

export type CarouselButtonProps = {
  onClick: () => void
  disabled?: boolean
  className?: string
  children?: ReactNode
}

const SLIDE_TRANSITION = 'transition-transform duration-300 ease-out-soft'

export function Carousel({
  children,
  className,
  autoPlay = false,
  interval = 4000,
  loop = true,
  onSlideChange,
}: CarouselProps) {
  const [current, setCurrent] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState(0)
  const [isHovered, setIsHovered] = useState(false)
  const [isFocused, setIsFocused] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const dragStartX = useRef(0)
  const generatedId = useId()
  const liveRegionId = `carousel-live-${generatedId}`
  const itemsRef = useRef<HTMLDivElement[]>([])

  const items = Array.isArray(children) ? children : [children]
  const count = items.length

  const goTo = (index: number) => {
    if (!loop && (index < 0 || index >= count)) return
    const next = loop ? ((index % count) + count) % count : Math.max(0, Math.min(index, count - 1))
    setCurrent(next)
    onSlideChange?.(next)
  }

  const goNext = () => goTo(current + 1)
  const goPrev = () => goTo(current - 1)

  useEffect(() => {
    if (!autoPlay || isHovered || isFocused || count <= 1) return
    const id = setInterval(goNext, interval)
    return () => clearInterval(id)
  }, [autoPlay, interval, isHovered, isFocused, count, goNext])

  const handlePointerDown = (e: React.PointerEvent) => {
    setIsDragging(true)
    dragStartX.current = e.clientX
    setDragOffset(0)
    ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return
    const delta = e.clientX - dragStartX.current
    setDragOffset(delta)
  }

  const handlePointerUp = (e: React.PointerEvent) => {
    if (!isDragging) return
    setIsDragging(false)
    const threshold = 50
    if (dragOffset > threshold) goPrev()
    else if (dragOffset < -threshold) goNext()
    setDragOffset(0)
    ;(e.target as HTMLElement).releasePointerCapture?.(e.pointerId)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault()
      goPrev()
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      goNext()
    }
  }

  const offset =
    -(current * 100) +
    (isDragging ? (dragOffset / (containerRef.current?.clientWidth ?? 1)) * 100 : 0)

  return (
    <div
      ref={containerRef}
      className={cn('relative overflow-hidden rounded-lg', className)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="region"
      aria-roledescription="carousel"
      aria-label="Carousel"
    >
      <div
        className={cn('flex', SLIDE_TRANSITION)}
        style={{ transform: `translateX(${offset}%)` }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={() => {
          setIsDragging(false)
          setDragOffset(0)
        }}
      >
        {items.map((item, index) => (
          <div
            key={index}
            ref={(el) => {
              if (el) itemsRef.current[index] = el
            }}
            className="w-full shrink-0"
            role="group"
            aria-roledescription="slide"
            aria-label={`Slide ${index + 1} of ${count}`}
            aria-hidden={index !== current}
          >
            {item}
          </div>
        ))}
      </div>

      {count > 1 && (
        <>
          <CarouselPrevious
            onClick={goPrev}
            disabled={!loop && current === 0}
            className="absolute inset-y-0 start-0 z-10 flex items-center"
          />
          <CarouselNext
            onClick={goNext}
            disabled={!loop && current === count - 1}
            className="absolute inset-y-0 end-0 z-10 flex items-center"
          />
        </>
      )}

      {count > 1 && <CarouselDots count={count} current={current} onDotClick={goTo} />}

      <div id={liveRegionId} className="sr-only" aria-live="polite" aria-atomic="true">
        Slide {current + 1} of {count}
      </div>
    </div>
  )
}

export function CarouselContent({ children, className }: CarouselContentProps) {
  return <div className={cn('flex', className)}>{children}</div>
}

export function CarouselItem({ children, className }: CarouselItemProps) {
  return <div className={cn('w-full shrink-0', className)}>{children}</div>
}

export function CarouselDots({ count, current, onDotClick, className }: CarouselDotsProps) {
  return (
    <div
      className={cn(
        'absolute inset-x-0 bottom-4 flex items-center justify-center gap-1.5',
        className,
      )}
      role="tablist"
      aria-label="Slide indicators"
    >
      {Array.from({ length: count }, (_, i) => (
        <button
          key={i}
          type="button"
          role="tab"
          aria-selected={i === current}
          aria-label={`Go to slide ${i + 1}`}
          onClick={() => onDotClick?.(i)}
          className={cn(
            'h-2 rounded-full transition-all duration-200',
            i === current ? 'w-6 bg-brand-600' : 'w-2 bg-white/60 hover:bg-white/80',
          )}
        />
      ))}
    </div>
  )
}

export function CarouselPrevious({ onClick, disabled, className, children }: CarouselButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label="Previous slide"
      className={cn('absolute inset-y-0 start-0 z-10 flex items-center', className)}
    >
      <span
        className="grid h-8 w-8 place-items-center rounded-full bg-white/80 shadow-md backdrop-blur hover:bg-white"
        aria-hidden="true"
      >
        {children ?? <ChevronRight size={18} />}
      </span>
    </button>
  )
}

export function CarouselNext({ onClick, disabled, className, children }: CarouselButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label="Next slide"
      className={cn('absolute inset-y-0 end-0 z-10 flex items-center', className)}
    >
      <span
        className="grid h-8 w-8 place-items-center rounded-full bg-white/80 shadow-md backdrop-blur hover:bg-white"
        aria-hidden="true"
      >
        {children ?? <ChevronLeft size={18} />}
      </span>
    </button>
  )
}
