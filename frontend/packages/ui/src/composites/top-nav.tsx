import { cn } from '@eco/utils'
import type { ReactNode } from 'react'
import { Button } from '../primitives'
import { Bell, Search } from '../primitives/icon'

export type TopNavProps = {
  brand?: ReactNode
  items?: { label: string; href?: string; onClick?: () => void }[]
  actions?: ReactNode
  className?: string
}

export function TopNav({ brand, items, actions, className }: TopNavProps) {
  return (
    <header
      className={cn(
        'sticky top-0 z-10 border-b border-ink/10 bg-surface/85 backdrop-blur-xl',
        className,
      )}
    >
      <div className="mx-auto flex h-14 max-w-content items-center gap-3 px-4 md:px-8">
        <div className="flex items-center gap-2">{brand}</div>
        <nav aria-label="ناوبری اصلی" className="hidden items-center gap-1 md:flex">
          {items?.map((item) => (
            <a
              key={item.label}
              href={item.href ?? '#'}
              onClick={item.onClick}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-ink-muted hover:bg-surface-muted hover:text-ink"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="ms-auto flex items-center gap-2">
          {actions}
          <Button variant="ghost" size="sm" icon={<Search size={16} />} aria-label="جستجو" />
          <Button variant="ghost" size="sm" icon={<Bell size={16} />} aria-label="اعلان‌ها">
            <span className="sr-only">اعلان‌ها</span>
          </Button>
        </div>
      </div>
    </header>
  )
}
