/**
 * Generic helpers for displaying structured motor output dictionaries.
 */
import type { ReactNode } from 'react'
import { Badge, Card, CardBody, CardHeader, Skeleton } from '../primitives'
import { type SemanticToken, tokenToBgClass, tokenToTextClass } from '../tokens'

export function ResultCard({
  title,
  subtitle,
  children,
  badge,
  statusTone,
}: {
  title: string
  subtitle?: string
  children: ReactNode
  badge?: { tone: 'success' | 'warning' | 'danger' | 'info'; label: string }
  statusTone?: SemanticToken
}) {
  const statusClasses = statusTone ? `border-s-4 border-s-${statusTone}-500` : ''
  return (
    <Card className={statusClasses}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold">{title}</h3>
          {badge && (
            <Badge
              tone={badge.tone}
              variant="soft"
              className={statusTone ? tokenToBgClass(statusTone, 100) : undefined}
            >
              {badge.label}
            </Badge>
          )}
        </div>
        {subtitle && <p className="text-xs text-ink-muted">{subtitle}</p>}
      </CardHeader>
      <CardBody>{children}</CardBody>
    </Card>
  )
}

export function KVGrid({
  data,
  statusColumn,
}: {
  data: Record<string, unknown>
  statusColumn?: string
}) {
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined && v !== '')
  if (entries.length === 0) {
    return <p className="text-sm text-ink-muted">No values reported.</p>
  }
  return (
    <div className="grid gap-2 md:grid-cols-2">
      {entries.map(([k, v]) => {
        const isStatus = statusColumn && k === statusColumn
        const token = isStatus ? (String(v) as SemanticToken) : null
        const textClass = token ? tokenToTextClass(token) : 'text-ink'
        return (
          <div key={k} className="rounded bg-surface-muted p-3 text-sm">
            <div className="text-[10px] uppercase tracking-wide text-ink-muted">{k}</div>
            <div className={`font-mono text-sm ${textClass}`}>
              {typeof v === 'number'
                ? v.toLocaleString('en-US', { maximumFractionDigits: 4 })
                : typeof v === 'object'
                  ? JSON.stringify(v)
                  : String(v)}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function RunResultView({
  data,
  loading,
  error,
}: {
  data: unknown
  loading?: boolean
  error?: Error | null
}) {
  if (loading) return <Skeleton className="h-32" />
  if (error) return <p className="text-sm text-danger">{error.message}</p>
  if (!data) return <p className="text-sm text-ink-muted">Run the model to see results.</p>
  if (typeof data !== 'object')
    return <pre className="overflow-auto text-[11px]">{String(data)}</pre>
  return <KVGrid data={data as Record<string, unknown>} />
}

export type ResultCardProps = {
  title: string
  subtitle?: string
  children: ReactNode
  badge?: { tone: 'success' | 'warning' | 'danger' | 'info'; label: string }
  statusTone?: SemanticToken
}

export type KVGridProps = {
  data: Record<string, unknown>
  statusColumn?: string
}

export type RunResultViewProps = {
  data: unknown
  loading?: boolean
  error?: Error | null
}
