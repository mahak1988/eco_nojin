import { cn } from '@eco/utils'
import { Link } from '@tanstack/react-router'
import type { HTMLAttributes, ReactNode } from 'react'
import { ChevronRight } from './icon'

export type BreadcrumbItem = {
  label: ReactNode
  href?: string
  current?: boolean
}

export type BreadcrumbProps = HTMLAttributes<HTMLElement> & {
  items: BreadcrumbItem[]
}

export function Breadcrumb({ items, className, ...rest }: BreadcrumbProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center gap-1 text-sm', className)}
      {...rest}
    >
      <ol className="flex items-center gap-1">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-1">
            {index > 0 && (
              <span className="text-ink-subtle" aria-hidden="true">
                <ChevronRight size={14} />
              </span>
            )}
            {item.href && !item.current ? (
              <Link to={item.href} className="text-ink-muted hover:text-ink transition-colors">
                {item.label}
              </Link>
            ) : (
              <span
                className={cn('font-medium', item.current ? 'text-ink' : 'text-ink-muted')}
                aria-current={item.current ? 'page' : undefined}
              >
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
