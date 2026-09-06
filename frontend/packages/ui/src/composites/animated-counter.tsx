import { cn } from '@eco/utils'
import { useEffect, useRef, useState } from 'react'

export type AnimatedCounterProps = {
  from: number
  to: number
  duration?: number
  className?: string
  formatter?: (value: number) => string
}

export function AnimatedCounter({
  from,
  to,
  duration = 1000,
  className,
  formatter,
}: AnimatedCounterProps) {
  const [value, setValue] = useState(from)
  const raf = useRef<number | NodeJS.Timeout>(0)

  useEffect(() => {
    const startTime = typeof performance !== 'undefined' ? performance.now() : Date.now()
    const step = (_now: number) => {
      const currentTime = typeof performance !== 'undefined' ? performance.now() : Date.now()
      const progress = Math.min(1, (currentTime - startTime) / duration)
      const current = from + (to - from) * easeOut(progress)
      setValue(current)
      if (progress < 1) {
        raf.current =
          typeof requestAnimationFrame !== 'undefined'
            ? requestAnimationFrame(step)
            : (setTimeout(() => step(Date.now()), 16) as unknown as number)
      }
    }
    raf.current =
      typeof requestAnimationFrame !== 'undefined'
        ? requestAnimationFrame(step)
        : (setTimeout(() => step(Date.now()), 16) as unknown as number)
    return () => {
      if (typeof cancelAnimationFrame !== 'undefined') cancelAnimationFrame(raf.current as number)
      else clearTimeout(raf.current as NodeJS.Timeout)
    }
  }, [from, to, duration])

  const display = formatter ? formatter(value) : Math.round(value).toLocaleString('fa-IR')

  return <span className={cn('tabular-nums', className)}>{display}</span>
}

function easeOut(t: number) {
  return 1 - (1 - t) ** 3
}
