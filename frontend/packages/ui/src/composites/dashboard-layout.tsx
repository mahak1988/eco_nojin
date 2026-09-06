import { cn } from '@eco/utils'
import type { ReactNode } from 'react'

export type DashboardLayoutProps = {
  sidebar: ReactNode
  header: ReactNode
  children: ReactNode
  footer?: ReactNode
  className?: string
}

export function DashboardLayout({
  sidebar,
  header,
  children,
  footer,
  className,
}: DashboardLayoutProps) {
  return (
    <div className={cn('min-h-screen bg-surface text-ink', className)}>
      <div className="flex">
        <aside className="hidden md:flex md:w-64 md:flex-col md:border-e md:border-ink/10 md:bg-surface-inverse md:text-ink-inverse md:fixed md:inset-y-0 md:start-0 md:z-20">
          {sidebar}
        </aside>
        <div className="flex-1 md:ms-64">
          <header className="sticky top-0 z-10 border-b border-ink/10 bg-surface/85 backdrop-blur-xl">
            {header}
          </header>
          <main className="p-4 md:p-8">{children}</main>
          {footer && (
            <footer className="border-t border-ink/10 bg-surface-muted/40 px-4 py-6 text-xs text-ink-muted">
              {footer}
            </footer>
          )}
        </div>
      </div>
    </div>
  )
}
