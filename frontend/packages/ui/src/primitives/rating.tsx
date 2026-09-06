import { cn } from '@eco/utils'
import { useState } from 'react'
import { Star } from './icon'

export type RatingProps = {
  value: number
  onChange?: (value: number) => void
  max?: number
  size?: number
  readonly?: boolean
  className?: string
}

export function Rating({
  value,
  onChange,
  max = 5,
  size = 20,
  readonly = false,
  className,
}: RatingProps) {
  const [hover, setHover] = useState(0)

  return (
    <div
      className={cn('inline-flex items-center gap-0.5', className)}
      role="radiogroup"
      aria-label="Rating"
    >
      {Array.from({ length: max }, (_, i) => i + 1).map((star) => {
        const filled = star <= (hover || value)
        return (
          <button
            key={star}
            type="button"
            role="radio"
            aria-checked={star === value}
            disabled={readonly}
            onClick={() => onChange?.(star)}
            onMouseEnter={() => !readonly && setHover(star)}
            onMouseLeave={() => !readonly && setHover(0)}
            className={cn('p-0 transition-colors', !readonly && 'cursor-pointer hover:scale-110')}
          >
            <Star
              size={size}
              className={cn(filled ? 'text-warning fill-warning' : 'text-ink-subtle')}
            />
          </button>
        )
      })}
    </div>
  )
}
