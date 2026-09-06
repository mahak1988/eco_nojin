import { cn } from '@eco/utils'
import { type ReactNode, useState } from 'react'

export type RippleEffectProps = {
  children: ReactNode
  className?: string
}

export function RippleEffect({ children, className }: RippleEffectProps) {
  const [ripples, setRipples] = useState<{ id: number; x: number; y: number }[]>([])

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const id = Date.now()
    setRipples((r) => [...r, { id, x: e.clientX - rect.left, y: e.clientY - rect.top }])
    setTimeout(() => setRipples((r) => r.filter((rp) => rp.id !== id)), 600)
  }

  return (
    <div onClick={handleClick} className={cn('relative overflow-hidden', className)}>
      {children}
      {ripples.map((r) => (
        <span
          key={r.id}
          className="pointer-events-none absolute h-24 w-24 -translate-x-1/2 -translate-y-1/2 animate-ripple rounded-full bg-ink/10"
          style={{ left: r.x, top: r.y }}
        />
      ))}
    </div>
  )
}
