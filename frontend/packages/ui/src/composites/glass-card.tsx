import { clsx } from 'clsx'
import { type HTMLAttributes, forwardRef } from 'react'
import { twMerge } from 'tailwind-merge'

export interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  glow?: 'green' | 'water' | 'soil' | 'violet' | 'amber' | 'none'
  threeD?: boolean
  gradientBorder?: boolean
}

const glows = {
  green: 'glow-green',
  water: 'glow-water',
  soil: 'glow-soil',
  violet: 'glow-violet',
  amber: 'glow-amber',
  none: '',
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  (
    { className, glow = 'none', threeD = true, gradientBorder = false, children, ...props },
    ref,
  ) => (
    <div
      ref={ref}
      className={twMerge(
        clsx(
          'glass rounded-2xl p-5',
          threeD && 'card-3d',
          gradientBorder && 'gradient-border',
          glows[glow],
          className,
        ),
      )}
      {...props}
    >
      {children}
    </div>
  ),
)
GlassCard.displayName = 'GlassCard'
