import { cn } from '@eco/utils'
import * as RN from '@radix-ui/react-navigation-menu'
import { forwardRef } from 'react'
import { ChevronDown } from './icon'

export const NavigationMenu = RN.Root
export const NavigationMenuList = RN.List
export const NavigationMenuItem = RN.Item

export const NavigationMenuTrigger = forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<typeof RN.Trigger>
>(function NavigationMenuTrigger({ className, children, ...rest }, ref) {
  return (
    <RN.Trigger
      ref={ref}
      className={cn(
        'group inline-flex h-10 items-center justify-center rounded-md px-4 text-sm font-medium text-ink',
        'hover:bg-surface-muted focus:outline-none focus:shadow-glow',
        className,
      )}
      {...rest}
    >
      {children}
      <ChevronDown
        size={14}
        className="ms-1 text-ink-subtle transition-transform group-data-[state=open]:rotate-180"
      />
    </RN.Trigger>
  )
})

export const NavigationMenuContent = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RN.Content>
>(function NavigationMenuContent({ className, ...rest }, ref) {
  return (
    <RN.Content
      ref={ref}
      className={cn(
        'absolute top-full z-50 mt-2 rounded-md border border-ink/10 bg-surface-raised p-3 shadow-raised',
        'data-[motion=from-start]:animate-slide-in-left data-[motion=from-end]:animate-slide-in-right',
        className,
      )}
      {...rest}
    />
  )
})

export const NavigationMenuLink = forwardRef<
  HTMLAnchorElement,
  React.ComponentPropsWithoutRef<typeof RN.Link>
>(function NavigationMenuLink({ className, ...rest }, ref) {
  return (
    <RN.Link
      ref={ref}
      className={cn(
        'flex flex-col gap-1 rounded-md p-2 text-sm text-ink hover:bg-surface-muted focus:outline-none focus:shadow-glow',
        className,
      )}
      {...rest}
    />
  )
})

export const NavigationMenuViewport = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof RN.Viewport>
>(function NavigationMenuViewport({ className, ...rest }, ref) {
  return (
    <div className="absolute top-full left-0 flex justify-center w-full">
      <RN.Viewport
        ref={ref}
        className={cn(
          'origin-top-center relative mt-2 h-[var(--radix-navigation-menu-viewport-height)] w-[var(--radix-navigation-menu-viewport-width)] overflow-hidden rounded-md border border-ink/10 bg-surface-raised shadow-raised',
          className,
        )}
        {...rest}
      />
    </div>
  )
})
