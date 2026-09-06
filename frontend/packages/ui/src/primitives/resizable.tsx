import { cn } from '@eco/utils'
import { forwardRef, useState } from 'react'
import type { HTMLAttributes } from 'react'

export type ResizablePanelGroupProps = HTMLAttributes<HTMLDivElement> & {
  direction?: 'horizontal' | 'vertical'
}

export const ResizablePanelGroup = forwardRef<HTMLDivElement, ResizablePanelGroupProps>(
  function ResizablePanelGroup({ className, direction = 'horizontal', children, ...rest }, ref) {
    return (
      <div
        ref={ref}
        className={cn('flex', direction === 'horizontal' ? 'flex-row' : 'flex-col', className)}
        {...rest}
      >
        {children}
      </div>
    )
  },
)

export type ResizablePanelProps = HTMLAttributes<HTMLDivElement> & {
  defaultSize?: number
  minSize?: number
  maxSize?: number
}

export const ResizablePanel = forwardRef<HTMLDivElement, ResizablePanelProps>(
  function ResizablePanel(
    { className, defaultSize = 50, minSize = 10, maxSize = 90, children, ...rest },
    ref,
  ) {
    const [size, setSize] = useState(defaultSize)
    return (
      <div
        ref={ref}
        className={cn('overflow-hidden', className)}
        style={{ flexBasis: `${size}%`, minWidth: `${minSize}%`, maxWidth: `${maxSize}%` }}
        {...rest}
      >
        {children}
      </div>
    )
  },
)

export type ResizableHandleProps = HTMLAttributes<HTMLDivElement> & {
  onResize?: (delta: number) => void
}

export const ResizableHandle = forwardRef<HTMLDivElement, ResizableHandleProps>(
  function ResizableHandle({ className, onResize, ...rest }, ref) {
    return (
      <div
        ref={ref}
        className={cn(
          'group relative flex items-center justify-center bg-ink/5 transition-colors hover:bg-brand-500/20',
          'w-1 cursor-col-resize',
          className,
        )}
        {...rest}
      >
        <div className="h-8 w-1 rounded-full bg-ink/10 group-hover:bg-brand-500" />
      </div>
    )
  },
)
