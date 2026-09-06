import { cn } from '@eco/utils'
import type { ReactNode } from 'react'

export type ChatBubbleProps = {
  content: ReactNode
  time?: string
  sender?: 'user' | 'other'
  avatar?: ReactNode
  className?: string
}

export function ChatBubble({
  content,
  time,
  sender = 'other',
  avatar,
  className,
}: ChatBubbleProps) {
  const isUser = sender === 'user'
  return (
    <div className={cn('flex gap-2', isUser && 'flex-row-reverse', className)}>
      {avatar && <div className="mt-auto">{avatar}</div>}
      <div className={cn('flex max-w-[75%] flex-col gap-1', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-2 text-sm',
            isUser
              ? 'rounded-br-md bg-brand-600 text-white'
              : 'rounded-bl-md bg-surface-muted text-ink',
          )}
        >
          {content}
        </div>
        {time && <span className="text-[10px] text-ink-subtle">{time}</span>}
      </div>
    </div>
  )
}
