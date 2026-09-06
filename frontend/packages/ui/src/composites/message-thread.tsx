import { cn } from '@eco/utils'
import type { ReactNode } from 'react'
import { ChatBubble } from './chat-bubble'

export type MessageThreadProps = {
  messages: {
    id: string
    content: ReactNode
    time: string
    sender: 'user' | 'other'
    avatar?: ReactNode
  }[]
  className?: string
}

export function MessageThread({ messages, className }: MessageThreadProps) {
  return (
    <div className={cn('flex flex-col gap-3', className)}>
      {messages.map((msg) => (
        <ChatBubble
          key={msg.id}
          content={msg.content}
          time={msg.time}
          sender={msg.sender}
          avatar={msg.avatar}
        />
      ))}
    </div>
  )
}
