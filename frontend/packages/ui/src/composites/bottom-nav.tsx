import { cn } from '@eco/utils'
import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

export type BottomNavItem = {
  label: string
  to: string
  icon: ReactNode
  badge?: number
}

export type BottomNavProps = {
  items: BottomNavItem[]
  className?: string
}

export function BottomNav({ items, className }: BottomNavProps) {
  return (
    <nav
      className={cn(
        'fixed inset-x-0 bottom-0 z-30 border-t border-ink/10 bg-surface/90 backdrop-blur-xl md:hidden',
        className,
      )}
      aria-label="ناوبری پایین"
    >
      <div className="mx-auto flex max-w-content items-center justify-around px-2">
        {items.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className="relative flex flex-1 flex-col items-center gap-0.5 py-2 text-ink-muted"
            activeProps={{ className: 'text-brand-700' }}
          >
            <span className="relative">
              <span aria-hidden="true" className="text-lg">
                {item.icon}
              </span>
              {item.badge != null && item.badge > 0 && (
                <span className="absolute -top-1 -end-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[9px] font-bold text-white">
                  {item.badge}
                </span>
              )}
            </span>
            <span className="text-[10px] font-medium">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  )
}
