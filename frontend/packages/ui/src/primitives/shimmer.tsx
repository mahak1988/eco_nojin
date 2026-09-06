import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type ShimmerProps = HTMLAttributes<HTMLDivElement> & {
  width?: string | number
  height?: string | number
}

export function Shimmer({ width = '100%', height = 16, className, ...rest }: ShimmerProps) {
  return (
    <div
      className={cn('overflow-hidden rounded bg-ink/5', className)}
      style={{ width, height }}
      {...rest}
    >
      <div
        className="h-full w-full"
        style={{
          background:
            'linear-gradient(90deg, transparent 0%, rgb(255 255 255 / 0.4) 50%, transparent 100%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 2s linear infinite',
        }}
      />
    </div>
  )
}
