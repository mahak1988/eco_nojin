import { cn } from '@eco/utils'
import type { ReactNode } from 'react'
import { Card, CardBody, CardFooter } from '../primitives'
import { Badge, Button } from '../primitives'

export type ProductCardProps = {
  title: string
  price: number
  originalPrice?: number
  image?: ReactNode
  badge?: {
    label: string
    tone?: 'success' | 'warning' | 'danger' | 'info' | 'brand' | 'sky' | 'leaf'
  }
  rating?: number
  onAddToCart?: () => void
  className?: string
}

export function ProductCard({
  title,
  price,
  originalPrice,
  image,
  badge,
  rating,
  onAddToCart,
  className,
}: ProductCardProps) {
  return (
    <Card interactive className={cn('flex flex-col', className)}>
      <CardBody className="flex flex-col gap-3">
        <div className="aspect-square overflow-hidden rounded-lg bg-surface-muted">
          {image ?? (
            <div className="flex h-full items-center justify-center text-ink-subtle">📦</div>
          )}
        </div>
        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-semibold text-ink line-clamp-2">{title}</h3>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-brand-700">
              {price.toLocaleString('fa-IR')} تومان
            </span>
            {originalPrice && (
              <span className="text-xs text-ink-subtle line-through">
                {originalPrice.toLocaleString('fa-IR')}
              </span>
            )}
          </div>
          {badge && (
            <Badge tone={badge.tone ?? 'brand'} variant="soft">
              {badge.label}
            </Badge>
          )}
          {rating != null && (
            <div className="flex items-center gap-1 text-xs text-ink-muted">
              <span>⭐</span>
              <span className="font-medium text-ink">{rating.toFixed(1)}</span>
            </div>
          )}
        </div>
      </CardBody>
      <CardFooter>
        <Button fullWidth onClick={onAddToCart}>
          افزودن به سبد
        </Button>
      </CardFooter>
    </Card>
  )
}
