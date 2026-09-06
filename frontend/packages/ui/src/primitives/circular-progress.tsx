import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type CircularProgressProps = HTMLAttributes<HTMLDivElement> & {
  value?: number
  size?: number
  strokeWidth?: number
  label?: string
}

export function CircularProgress({
  value = 0,
  size = 80,
  strokeWidth = 6,
  label,
  className,
  ...rest
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.min(100, Math.max(0, value)) / 100) * circumference
  const center = size / 2

  return (
    <div
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cn('relative inline-flex items-center justify-center', className)}
      style={{ width: size, height: size }}
      {...rest}
    >
      <svg width={size} height={size} className="rotate-[-90deg]">
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-ink/10"
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="text-brand-600 transition-all duration-300 ease-out"
        />
      </svg>
      {(label || value !== undefined) && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-semibold text-ink">{label ?? `${Math.round(value)}٪`}</span>
        </div>
      )}
    </div>
  )
}
