import { cn } from '@eco/utils'
import { useState } from 'react'

export type KanbanColumn = {
  id: string
  title: string
  items: { id: string; title: string; description?: string; assignee?: string }[]
}

export type KanbanBoardProps = {
  columns: KanbanColumn[]
  onMove?: (itemId: string, fromColumn: string, toColumn: string) => void
  className?: string
}

export function KanbanBoard({ columns, onMove, className }: KanbanBoardProps) {
  const [draggedItem, setDraggedItem] = useState<{ itemId: string; fromColumn: string } | null>(
    null,
  )

  const handleDragStart = (itemId: string, columnId: string) => {
    setDraggedItem({ itemId, fromColumn: columnId })
  }

  const handleDrop = (columnId: string) => {
    if (draggedItem && draggedItem.fromColumn !== columnId) {
      onMove?.(draggedItem.itemId, draggedItem.fromColumn, columnId)
    }
    setDraggedItem(null)
  }

  return (
    <div className={cn('flex gap-4 overflow-x-auto pb-4', className)}>
      {columns.map((column) => (
        <div
          key={column.id}
          onDragOver={(e) => e.preventDefault()}
          onDrop={() => handleDrop(column.id)}
          className="flex min-w-[280px] flex-col rounded-lg border border-ink/10 bg-surface-muted/50 p-3"
        >
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-ink">{column.title}</h3>
            <span className="rounded-full bg-ink/10 px-2 py-0.5 text-xs text-ink-muted">
              {column.items.length}
            </span>
          </div>
          <div className="flex flex-col gap-2">
            {column.items.map((item) => (
              <div
                key={item.id}
                draggable
                onDragStart={() => handleDragStart(item.id, column.id)}
                className="cursor-move rounded-md border border-ink/5 bg-surface-raised p-3 shadow-sm hover:shadow-md"
              >
                <p className="text-sm font-medium text-ink">{item.title}</p>
                {item.description && (
                  <p className="mt-1 text-xs text-ink-muted">{item.description}</p>
                )}
                {item.assignee && (
                  <div className="mt-2 flex items-center gap-1.5">
                    <div className="h-5 w-5 rounded-full bg-brand-100 text-[10px] font-medium text-brand-800 flex items-center justify-center">
                      {item.assignee[0]}
                    </div>
                    <span className="text-xs text-ink-muted">{item.assignee}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
