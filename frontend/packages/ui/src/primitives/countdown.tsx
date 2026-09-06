import { cn } from '@eco/utils'
import { useEffect, useMemo, useState } from 'react'

export type CountdownProps = {
  target: Date | number | string
  onComplete?: () => void
  className?: string
}

function getTimeRemaining(target: number) {
  const total = Math.max(0, target - (typeof window !== 'undefined' ? Date.now() : 0))
  const seconds = Math.floor((total / 1000) % 60)
  const minutes = Math.floor((total / 1000 / 60) % 60)
  const hours = Math.floor((total / (1000 * 60 * 60)) % 24)
  const days = Math.floor(total / (1000 * 60 * 60 * 24))
  return { total, days, hours, minutes, seconds }
}

export function Countdown({ target, onComplete, className }: CountdownProps) {
  const targetTime = useMemo(() => {
    if (target instanceof Date) return target.getTime()
    if (typeof target === 'number') return target
    return new Date(target).getTime()
  }, [target])

  const [timeLeft, setTimeLeft] = useState(() => getTimeRemaining(targetTime))

  useEffect(() => {
    const timer = setInterval(() => {
      const next = getTimeRemaining(targetTime)
      setTimeLeft(next)
      if (next.total <= 0) {
        clearInterval(timer)
        onComplete?.()
      }
    }, 1000)
    return () => clearInterval(timer)
  }, [targetTime, onComplete])

  if (timeLeft.total <= 0) {
    return <div className={cn('text-sm font-medium text-ink-muted', className)}>تکمیل شد</div>
  }

  const pad = (n: number) => String(n).padStart(2, '0')

  return (
    <div
      className={cn('inline-flex items-center gap-2 text-sm font-medium tabular-nums', className)}
    >
      {timeLeft.days > 0 && (
        <>
          <span className="rounded-md bg-surface-muted px-2 py-1">{pad(timeLeft.days)}</span>
          <span className="text-ink-subtle">:</span>
        </>
      )}
      <span className="rounded-md bg-surface-muted px-2 py-1">{pad(timeLeft.hours)}</span>
      <span className="text-ink-subtle">:</span>
      <span className="rounded-md bg-surface-muted px-2 py-1">{pad(timeLeft.minutes)}</span>
      <span className="text-ink-subtle">:</span>
      <span className="rounded-md bg-brand-50 px-2 py-1 text-brand-700">
        {pad(timeLeft.seconds)}
      </span>
    </div>
  )
}
