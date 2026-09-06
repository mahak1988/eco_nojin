import { cn } from '@eco/utils'
import { Card, CardBody, CardFooter, CardHeader } from '../primitives'
import { Button } from '../primitives'

export type PricingCardProps = {
  name: string
  price: string
  period?: string
  description?: string
  features: string[]
  ctaLabel: string
  onCta?: () => void
  highlighted?: boolean
  className?: string
}

export function PricingCard({
  name,
  price,
  period,
  description,
  features,
  ctaLabel,
  onCta,
  highlighted,
  className,
}: PricingCardProps) {
  return (
    <Card className={cn('flex flex-col', highlighted && 'border-brand-400 shadow-glow', className)}>
      <CardHeader>
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold text-ink">{name}</h3>
          {description && <p className="text-sm text-ink-muted">{description}</p>}
        </div>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-extrabold tracking-tight text-ink">{price}</span>
          {period && <span className="text-sm text-ink-muted">/{period}</span>}
        </div>
        <ul className="flex flex-col gap-2 text-sm text-ink-muted">
          {features.map((f) => (
            <li key={f} className="flex items-center gap-2">
              <span className="text-success">✓</span>
              {f}
            </li>
          ))}
        </ul>
      </CardBody>
      <CardFooter>
        <Button fullWidth variant={highlighted ? 'primary' : 'secondary'} onClick={onCta}>
          {ctaLabel}
        </Button>
      </CardFooter>
    </Card>
  )
}
