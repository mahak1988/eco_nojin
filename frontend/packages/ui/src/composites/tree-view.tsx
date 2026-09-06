import { cn } from '@eco/utils'
import { type ReactNode, useState } from 'react'
import { Card, CardBody } from '../primitives'

export type TreeNode = {
  id: string
  label: string
  icon?: ReactNode
  children?: TreeNode[]
}

export type TreeViewProps = {
  data: TreeNode[]
  onSelect?: (node: TreeNode) => void
  className?: string
}

export function TreeView({ data, onSelect, className }: TreeViewProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const renderNode = (node: TreeNode, depth = 0) => {
    const hasChildren = node.children && node.children.length > 0
    const isExpanded = expanded.has(node.id)

    return (
      <div key={node.id}>
        <button
          type="button"
          onClick={() => {
            if (hasChildren) toggle(node.id)
            onSelect?.(node)
          }}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-ink',
            'hover:bg-surface-muted focus:outline-none focus:shadow-glow',
          )}
          style={{ paddingRight: depth * 16 + 8 }}
        >
          {hasChildren ? (
            <span className="text-ink-subtle">{isExpanded ? '▼' : '▶'}</span>
          ) : (
            <span className="w-3" />
          )}
          {node.icon && <span className="text-ink-subtle">{node.icon}</span>}
          <span className="truncate">{node.label}</span>
        </button>
        {hasChildren && isExpanded && (
            <div>{node.children?.map((child) => renderNode(child, depth + 1))}</div>
        )}
      </div>
    )
  }

  return (
    <Card className={cn('p-2', className)}>
      <CardBody className="p-0">
        <div className="flex flex-col gap-0.5">{data.map((node) => renderNode(node))}</div>
      </CardBody>
    </Card>
  )
}
