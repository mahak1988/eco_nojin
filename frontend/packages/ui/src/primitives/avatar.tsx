import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'

export type AvatarProps = HTMLAttributes<HTMLSpanElement> & {
  name?: string
  src?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}

const SIZE = {
  xs: 'h-6 w-6 text-[10px]',
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-14 w-14 text-base',
  xl: 'h-20 w-20 text-xl',
} as const

function initials(name: string): string {
  const parts = name.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase() || '?'
}

export function Avatar({ name, src, size = 'md', className, ...rest }: AvatarProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center overflow-hidden rounded-full bg-brand-100 font-medium text-brand-800',
        SIZE[size],
        className,
      )}
      {...rest}
    >
      {src ? (
        <img src={src} alt={name ?? ''} className="h-full w-full object-cover" />
      ) : (
        <span aria-label={name}>{name ? initials(name) : '?'}</span>
      )}
    </span>
  )
}
