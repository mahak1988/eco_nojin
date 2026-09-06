import type { ReactNode } from 'react'
import { Icon, type IconName } from '../primitives/icon'
import { Skeleton } from '../primitives/skeleton'
import { tokenToTextClass } from '../tokens'

export interface StatCard3DProps {
  title?: string
  label?: string
  value: number | string
  icon?: ReactNode | string
  color?: string
  suffix?: string
  trend?: { value: number; direction: 'up' | 'down' }
  loading?: boolean
  index?: number
}

const isIconName = (v: string): v is IconName =>
  (
    [
      'leaf',
      'droplet',
      'sun',
      'cloud',
      'satellite',
      'coin',
      'chart',
      'sparkles',
      'shield',
      'bolt',
      'map',
      'database',
      'cpu',
      'flask',
      'waves',
      'gauge',
      'bell',
      'search',
      'globe',
      'mountain',
      'sprout',
      'check',
      'x',
      'menu',
      'arrow',
      'settings',
      'user',
    ] as string[]
  ).includes(v)

export function StatCard3D({
  title,
  label,
  value,
  icon,
  color = '#16a34a',
  suffix,
  trend,
  loading,
  index = 0,
}: StatCard3DProps) {
  const displayTitle = title ?? label ?? ''
  if (loading) return <Skeleton className="h-28" />

  return (
    <div
      className="glass card-3d gradient-border rounded-2xl p-5 animate-fade-up"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink-muted">{displayTitle}</p>
          <p className="mt-1.5 text-3xl font-extrabold tracking-tight" style={{ color }}>
            {typeof value === 'number' ? value.toLocaleString('fa-IR') : value}
            {suffix && <span className="ms-1 text-sm font-medium text-ink-subtle">{suffix}</span>}
          </p>
          {trend && (
            <p
              className={`mt-1 text-xs font-semibold ${trend.direction === 'up' ? tokenToTextClass('success') : tokenToTextClass('danger')}`}
            >
              {trend.direction === 'up' ? '▲' : '▼'} {Math.abs(trend.value)}٪
            </p>
          )}
        </div>

        <div
          className="icon-tile shrink-0 animate-float"
          style={{ background: `linear-gradient(135deg, ${color}d9, ${color})` }}
        >
          {typeof icon === 'string' && isIconName(icon) ? (
            <Icon name={icon} size={22} />
          ) : (
            <span className="text-xl" aria-hidden="true">
              {icon ?? '📊'}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
