import { cn } from '@eco/utils'
import * as RT from '@radix-ui/react-tabs'
import { forwardRef } from 'react'

export type TabsProps = RT.TabsProps

export const Tabs = RT.Root

export const TabsList = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RT.TabsList>
>(function TabsList({ className, ...rest }, ref) {
  return (
    <RT.TabsList
      ref={ref}
      className={cn(
        'inline-flex h-10 items-center gap-1 rounded-md bg-surface-muted p-1 text-ink-muted',
        className,
      )}
      {...rest}
    />
  )
})

export const TabsTrigger = forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<typeof RT.TabsTrigger>
>(function TabsTrigger({ className, ...rest }, ref) {
  return (
    <RT.TabsTrigger
      ref={ref}
      className={cn(
        'inline-flex h-8 items-center justify-center rounded px-3 text-sm font-medium',
        'data-[state=active]:bg-surface-raised data-[state=active]:text-ink data-[state=active]:shadow-soft',
        'focus-visible:outline-none focus-visible:shadow-glow',
        className,
      )}
      {...rest}
    />
  )
})

export const TabsContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RT.TabsContent>
>(function TabsContent({ className, ...rest }, ref) {
  return <RT.TabsContent ref={ref} className={cn('mt-4', className)} {...rest} />
})
