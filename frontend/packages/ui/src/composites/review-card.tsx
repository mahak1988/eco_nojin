import { cn } from '@eco/utils'
import { Card, CardBody } from '../primitives'
import { Rating } from '../primitives'
import { Avatar } from '../primitives'

export type ReviewCardProps = {
  author: string
  avatar?: string
  rating: number
  date: string
  content: string
  helpful?: number
  className?: string
}

export function ReviewCard({
  author,
  avatar,
  rating,
  date,
  content,
  helpful,
  className,
}: ReviewCardProps) {
  return (
    <Card className={cn('flex flex-col gap-3', className)}>
      <CardBody className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Avatar name={author} src={avatar} size="sm" />
            <div>
              <p className="text-sm font-medium text-ink">{author}</p>
              <p className="text-xs text-ink-subtle">{date}</p>
            </div>
          </div>
          <Rating value={rating} readonly size={14} />
        </div>
        <p className="text-sm text-ink-muted leading-relaxed">{content}</p>
        {helpful != null && (
          <p className="text-xs text-ink-subtle">
            {helpful.toLocaleString('fa-IR')} نفر این بررسی را مفید یافتند
          </p>
        )}
      </CardBody>
    </Card>
  )
}
